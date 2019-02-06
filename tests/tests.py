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
from zengo.models import Comment, Event, Ticket

from . import api_responses


api_url_base = "https://example.zendesk.com/api/v2/"


# test processor methods
def add_api_responses(comments=None):
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "tickets/123.json",
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
            url=api_url_base + "tickets/123/comments.json",
            match_querystring=False,
            json=comments if comments else api_responses.no_comments,
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
    add_api_responses()

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


# test WebhookView


@pytest.mark.django_db
def test_webhook_view_missing_secret(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses()
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
    add_api_responses()
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
    add_api_responses()
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
    add_api_responses()
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
    add_api_responses()
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
            url=api_url_base + "search.json",
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
            url=api_url_base + "search.json?query=external_id:%221%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20external_id:%221%22",
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
            url=api_url_base + "search.json?query=email:%22monica@example.com%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above but sometimes query params are reversed in order
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20email:%22monica@example.com%22",
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
    email.save(update_fields=('verified',))

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
            url=api_url_base + "search.json?query=external_id:%221%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20external_id:%221%22",
            match_querystring=True,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # and a single result when searching by email
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=email:%22monica@example.com%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above but sometimes query params are reversed in order
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20email:%22monica@example.com%22",
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
            url=api_url_base + "search.json""",
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
            url=api_url_base + "users.json""",
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
            url=api_url_base + "users.json""",
            match_querystring=False,
            json=api_responses.create_user_dupe,
            status=400,
        )
    )

    # and then a search by external ID will return the one user
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=external_id:%221%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20external_id:%221%22",
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
            url=api_url_base + "search.json?query=external_id:%221%22%20type:%22user%22",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    # same as above, but sometimes the params are reversed
    responses.add(
        responses.Response(
            method="GET",
            url=api_url_base + "search.json?query=type:%22user%22%20external_id:%221%22",
            match_querystring=True,
            json=api_responses.search_one_result,
            status=200,
        )
    )
    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(user)
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
            url=api_url_base + "search.json""",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # creation works
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json""",
            match_querystring=False,
            json=api_responses.create_user_result,
            status=201,
        )
    )
    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(user)
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
            url=api_url_base + "search.json""",
            match_querystring=False,
            json=api_responses.search_one_result,
            status=200,
        )
    )

    remote, is_definite = service.ZengoService().get_or_create_remote_zd_user_for_local_user(user)

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
            url=api_url_base + "search.json""",
            match_querystring=False,
            json=api_responses.search_no_results,
            status=200,
        )
    )
    # creation of a user will work
    responses.add(
        responses.Response(
            method="POST",
            url=api_url_base + "users.json""",
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
            url=api_url_base + "search.json""",
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
            url=api_url_base + "search.json""",
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
    remote_ticket = service.ZengoService().client.tickets(id=123)
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
    local_ticket, created = service.ZengoService().sync_ticket_id(123)
    assert created
    assert local_ticket is not None
    assert len(responses.calls) == 3


@responses.activate
@pytest.mark.django_db
def test_sync_comments():
    add_api_responses(comments=api_responses.two_comments)
    # assume local ticket has already been created
    local_ticket = mommy.make('zengo.Ticket')
    assert Comment.objects.count() == 0
    remote_ticket = service.ZengoService().client.tickets(id=123)

    local_comments = service.ZengoService().sync_comments(
        remote_ticket, local_ticket
    )
    assert len(local_comments) == 2
    assert Comment.objects.count() == 2

    remote_comments = service.ZengoService().client.tickets.comments(remote_ticket.id)

    remote = list(remote_comments)[0]
    local = local_comments[0]

    assert local.zendesk_id == remote.id
    assert local.ticket == local_ticket
    assert local.author.zendesk_id == remote.author.id
    assert local.body == remote.body
    assert local.public == remote.public
    assert local.created_at == remote.created_at


@responses.activate
@pytest.mark.django_db
def test_sync_comments_one_comment_already_exists():
    add_api_responses(comments=api_responses.two_comments)
    # assume local ticket has already been created
    local_ticket = mommy.make('zengo.Ticket')
    remote_ticket = service.ZengoService().client.tickets(id=123)
    remote_comments = list(
        service.ZengoService().client.tickets.comments(remote_ticket.id)
    )

    # create one of the comments ahead of time
    comment = mommy.make(
        "zengo.Comment",
        zendesk_id=remote_comments[0].id,
        ticket=local_ticket,
    )

    assert local_ticket.comments.count() == 1

    # now sync comments, which should discover the second comment
    local_comments = service.ZengoService().sync_comments(
        remote_ticket, local_ticket
    )
    assert len(local_comments) == 2

    assert local_ticket.comments.count() == 2

    # ensure the earlier comment is the same instance
    assert local_comments[0] == comment
