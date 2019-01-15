# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError

from model_mommy import mommy

import pytest

import responses

from zengo import service
from zengo import strings
from zengo.models import Ticket

from . import api_responses


def test_get_zenpy_client():
    assert service.get_zenpy_client() is not None


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


# def get_updates(self, **kwargs):
#     """
#     Get new comments and updated fields and custom fields.

#     Further update detection can be done by projects using the
#     `ticket_updated` signal in combination with the passed `change_context`.
#     """
#     return {
#         "new_comments": self.get_new_comments(**kwargs),
#         "updated_fields": self.get_updated_fields(**kwargs),
#     }

# def get_new_comments(self, pre_ticket, post_ticket, pre_comments, post_comments):
#     new_comments = []
#     if len(post_comments) > len(pre_comments):
#         new_comment_ids = set([c.zendesk_id for c in post_comments]) - set(
#             [c.zendesk_id for c in pre_comments]
#         )
#         new_comments = [c for c in post_comments if c.zendesk_id in new_comment_ids]
#     return new_comments

# def get_updated_fields(self, pre_ticket, post_ticket, pre_comments, post_comments):
#     updates = {}

#     if not (pre_ticket and post_ticket):
#         return updates

#     pre_fields = model_to_dict(pre_ticket)
#     post_fields = model_to_dict(post_ticket)

#     # note: we do this using comparison rather than set operations to
#     # avoid issues with more complex, non-hashable fields
#     for k in pre_fields.keys():
#         if k in ("created_at", "updated_at"):
#             # don't bother detecting changes in these, it's not useful
#             # and timestamps are often mismatched as datetimes and strings
#             continue
#         if pre_fields.get(k) != post_fields.get(k):
#             updates[k] = {"old": pre_fields.get(k), "new": post_fields.get(k)}
#     return updates


# test service methods


# test WebhookView

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
