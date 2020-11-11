# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import contextlib
import importlib
import json
import logging
import traceback

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils import timezone

from zenpy import Zenpy
from zenpy.lib.api_objects import User as RemoteZendeskUser
from zenpy.lib.exception import APIException

from . import models
from . import signals
from . import strings
from .settings import app_settings


logger = logging.getLogger(__name__)


"""
~ Caution ~

This service handles three different types of users; please read about the
types below as it will make things much more comprehensible!

1) Local User
The Django User object.

2) Local ZendeskUser
This is the Zengo ZendeskUser model, which is a cache of actual Zendesk users
and a linkage to a local User.

3) Remote ZendeskUser
This is the underlying User object returned by the Zendesk API and instantiated
by the API wrapper, Zenpy.
"""


class ZengoService(object):
    """Encapsulate behaviour allowing easy customisation."""

    def __init__(self, *args, **kwargs):
        creds = {
            "email": settings.ZENDESK_EMAIL,
            "token": settings.ZENDESK_TOKEN,
            "subdomain": settings.ZENDESK_SUBDOMAIN,
        }
        self.client = Zenpy(**creds)

    # extraction of data from local users for injection into Zendesk

    def get_local_user_name(self, local_user):
        return local_user.first_name

    def get_local_user_external_id(self, local_user):
        return local_user.id

    def get_local_user_profile_image(self, local_user):
        return None

    def get_local_user_for_external_id(self, external_id):
        return get_user_model().objects.filter(id=external_id).first()

    def get_remote_zd_user_for_local_user(self, local_user):
        """
        Attempt to resolve the provided user to an extant Zendesk User.

        Returns a Zendesk API User instance, and a boolean that indicates how
        definite the resolution is, based on how they've been found.
        """
        result = self.client.search(
            type="user", external_id=self.get_local_user_external_id(local_user)
        )
        if result.count:
            # strong match by external_id
            return result.next(), True

        # else check by associated emails, if allauth is installed and being used
        if "allauth.account" in settings.INSTALLED_APPS:
            emails = local_user.emailaddress_set.all()
            for e in emails:
                result = self.client.search(type="user", email=e.email)
                if result.count:
                    # match strength based on email verification state
                    return result.next(), e.verified

        # check for a weak match match using the email field on user instance
        if local_user.email:
            result = self.client.search(type="user", email=local_user.email)
            if result.count:
                return result.next(), False

        # no match at all, buh-bow
        return None, False

    def create_remote_zd_user_for_local_user(self, local_user):
        """Create a remote zendesk user based on the given local user's details."""
        try:
            remote_zd_user = self.client.users.create(
                RemoteZendeskUser(
                    name=self.get_local_user_name(local_user),
                    external_id=self.get_local_user_external_id(local_user),
                    email=local_user.email,
                    remote_photo_url=self.get_local_user_profile_image(local_user),
                )
            )
        except APIException as a:
            # if this is a duplicate error try one last time to get the user
            print(a.response.json())
            details = a.response.json()["details"]
            if any([d[0]["error"] == "DuplicateValue" for d in details.values()]):
                (
                    remote_zd_user,
                    is_definite_match,
                ) = self.get_remote_zd_user_for_local_user(local_user)
            else:
                raise
        return remote_zd_user

    def get_or_create_remote_zd_user_for_local_user(self, local_user):
        user, is_definite_match = self.get_remote_zd_user_for_local_user(local_user)
        if user:
            return user, is_definite_match
        # we create a remote user in Zendesk for this local user
        return self.create_remote_zd_user_for_local_user(local_user), True

    def get_special_zendesk_user(self):
        """
        Return a ZendeskUser instance representing the special Zendesk user that
        automations can add use to add comments.
        """
        instance, created = models.ZendeskUser.objects.get_or_create(
            zendesk_id=-1,
            defaults=dict(
                name="Zendesk",
                active=True,
                role=models.ZendeskUser.roles.admin,
                created_at=timezone.now(),
            ),
        )
        return instance

    def update_remote_zd_user_for_local_user(self, local_user, remote_zd_user):
        """
        Compare the User and ZendeskUser instances and determine whether we
        need to update the data in Zendesk.

        This method is suitable to be called when a local user changes their
        email address or other user data.
        """
        changed = False
        email_changed = False

        if self.get_local_user_name(local_user) != remote_zd_user.name:
            remote_zd_user.name = self.get_local_user_name(local_user)
            changed = True

        if self.get_local_user_external_id(local_user) != remote_zd_user.external_id:
            remote_zd_user.external_id = self.get_local_user_external_id(local_user)
            changed = True

        if local_user.email and local_user.email != remote_zd_user.email:
            remote_zd_user.email = local_user.email
            changed = True
            email_changed = True

        if changed:
            remote_zd_user = self.client.users.update(remote_zd_user)

        if email_changed:
            # then in addition to the above, we have to mark the newly
            # created identity as verified and promote it to be primary
            results = self.client.users.identities(id=remote_zd_user.id)
            for identity in results:
                if identity.value == local_user.email:
                    self.client.users.identities.make_primary(
                        user=remote_zd_user, identity=identity
                    )
                    break

    def update_or_create_remote_zd_user(self, local_user):
        remote_zd_user, is_definite_match = self.get_remote_zd_user_for_local_user(
            local_user
        )
        if remote_zd_user and is_definite_match:
            # check if we need to do any updates
            self.update_remote_zd_user_for_local_user(local_user, remote_zd_user)
        else:
            remote_zd_user = self.create_remote_zd_user_for_local_user(local_user)
        return remote_zd_user

    def sync_user(self, remote_zd_user):
        """
        Given a RemoteZendeskUser instance, persist it as a local ZendeskUser instance.
        """
        instance, created = models.ZendeskUser.objects.update_or_create(
            zendesk_id=remote_zd_user.id,
            defaults=dict(
                # attempt to resolve the local user if possible
                user=self.get_local_user_for_external_id(remote_zd_user.external_id),
                alias=remote_zd_user.alias,
                email=remote_zd_user.email,
                created_at=remote_zd_user.created_at,
                name=remote_zd_user.name,
                active=remote_zd_user.active,
                role=remote_zd_user.role,
                # store their latest photo JSON data
                photos_json=json.dumps(remote_zd_user.photo),
            ),
        )
        return instance

    def sync_ticket_id(self, ticket_id):
        return self.sync_ticket(self.client.tickets(id=ticket_id))

    def sync_ticket(self, remote_zd_ticket):
        """
        Create or update local representations of a Zendesk ticket, its comments
        and all associated Zendesk users.

        This uses `update_or_create` to avoid integrity errors, demanding that
        comments and users be sync'd in a consistent order to avoid deadlock.

        Todo: only pull comments beyond those we've already got in the database
        """

        kwargs = dict(include_inline_images=True)

        remote_comments = [
            c for c in self.client.tickets.comments(remote_zd_ticket.id, **kwargs)
        ]

        remote_comments.sort(key=lambda c: (c.created_at, c.id))

        # establish a distinct, ordered list of Zendesk users
        users = set(
            [remote_zd_ticket.requester]
            + [c.author for c in remote_comments if c.author_id != -1]  # noqa
        )
        users = list(users)
        users.sort(key=lambda u: u.id)

        # sync the users and establish a mapping to local records
        user_map = {u: self.sync_user(u) for u in users}

        defaults = dict(
            requester=user_map[remote_zd_ticket.requester],
            subject=remote_zd_ticket.subject,
            url=remote_zd_ticket.url,
            status=models.Ticket.states.by_id.get(remote_zd_ticket.status.lower()),
            custom_fields=json.dumps(remote_zd_ticket.custom_fields),
            tags=json.dumps(remote_zd_ticket.tags),
            created_at=remote_zd_ticket.created_at,
            updated_at=remote_zd_ticket.updated_at,
        )

        # In some API responses we don't get a priority, but it could be an existing ticket with
        # priority already initialised so we don't want to overwrite the priority to the Ticket
        # object.
        if remote_zd_ticket.priority is not None:
            defaults["priority"] = models.Ticket.priorities.by_id.get(
                remote_zd_ticket.priority.lower()
            )

        # update or create the ticket
        local_ticket, created = models.Ticket.objects.update_or_create(
            zendesk_id=remote_zd_ticket.id,
            defaults=defaults,
        )
        # and now update or create the comments - baring in mind some might be type `VoiceComment`
        # https://developer.zendesk.com/rest_api/docs/support/ticket_audits#voice-comment-event
        for remote_comment in remote_comments:
            # if we know Zendesk created this comment as part of an automation or
            # merge, link it to the Zendesk user (skipping any zenpy/network hits)
            if remote_comment.author_id == -1:
                author = self.get_special_zendesk_user()
            else:
                author = user_map[remote_comment.author]

            local_comment, _created = models.Comment.objects.update_or_create(
                zendesk_id=remote_comment.id,
                ticket=local_ticket,
                defaults=dict(
                    author=author,
                    body=remote_comment.body,
                    html_body=remote_comment.html_body,
                    # VoiceComments have no `plain_body` content
                    plain_body=getattr(remote_comment, "plain_body", None),
                    public=remote_comment.public,
                    created_at=remote_comment.created_at,
                ),
            )
            for attachment in remote_comment.attachments:
                local_attachment, _created = models.Attachment.objects.update_or_create(
                    zendesk_id=attachment.id,
                    comment=local_comment,
                    defaults=dict(
                        file_name=attachment.file_name,
                        content_url=attachment.content_url,
                        content_type=attachment.content_type,
                        size=attachment.size,
                        width=attachment.width,
                        height=attachment.height,
                        inline=attachment.inline,
                    ),
                )
                for photo in attachment.thumbnails:
                    local_photo, _created = models.Photo.objects.update_or_create(
                        zendesk_id=photo.id,
                        attachment=local_attachment,
                        defaults=dict(
                            file_name=photo.file_name,
                            content_url=photo.content_url,
                            content_type=photo.content_type,
                            size=photo.size,
                            width=photo.width,
                            height=photo.height,
                        ),
                    )

        return local_ticket, created


