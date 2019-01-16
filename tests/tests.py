# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
def test_webhook_view_missing_secret():
    pass


@pytest.mark.django_db
def test_webhook_view_invalid_secret():
    pass


@pytest.mark.django_db
def test_webhook_view_no_body():
    pass


@pytest.mark.django_db
def test_webhook_view_invalid_body():
    pass


@responses.activate
@pytest.mark.django_db
def test_webhook_view_ok(client):
    assert Event.objects.count() == 0
    assert Ticket.objects.count() == 0
    add_api_responses_no_comment()
    response = client.post(
        reverse("webhook_view") + "?secret=zoomzoom", data={"id": 123}
    )
    # we should be being redirected to our post-login redirect URL
    print(response.content)
    assert response.status_code == 200
    assert Event.objects.count() == 1
    assert Ticket.objects.count() == 1


# Event
# - receipt
# - storage
# - firing of processing

# User
# - sync, lookup

# Processing and signal firing
# - new ticket
# - new comment
# - tag change
# - custom field change
