from django.test import TestCase
from django.test.utils import override_settings

from .utils import unique_emails
from .models import EmailQueue, EmailTemplate


class TestUtils(TestCase):

    emails = [
        "test@domain.com",
        "test1@domain.com",
        "test2@domain.com",
        "test2@domain.com",
    ]
    emails2 = [
        "test@example.com",
        "test1@example.com",
        "test2@example.com",
        "test2@example.com",
    ]

    def test_unique_emails_is_unique(self):

        ue = unique_emails(self.emails)
        self.assertEqual(3, len(ue))

        ue = unique_emails(self.emails, self.emails2)
        self.assertEqual(6, len(ue))

    def test_unique_emails_joiner(self):

        output = unique_emails(self.emails, joiner=";")

        self.assertTrue(isinstance(output, str))
        self.assertEqual(3, len(output.split(";")))

    def test_unique_emails_ignore_none_strings(self):

        emails = self.emails.copy()
        emails.append(None)
        ue = unique_emails(emails)
        self.assertEqual(3, len(ue))

        ue = unique_emails(emails, self.emails2)
        self.assertEqual(6, len(ue))

        ue = unique_emails(emails, self.emails2, None)
        self.assertEqual(6, len(ue))

    def test_unique_emails_fails_dict(self):

        ue = unique_emails(self.emails, {'fails': 'test@domain.com'})
        self.assertEqual(3, len(ue))


class TestEmailQueueQueueEmail(TestCase):

    def setUp(self) -> None:
        self.template = EmailTemplate.objects.create(
            name='Test Template',
            subject='Test',
            body='Test Body! {{domain}}'
        )

    def test_no_context(self):
        eq = EmailQueue.queue_email(
            template_name='Test Template',
            send_to='test@domain.com',
        )
        self.assertEqual('Test', eq.subject)
        self.assertEqual('Test Body! ', eq.body)

    def test_with_context(self):
        eq = EmailQueue.queue_email(
            template_name='Test Template',
            send_to='test@domain.com',

            domain='here as context'
        )
        self.assertEqual('Test', eq.subject)
        self.assertEqual('Test Body! here as context', eq.body)

    @override_settings(
        TEMPLATED_EMAILER_GLOBAL_CONTEXTS={'domain': 'here in global context'}
    )
    def test_with_global_context(self):
        eq = EmailQueue.queue_email(
            template_name='Test Template',
            send_to='test@domain.com',
        )
        self.assertEqual('Test', eq.subject)
        self.assertEqual('Test Body! here in global context', eq.body)

    @override_settings(
        TEMPLATED_EMAILER_GLOBAL_CONTEXTS={'domain': 'here in global context'}
    )
    def test_global_context_does_not_overwrite_local_context(self):
        eq = EmailQueue.queue_email(
            template_name='Test Template',
            send_to='test@domain.com',

            domain='test here in method'
        )
        self.assertEqual('Test', eq.subject)
        self.assertEqual('Test Body! test here in method', eq.body)
