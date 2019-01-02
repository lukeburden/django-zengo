# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import contextlib
import importlib
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict

from django_pglocks import advisory_lock

from zenpy import Zenpy
from zenpy.lib.api_objects import User as RemoteZendeskUser
from zenpy.lib.exception import APIException

from . import signals
from .models import Comment
from .models import Event
from .models import Ticket
from .models import ZendeskUser as LocalZendeskUser
from .settings import app_settings


def get_zenpy_client():
    creds = {
        "email": settings.ZENDESK_EMAIL,
        "token": settings.ZENDESK_TOKEN,
        "subdomain": settings.ZENDESK_SUBDOMAIN,
    }
    return Zenpy(**creds)


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
        self.client = get_zenpy_client()

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

        # else check by associated emails
        # TODO: move into handler, or make conditional on allauth available
        # emails = local_user.emailaddress_set.all()
        # for e in emails:
        #     result = self.client.search(type="user", email=e.email)
        #     if result.count:
        #         # match strength based on email verification state
        #         return result.next(), e.verified

        # finally try local_user.email value in case an EmailAddress entry does not exist
        if local_user.email:
            result = self.client.search(type="user", email=local_user.email)
            if result.count:
                # weak match match by external_id
                return result.next(), False

        # no match at all, buh-bow
        return None, False

    def create_remote_zd_user_for_local_user(self, local_user):
        # create a remote zendesk user based on the given local user's details
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
            details = a.response.json()["details"]
            if any([d[0]["error"] for d in details.values()]):
                remote_zd_user, is_definite_match = self.get_remote_zd_user_for_local_user(
                    local_user
                )
            else:
                raise
        return remote_zd_user

    def get_or_create_remote_zd_user_for_local_user(self, local_user):
        user, is_definite_match = self.get_remote_zd_user_for_local_user(local_user)
        if user:
            return user, is_definite_match
        return self.create_remote_zd_user_for_local_user(local_user), True

    def update_remote_zd_user_for_local_user(self, local_user, remote_zd_user):
        """
        Compare the User and ZendeskUser instances and determine whether we
        need to update the data in Zendesk.

        This method is suitable to be called when a local user changes their
        email address or other user data.
        """
        changed = False
        email_changed = False

        if self.get_local_user_name() != remote_zd_user.name:
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

    def update_or_create_local_zd_user_for_remote_zd_user(self, remote_zd_user):
        """
        Given a RemoteZendeskUser instance, persist it as a LocalZendeskUser instance.
        """
        instance, created = LocalZendeskUser.objects.update_or_create(
            zendesk_id=remote_zd_user.id,
            defaults=dict(
                # attempt to resolve the local user if possible
                user=self.get_local_user_for_external_id(remote_zd_user.external_id),
                email=remote_zd_user.email,
                created_at=remote_zd_user.created_at,
                name=remote_zd_user.name,
            ),
        )
        return instance

    @contextlib.contextmanager
    def get_ticket_lock(self, ticket_id):
        # detect both postgres and postgis, upon which we serialize ticket
        # updates using a database lock
        if "postg" in settings.DATABASES["default"]["ENGINE"]:
            with advisory_lock("zengo-ticket-{}".format(ticket_id)):
                yield
        else:
            yield

    # def create_ticket_for_local_user(self, ticket):
    #     """
    #     Takes a Zenpy Ticket instance, creates it and then syncs the remote
    #     ticket into our local database. If all goes well, returns a local Ticket
    #     instance.
    #     """
    #     remote_zd_ticket = self.client.tickets.create(ticket)
    #     return self.sync_ticket(remote_zd_ticket)

    def sync_ticket_id(self, ticket_id):
        return self.sync_ticket(self.client.tickets(id=ticket_id))

    def sync_ticket(self, remote_zd_ticket):
        """
        Given a remote Zendesk ticket, store its details, comments and associated users.

        Additionally, we detect changes that have happened to the ticket comparing it
        against the state we have on hand for it prior to the new sync.
        """

        # take a snapshot of the ticket and its comments in their old state
        pre_sync_ticket = Ticket.objects.filter(zendesk_id=remote_zd_ticket.id).first()
        pre_sync_comments = list(Comment.objects.filter(ticket=pre_sync_ticket))

        # sync the ticket and comments to establish the new state
        local_zd_user = self.update_or_create_local_zd_user_for_remote_zd_user(
            remote_zd_ticket.requester
        )

        local_ticket, created = Ticket.objects.update_or_create(
            zendesk_id=remote_zd_ticket.id,
            defaults=dict(
                requester=local_zd_user,
                subject=remote_zd_ticket.subject,
                description=remote_zd_ticket.description,
                url=remote_zd_ticket.url,
                status=Ticket.states.by_id.get(remote_zd_ticket.status.lower()),
                custom_fields=remote_zd_ticket.custom_fields,
                tags=remote_zd_ticket.tags,
                created_at=remote_zd_ticket.created_at,
                updated_at=remote_zd_ticket.updated_at,
            ),
        )

        # sync comments that exist - for a new ticket, there may be none
        # as the first message is the ticket.description
        comments = self.sync_comments(remote_zd_ticket, local_ticket)

        update_context = {
            "pre_ticket": pre_sync_ticket,
            "post_ticket": local_ticket,
            "pre_comments": pre_sync_comments,
            "post_comments": comments,
        }

        if created and not comments:
            # it's possible the ticket isn't new but this is the first we're
            # seeing of it, so only consider it new if there are no comments
            signals.ticket_created.send(
                sender=Ticket, ticket=local_ticket, context=update_context
            )

        else:
            signals.ticket_updated.send(
                sender=Ticket,
                ticket=local_ticket,
                updates=self.get_updates(**update_context),
                context=update_context,
            )

        return local_ticket

    def sync_comments(self, zd_ticket, local_ticket):
        local_comments = []
        # no need to sync the ticket requester as we'll have just done that
        user_map = {zd_ticket.requester: local_ticket.requester}
        for remote_comment in self.client.tickets.comments(zd_ticket.id):
            if remote_comment.author not in user_map:
                author = self.update_or_create_local_zd_user_for_remote_zd_user(
                    remote_comment.author
                )
                user_map[remote_comment.author] = author
            else:
                author = user_map[remote_comment.author]
            local_comment, created = Comment.objects.update_or_create(
                zendesk_id=remote_comment.id,
                ticket=local_ticket,
                defaults=dict(
                    author=author,
                    body=remote_comment.body,
                    public=remote_comment.public,
                    created_at=remote_comment.created_at,
                ),
            )
            local_comments.append(local_comment)
        # sort increasing by created and id
        local_comments.sort(key=lambda c: (c.created_at, c.id))
        return local_comments

    def store_event(self, data):
        """Take raw request body and parse then store an event."""
        event = Event.objects.create(raw_data=data)
        event.save()
        try:
            data = json.loads(data)
        except (TypeError, ValueError) as e:
            raise ValidationError(e.message)
        else:
            event.json = data
            event.save(update_fields=("json",))
        return event

    def process_event(self, event):
        """
        At this stage we have a JSON structure - process it.

        {
            "id": "{{ ticket.id }}"
        }
        """
        # minimum we need to get sync'ing is a ZD ticket ID
        try:
            ticket_id = int(event.json["id"])
        except KeyError:
            raise ValidationError("`id` not found in data")
        except ValueError:
            raise ValidationError("`id` not found in data")

        # we lock on the ticket ID, so we never double up on
        # processing
        with self.get_ticket_lock(ticket_id):
            try:
                self.sync_ticket_id(ticket_id)
            except Exception:
                import traceback

                print(traceback.format_exc())
                raise

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


def import_attribute(path):
    assert isinstance(path, str)
    pkg, attr = path.rsplit(".", 1)
    ret = getattr(importlib.import_module(pkg), attr)
    return ret


def get_service():
    cls = app_settings.SERVICE_CLASS
    if cls is None:
        return ZengoService()
    return import_attribute(cls)()
