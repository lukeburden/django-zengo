# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from copy import copy

import dateutil

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
from zengo.models import Comment, Event, Ticket

from . import api_responses


api_url_base = "https://example.zendesk.com/api/v2/"


# test processor methods
def add_api_responses(comments=None):
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "tickets/1.json",
            match_querystring=False,
            json=api_responses.new_ticket,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "users/1.json",
            match_querystring=False,
            json=api_responses.requester,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "users/2.json",
            match_querystring=False,
            json=api_responses.submitter,
            status=200,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "tickets/1/comments.json",
            match_querystring=False,
            json=comments if comments else api_responses.no_comments,
            status=200,
        )
    )


@responses.activate
@pytest.mark.django_db
def test_processor_store_event_empty_body():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("")
    assert exc_info.value.message == strings.data_malformed


@responses.activate
@pytest.mark.django_db
def test_processor_store_event_no_ticket_id():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("{}")
    assert exc_info.value.message == strings.data_no_ticket_id


@responses.activate
@pytest.mark.django_db
def test_processor_store_event_no_ticket_int_id():
    processor = service.ZengoProcessor()
    with pytest.raises(ValidationError) as exc_info:
        processor.store_event("""{"id": "donkey"}""")
    assert exc_info.value.message == strings.data_no_ticket_id


@responses.activate
@pytest.mark.django_db
def test_processor_store_event_ok():
    processor = service.ZengoProcessor()
    data = """{"id": 1}"""
    event = processor.store_event(data)
    assert event.raw_data == data
    assert event.json == {"id": 1}
    assert event.remote_ticket_id == 1


@responses.activate
@pytest.mark.django_db
def test_processor_begin_processing_event(mocker):
    # not much to test here, just that it chains through
    processor = service.ZengoProcessor()
    processor.process_event_and_record_errors = mocker.Mock()
    processor.begin_processing_event("event")
    assert processor.process_event_and_record_errors.called


@responses.activate
@pytest.mark.django_db
def test_processor_process_event_and_record_errors_error(mocker):
    processor = service.ZengoProcessor()
    event = processor.store_event("""{"id": 1}""")

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
    event = processor.store_event("""{"id": 1}""")
    processor.process_event = mocker.Mock()
    processor.process_event_and_record_errors(event)
    assert processor.process_event.called_with_args(event)
    assert event.error is None


@responses.activate
@pytest.mark.django_db
def test_processor_process_event_ticket_created(mocker):
    processor = service.ZengoProcessor()
    event = processor.store_event("""{"id": 1}""")

    # setup fake API
    add_api_responses()

    mocked_created_signal = mocker.patch("zengo.signals.ticket_created.send")
    mocked_updated_signal = mocker.patch("zengo.signals.ticket_updated.send")
    processor.process_event(event)

    # ticket should now exist
    ticket = Ticket.objects.get(zendesk_id=1)

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
    ticket = mommy.make("zengo.Ticket", zendesk_id=1, requester__zendesk_id=1)
    event = processor.store_event("""{"id": 1}""")
    add_api_responses()

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


@responses.activate
@pytest.mark.django_db
def test_processor_get_new_comments_new_ticket(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=1, requester__zendesk_id=1)

    update_context = {
        "pre_ticket": None,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [],
    }

    assert processor.get_new_comments(**update_context) == []


@responses.activate
@pytest.mark.django_db
def test_processor_get_new_comments_new_ticket_plus_comment(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=1, requester__zendesk_id=1)
    comment = mommy.make("zengo.Comment", ticket=ticket)
    update_context = {
        "pre_ticket": None,
        "post_ticket": ticket,
        "pre_comments": [],
        "post_comments": [comment],
    }
    assert processor.get_new_comments(**update_context) == [comment]


