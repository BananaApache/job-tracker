import json
import os.path
from email.utils import parseaddr, parsedate_to_datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_emails_from_file(file_path):
    with open(file_path, "r") as f:
        emails = json.load(f)
    return emails


def fetch_emails_from_gmail(max_results=100):
    SCOPES = ["https://www.googleapis.com/auth/gmail.metadata"]

    GMAIL_CREDENTIALS_PATH = getattr(settings, "GMAIL_CREDENTIALS_PATH", "credentials.json")
    GMAIL_TOKEN_PATH = getattr(settings, "GMAIL_TOKEN_PATH", "token.json")

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    "Error: Gmail credentials not found. Please create/place your credentials.json \
                    in the project root or set GMAIL_CREDENTIALS_PATH in your .env."
                )

            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
            # creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open(GMAIL_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=max_results).execute()
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
                    metadataHeaders=["Subject", "From", "Delivered-To", "Content-Type", "To", "Date"],
                )
                .execute()
            )
            all_messages.append(msg)

        return all_messages

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def parse_emails(emails):
    parsed_emails = []

    for email in emails:
        headers = email.get("payload", {}).get("headers", [])
        headers = {header["name"]: header["value"] for header in headers}  # should be O(6) always

        raw_from = headers.get("From", "")
        sender_name, sender_email = parseaddr(raw_from)

        received_at = parsedate_to_datetime(headers.get("Date", ""))
        if timezone.is_naive(received_at):
            received_at = timezone.make_aware(received_at)

        parsed_email = {
            "gmail_id": email.get("id"),
            "subject": headers.get("Subject", ""),
            "sender_email": sender_email,
            "sender_name": sender_name,
            "received_at": received_at,
            "content_type": headers.get("Content-Type", ""),
            "size_estimate": email.get("sizeEstimate", -1),
            "importance": 1,  # Default importance
            "labels": email.get("labelIds", ["INBOX"]),
        }

        parsed_emails.append(parsed_email)

    return parsed_emails


def populate_database(user, parsed_emails):
    from api.models import JobEmail, Label

    stats = {"created": 0, "updated": 0}

    for email_data in parsed_emails:
        label_names = email_data.pop("labels", [])

        email_obj, created = JobEmail.objects.update_or_create(
            gmail_id=email_data["gmail_id"], defaults={**email_data, "user": user}
        )

        if not created:
            for key, value in email_data.items():
                if key != "gmail_id":
                    setattr(email_obj, key, value)
            email_obj.save()

        if label_names:
            label_objs = [Label.objects.get_or_create(name=name)[0] for name in label_names]
            email_obj.labels.set(label_objs)

        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    return stats


class Command(BaseCommand):
    help = "Populate database once with gmail data"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, nargs="?", help="Path to JSON file with email data")

    def handle(self, *args, **options):
        from api.models import User

        if options["file"]:
            file_path = options["file"]
            emails = load_emails_from_file(file_path)
        else:
            emails = fetch_emails_from_gmail(max_results=100)

        user = User.objects.first()

        if not user:
            raise CommandError("User with email test@example.com does not exist.")

        parsed_emails = parse_emails(emails)
        stats = populate_database(user, parsed_emails)

        self.stdout.write(
            self.style.SUCCESS(f"Database populated: {stats['created']} created, {stats['updated']} updated.")
        )
