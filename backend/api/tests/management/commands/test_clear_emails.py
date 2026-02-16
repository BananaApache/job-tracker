from django.core.management import call_command
from django.test import TestCase

from api.models import JobEmail, User


class TestClearEmails(TestCase):
    def setUp(self):
        self.user_email = "testuser@example.com"
        self.user = User.objects.create(email=self.user_email)

        """
        class JobEmail(models.Model):
            id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
            user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emails")

            gmail_id = models.CharField(max_length=255, unique=True)
            subject = models.CharField(max_length=500)
            sender_email = models.EmailField()
            sender_name = models.CharField(max_length=255)
            received_at = models.DateTimeField()
            content_type = models.CharField(max_length=100)
            size_estimate = models.IntegerField()
            importance = models.IntegerField()

            labels = models.ManyToManyField(Label, related_name="emails")
        """

        JobEmail.objects.create(
            user=self.user,
            gmail_id="1",
            subject="Test Subject",
            sender_email="sender@example.com",
            received_at="2026-02-01T03:33:03Z",
            content_type="text/html",
            size_estimate=68023,
            importance=1,
        )

        JobEmail.objects.create(
            user=self.user,
            gmail_id="2",
            subject="Another Test Subject",
            sender_email="another_sender@example.com",
            received_at="2026-02-01T04:33:03Z",
            content_type="text/plain",
            size_estimate=12345,
            importance=2,
        )

    def test_clear_emails_command(self):
        call_command("clear_emails", email=self.user_email)

        self.assertFalse(JobEmail.objects.filter(user=self.user).exists())
        self.assertEqual(JobEmail.objects.count(), 0)