@responses.activate
@pytest.mark.django_db
def test_processor_get_new_comments_existing_ticket_plus_comment(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make("zengo.Ticket", zendesk_id=1, requester__zendesk_id=1)
    comment = mommy.make("zengo.Comment", ticket=ticket)
    another_comment = mommy.make("zengo.Comment", ticket=ticket)
    update_context = {
        "pre_ticket": ticket,
        "post_ticket": ticket,
        "pre_comments": [comment],
        "post_comments": [comment, another_comment],
    }
    assert processor.get_new_comments(**update_context) == [another_comment]


@responses.activate
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


@responses.activate
@pytest.mark.django_db
def test_processor_get_updated_fields_several_fields_changed(mocker):
    processor = service.ZengoProcessor()
    ticket = mommy.make(
        "zengo.Ticket",
        zendesk_id=1,
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


# test WebhookView


@responses.activate
@pytest.mark.django_db
def test_webhook_view_missing_secret(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses()
    response = client.post(
        reverse("webhook_view"),
        data=json.dumps({"id": 1}),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0


@responses.activate
@pytest.mark.django_db
def test_webhook_view_invalid_secret(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses()
    response = client.post(
        reverse("webhook_view") + "?secret=face",
        data=json.dumps({"id": 1}),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0


@responses.activate
@pytest.mark.django_db
def test_webhook_view_no_body(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom", content_type="application/json"
    )
    assert response.status_code == 400
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.raw_data == "{}"
    assert Ticket.objects.count() == 0


@responses.activate
@pytest.mark.django_db
def test_webhook_view_invalid_body(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom",
        data="iamnbotjosn.{}",
        content_type="application/json",
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
    add_api_responses()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom",
        data=json.dumps({"id": 1}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert Event.objects.count() == 1
    assert Ticket.objects.count() == 1


# test service methods


@responses.activate
@pytest.mark.django_db
def test_get_local_user_name():
    user = mommy.make("auth.User")
    assert service.ZengoService().get_local_user_name(user) == user.first_name


@responses.activate
@pytest.mark.django_db
def test_get_local_user_external_id():
    user = mommy.make("auth.User")
    assert service.ZengoService().get_local_user_external_id(user) == user.id


@responses.activate
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
            url=api_url_base + "search.json",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # there will be no match, all searches return no results
    assert service.ZengoService().get_remote_zd_user_for_local_user(user) == (
        None,
        False,
    )


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_with_external_id_match():
    user = mommy.make("auth.User", id=1)
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # there will be a strong match based on external id
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert is_definite
    assert remote.external_id == user.id


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_with_allauth_email():
    user = mommy.make("auth.User", id=1)
    # no search results when searching by external ID
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=external_id:1%20type:user",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:user%20external_id:1",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )

    email = mommy.make(
        "account.EmailAddress", user=user, verified=False, email="monica@example.com"
    )
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=email:monica@example.com%20type:user",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above but sometimes query params are reversed in order
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:user%20email:monica@example.com",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert not is_definite
    assert remote.email == email.email

    # adjust the local email to be verified
    email.verified = True
    email.save(update_fields=("verified",))

    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert is_definite
    assert remote.email == email.email


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_with_user_email_attribute():
    user = mommy.make("auth.User", id=1, email="monica@example.com")
    # no search results when searching by external ID
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=external_id:1%20type:user",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:user%20external_id:1",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # and a single result when searching by email
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=email:monica@example.com%20type:user",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above but sometimes query params are reversed in order
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:user%20email:monica@example.com",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert not is_definite
    assert remote.email == user.email


@responses.activate
@pytest.mark.django_db
def test_get_remote_zd_user_for_local_user_no_match():
    user = mommy.make("auth.User")
    # same as above but sometimes query params are reversed in order
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)
    assert not is_definite
    assert remote is None


@responses.activate
@pytest.mark.django_db
def test_create_remote_zd_user_for_local_user():
    user = mommy.make("auth.User")
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json" "",
            match_querystring=False,
            json=api_responses.create_user_result,
            status=201,
        )
    )
    remote = service.ZengoService().create_remote_zd_user_for_local_user(user)
    assert remote.email == "monica@example.com"


@responses.activate
@pytest.mark.django_db
def test_create_remote_zd_user_for_local_user_dupe_detected():
    user = mommy.make("auth.User")
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json" "",
            match_querystring=False,
            json=api_responses.create_user_dupe,
            status=400,
        )
    )

    # and then a search by external ID will return the one user
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=external_id:1%20type:user",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:user%20external_id:1",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )

    remote = service.ZengoService().create_remote_zd_user_for_local_user(user)
    assert remote.email == "monica@example.com"


@responses.activate
@pytest.mark.django_db
def test_get_or_create_remote_zd_user_for_local_user_get():
    user = mommy.make("auth.User")
    # search by external ID returns a result
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(
        user
    )
    # user will be found based on external ID, so definite
    assert is_definite
    assert remote is not None


@responses.activate
@pytest.mark.django_db
def test_get_or_create_remote_zd_user_for_local_user_create():
    user = mommy.make("auth.User")
    # all searches return no result
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # creation works
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json" "",
            match_querystring=False,
            json=api_responses.create_user_result,
            status=201,
        )
    )
    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(
        user
    )
    # user will be created with external ID set
    assert is_definite
    assert remote is not None


