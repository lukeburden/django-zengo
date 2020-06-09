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
    search_fields = ["subject", "zendesk_id"]

    def get_queryset(self, request):
        return models.Ticket.objects.all().select_related("requester")


class CommentAdmin(admin.ModelAdmin):
    list_display = [
        "zendesk_id",
        "ticket_id",
        "author",
        "get_body",
        "public",
        "created_at",
    ]
    list_filter = ["public", "created_at"]
    # for Django <2.1
    raw_id_fields = ["ticket", "author"]
    # for Django >=2.1
    autocomplete_fields = ["ticket", "author"]

    def get_body(self, instance):
        return instance.plain_body or instance.body

    get_body.short_description = "Body"

    def get_queryset(self, request):
        return models.Comment.objects.all().select_related("ticket", "author")


class AttachmentAdmin(admin.ModelAdmin):

    list_display = ["zendesk_id", "comment_id", "file_name", "content_type", "inline"]
    list_filter = ["inline", "content_type"]
    # for Django <2.1
    raw_id_fields = ["comment"]

    def get_queryset(self, request):
        return models.Attachment.objects.all().prefetch_related("photos")


class PhotoAdmin(admin.ModelAdmin):

    list_display = ["zendesk_id", "attachment_id", "file_name", "content_type"]
    list_filter = ["content_type"]
    # for Django <2.1
    raw_id_fields = ["attachment"]

    def get_queryset(self, request):
        return models.Photo.objects.all()


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
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Photo, PhotoAdmin)
admin.site.register(models.Event, EventAdmin)
