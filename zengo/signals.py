from django.dispatch import Signal


new_comments = Signal(providing_args=["ticket", "comments"])
new_ticket = Signal(providing_args=["ticket"])
