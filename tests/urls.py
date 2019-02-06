from zengo.views import WebhookView

try:
    from django.urls import path

    urlpatterns = [path("webhook/", WebhookView.as_view(), name="webhook_view")]

except ImportError:
    from django.conf.urls import url

    urlpatterns = [url(r"^webhook/", WebhookView.as_view(), name="webhook_view")]
