import logging
from typing import Dict, List, Optional

from api.models import JobEmail, Label, User

from .gmail_service import fetch_emails_from_gmail, fetch_total_emails

logger = logging.getLogger(__name__)


def wipe_emails_for_user(user: User):
    """Delete all emails for a user from the database."""
    count, _ = JobEmail.objects.filter(user=user).delete()
    logger.info(f"Deleted {count} emails for user {user.id}")
    return count


def populate_email_database(user: User, parsed_emails: List[Dict]):
    """
    Save/update emails in the database.

    Args:
        user: User who owns these emails
        parsed_emails: List of parsed email dictionaries

    Returns:
        Dict with 'created' and 'updated' counts
    """
    stats = {"created": 0, "updated": 0}

    for email_data in parsed_emails:
        label_names = email_data.pop("labels", [])

        email_obj, created = JobEmail.objects.update_or_create(
            gmail_id=email_data["gmail_id"], user=user, defaults=email_data
        )

        if not created:
            for key, value in email_data.items():
                if key != "gmail_id":
                    setattr(email_obj, key, value)
            email_obj.save()

        if label_names:
            label_objs = [Label.objects.get_or_create(name=name)[0] for name in label_names]
            email_obj.labels.set(label_objs)

        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    logger.info(f"Database stats: {stats}")
    return stats


def sync_user_emails(user: User, total_count: int = 100, parser_func: Optional[callable] = None) -> Dict:
    """
    High-level function to fetch and sync emails to database.

    Args:
        user: User to sync emails for
        total_count: Total number of emails to sync
        parser_func: Function to parse raw Gmail API response into your email format
                     Should take List[Dict] and return List[Dict]

    Returns:
        Dict with sync statistics

    Example:
        def parse_gmail_response(raw_emails):
            parsed = []
            for email in raw_emails:
                headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
                parsed.append({
                    "gmail_id": email["id"],
                    "subject": headers.get("Subject", ""),
                    "sender": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "labels": email.get("labelIds", [])
                })
            return parsed

        stats = sync_user_emails(user, 3000, parse_gmail_response)
    """
    logger.info(f"Starting email sync for user {user.id}, fetching {total_count} emails")

    stats = {"fetched": 0, "created": 0, "updated": 0, "errors": 0}

    try:

        def log_progress(current, total):
            logger.info(f"Progress: {current}/{total} message IDs collected")

        if total_count <= 500:
            raw_emails = fetch_emails_from_gmail(user, max_results=total_count)
        else:
            raw_emails = fetch_total_emails(user, total_count, progress_callback=log_progress)

        stats["fetched"] = len(raw_emails)
        logger.info(f"Fetched {stats['fetched']} emails from Gmail")

        if parser_func:
            parsed_emails = parser_func(raw_emails)
        else:
            parsed_emails = _default_email_parser(raw_emails)

        db_stats = populate_email_database(user, parsed_emails)
        stats["created"] = db_stats["created"]
        stats["updated"] = db_stats["updated"]

    except Exception as e:
        logger.error(f"Email sync failed: {e}", exc_info=True)
        stats["errors"] = 1

    logger.info(f"Sync complete: {stats}")
    return stats


def _default_email_parser(raw_emails: List[Dict]) -> List[Dict]:
    """
    Default parser to convert Gmail API response to your email format.
    Customize this to match your JobEmail model fields.
    """
    parsed = []
    for email in raw_emails:
        headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}

        parsed.append(
            {
                "gmail_id": email["id"],
                "subject": headers.get("Subject", ""),
                "sender": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "thread_id": email.get("threadId", ""),
                "snippet": email.get("snippet", ""),
                "labels": email.get("labelIds", []),
            }
        )

    return parsed


def get_email_count(user: User) -> int:
    """Get the count of emails stored for a user."""
    return JobEmail.objects.filter(user=user).count()
