import json
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase
from google.oauth2.credentials import Credentials

from api.models import GoogleAuthToken, User
from api.services.gmail_service import fetch_emails_from_gmail, fetch_total_emails


class GmailServiceTest(TestCase):
    # @ HELPERS AND SETUP STUFF
    def setUp(self):
        """Standardized setup for all Gmail service tests."""
        self.user = User.objects.create(email="test@example.com")
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
        self.mock_creds_data = {
            "token": "mock_token",
            "refresh_token": "mock_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.metadata"],
        }
        GoogleAuthToken.objects.create(user=self.user, token_json=json.dumps(self.mock_creds_data))

    def _create_mock_batch(self, messages_to_return):
        mock_batch = MagicMock()
        mock_batch._callbacks = []

        def add_request(req, callback):
            mock_batch._callbacks.append(callback)

        def execute_batch():
            for i, callback in enumerate(mock_batch._callbacks):
                # if we have enough mock messages, return them, else return a default
                msg = messages_to_return[i] if i < len(messages_to_return) else messages_to_return[0]
                callback(None, msg, None)

        mock_batch.add = add_request
        mock_batch.execute = execute_batch
        return mock_batch

    # @ TESTS FOR FETCH_EMAILS_FROM_GMAIL

    @patch("api.services.gmail_service.fetch_message_details_batch")
    @patch("api.services.gmail_service.list_message_ids")
    def test_fetch_emails_from_gmail_success(self, mock_list, mock_batch):
        mock_list.return_value = {"messages": [{"id": "1"}]}
        mock_batch.return_value = [self.mock_full_email]

        results = fetch_emails_from_gmail(self.user, max_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")
        self.assertIn("Chess.com", str(results[0]))

    @patch("api.services.gmail_service.build")
    @patch("api.services.gmail_service.get_creds")
    def test_fetch_emails_basic_success_returns_list(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = Mock(spec=Credentials)
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {"messages": [{"id": "msg1"}, {"id": "msg2"}]}

        mock_messages = [{"id": "msg1", "payload": {"headers": []}}, {"id": "msg2", "payload": {"headers": []}}]
        mock_service.new_batch_http_request.return_value = self._create_mock_batch(mock_messages)

        results = fetch_emails_from_gmail(self.user, max_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "msg1")

    @patch("api.services.gmail_service.build")
    @patch("api.services.gmail_service.get_creds")
    def test_fetch_emails_with_filters_applies_query_params(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = Mock(spec=Credentials)
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {"messages": [{"id": "msg1"}]}
        mock_service.new_batch_http_request.return_value = self._create_mock_batch(
            [{"id": "msg1", "payload": {"headers": []}}]
        )

        fetch_emails_from_gmail(self.user, label_ids=["INBOX"], query="from:chess.com")

        call_args = mock_service.users().messages().list.call_args[1]
        self.assertEqual(call_args["labelIds"], ["INBOX"])
        self.assertEqual(call_args["q"], "from:chess.com")

    @patch("api.services.gmail_service.build")
    @patch("api.services.gmail_service.get_creds")
    def test_fetch_emails_empty_mailbox_returns_empty_list(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = Mock(spec=Credentials)
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {"messages": []}

        results = fetch_emails_from_gmail(self.user)
        self.assertEqual(results, [])

    # @ TESTS FOR FETCH_TOTAL_EMAILS

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

    @patch("api.services.gmail_service.build")
    @patch("api.services.gmail_service.get_creds")
    def test_fetch_total_pagination_returns_all_pages(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = Mock(spec=Credentials)
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.side_effect = [
            {"messages": [{"id": "1"}], "nextPageToken": "page2"},
            {"messages": [{"id": "2"}]},
        ]
        mock_service.new_batch_http_request.side_effect = lambda: self._create_mock_batch(
            [{"id": "mock", "payload": {"headers": []}}]
        )

        results = fetch_total_emails(self.user, total_count=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(mock_service.users().messages().list().execute.call_count, 2)

    @patch("api.services.gmail_service.build")
    @patch("api.services.gmail_service.get_creds")
    def test_fetch_total_mailbox_exhaustion_stops_early(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = Mock(spec=Credentials)
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {"messages": [{"id": "small"} for _ in range(10)]}
        mock_service.new_batch_http_request.side_effect = lambda: self._create_mock_batch(
            [{"id": "mock", "payload": {"headers": []}}]
        )

        results = fetch_total_emails(self.user, total_count=1000)
        self.assertEqual(len(results), 10)
