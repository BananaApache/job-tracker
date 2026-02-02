from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

# Create your tests here.


class PopulateDataCommandTest(TestCase):
    def setUp(self):
        from api.models import User

        self.test_email = "test@example.com"
        User.objects.create_user(email=self.test_email)

    @patch("api.management.commands.populate_data.fetch_emails_from_gmail")
    def test_populate_data_command(self, mock_fetch):
        from api.models import JobEmail

        mock_fetch.return_value = [
            {
                "id": "1",
                "threadId": "1",
                "labelIds": ["INBOX"],
                "payload": {
                    "partId": "",
                    "headers": [
                        {"name": "Delivered-To", "value": "test@example.com"},
                        {"name": "Content-Type", "value": "text/html; charset=utf-8"},
                        {"name": "Date", "value": "Sun, 01 Feb 2026 03:33:03 +0000 (UTC)"},
                        {"name": "From", "value": '"\u265fChess.com" <hello@chess.com>'},
                        {"name": "Subject", "value": "Your 1 Day Streak is Paused! \u23f8\ufe0f"},
                        {"name": "To", "value": "test@example.com"},
                    ],
                },
                "sizeEstimate": 68023,
                "historyId": "2102744",
                "internalDate": "1769916783000",
            }
        ]

        call_command("populate_data")

        self.assertTrue(JobEmail.objects.exists())
        self.assertGreater(JobEmail.objects.count(), 0)
