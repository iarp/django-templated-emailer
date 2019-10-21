from django.test import TestCase

from .utils import unique_emails


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
