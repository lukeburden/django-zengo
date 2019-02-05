# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from copy import copy

from django.core.exceptions import ValidationError

try:
    from django.urls import reverse
except ImportError:
    # fall back to < 2
    from django.core.urlresolvers import reverse

from model_mommy import mommy

import pytest

import responses

from zengo import service
from zengo import strings
from zengo.models import Event, Ticket

from . import api_responses


# test processor methods
def add_api_responses_no_comment():
    responses.add(
        responses.Response(
            method="GET",
            url="https://example.zendesk.com/api/v2/tickets/123.json",
            match_querystring=False,
            json=api_responses.new_ticket,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://example.zendesk.com/api/v2/users/1.json",
            match_querystring=False,
            json=api_responses.requester,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://example.zendesk.com/api/v2/users/2.json",
            match_querystring=False,
            json=api_responses.submitter,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://example.zendesk.com/api/v2/tickets/123/comments.json",
            match_querystring=False,
            json=api_responses.no_comments,
            status=200,
        )
    )


@pytest.mark.django_db
def test_processor_store_event_empty_body():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("")
    assert exc_info.value.message == strings.data_malformed


@pytest.mark.django_db
def test_processor_store_event_no_ticket_id():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("{}")
    assert exc_info.value.message == strings.data_no_ticket_id


@pytest.mark.django_db
def test_processor_store_event_no_ticket_int_id():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("""{"id": "donkey"}""")
    assert exc_info.value.message == strings.data_no_ticket_id


@pytest.mark.django_db
def test_processor_store_event_ok():
    processor = service.ZengoProcessor()
    data = """{"id": 123}"""
    event = processor.store_event(data)
    assert event.raw_data == data
    assert event.json == {"id": 123}
    assert event.remote_ticket_id == 123


@pytest.mark.django_db
def test_processor_begin_processing_event(mocker):
    # not much to test here, just that it chains through
    processor = service.ZengoProcessor()
    processor.process_event_and_record_errors = mocker.Mock()
    processor.begin_processing_event("event")
    assert processor.process_event_and_record_errors.called


@pytest.mark.django_db
def test_processor_process_event_and_record_errors_error(mocker):
    processor = service.ZengoProcessor()
    event = processor.store_event("""{"id": 123}""")

    def broken_process_event(*args, **kwargs):
        raise ValueError("hoho")

    processor.process_event = broken_process_event
    with pytest.raises(ValueError):
        processor.process_event_and_record_errors(event)

    assert event.error is not None


@responses.activate
@pytest.mark.django_db
def test_processor_process_event_and_record_errors_ok(mocker):
    processor = service.ZengoProcessor()
    event = processor.store_event("""{"id": 123}""")
    processor.process_event = mocker.Mock()
    processor.process_event_and_record_errors(event)
    assert processor.process_event.called_with_args(event)
    assert event.error is None


@responses.activate
@pytest.mark.django_db
def test_processor_process_event_ticket_created(mocker):
    processor = service.ZengoProcessor()
    event = processor.store_event("""{"id": 123}""")

    # setup fake API
    add_api_responses_no_comment()

    mocked_created_signal = mocker.patch("zengo.signals.ticket_created.send")
    mocked_updated_signal = mocker.patch("zengo.signals.ticket_updated.send")
    processor.process_event(event)

    # ticket should now exist
    ticket = Ticket.objects.get(zendesk_id=123)

    update_context = {
        "pre_ticket": ticket,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [],
    }

    assert mocked_created_signal.called_with_args(
        sender=Ticket, ticket=ticket, context=update_context
    )
    assert not mocked_updated_signal.called


