# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.dispatch import Signal


new_ticket = Signal(providing_args=["ticket", "context"])
new_comments = Signal(providing_args=["ticket", "comments", "context"])
custom_fields_changed = Signal(providing_args=["ticket", "changes", "context"])
