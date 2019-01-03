# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings


DEFAULTS = {"SERVICE_CLASS": None, "WEBHOOK_SECRET": None, "PROCESSOR_CLASS": None}


class AppSettings(object):
    def __init__(self, prefix, defaults):
        self.prefix = prefix
        self.defaults = defaults

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid app setting: "{}"'.format(attr))
        return getattr(settings, "{}_{}".format(self.prefix, attr), self.defaults[attr])


app_settings = AppSettings("ZENGO", DEFAULTS)
