from django.contrib import messages as flash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property
from .models import Conversation, Message


@login_required
def inbox(request):
    conversations = (
        Conversation.objects.filter(Q(buyer=request.user) | Q(owner=request.user))
        .select_related("property", "buyer", "owner")
        .order_by("-updated_at")
    )
    # Attach last message + unread flag for the list view
    threads = []
    for conv in conversations:
        last = conv.messages.last()
        unread = conv.messages.filter(is_read=False).exclude(sender=request.user).exists()
        threads.append({"conv": conv, "last": last, "unread": unread})
    return render(request, "messaging/inbox.html", {"threads": threads})


@login_required
def conversation_detail(request, pk):
    conv = get_object_or_404(
        Conversation.objects.filter(Q(buyer=request.user) | Q(owner=request.user)),
        pk=pk,
    )
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(conversation=conv, sender=request.user, body=body)
            conv.save()  # bump updated_at
        return redirect("messaging:conversation", pk=conv.pk)

    # Mark incoming messages as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(
        request,
        "messaging/conversation.html",
        {"conv": conv, "other": conv.other_party(request.user)},
    )


@login_required
def start_conversation(request, property_id):
    prop = get_object_or_404(Property, pk=property_id)
    if prop.owner == request.user:
        flash.info(request, "This is your own property.")
        return redirect("property_detail", slug=prop.slug)

    conv, _ = Conversation.objects.get_or_create(
        property=prop, buyer=request.user, defaults={"owner": prop.owner}
    )
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(conversation=conv, sender=request.user, body=body)
            conv.save()
            flash.success(request, "Message sent to the owner.")
            return redirect("messaging:conversation", pk=conv.pk)
    return redirect("messaging:conversation", pk=conv.pk)
