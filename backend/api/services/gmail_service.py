import json
import os.path

from django.conf import settings
from google.auth.transport.requests import Request
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from api.models import GoogleAuthToken, User

SCOPES = ["https://www.googleapis.com/auth/gmail.metadata"]


def get_creds(user: User) -> Credentials:
    auth_record = GoogleAuthToken.objects.filter(user=user).first()
    creds = None

    if auth_record:
        creds = Credentials.from_authorized_user_info(json.loads(auth_record.token_json), SCOPES)

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        auth_record.token_json = creds.to_json()
        auth_record.save()

    if not creds or not creds.valid:
        # try local file first but fallback to GSM
        client_config = get_client_config()
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        # creds = flow.run_local_server(port=8080)
        creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")

        # saves
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


def fetch_emails_from_gmail(user: User, max_results=100):
    creds = get_creds(user)

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=max_results).execute()

        messages = results.get("messages", [])
        if not messages:
            return []

        all_messages = []
        for message in messages:
            msg = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            all_messages.append(msg)

        return all_messages

    except HttpError as error:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Gmail API error: {error}")
        return []