@responses.activate
@pytest.mark.django_db
def test_update_remote_zd_user_for_local_user():
    user = mommy.make("auth.User", email="monica@example.com")

    # any search returns our one user
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )

    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(
        user
    )

    assert remote is not None
    assert remote.email == "monica@example.com"

    # make a change of the user's email, triggering an identity update
    user.email = "monica2@example.com"

    # our individual user updated
    responses.add(
        responses.Response(
            method="PUT",
            url=api_url_base + "users/1.json",
            match_querystring=False,
            json=api_responses.update_user_ok,
            status=200,
        )
    )

    # add support for looking up a user's identities
    responses.add(
        responses.Response(
            method="GET",
            url="https:////example.zendesk.com/api/v2/users/1/identities.json",
            match_querystring=False,
            json=api_responses.user_identities,
            status=200,
        )
    )

    # and when the second identity is found, it will be made primary
    responses.add(
        responses.Response(
            method="PUT",
            url=api_url_base + "users/1/identities/2/make_primary",
            match_querystring=False,
            json=api_responses.identity_make_primary,
            status=200,
        )
    )

    service.ZengoService().update_remote_zd_user_for_local_user(user, remote)

    assert len(responses.calls) == 4


@responses.activate
@pytest.mark.django_db
def test_update_or_create_remote_zd_user_create():
    # all searches return no results
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # creation of a user will work
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json" "",
            match_querystring=False,
            json=api_responses.create_user_result,
            status=201,
        )
    )
    user = mommy.make("auth.User")
    remote = service.ZengoService().update_or_create_remote_zd_user(user)
    assert remote is not None
    assert len(responses.calls) == 2


@responses.activate
@pytest.mark.django_db
def test_update_or_create_remote_zd_user_update():
    # all searches return no results
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    user = mommy.make("auth.User")
    user.email = "monica2@example.com"
    user.save(update_fields=("email",))

    # our individual user updated
    responses.add(
        responses.Response(
            method="PUT",
            url=api_url_base + "users/1.json",
            match_querystring=False,
            json=api_responses.update_user_ok,
            status=200,
        )
    )

    # add support for looking up a user's identities
    responses.add(
        responses.Response(
            method="GET",
            url="https:////example.zendesk.com/api/v2/users/1/identities.json",
            match_querystring=False,
            json=api_responses.user_identities,
            status=200,
        )
    )

    # and when the second identity is found, it will be made primary
    responses.add(
        responses.Response(
            method="PUT",
            url=api_url_base + "users/1/identities/2/make_primary",
            match_querystring=False,
            json=api_responses.identity_make_primary,
            status=200,
        )
    )

    remote = service.ZengoService().update_or_create_remote_zd_user(user)
    assert remote is not None
    assert len(responses.calls) == 4


@responses.activate
@pytest.mark.django_db
def test_sync_user():
    user = mommy.make("auth.User", id=1)
    # allow for discovery of a remote user
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json" "",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_remote_zd_user_for_local_user(user)

    # this is a local instance representing the remote ZD user
    local_zd_user = service.ZengoService().sync_user(remote)

    assert local_zd_user.zendesk_id == remote.id
    assert local_zd_user.email == remote.email
    assert local_zd_user.alias == remote.alias
    # user should be found and linked
    assert local_zd_user.user == user
    assert local_zd_user.created_at == remote.created_at
    assert local_zd_user.name == remote.name
    assert local_zd_user.active == remote.active
    assert local_zd_user.role == remote.role
    assert json.loads(local_zd_user.photos_json) == remote.photo


