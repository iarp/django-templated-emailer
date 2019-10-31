from django.contrib import admin, messages

from .app_settings import app_settings
from .models import EmailTemplate, EmailQueue


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):

    list_display = ('name', 'send_tos', 'subject', 'default')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'send_to', 'cc_to', 'bcc_to', 'send_to_switch_true', 'send_to_switch_false')
        }),
        ('Email', {
            'fields': ('subject', 'body', 'available_contexts', 'default')
        })
    )

    def send_tos(self, obj):
        orig_send_to = '; '.join(e.split('@')[0] for e in obj.send_to.split(';'))
        send_to = orig_send_to
        send_to_switch_true = '; '.join(e.split('@')[0] for e in obj.send_to_switch_true.split(';'))
        send_to_switch_false = '; '.join(e.split('@')[0] for e in obj.send_to_switch_false.split(';'))

        if orig_send_to and (send_to_switch_true or send_to_switch_false):
            send_to += ' AND '

        if send_to_switch_true or send_to_switch_false:
            send_to += '('

        if send_to_switch_true:
            send_to += send_to_switch_true

        if send_to_switch_true and send_to_switch_false:
            send_to += ' OR '

        if send_to_switch_false:
            send_to += send_to_switch_false

        if send_to_switch_true or send_to_switch_false:
            send_to += ')'

        return send_to
    send_tos.short_description = 'Send To'

    def delete_model(self, request, obj):
        if not app_settings.TEMPLATE_DEFAULT_ALLOW_DELETE and obj.default:
            messages.error(request, 'Settings disallow deletion of default=True EmailTemplate objects.')
            return
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset.all():
            self.delete_model(request, obj)


def requeue_email_queue(modeladmin, request, queryset):
    for item in queryset:
        item.pk = None
        item.sent = False
        item.date_sent = None
        item.save()
requeue_email_queue.short_description = 'ReQueue Selected Emails.'


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ('subject', 'send_at_this_time', 'sent', 'send_tos')

    actions = [requeue_email_queue]

    ordering = ['-date_sent']

    # readonly_fields = ('updated', 'inserted', 'sent', 'date_sent')
    readonly_fields = ('updated', 'inserted')

    search_fields = ('send_to', 'subject')

    fieldsets = (
        (None, {
            'fields': ('template_name', 'send_to', 'reply_to', 'cc_to', 'bcc_to', ('sent', 'date_sent'), ('model_one_name', 'model_one_id'), ('model_two_name', 'model_two_id'))
        }),
        ('Email', {
            'fields': ('subject', 'body', 'attachments')
        }),
        ('System', {
            'fields': ('updated', 'inserted')
        })
    )

    def send_at_this_time(self, obj):
        return obj.send_at_this_time()

    def send_tos(self, obj):
        return obj.get_send_to_names()
    send_tos.short_description = 'Send To'
