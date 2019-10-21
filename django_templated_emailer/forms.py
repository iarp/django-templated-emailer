from django import forms

from ckeditor.fields import CKEditorWidget
from configurables.models import EmailQueue


class EmailTemplateEditor(forms.Form):

    subject = forms.CharField()
    body = forms.CharField(widget=CKEditorWidget())


class EmailQueueEditor(EmailTemplateEditor):

    def __init__(self, template_name, data=None, files=None, *args, **kwargs):
        self.eq = EmailQueue.prepare_email(template_name=template_name, *args, **kwargs)
        self.contexts = kwargs

        initial = {
            'subject': self.eq.subject,
            'body': self.eq.body,
        }

        super().__init__(data=data, files=files, initial=initial)

    def send(self, *args, **kwargs):
        return EmailQueue.queue_email(
            template_name=self.eq.template_name,

            **self.contexts,

            **kwargs,

            **self.cleaned_data,
        )
