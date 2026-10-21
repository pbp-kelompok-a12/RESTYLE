from django import template

register = template.Library()


@register.inclusion_tag("community/_notification_menu.html", takes_context=True)
def notification_menu(context):
    """lonceng + panel notifikasi di navbar. Bisa dipakai di halaman mana saja."""
    user = context["user"]
    return {
        "notifications": user.notifications.select_related("actor", "post", "comment")[:5],
        "unread_count": user.notifications.filter(is_read=False).count(),
        "csrf_token": context.get("csrf_token"),
    }