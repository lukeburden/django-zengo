from django.contrib import admin
from django.urls import path

from zengo.views import WebhookView

from . import receivers  # noqa


urlpatterns = [
    path('admin/', admin.site.urls),
    path('zengo/webhook/', WebhookView.as_view())
]
