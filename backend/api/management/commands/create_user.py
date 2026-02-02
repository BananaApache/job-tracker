from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a test user"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, nargs="?", help="Email of the test user to create")

    def handle(self, *args, **options):
        from api.models import User

        test_email = options["email"] if options["email"] else "test@example.com"

        if not User.objects.filter(email=test_email).exists():
            User.objects.create_user(email=test_email)
            self.stdout.write(self.style.SUCCESS(f"Successfully created test user: {test_email}"))
        else:
            self.stdout.write(self.style.WARNING(f"Test user {test_email} already exists"))
