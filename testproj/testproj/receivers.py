from django.dispatch import receiver

from zengo import signals


@receiver(signals.ticket_created)
def handle_ticket_created(sender, ticket, context, **kwargs):
    print("{}: ticket created".format(ticket.zendesk_id))


@receiver(signals.ticket_updated)
def handle_ticket_updated(sender, ticket, updates, context, **kwargs):
    print("{}: ticket updated".format(ticket.zendesk_id))
