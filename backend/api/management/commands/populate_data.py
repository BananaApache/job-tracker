import json

from django.core.management.base import BaseCommand, CommandError

from api.models import User
from api.services.gmail_service import fetch_emails_from_gmail, fetch_total_emails
from api.services.gmail_sync import populate_email_database
from api.utils.parsers import parse_emails


def load_emails_from_file(file_path):
    with open(file_path, "r") as f:
        emails = json.load(f)
    return emails


class Command(BaseCommand):
    help = "Populate database with gmail data"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Email address to fetch emails for")
        parser.add_argument(
            "--maxResults",
            type=int,
            default=500,
            help="Maximum number of emails to fetch (supports pagination for large counts)",
        )
        parser.add_argument("--file", type=str, nargs="?", help="Path to JSON file with email data")
        parser.add_argument(
            "--inbox-only", action="store_true", help="Fetch only from INBOX, excluding promotions, social, etc."
        )
        parser.add_argument("--query", type=str, help='Custom Gmail search query (e.g., "from:example.com is:unread")')

    def handle(self, *args, **options):
        if options["email"] is not None:
            try:
                user = User.objects.get(email=options["email"])
                self.stdout.write(self.style.SUCCESS(f"Using user: {user.email}"))
            except User.DoesNotExist as e:
                raise CommandError(f"User with email {options['email']} does not exist.") from e
        else:
            raise CommandError("Please provide an email address using --email")

        if options["file"]:
            file_path = options["file"]
            try:
                self.stdout.write(f"Loading emails from file: {file_path}")
                emails = load_emails_from_file(file_path)
                self.stdout.write(self.style.SUCCESS(f"Loaded {len(emails)} emails from file"))
            except Exception as e:
                raise CommandError(f"Failed to load emails from file {file_path}: {e}") from e
        else:
            max_results = options["maxResults"]

            label_ids = None
            query = None

            if options["inbox_only"]:
                label_ids = ["INBOX"]
                query = "-category:promotions -category:social"

            if options["query"]:
                query = options["query"]

            if max_results <= 500:
                emails = fetch_emails_from_gmail(user, max_results=max_results, label_ids=label_ids, query=query)
            else:
                emails = fetch_total_emails(user, max_results, label_ids=label_ids, query=query)

        parsed_emails = parse_emails(emails)

        stats = populate_email_database(user, parsed_emails)

        self.stdout.write(
            self.style.SUCCESS(f"Database populated: {stats['created']} created, {stats['updated']} updated.")
        )