class ZengoProcessor(object):
    """
    Store and process updates from Zendesk.

    Subclass this processor to serialize ticket processing, process
    asynchronously, etc.
    """

    def store_event(self, data):
        """Take raw request body and parse then store an event."""
        event = models.Event.objects.create(raw_data=data)
        event.save()
        try:
            data = json.loads(data)
        except (TypeError, ValueError):
            raise ValidationError(strings.data_malformed)

        # minimum we need to be able to process the update is
        # a remote ZD ticket ID
        try:
            int(data["id"])
        except KeyError:
            raise ValidationError(strings.data_no_ticket_id)
        except ValueError:
            raise ValidationError(strings.data_no_ticket_id)

        event.remote_ticket_id = data["id"]
        event.save(update_fields=("remote_ticket_id", "updated_at"))
        return event

    def begin_processing_event(self, event):
        return self.process_event_and_record_errors(event)

    def process_event_and_record_errors(self, event):
        try:
            # potentially serialize processing per-ticket such that there isn't
            # doubling up on signals firing
            with self.acquire_ticket_lock(event.remote_ticket_id):
                self.process_event(event)

        except Exception:
            logger.exception(
                "Failed to process Zendesk event",
                extra=dict(
                    event_id=event.id,
                ),
            )
            # Attempt to store a traceback in our DB for convenience and legacy's sake.
            # The earlier call to `logger.exception` should be ideally surfaced via dev
            # error reporting (Sentry, etc)
            event.error = traceback.format_exc()
            event.save(update_fields=("error", "updated_at"))
            raise

    def process_event(self, event):
        """
        At this stage we have a JSON structure - process it.

        {
            "id": "{{ ticket.id }}"
        }
        """
        ticket_id = event.remote_ticket_id

        # take a snapshot of the ticket and its comments in their old state
        pre_sync_ticket = models.Ticket.objects.filter(zendesk_id=ticket_id).first()
        pre_sync_comments = []
        if pre_sync_ticket:
            pre_sync_comments = list(pre_sync_ticket.comments.all())

        post_sync_ticket, created = get_service().sync_ticket_id(ticket_id)

        post_sync_comments = list(post_sync_ticket.comments.all())

        # build update context for passing downstream
        update_context = {
            "pre_ticket": pre_sync_ticket,
            "post_ticket": post_sync_ticket,
            "pre_comments": pre_sync_comments,
            "post_comments": post_sync_comments,
        }

        if created and not post_sync_comments:
            signals.ticket_created.send(
                sender=models.Ticket, ticket=post_sync_ticket, context=update_context
            )

        else:
            signals.ticket_updated.send(
                sender=models.Ticket,
                ticket=post_sync_ticket,
                updates=self.get_updates(**update_context),
                context=update_context,
            )

    def get_updates(self, **kwargs):
        """
        Get new comments and updated fields and custom fields.

        Further update detection can be done by projects using the
        `ticket_updated` signal in combination with the passed `change_context`.
        """
        return {
            "new_comments": self.get_new_comments(**kwargs),
            "updated_fields": self.get_updated_fields(**kwargs),
        }

    def get_new_comments(self, pre_ticket, post_ticket, pre_comments, post_comments):
        new_comments = []
        if len(post_comments) > len(pre_comments):
            new_comment_ids = set([c.zendesk_id for c in post_comments]) - set(
                [c.zendesk_id for c in pre_comments]
            )
            new_comments = [c for c in post_comments if c.zendesk_id in new_comment_ids]
        return new_comments

    def get_updated_fields(self, pre_ticket, post_ticket, pre_comments, post_comments):
        updates = {}

        if not (pre_ticket and post_ticket):
            return updates

        pre_fields = model_to_dict(pre_ticket)
        post_fields = model_to_dict(post_ticket)

        # note: we do this using comparison rather than set operations to
        # avoid issues with more complex, non-hashable fields
        for k in pre_fields.keys():
            if k in ("created_at", "updated_at"):
                # don't bother detecting changes in these, it's not useful
                # and timestamps are often mismatched as datetimes and strings
                continue
            if pre_fields.get(k) != post_fields.get(k):
                updates[k] = {"old": pre_fields.get(k), "new": post_fields.get(k)}
        return updates

    @contextlib.contextmanager
    def acquire_ticket_lock(self, ticket_id):
        # subclass to serialize ticket updates
        yield


def get_processor():
    cls = app_settings.PROCESSOR_CLASS
    if cls is None:
        return ZengoProcessor()
    return import_attribute(cls)()


def get_service():
    cls = app_settings.SERVICE_CLASS
    if cls is None:
        return ZengoService()
    return import_attribute(cls)()


def import_attribute(path):
    assert isinstance(path, str)
    pkg, attr = path.rsplit(".", 1)
    ret = getattr(importlib.import_module(pkg), attr)
    return ret
