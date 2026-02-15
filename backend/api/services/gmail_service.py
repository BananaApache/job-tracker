import json
import logging
import os.path
import time
from typing import Dict, List, Optional

from django.conf import settings
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from api.models import GoogleAuthToken, User

SCOPES = ["https://www.googleapis.com/auth/gmail.metadata"]
logger = logging.getLogger(__name__)


def get_creds(user: User) -> Credentials:
    auth_record = GoogleAuthToken.objects.filter(user=user).first()
    creds = None

    if auth_record:
        creds = Credentials.from_authorized_user_info(json.loads(auth_record.token_json), SCOPES)

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            auth_record.token_json = creds.to_json()
            auth_record.save()
        except RefreshError:
            auth_record.delete()
            creds = None

    if not creds or not creds.valid:
        client_config = get_client_config()
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")
        GoogleAuthToken.objects.update_or_create(user=user, defaults={"token_json": creds.to_json()})

    return creds


def get_client_config():
    path = getattr(settings, "GMAIL_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)

    project_id = getattr(settings, "GCP_PROJECT_ID", None)
    secret_id = getattr(settings, "GCP_CREDENTIALS_SECRET_ID", None)
    if project_id:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return json.loads(response.payload.data.decode("UTF-8"))

    raise FileNotFoundError("No client credentials found in JSON or GSM.")


def list_message_ids(user: User, max_results: int = 100, page_token: Optional[str] = None) -> Dict:
    """
    List message IDs from Gmail (lightweight operation).

    Args:
        user: User to fetch messages for
        max_results: Number of messages to fetch (max 500 per page)
        page_token: Token for pagination

    Returns:
        Dict with 'messages' list and optional 'nextPageToken'
    """
    creds = get_creds(user)
    service = build("gmail", "v1", credentials=creds)

    max_results = min(max_results, 500)

    params = {"userId": "me", "maxResults": max_results}
    if page_token:
        params["pageToken"] = page_token

    results = service.users().messages().list(**params).execute()
    return results


def _execute_batch_with_retry(service, message_ids: List[str]) -> tuple[List[Dict], List[str]]:
    """
    Execute a batch request with error handling.

    Args:
        service: Gmail API service
        message_ids: List of message IDs to fetch

    Returns:
        Tuple of (successful_responses, failed_message_ids)
    """
    batch = service.new_batch_http_request()
    batch_responses = []
    failed_message_ids = []

    def create_callback(msg_id):
        def callback(request_id, response, exception):
            if exception is not None:
                if isinstance(exception, HttpError) and exception.resp.status == 429:
                    failed_message_ids.append(msg_id)
                else:
                    logger.error(f"Batch request error for message {msg_id}: {exception}")
            else:
                batch_responses.append(response)

        return callback

    for msg_id in message_ids:
        batch.add(
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject", "From", "Date"]),
            callback=create_callback(msg_id),
        )

    batch.execute()

    return batch_responses, failed_message_ids


def fetch_message_details_batch(user: User, message_ids: List[str]) -> List[Dict]:
    """
    Fetch full message details for a list of message IDs using batch requests.

    Args:
        user: User to fetch messages for
        message_ids: List of Gmail message IDs

    Returns:
        List of message detail dictionaries
    """
    creds = get_creds(user)
    service = build("gmail", "v1", credentials=creds)

    all_messages = []
    batch_size = 50
    max_retries = 3

    for i in range(0, len(message_ids), batch_size):
        batch_ids = message_ids[i : i + batch_size]
        remaining_ids = batch_ids

        for attempt in range(max_retries):
            try:
                batch_results, failed_ids = _execute_batch_with_retry(service, remaining_ids)
                all_messages.extend(batch_results)

                if not failed_ids:
                    break

                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"{len(failed_ids)} requests hit rate limit, "
                        f"waiting {wait_time}s before retry {attempt + 2}/{max_retries}"
                    )
                    time.sleep(wait_time)
                    remaining_ids = failed_ids
                else:
                    logger.error(f"Failed to fetch {len(failed_ids)} messages after {max_retries} attempts")

            except HttpError as e:
                if e.resp.status != 429:
                    logger.error(f"Non-rate-limit error: {e}")
                    break
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Batch-level rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)

        if i + batch_size < len(message_ids):
            time.sleep(1)

    logger.info(f"Successfully fetched {len(all_messages)} out of {len(message_ids)} emails")
    return all_messages


def fetch_emails_from_gmail(user: User, max_results: int = 100) -> List[Dict]:
    """
    Fetch emails from Gmail with rate limiting and retry logic.
    Does NOT handle pagination, use fetch_total_emails for large counts.

    Args:
        user: User to fetch emails for
        max_results: Maximum number of emails to fetch (up to 500)

    Returns:
        List of email message dictionaries
    """
    try:
        results = list_message_ids(user, max_results=min(max_results, 500))
        messages = results.get("messages", [])

        if not messages:
            return []

        message_ids = [msg["id"] for msg in messages]
        return fetch_message_details_batch(user, message_ids)

    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return []


def fetch_total_emails(user: User, total_count: int, progress_callback: Optional[callable] = None) -> List[Dict]:
    """
    Fetch a specific total number of emails using pagination.

    Args:
        user: User to fetch emails for
        total_count: Total number of emails to fetch (e.g., 3000)
        progress_callback: Optional callback function called with (current, total)

    Returns:
        List of all fetched email dictionaries

    Example:
        def on_progress(current, total):
            print(f"Fetched {current}/{total} emails")
        emails = fetch_total_emails(user, 3000, on_progress)
    """
    all_message_ids = []
    page_token = None
    fetched_count = 0

    logger.info(f"Collecting message IDs for {total_count} emails...")

    while fetched_count < total_count:
        remaining = total_count - fetched_count
        batch_size = min(remaining, 500)

        try:
            results = list_message_ids(user, max_results=batch_size, page_token=page_token)
            messages = results.get("messages", [])

            if not messages:
                logger.info(f"No more messages available. Got {fetched_count} total.")
                break

            message_ids = [msg["id"] for msg in messages]
            all_message_ids.extend(message_ids)
            fetched_count += len(message_ids)

            if progress_callback:
                progress_callback(fetched_count, total_count)

            page_token = results.get("nextPageToken")
            if not page_token:
                logger.info(f"Reached end of mailbox. Got {fetched_count} total emails.")
                break

        except Exception as e:
            logger.error(f"Error fetching message IDs: {e}")
            break

    logger.info(f"Collected {len(all_message_ids)} message IDs. Now fetching details...")

    all_emails = fetch_message_details_batch(user, all_message_ids)

    return all_emails