@responses.activate
@pytest.mark.django_db
def test_processor_process_event_ticket_updated(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=123, requester__zendesk_id=1)
    event = processor.store_event("""{"id": 123}""")
    add_api_responses_no_comment()

    mocked_created_signal = mocker.patch("zengo.signals.ticket_created.send")
    mocked_updated_signal = mocker.patch("zengo.signals.ticket_updated.send")

    processor.process_event(event)

    assert not mocked_created_signal.called
    update_context = {
        "pre_ticket": ticket,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [],
    }

    assert mocked_updated_signal.called_with_args(
        sender=Ticket,
        ticket=ticket,
        context=update_context,
        updates=service.ZengoProcessor().get_updates(**update_context),
    )


@pytest.mark.django_db
def test_processor_get_new_comments_new_ticket(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=123, requester__zendesk_id=1)

    update_context = {
        "pre_ticket": None,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [],
    }

    assert processor.get_new_comments(**update_context) == []


@pytest.mark.django_db
def test_processor_get_new_comments_new_ticket_plus_comment(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=123, requester__zendesk_id=1)
    comment = mommy.make("zengo.Comment", ticket=ticket)
    update_context = {
        "pre_ticket": None,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [comment],
    }
    assert processor.get_new_comments(**update_context) == [comment]


@pytest.mark.django_db
def test_processor_get_new_comments_existing_ticket_plus_comment(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=123, requester__zendesk_id=1)
    comment = mommy.make("zengo.Comment", ticket=ticket)
    another_comment = mommy.make("zengo.Comment", ticket=ticket)
    update_context = {
        "pre_ticket": ticket,
        "post_ticket": ticket,
        "pre_comments": [comment],
        "post_comments": [comment, another_comment],
    }
    assert processor.get_new_comments(**update_context) == [another_comment]


@pytest.mark.django_db
def test_processor_get_updated_fields_no_changes(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket")
    update_context = {
        "pre_ticket": ticket,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [],
    }
    assert processor.get_updated_fields(**update_context) == {}


@pytest.mark.django_db
def test_processor_get_updated_fields_several_fields_changed(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make(
        "zengo.Ticket",
        zendesk_id=123,
        requester__zendesk_id=1,
        custom_fields="some json text",
        status=Ticket.states.open,
    )
    post_ticket = copy(ticket)
    post_ticket.custom_fields = "different json text"
    post_ticket.status = Ticket.states.pending
    update_context = {
        "pre_ticket": ticket,
        "post_ticket": post_ticket,
        "pre_comments": [],
        "post_comments": [],
    }
    assert processor.get_updated_fields(**update_context) == {
        "custom_fields": {"new": "different json text", "old": "some json text"},
        "status": {"new": Ticket.states.pending, "old": Ticket.states.open},
    }


# test service methods


# test WebhookView


@pytest.mark.django_db
def test_webhook_view_missing_secret(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view"), data=json.dumps(
            {"id": 123}
        ),
        content_type="application/json"
    )
    assert response.status_code == 403
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0


@pytest.mark.django_db
def test_webhook_view_invalid_secret(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view") + "?secret=face", data=json.dumps(
            {"id": 123}
        ),
        content_type="application/json"
    )
    assert response.status_code == 403
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0


@pytest.mark.django_db
def test_webhook_view_no_body(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom",
        content_type="application/json"
    )
    assert response.status_code == 400
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.raw_data == "{}"
    assert Ticket.objects.count() == 0


@pytest.mark.django_db
def test_webhook_view_invalid_body(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom", data="iamnbotjosn.{}",
        content_type="application/json"
    )
    assert response.status_code == 400
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.raw_data == "iamnbotjosn.{}"
    # no processing yet, so error is still none
    assert event.error is None
    # and the `json` property will be unhappy
    with pytest.raises(ValueError):
        event.json()


@responses.activate
@pytest.mark.django_db
def test_webhook_view_ok(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom", data=json.dumps(
            {"id": 123}
        ),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert Event.objects.count() == 1
    assert Ticket.objects.count() == 1


# test service methods


@pytest.mark.django_db
def test_get_local_user_name():
    user = mommy.make("auth.User")
    assert service.ZengoService().get_local_user_name(user) == user.first_name


@pytest.mark.django_db
def test_get_local_user_external_id():
    user = mommy.make("auth.User")
    assert service.ZengoService().get_local_user_external_id(user) == user.id