@responses.activate
@pytest.mark.django_db
def test_sync_ticket():
    # allow for fetching of a ticket with no comments
    add_api_responses()
    remote_ticket = service.ZengoService().client.tickets(id=1)
    local_ticket, created = service.ZengoService().sync_ticket(remote_ticket)

    assert created
    assert local_ticket.zendesk_id == remote_ticket.id
    assert local_ticket.requester.zendesk_id == remote_ticket.requester.id
    assert local_ticket.subject == remote_ticket.subject
    assert local_ticket.url == remote_ticket.url
    assert local_ticket.status == remote_ticket.status
    assert json.loads(local_ticket.custom_fields) == remote_ticket.custom_fields
    assert json.loads(local_ticket.tags) == remote_ticket.tags
    assert local_ticket.created_at == remote_ticket.created_at
    assert local_ticket.updated_at == remote_ticket.updated_at

    assert local_ticket.comments.count() == 0

    assert len(responses.calls) == 3


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_id():
    # allow for fetching of a ticket with no comments
    add_api_responses()
    local_ticket, created = service.ZengoService().sync_ticket_id(1)
    assert created
    assert local_ticket is not None
    assert len(responses.calls) == 3


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_with_comments():
    add_api_responses(comments=api_responses.two_comments)

    assert Comment.objects.count() == 0
    local_ticket, created = service.ZengoService().sync_ticket_id(1)
    assert created
    local_comments = local_ticket.comments.all()
    assert local_comments.count() == 2

    remote_comments = service.ZengoService().client.tickets.comments(1)
    remote = list(remote_comments)[0]
    local = local_comments.first()

    assert local.zendesk_id == remote.id
    assert local.ticket == local_ticket
    assert local.author.zendesk_id == remote.author.id
    assert local.body == remote.body
    assert local.html_body == remote.html_body
    assert local.plain_body == remote.plain_body
    assert local.public == remote.public
    assert local.created_at == dateutil.parser.parse(remote.created_at)


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_already_exists_with_one_comment():
    add_api_responses(comments=api_responses.two_comments)
    # assume local ticket has already been sync'd along with a single comment
    local_ticket = mommy.make("zengo.Ticket", zendesk_id=1)
    remote_ticket = service.ZengoService().client.tickets(id=1)
    remote_comments = list(
        service.ZengoService().client.tickets.comments(remote_ticket.id)
    )
    mommy.make("zengo.Comment", zendesk_id=remote_comments[0].id, ticket=local_ticket)

    assert local_ticket.comments.count() == 1

    # now sync comments, which should discover the second comment
    local_ticket, created = service.ZengoService().sync_ticket_id(1)
    assert not created
    local_comments = local_ticket.comments.all()
    assert local_comments.count() == 2

    # ensure the later comment is the same as the remote
    remote = remote_comments[1]
    local = local_comments[1]

    assert local.zendesk_id == remote.id
    assert local.ticket == local_ticket
    assert local.author.zendesk_id == remote.author.id
    assert local.body == remote.body
    assert local.public == remote.public
    assert local.created_at == dateutil.parser.parse(remote.created_at)


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_with_attachments():
    add_api_responses(comments=api_responses.two_comments_with_attachments)

    local_ticket, created = service.ZengoService().sync_ticket_id(1)

    local_comments = local_ticket.comments.all()
    assert local_comments.count() == 2

    # there should be three attachments on the first comment
    assert local_comments[0].attachments.count() == 3
    # and only one on the second
    assert local_comments[1].attachments.count() == 1

    # first attachment is an inline image from the Zendesk webapp
    local = local_comments[0].attachments.all()[0]

    assert local.zendesk_id == 365674118331
    assert (
        local.file_name
        == "IMG_20190101_001154-some-really-ridiculously-long-file-name-how-could-people-bring-themselves-to-be-this-verbose-but-really-how-and-what-is-it-they-hoped-to-achieve-is-it-world-domination-or-an-abomination-foos.jpg"
    )
    assert (
        local.content_url
        == "https://example.zendesk.com/attachments/token/jFGBxOznWMG8lWRXUt0DAi1UQ/?name=IMG_20190101_001154-some-really-ridiculously-long-file-name-how-could-people-bring-themselves-to-be-this-verbose-but-really-how-and-what-is-it-they-hoped-to-achieve-is-it-world-domination-or-an-abomination-foos.jpg"
    )  # noqa
    assert local.content_type == "image/jpeg"
    assert local.size == 2599824
    assert local.width == 4032
    assert local.height == 3024
    assert local.inline
    assert local.photos.count() == 1
    photo = local.photos.first()
    assert photo.zendesk_id == 365674118571
    assert photo.file_name == "IMG_20190101_001154_thumb.jpg"
    assert (
        photo.content_url
        == "https://example.zendesk.com/attachments/token/MFe8s8o4hbPI6suwHBdkvMWgV/?name=IMG_20190101_001154_thumb.jpg"
    )  # noqa
    assert photo.content_type == "image/jpeg"
    assert photo.size == 2694
    assert photo.width == 80
    assert photo.height == 60

    # second attachment is an image but not inline
    local = local_comments[0].attachments.all()[1]
    assert local.zendesk_id == 365692390412
    assert local.file_name == "download.jpg"
    assert (
        local.content_url
        == "https://example.zendesk.com/attachments/token/JzYm4m7TNc3ZXlbNhgZDC2ugs/?name=download.jpg"
    )  # noqa
    assert local.content_type == "image/jpeg"
    assert local.size == 6339
    assert local.width == 242
    assert local.height == 208
    assert not local.inline
    assert local.photos.count() == 1
    photo = local.photos.first()
    assert photo.zendesk_id == 365692390492
    assert photo.file_name == "download_thumb.jpg"
    assert (
        photo.content_url
        == "https://example.zendesk.com/attachments/token/aNdp5xiwsW2u96U7IaZApCdk5/?name=download_thumb.jpg"
    )  # noqa
    assert photo.content_type == "image/jpeg"
    assert photo.size == 1917
    assert photo.width == 80
    assert photo.height == 69

    # third attachment is a PDF
    local = local_comments[0].attachments.all()[2]
    assert local.zendesk_id == 365692415672
    assert local.file_name == "lyft-2019-02-24.pdf"
    assert (
        local.content_url
        == "https://example.zendesk.com/attachments/token/2AO6OpL1pdAn6ouPrG9CpLeky/?name=lyft-2019-02-24.pdf"
    )  # noqa
    assert local.content_type == "application/pdf"
    assert local.size == 622787
    assert local.width is None
    assert local.height is None
    assert not local.inline
    assert local.photos.count() == 0

    # fourth attachment is an inline image that came in via email
    # but it is not functionally different to the first attachment
    local = local_comments[1].attachments.all()[0]
    assert local.zendesk_id == 365692692292
    assert local.file_name == "fuse.jpg"
    assert (
        local.content_url
        == "https://example.zendesk.com/attachments/token/EcuesBNtbQm3I3FLvuDP9kpUK/?name=fuse.jpg"
    )
    assert local.content_type == "image/jpeg"
    assert local.size == 48754
    # for some reason, when sending via email, the main attachment's
    # dimensions are not available
    assert local.width is None
    assert local.height is None
    assert local.inline
    assert local.photos.count() == 1
    photo = local.photos.first()
    assert photo.zendesk_id == 365674480751
    assert photo.file_name == "fuse_thumb.jpg"
    assert (
        photo.content_url
        == "https://example.zendesk.com/attachments/token/BvMqGiqQg9t1Kt8egzlmz87l4/?name=fuse_thumb.jpg"
    )  # noqa
    assert photo.content_type == "image/jpeg"
    assert photo.size == 1588
    assert photo.width == 80
    assert photo.height == 45


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_with_voice_comment():
    # ensure our sync doesn't trip up on a VoiceComment
    add_api_responses(comments=api_responses.voice_comment)

    local_ticket, created = service.ZengoService().sync_ticket_id(1)

    local_comments = local_ticket.comments.all()
    assert local_comments.count() == 1

    # no plain_body is available
    assert local_comments[0].plain_body is None


@responses.activate
@pytest.mark.django_db
def test_sync_ticket_with_comment_with_no_author():
    # when a comment on a ticket has an author value of `-1`, this is
    # Zendesk adding a comment usually to do with some ticket merging
    # As these messages have mostly low-value to users, we just skip
    # them for now.
    add_api_responses(comments=api_responses.comment_with_no_author)

    local_ticket, created = service.ZengoService().sync_ticket_id(1)

    local_comments = local_ticket.comments.all()
    assert local_comments.count() == 3
    assert local_comments[0].author.zendesk_id == 1
    assert local_comments[1].author.zendesk_id == -1
    assert not local_comments[1].public
    assert local_comments[2].author.zendesk_id == 2


@responses.activate
@pytest.mark.django_db
def test_get_special_zendesk_user():
    user = service.ZengoService().get_special_zendesk_user()
    assert user.zendesk_id == -1
    assert user.name == "Zendesk"
    assert user.role.admin

    # and it will only be created once
    user_2 = service.ZengoService().get_special_zendesk_user()
    assert user.id == user_2.id
