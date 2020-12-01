# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.dispatch import Signal


# fired any time a ticket is newly created
ticket_created = Signal(providing_args=["ticket", "context"])

# fired upon any change to a ticket beyond its initial creation
ticket_updated = Signal(providing_args=["ticket", "updates", "context"])
