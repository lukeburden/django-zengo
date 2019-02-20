from django.contrib import admin

from . import models


class ZendeskUserAdmin(admin.ModelAdmin):

    list_display = [
        "zendesk_id",
        "name",
        "email",
        "active",
        "role",
        "user",
        "created_at",
    ]
    list_filter = ["active", "role", "created_at"]
    raw_id_fields = ["user"]
    search_fields = ["zendesk_id", "name", "email"]

    def get_queryset(self, request):
        return models.ZendeskUser.objects.all().select_related("user")


class TicketAdmin(admin.ModelAdmin):

    list_display = [
        "zendesk_id",
        "requester",
        "subject",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    # for Django <2.1
    raw_id_fields = ["requester"]
    # for Django >=2.1
    autocomplete_fields = ["requester"]
    search_fields = ["ticket__subject", "ticket__zendesk_id"]

    def get_queryset(self, request):
        return models.Ticket.objects.all().select_related("requester")


class CommentAdmin(admin.ModelAdmin):
    list_display = ["zendesk_id", "ticket_id", "author", "body", "public", "created_at"]
    list_filter = ["public", "created_at"]
    # for Django <2.1
    raw_id_fields = ["ticket", "author"]
    # for Django >=2.1
    autocomplete_fields = ["ticket", "author"]

    def get_queryset(self, request):
        return models.Comment.objects.all().select_related("ticket", "author")


class EventAdmin(admin.ModelAdmin):
    list_display = ["remote_ticket_id", "processing_ok", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    # for Django <2.1
    raw_id_fields = ["ticket"]
    # for Django >=2.1
    autocomplete_fields = ["ticket"]

    def processing_ok(self, instance):
        return False if instance.error else True

    processing_ok.boolean = True


admin.site.register(models.ZendeskUser, ZendeskUserAdmin)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.Comment, CommentAdmin)
admin.site.register(models.Event, EventAdmin)
