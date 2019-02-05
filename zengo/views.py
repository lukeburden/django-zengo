# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from . import strings
from .service import get_processor
from .settings import app_settings


@method_decorator(csrf_exempt, name="dispatch")
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
            return HttpResponseForbidden(strings.secret_missing_or_wrong)
        processor = get_processor()
        try:
            event = processor.store_event(request.body.decode("utf-8"))
        except ValidationError as ve:
            return HttpResponseBadRequest(ve.message)
        processor.begin_processing_event(event)
        return HttpResponse()
