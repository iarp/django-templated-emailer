import glob
import os
import tempfile
import datetime
import logging
import shutil

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings as django_settings

from . import utils, settings

logger = logging.getLogger('django_templated_emailer')


class BaseEmailFields(models.Model):
    class Meta:
        abstract = True

    reply_to = models.TextField(null=True, blank=True)
    send_to = models.TextField(null=True, blank=True)
    cc_to = models.TextField(null=True, blank=True)
    bcc_to = models.TextField(null=True, blank=True)

    send_after_minutes = models.IntegerField(null=True, blank=True)

    subject = models.CharField(max_length=500)

    attachments = models.TextField(blank=True, help_text='Comma separated list of file paths. '
                                                         'If it is a URL, must be full proper url form.')

    inserted = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class EmailTemplate(BaseEmailFields):

    class Meta:
        verbose_name = 'Email Template'

    admin_list_help = """Emails wrapped in ( ) are conditional Send To type"""

    name = models.CharField(max_length=255)
    body = settings.TEMPLATE_BODY_FIELD_TYPE

    send_to_switch_true = models.CharField(max_length=500, blank=True, help_text='Email Address to add to the Send To field when the switch statement is True')
    send_to_switch_false = models.CharField(max_length=500, blank=True, help_text='Email Address to add to the Send To field when the switch statement is False')

    available_contexts = models.TextField(blank=True)

    default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if settings.TEMPLATE_DEFAULT_ALLOW_CHANGING_NAME and self.pk and self.default:
            # Prevent someone changing the Name value which is used by the programming logic to find the template.
            orig_data = EmailTemplate.objects.get(pk=self.pk)
            if self.name != orig_data.name:
                self.name = orig_data.name

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if settings.TEMPLATE_DEFAULT_ALLOW_DELETE and not self.default:
            super().delete(*args, **kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def get_template(cls, name):
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            logger.warning(f'No EmailTemplate.name="{name}" object was found.')
            return
        except cls.MultipleObjectsReturned:
            logger.warning(f'Multiple EmailTemplate.name="{name}" objects found. Using first by last updated.')
            return cls.objects.filter(name=name).order_by('-updated').first()


class EmailQueue(BaseEmailFields):
    """ Storage for emails ready to be sent.

        Avoid waiting for SMTP and making the user wait, we'll just queue emails they want into this
        table and let a queue processor handle everything for us.

        Use the following command to run the process:

            python manage.py emailqueue_send
    """

    class Meta:
        verbose_name = 'Email Queue'

    # What module within django is sending this? Just for tracking purposes.
    template_name = models.CharField(max_length=255, blank=True)

    body = settings.QUEUE_BODY_FIELD_TYPE

    # A Way to link the email to a specific item
    model_one_name = models.CharField(max_length=255, blank=True)
    model_one_id = models.CharField(max_length=255, blank=True)
    model_two_name = models.CharField(max_length=255, null=True, blank=True)
    model_two_id = models.CharField(max_length=255, null=True, blank=True)

    sent = models.BooleanField(default=False)
    date_sent = models.DateTimeField(null=True, blank=True)
    fake_sent = models.BooleanField(default=False)

    sent_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='dte_sent_emails')

    def get_send_to_names(self):
        return '; '.join(e.split('@')[0] for e in self.send_to.split(';')) if self.send_to else ''

    @staticmethod
    def prepare_email(template_name=None, attachments=None, send_to=None,
                      send_after_minutes=None, model_one=None, model_two=None, subject=None, body=None,
                      sent_by=None, reply_to=None, cc_to=None, bcc_to=None, send_to_switch=None,
                      override_template_name=None, override_subject=None, override_body=None, **contexts):
        """ Prepares an EmailQueue object for sending without Saving or Sending it.

            Useful when we want to quickly template out an EmailTemplate object for use in a custom form.

        Args:
            template_name: Template name to pre-load from EmailTemplate objects.
            attachments: Any items to attach to the outgoing email.
            send_to: Email addresses to send to, can be a delimited list
            send_after_minutes: How many minutes to send the email after saved.
            model_one: A model that the email refers to
            model_two: A secondary model that the email refers to
            subject: Supply if you wish to override the subject from the EmailTemplate object.
            body: Supply if you wish to override the body from the EmailTemplate object.
            sent_by: User object sending the email.
            reply_to: Email addresses to reply to, can be a delimited list
            cc_to: Email addresses to cc to, can be a delimited list
            bcc_to: Email addresses to bcc to, can be a delimited list
            send_to_switch: Some emails send to 1 person if a switch is true or a
                            2nd person if false, supply the switch result here.
            **contexts: All keyword items to add to the EmailTemplate subject and body rendering.

        Returns:
            EmailQueue: EmailQueue object unsaved and ready to be saved for sending.
        """

        eq = EmailQueue()

        if isinstance(template_name, EmailTemplate):
            template = template_name
            template_name = template_name.name

        elif template_name:
            template = EmailTemplate.get_template(name=template_name)
            if not template:
                return

        else:
            template = EmailTemplate()

        template_supplied_attachments = [a.strip() for a in template.attachments.split(',') if a]

        combined_attachments = template_supplied_attachments.copy()
        if attachments and isinstance(attachments, list):
            combined_attachments.extend(attachments)
        elif attachments and isinstance(attachments, str):
            combined_attachments.append(attachments)

        eq.attachments = ','.join(combined_attachments)

        if isinstance(sent_by, get_user_model()):
            eq.sent_by = sent_by
        if isinstance(send_to, get_user_model()):
            send_to = send_to.email

        if send_to_switch is not None:
            if send_to_switch:
                template.send_to = template.send_to_switch_true
            else:
                template.send_to = template.send_to_switch_false

        eq.send_to = utils.unique_emails(template.send_to, send_to, joiner=';')
        eq.reply_to = utils.unique_emails(reply_to, joiner=';')
        eq.cc_to = utils.unique_emails(template.cc_to, cc_to, joiner=';')
        eq.bcc_to = utils.unique_emails(template.bcc_to, bcc_to, joiner=';')

        for k in ['model_one_name', 'model_one_id', 'model_two_name', 'model_two_id']:
            if k in contexts:
                setattr(eq, k, contexts.pop(k))

        if model_one or model_two:
            eq.set_model_data(model_one=model_one, model_two=model_two)

        try:
            eq.send_after_minutes = int(send_after_minutes)
        except (TypeError, ValueError):
            eq.send_after_minutes = template.send_after_minutes

        eq.template_name = template_name
        eq.body = template.body
        eq.subject = template.subject

        if override_template_name and override_template_name.strip():
            eq.template_name = override_template_name

        if subject:
            eq.subject = subject
        elif override_subject:
            eq.subject = override_subject

        if body:
            eq.body = body
        elif override_body:
            eq.body = override_body

        if callable(eq.subject):
            eq.subject = eq.subject(eq, **contexts)
        if callable(eq.body):
            eq.body = eq.body(eq, **contexts)

        eq.subject = Template(eq.subject).render(context=Context(contexts))
        eq.body = Template(eq.body).render(context=Context(contexts))

        return eq

    @staticmethod
    def queue_email(send_immediately=False, sent=False, fake_sent=False,
                    delete_unsent_matching=False, *args, **kwargs):
        """ Queues an email to be sent out.

        Args:
            send_immediately (bool): Bypass all restrictions and send right away?
            sent (bool): Whether or not to be marked as sent but not actually having sent the email.
            fake_sent (bool): relic from tryout system. Idea was to show the
                                end-user as being sent but not actually sent.
            delete_unsent_matching: If you're re-queueing an email, supply exact same details and any
                                        unsent where subject, send_to, and template_name match are deleted.
            *args: See prepare_email
            **kwargs: See prepare_email

        Returns:
            EmailQueue: EmailQueue object saved and queued to be sent by system.
        """

        eq = EmailQueue.prepare_email(*args, **kwargs)

        if not eq:
            return

        if not eq.send_to and not eq.cc_to and not eq.bcc_to:
            logger.warning(f'{eq} email has no email address to send to')
            return False

        if send_immediately is True:
            eq.send(send_immediately=True)
        elif sent is True:
            eq.mark_as_sent_now(fake_sent=True)

        if fake_sent:
            eq.fake_sent = True

        if delete_unsent_matching and eq.template_name:

            eqs = EmailQueue.objects.filter(
                sent=False,
                subject=eq.subject,
                send_to=eq.send_to,
                template_name=eq.template_name
            )

            if eq.model_one_name:
                eqs = eqs.filter(model_one_name=eq.model_one_name, model_one_id=eq.model_one_id)
            if eq.model_two_name:
                eqs = eqs.filter(model_two_name=eq.model_two_name, model_two_id=eq.model_two_id)

            eqs.delete()

        eq.save()

        return eq

    def send(self, send_immediately=False):

        if self.sent:
            return True

        if self.send_after_minutes and not send_immediately:

            if self.send_at_this_time() > timezone.now():
                return False

        email_message = EmailMultiAlternatives(
            to=utils.unique_emails(self.send_to),
            reply_to=utils.unique_emails(self.reply_to),
            cc=utils.unique_emails(self.cc_to),
            bcc=utils.unique_emails(self.bcc_to),
            subject=self.subject,
            body=self.body,
        )
        email_message.attach_alternative(self.body, 'text/html')

        temp_folder = None
        if self.attachments:

            for attachment in self.attachments.split(','):

                if attachment.startswith('http') or attachment.startswith('www'):

                    if not temp_folder:
                        temp_folder = tempfile.mkdtemp(dir=os.path.join(django_settings.BASE_DIR, 'cache'))

                    try:
                        url = attachment
                        attachment = os.path.join(temp_folder, os.path.basename(attachment))
                        utils.download_file(url, attachment)
                    except:
                        logger.exception(f'EmailQueue.pk="{self.pk}" send attachment failure')
                        continue

                if os.path.isfile(attachment):
                    email_message.attach_file(attachment)

        try:
            email_message.send()
            self.sent = True
            self.date_sent = timezone.now()
            self.save()
        except:
            raise

        finally:
            if temp_folder:
                shutil.rmtree(temp_folder, ignore_errors=True)

        return self.sent

    def send_at_this_time(self):
        return self.inserted + datetime.timedelta(minutes=self.send_after_minutes or 0)

    def seconds_until_sent(self):
        if timezone.now() >= self.send_at_this_time():
            return -1
        return (self.send_at_this_time() - timezone.now()).seconds

    def __str__(self):
        return f'{self.send_to}: {self.subject}'

    def cancel_send(self, user):
        self.template_name = '{} - Undo by {} on {}'.format(
            self.template_name,
            user.email,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.mark_as_sent_now(fake_sent=True)

    def mark_as_sent_now(self, fake_sent=False, commit=True):
        self.sent = True
        self.date_sent = timezone.now()
        if fake_sent:
            self.fake_sent = True
        if commit:
            self.save()

    def set_model_data(self, model_one=None, model_two=None):

        if getattr(model_one, 'pk', None):
            self.model_one_name = model_one.__class__.__name__
            self.model_one_id = model_one.pk

        if getattr(model_two, 'pk', None):
            self.model_two_name = model_two.__class__.__name__
            self.model_two_id = model_two.pk

    @staticmethod
    def search_for(model_one=None, model_two=None, search_both=False, *args, **kwargs):
        """ Searches for EmailQueue objects where model_one and model_two match.

        Supply model_one and search_both=True to do an OR search on model_one and model_two.

        Args:
            model_one: First model to look for
            model_two: Second model to look for
            search_both: True/False if we're searching for model_one in either model_* spots.
            *args: args to be passed to an EmailQueue filter
            **kwargs: kwargs to be passed to an EmailQueue filter

        Returns:
            EmailQueue filtered queryset
        """
        eqf = EmailQueue.objects.filter(*args, **kwargs)

        # If we're passed search_both=True then we're searching for EmailQueue
        # items where model_one OR model_two equals the model_one supplied object.
        if search_both and getattr(model_one, 'pk', None):

            eqf = eqf.filter(
                models.Q(model_one_name=model_one.__class__.__name__, model_one_id=model_one.pk) |
                models.Q(model_two_name=model_one.__class__.__name__, model_two_id=model_one.pk),
            )

        else:

            if getattr(model_one, 'pk', None):
                eqf = eqf.filter(model_one_name=model_one.__class__.__name__, model_one_id=model_one.pk)

            if getattr(model_two, 'pk', None):
                eqf = eqf.filter(model_two_name=model_two.__class__.__name__, model_two_id=model_two.pk)

        return eqf

    # def delete_attachments_in_body(self, folder):
    #     """ Finds attachments in the email body and deletes them.
    #
    #     :param folder: If supplied, also ensures this value was in the url to the attachment.
    #     :return:
    #     """
    #     deleted = []
    #     links = []
    #
    #     soup = BeautifulSoup(self.body, 'html.parser')
    #     for a in soup.find_all('a', href=True):
    #         links.append(a)
    #         if django_settings.STATIC_URL in a['href']:
    #
    #             if folder.replace(' ', '+') not in a['href']:
    #                 continue
    #
    #             try:
    #                 default_storage.delete(
    #                     a['href'].replace(django_settings.STATIC_URL, '').replace('+', ' ')
    #                 )
    #                 deleted.append(a)
    #             except:
    #                 logger.debug(traceback.format_exc())
    #
    #     return links, deleted
