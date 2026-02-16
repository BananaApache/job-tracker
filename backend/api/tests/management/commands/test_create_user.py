from django.core.management import call_command
from django.test import TestCase

from api.models import User


class CreateTestUserCommandTest(TestCase):
    def test_create_test_user_command(self):
        call_command("create_user")

        test_email = "test@example.com"

        user_exists = User.objects.filter(email=test_email).exists()
        self.assertTrue(user_exists)
