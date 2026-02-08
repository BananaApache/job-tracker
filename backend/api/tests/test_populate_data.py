from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from api.models import JobEmail, User

# Create your tests here.


class PopulateDataCommandTest(TestCase):
    def setUp(self):
        self.test_email = "test@example.com"
        User.objects.create_user(email=self.test_email)

    @patch("api.services.gmail_service.fetch_emails_from_gmail")
    def test_populate_data_command(self, mock_fetch):
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
                        {"name": "From", "value": '"Chess.com" <hello@chess.com>'},
                        {"name": "Subject", "value": "Your 1 Day Streak is Paused!"},
                        {"name": "To", "value": "test@example.com"},
                    ],
                },
                "sizeEstimate": 68023,
                "historyId": "2102744",
                "internalDate": "1769916783000",
            }
        ]

        call_command("populate_data", email=self.test_email)

        test_user = User.objects.get(email=self.test_email)

        mock_fetch.assert_called_once_with(test_user, max_results=100)
        self.assertTrue(JobEmail.objects.exists())
        self.assertGreater(JobEmail.objects.count(), 0)

        job_email = JobEmail.objects.get(gmail_id="1")
        self.assertEqual(job_email.subject, "Your 1 Day Streak is Paused!")
        self.assertEqual(job_email.sender_email, "hello@chess.com")
