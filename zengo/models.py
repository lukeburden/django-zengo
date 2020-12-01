# -*- coding: utf-8 -*-
from __future__ import absolute_import

from functools import partial
import json

from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone

from konst import Constant, Constants
from konst.models.fields import ConstantChoiceCharField


# As the source is always Zendesk, we are permissive regarding length of URLs
TextURLField = partial(models.TextField, validators=[URLValidator()])  # noqa


class ZendeskUser(models.Model):
    """
    Link between a user in Zendesk and the local system.

    Depending on how users access Zendesk services, it may sometime
    not be possible to link all Zendesk users to local users, so `user`
    can be null.
    """

    roles = Constants(
        Constant(end_user="end-user"), Constant(agent="agent"), Constant(admin="admin")
    )

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)

    name = models.TextField(null=True, blank=True)
    alias = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    active = models.BooleanField(default=True)
    # we store all of the photo details from the API as JSON encoded text
    photos_json = models.TextField(null=True, blank=True)

    role = ConstantChoiceCharField(constants=roles, max_length=8)

    created_at = models.DateTimeField()

    # an optional reference to a local user instance
    user = models.ForeignKey(
        get_user_model(), null=True, blank=True, on_delete=models.PROTECT
    )

    def __str__(self):
        return "{} - {} (id={} zendesk_id={})".format(
            self.name, self.email, self.id, self.zendesk_id
        )

    @property
    def photo_url(self):
        if self.photos_json:
            j = json.loads(self.photos_json)
            if j and isinstance(j, dict):
                return j.get("content_url")


class Ticket(models.Model):

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)
    requester = models.ForeignKey(ZendeskUser, on_delete=models.CASCADE)
    subject = models.TextField(null=True, blank=True)
    url = TextURLField(null=True, blank=True)
    states = Constants(
        Constant(new="new"),
        Constant(open="open"),
        Constant(pending="pending"),
        Constant(hold="hold"),
        Constant(solved="solved"),
        Constant(closed="closed"),
    )
    status = ConstantChoiceCharField(constants=states, max_length=8)
    priorities = Constants(
        Constant(urgent="urgent"),
        Constant(high="high"),
        Constant(normal="normal"),
        Constant(low="low"),
    )
    priority = ConstantChoiceCharField(
        constants=priorities, max_length=8, null=True, blank=True
    )
    # custom fields and tags are stored here, relatively unprocessed and
    # are None, or parseable JSON
    custom_fields = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{} - {} (id={} zendesk_id={})".format(
            self.subject, self.status, self.id, self.zendesk_id
        )


class Comment(models.Model):

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)
    ticket = models.ForeignKey(
        Ticket, related_name="comments", on_delete=models.CASCADE
    )
    author = models.ForeignKey(ZendeskUser, on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    html_body = models.TextField(null=True, blank=True)
    plain_body = models.TextField(null=True, blank=True)
    public = models.BooleanField()
    created_at = models.DateTimeField()

    def __str__(self):
        return "{} - {} (id={} zendesk_id={})".format(
            self.author, self.public, self.id, self.zendesk_id
        )


class Attachment(models.Model):

    id = models.BigAutoField(primary_key=True)

    zendesk_id = models.BigIntegerField(unique=True)
    file_name = models.TextField()
    content_url = TextURLField()
    content_type = models.TextField()
    size = models.BigIntegerField()

    # image only fields
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    inline = models.BooleanField()

    # which comment this attachment belongs to
    comment = models.ForeignKey(
        Comment, related_name="attachments", on_delete=models.CASCADE
    )

    def __str__(self):
        return "{} (id={} zendesk_id={})".format(
            self.file_name, self.id, self.zendesk_id
        )


class Photo(models.Model):

    id = models.BigAutoField(primary_key=True)

    zendesk_id = models.BigIntegerField(unique=True)
    file_name = models.TextField()
    content_url = TextURLField()
    content_type = models.TextField()
    size = models.BigIntegerField()
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    # what attachment these are a thumbnail for
    attachment = models.ForeignKey(
        Attachment, related_name="photos", on_delete=models.CASCADE
    )

    def __str__(self):
        return "{} (id={} zendesk_id={})".format(
            self.file_name, self.id, self.zendesk_id
        )


class Event(models.Model):
    """
    Persist details around a single occurrence of Zendesk hitting the webhook view.
    """

    # limit the length to limit abuse
    raw_data = models.TextField(max_length=1024)

    # the remote ticket ID extracted from the data
    remote_ticket_id = models.PositiveIntegerField(null=True, blank=True)

    # if processing failed, an error will appear here
    error = models.TextField(null=True, blank=True)

    # if processing succeeded, this will point at a local Ticket instance
    # with comments etc
    ticket = models.ForeignKey(
        Ticket, null=True, blank=True, related_name="events", on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} (id={} remote_ticket_id={})".format(
            "Errored" if self.error else "Processed", self.id, self.remote_ticket_id
        )

    @property
    def json(self):
        return json.loads(self.raw_data)
