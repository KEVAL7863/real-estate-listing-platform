from messaging.models import Message


def global_counts(request):
    """Expose unread-message count to every template's navbar."""
    if not request.user.is_authenticated:
        return {}
    unread = (
        Message.objects.filter(is_read=False)
        .filter(conversation__owner=request.user)
        .exclude(sender=request.user)
        .count()
        + Message.objects.filter(is_read=False)
        .filter(conversation__buyer=request.user)
        .exclude(sender=request.user)
        .count()
    )
    return {"navbar_unread": unread}
