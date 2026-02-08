import json

from django.core.management.base import BaseCommand, CommandError

from api.models import User
from api.services.gmail_service import fetch_emails_from_gmail
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
        parser.add_argument("--maxResults", type=int, help="Maximum number of emails to fetch")
        parser.add_argument("--file", type=str, nargs="?", help="Path to JSON file with email data")

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
                emails = load_emails_from_file(file_path)
            except Exception as e:
                raise CommandError(f"Failed to load emails from file {file_path}: {e}") from e
        else:
            max_results = options.get("maxResults", 100)
            emails = fetch_emails_from_gmail(user, max_results=max_results)

        parsed_emails = parse_emails(emails)
        stats = populate_email_database(user, parsed_emails)

        self.stdout.write(
            self.style.SUCCESS(f"Database populated: {stats['created']} created, {stats['updated']} updated.")
        )
