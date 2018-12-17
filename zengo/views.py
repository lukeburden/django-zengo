# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils.crypto import constant_time_compare
from django.views.generic.base import View

from .service import get_service
from .settings import app_settings


class WebhookView(View):
    """Receive an update from Zendesk that a ticket has changed."""

    secret_name = "secret"
    secret = app_settings.WEBHOOK_SECRET

    def validate_secret(self):
        secret_given = self.request.GET.get(self.secret_name) or self.request.POST.get(
            self.secret_name
        )
        return secret_given is not None and constant_time_compare(
            secret_given, self.secret
        )

    def post(self, request):
        if not self.validate_secret():
            return HttpResponseForbidden("Secret missing or wrong")
        service = get_service()
        try:
            event = service.store_event(request.body)
        except ValidationError:
            return HttpResponseBadRequest()
        service.process_event(event)
        return HttpResponse()