@pytest.mark.django_db
def test_get_local_user_for_external_id():
    user = mommy.make("auth.User")
    assert service.ZengoService().get_local_user_for_external_id(user.id) == user


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_no_matches():
    user = mommy.make("auth.User", id=1)
    responses.add(
        responses.Response(
            method="GET",
            url="""https://example.zendesk.com/api/v2/search.json""",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # there will be no match, all searches return no results
    assert service.ZengoService().get_remote_zd_user_for_local_user(user) == (None, False)


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_with_external_id_match():
    user = mommy.make("auth.User", id=1)
    responses.add(
        responses.Response(
            method="GET",
            url="""https://example.zendesk.com/api/v2/search.json""",
            match_querystring=False,
            json=api_responses.search_by_external_id_matches,
            status=200,
        )
    )
    # there will be a strong match based on external id
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert is_definite
    assert remote.external_id == user.id


#     def get_remote_zd_user_for_local_user(self, local_user):
#         """
#         Attempt to resolve the provided user to an extant Zendesk User.

#         Returns a Zendesk API User instance, and a boolean that indicates how
#         definite the resolution is, based on how they've been found.
#         """
#         result = self.client.search(
#             type="user", external_id=self.get_local_user_external_id(local_user)
#         )
#         if result.count:
#             # strong match by external_id
#             return result.next(), True

#         # else check by associated emails, if allauth is installed and being used
#         if 'allauth.account' in settings.INSTALLED_APPS:
#             emails = local_user.emailaddress_set.all()
#             for e in emails:
#                 result = self.client.search(type="user", email=e.email)
#                 if result.count:
#                     # match strength based on email verification state
#                     return result.next(), e.verified

#         # check for a weak match using the email field on user instance
#         if local_user.email:
#             result = self.client.search(type="user", email=local_user.email)
#             if result.count:
#                 return result.next(), False

#         # no match at all, buh-bow
#         return None, False

#     def create_remote_zd_user_for_local_user(self, local_user):
#         """Create a remote zendesk user based on the given local user's details."""
#         try:
#             remote_zd_user = self.client.users.create(
#                 RemoteZendeskUser(
#                     name=self.get_local_user_name(local_user),
#                     external_id=self.get_local_user_external_id(local_user),
#                     email=local_user.email,
#                     remote_photo_url=self.get_local_user_profile_image(local_user),
#                 )
#             )
#         except APIException as a:
#             # if this is a duplicate error try one last time to get the user
#             details = a.response.json()["details"]
#             if any([d[0]["error"] for d in details.values()]):
#                 remote_zd_user, is_definite_match = self.get_remote_zd_user_for_local_user(
#                     local_user
#                 )
#             else:
#                 raise
#         return remote_zd_user

#     def get_or_create_remote_zd_user_for_local_user(self, local_user):
#         user, is_definite_match = self.get_remote_zd_user_for_local_user(local_user)
#         if user:
#             return user, is_definite_match
#         # we create a remote user in Zendesk for this local user
#         return self.create_remote_zd_user_for_local_user(local_user), True

#     def update_remote_zd_user_for_local_user(self, local_user, remote_zd_user):
#         """
#         Compare the User and ZendeskUser instances and determine whether we
#         need to update the data in Zendesk.

#         This method is suitable to be called when a local user changes their
#         email address or other user data.
#         """
#         changed = False
#         email_changed = False

#         if self.get_local_user_name() != remote_zd_user.name:
#             remote_zd_user.name = self.get_local_user_name(local_user)
#             changed = True

#         if self.get_local_user_external_id(local_user) != remote_zd_user.external_id:
#             remote_zd_user.external_id = self.get_local_user_external_id(local_user)
#             changed = True

#         if local_user.email and local_user.email != remote_zd_user.email:
#             remote_zd_user.email = local_user.email
#             changed = True
#             email_changed = True

#         if changed:
#             remote_zd_user = self.client.users.update(remote_zd_user)

#         if email_changed:
#             # then in addition to the above, we have to mark the newly
#             # created identity as verified and promote it to be primary
#             results = self.client.users.identities(id=remote_zd_user.id)
#             for identity in results:
#                 if identity.value == local_user.email:
#                     self.client.users.identities.make_primary(
#                         user=remote_zd_user, identity=identity
#                     )
#                     break

#     def update_or_create_remote_zd_user(self, local_user):
#         remote_zd_user, is_definite_match = self.get_remote_zd_user_for_local_user(
#             local_user
#         )
#         if remote_zd_user and is_definite_match:
#             # check if we need to do any updates
#             self.update_remote_zd_user_for_local_user(local_user, remote_zd_user)
#         else:
#             remote_zd_user = self.create_remote_zd_user_for_local_user(local_user)
#         return remote_zd_user

#     def update_or_create_local_zd_user_for_remote_zd_user(self, remote_zd_user):
#         """
#         Given a RemoteZendeskUser instance, persist it as a LocalZendeskUser instance.
#         """
#         instance, created = LocalZendeskUser.objects.update_or_create(
#             zendesk_id=remote_zd_user.id,
#             defaults=dict(
#                 # attempt to resolve the local user if possible
#                 user=self.get_local_user_for_external_id(remote_zd_user.external_id),
#                 email=remote_zd_user.email,
#                 created_at=remote_zd_user.created_at,
#                 name=remote_zd_user.name,
#                 active=remote_zd_user.active,
#                 role=remote_zd_user.role,
#                 # store their latest photo JSON data
#                 photos_json=json.dumps(remote_zd_user.photo),
#             ),
#         )
#         return instance

#     def sync_ticket_id(self, ticket_id):
#         return self.sync_ticket(self.client.tickets(id=ticket_id))

#     def sync_ticket(self, remote_zd_ticket):
#         """
#         Given a remote Zendesk ticket, store its details, comments and associated users.
#         """
#         # sync the ticket and comments to establish the new state
#         local_zd_user = self.update_or_create_local_zd_user_for_remote_zd_user(
#             remote_zd_ticket.requester
#         )

#         local_ticket, created = Ticket.objects.update_or_create(
#             zendesk_id=remote_zd_ticket.id,
#             defaults=dict(
#                 requester=local_zd_user,
#                 subject=remote_zd_ticket.subject,
#                 url=remote_zd_ticket.url,
#                 status=Ticket.states.by_id.get(remote_zd_ticket.status.lower()),
#                 custom_fields=json.dumps(remote_zd_ticket.custom_fields),
#                 tags=json.dumps(remote_zd_ticket.tags),
#                 created_at=remote_zd_ticket.created_at,
#                 updated_at=remote_zd_ticket.updated_at,
#             ),
#         )
#         self.sync_comments(remote_zd_ticket, local_ticket)

#         return local_ticket, created

#     def sync_comments(self, zd_ticket, local_ticket):
#         local_comments = []
#         # no need to sync the ticket requester as we'll have just done that
#         user_map = {zd_ticket.requester: local_ticket.requester}
#         for remote_comment in self.client.tickets.comments(zd_ticket.id):
#             if remote_comment.author not in user_map:
#                 author = self.update_or_create_local_zd_user_for_remote_zd_user(
#                     remote_comment.author
#                 )
#                 user_map[remote_comment.author] = author
#             else:
#                 author = user_map[remote_comment.author]
#             local_comment, created = Comment.objects.update_or_create(
#                 zendesk_id=remote_comment.id,
#                 ticket=local_ticket,
#                 defaults=dict(
#                     author=author,
#                     body=remote_comment.body,
#                     public=remote_comment.public,
#                     created_at=remote_comment.created_at,
#                 ),
#             )
#             local_comments.append(local_comment)
#         # sort increasing by created and id
#         local_comments.sort(key=lambda c: (c.created_at, c.id))
#         return local_comments
