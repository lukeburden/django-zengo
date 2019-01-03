# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from konst import Constant, Constants
from konst.models.fields import ConstantChoiceCharField

# detect both postgres and postgis, upon which we use their native
# JSONField
if "postg" in settings.DATABASES["default"]["ENGINE"]:
    from django.contrib.postgres.fields import JSONField
else:
    from jsonfield import JSONField


class ZendeskUser(models.Model):
    """
    Link between a user in Zendesk and the local system.

    Depending on how users access Zendesk services, it may sometime
    not be possible to link all Zendesk users to local users, so `user`
    can be null.
    """

    class Meta:
        app_label = "zengo"

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)
    name = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    user = models.ForeignKey(
        get_user_model(), null=True, blank=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField()


class Ticket(models.Model):
    class Meta:
        app_label = "zengo"

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)
    requester = models.ForeignKey(ZendeskUser, on_delete=models.CASCADE)
    subject = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    states = Constants(
        Constant(new="new"),
        Constant(open="open"),
        Constant(pending="pending"),
        Constant(hold="hold"),
        Constant(solved="solved"),
        Constant(closed="closed"),
    )
    status = ConstantChoiceCharField(constants=states, max_length=8)
    # custom fields and tags are stored here, relatively unprocessed
    custom_fields = JSONField(null=True, blank=True)
    tags = JSONField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)


class Comment(models.Model):
    class Meta:
        app_label = "zengo"

    id = models.BigAutoField(primary_key=True)
    zendesk_id = models.BigIntegerField(unique=True)
    ticket = models.ForeignKey(
        Ticket, related_name="comments", on_delete=models.CASCADE
    )
    author = models.ForeignKey(ZendeskUser, on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    public = models.BooleanField()
    created_at = models.DateTimeField()


class Event(models.Model):
    class Meta:
        app_label = "zengo"

    raw_data = models.TextField()
    json = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    # if processing failed there was an error, it will appear here
    error = models.TextField(null=True, blank=True)
    # these should be populated if it was processed OK
    ticket = models.ForeignKey(
        Ticket, null=True, blank=True, related_name="events", on_delete=models.SET_NULL
    )
    actor = models.ForeignKey(
        ZendeskUser, null=True, blank=True, on_delete=models.SET_NULL
    )
