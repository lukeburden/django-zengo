# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import contextlib
import importlib
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from django_pglocks import advisory_lock

from zenpy import Zenpy

from . import signals
from .models import Comment
from .models import Event
from .models import Ticket
from .models import ZendeskUser
from .settings import app_settings


def get_zenpy_client():
    creds = {
        "email": settings.ZENDESK_EMAIL,
        "token": settings.ZENDESK_TOKEN,
        "subdomain": settings.ZENDESK_SUBDOMAIN,
    }
    return Zenpy(**creds)


class ZengoService(object):
    """Encapsulate behaviour allowing easy customisation."""

    def get_user_for_external_id(self, external_id):
        return get_user_model().objects.filter(id=external_id).first()

    @contextlib.contextmanager
    def get_ticket_lock(self, ticket_id):
        # detect both postgres and postgis, upon which we serialize ticket
        # updates using a database lock
        if "postg" in settings.DATABASES["default"]["ENGINE"]:
            with advisory_lock("zengo-ticket-{}".format(ticket_id)):
                yield
        else:
            yield

    def sync_user(self, zendesk_user):
        instance, created = ZendeskUser.objects.update_or_create(
            zendesk_id=zendesk_user.id,
            user=self.get_user_for_external_id(zendesk_user.external_id),
            defaults=dict(
                email=zendesk_user.email,
                created=zendesk_user.created_at,
                name=zendesk_user.name,
            ),
        )
        return instance

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

    def sync_ticket_id(self, ticket_id):
        return self.sync_ticket(get_zenpy_client().tickets(id=ticket_id))

    def sync_ticket(self, zd_ticket):
        """Sync a ticket, comments and associated users."""
        # take a snapshot of the ticket and its comments in their old state
        pre_ticket = Ticket.objects.filter(zendesk_id=zd_ticket.id).first()
        pre_comments = list(Comment.objects.filter(ticket=pre_ticket))
        # sync the ticket and comments to establish the new state
        zd_user = self.sync_user(zd_ticket.requester)
        ticket, created = Ticket.objects.update_or_create(
            zendesk_id=zd_ticket.id,
            defaults=dict(
                zendesk_user=zd_user,
                subject=zd_ticket.subject,
                description=zd_ticket.description,
                url=zd_ticket.url,
                status=Ticket.states.by_id.get(zd_ticket.status.lower()),
                custom_fields=zd_ticket.custom_fields,
                tags=zd_ticket.tags,
                created=zd_ticket.created_at,
                updated=zd_ticket.updated_at,
            ),
        )

        # sync comments that exist - for a new ticket, there may be none
        # as the first message is the ticket.description
        comments = self.sync_comments(zd_ticket, ticket)

        # it's possible the ticket isn't new but this is the first we're
        # seeing of it, so only fire the new_ticket if there are no comments
        is_new_ticket = created and not comments

        if is_new_ticket:
            signals.new_ticket.send(sender=Ticket, ticket=ticket)
            print("New ticket!")

        elif len(comments) > len(pre_comments):
            new_comment_ids = set([c.zendesk_id for c in comments]) - set(
                [c.zendesk_id for c in pre_comments]
            )
            new_comments = [c for c in comments if c.zendesk_id in new_comment_ids]
            if new_comments:
                print("New comments!")
                signals.new_comments.send(
                    sender=Ticket, ticket=ticket, comments=new_comments
                )

        if (
            not is_new_ticket
            and pre_ticket
            and pre_ticket.custom_fields != ticket.custom_fields
        ):
            print(ticket.custom_fields)
            print("Custom fields have changed!")

        # # except tags will always have changed it custom fields have changed due
        # # to how Zendesk has implemented this
        # if not created and pre_ticket.tags != ticket.tags:
        #     print("Tags have changed!")

        return ticket

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
            self.sync_ticket_id(ticket_id)

    def sync_comments(self, zd_ticket, ticket):
        comments = []
        # no need to sync the ticket requester as we'll have just done that
        user_map = {zd_ticket.requester: ticket.zendesk_user}
        for comment in get_zenpy_client().tickets.comments(zd_ticket.id):
            if comment.author not in user_map:
                author = self.sync_user(comment.author)
                user_map[comment.author] = author
            else:
                author = user_map[comment.author]
            instance, created = Comment.objects.update_or_create(
                zendesk_id=comment.id,
                ticket=ticket,
                defaults=dict(
                    # todo: avoid syncing same user over and over
                    author=author,
                    body=comment.body,
                    public=comment.public,
                    created=comment.created_at,
                ),
            )
            comments.append(instance)
        # sort increasing by created and id
        comments.sort(key=lambda x: (x.created, x.id))
        return comments


def import_attribute(path):
    assert isinstance(path, str)
    pkg, attr = path.rsplit('.', 1)
    ret = getattr(importlib.import_module(pkg), attr)
    return ret


def get_service():
    cls = app_settings.SERVICE_CLASS
    if cls is None:
        return ZengoService()
    return import_attribute(cls)()
