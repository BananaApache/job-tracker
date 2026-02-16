from unittest.mock import patch

from django.test import TestCase

from api.models import GoogleAuthToken, User
from api.services.gmail_service import fetch_emails_from_gmail, fetch_total_emails


class GmailServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        GoogleAuthToken.objects.create(user=self.user, token_json='{"token": "mock_access_token"}')

        self.mock_full_email = {
            "id": "1",
            "threadId": "1",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Date", "value": "Sun, 01 Feb 2026 03:33:03 +0000"},
                    {"name": "From", "value": '"Chess.com" <hello@chess.com>'},
                    {"name": "Subject", "value": "Your 1 Day Streak is Paused!"},
                ],
            },
            "internalDate": "1769916783000",
        }

    @patch("api.services.gmail_service.fetch_message_details_batch")
    @patch("api.services.gmail_service.list_message_ids")
    def test_fetch_emails_from_gmail_success(self, mock_list, mock_batch):
        mock_list.return_value = {"messages": [{"id": "1"}]}
        mock_batch.return_value = [self.mock_full_email]

        results = fetch_emails_from_gmail(self.user, max_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")
        self.assertIn("Chess.com", str(results[0]))

    @patch("api.services.gmail_service.fetch_message_details_batch")
    @patch("api.services.gmail_service.list_message_ids")
    def test_fetch_total_emails_pagination(self, mock_list, mock_batch):
        mock_list.side_effect = [
            {"messages": [{"id": "1"}], "nextPageToken": "page_2_token"},
            {"messages": [{"id": "2"}]},
        ]
        mock_batch.return_value = [self.mock_full_email, self.mock_full_email]

        results = fetch_total_emails(self.user, total_count=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(mock_list.call_count, 2)
