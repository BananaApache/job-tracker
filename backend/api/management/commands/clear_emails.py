from django.core.management.base import BaseCommand

from api.models import User
from api.services.gmail_sync import wipe_emails_for_user


class Command(BaseCommand):
    help = "Clear all job emails for a specific user"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Email of the user whose job emails should be cleared")

    def handle(self, *args, **options):
        email = options.get("email")
        if not email:
            self.stdout.write(self.style.ERROR("Email argument is required."))
            return

        user = User.objects.filter(email=email).first()
        if not user:
            self.stdout.write(self.style.ERROR(f"No user found with email: {email}"))
            return

        count = wipe_emails_for_user(user)
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} job emails for user {email}"))
