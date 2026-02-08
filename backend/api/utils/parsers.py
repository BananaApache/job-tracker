from email.utils import parseaddr, parsedate_to_datetime

from django.utils import timezone


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
