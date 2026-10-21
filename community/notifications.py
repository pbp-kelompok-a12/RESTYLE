"""Fungsi kecil untuk membuat dan menghapus notifikasi.
Dipanggil dari views.py setiap ada balasan, like, atau follow."""

from django.utils import timezone

from community.models import Notification


def notify_reply(comment):
    """kabari pemilik post (dan pemilik komentar yang dibalas) bahwa ada balasan baru."""
    recipients = {comment.post.author}
    if comment.parent:
        recipients.add(comment.parent.author)
    recipients.discard(comment.author)  # tidak perlu notifikasi untuk diri sendiri

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            actor=comment.author,
            kind=Notification.REPLY,
            post=comment.post,
            comment=comment,
        )


def notify_like(post, liker):
    """satu post cukup punya satu notifikasi like, isinya diperbarui ke orang terakhir yang nge-like."""
    if liker == post.author:
        return
    Notification.objects.update_or_create(
        recipient=post.author,
        kind=Notification.LIKE,
        post=post,
        defaults={"actor": liker, "is_read": False, "created_at": timezone.now()},
    )


def undo_like(post, liker):
    """dipanggil saat like dibatalkan."""
    notification = Notification.objects.filter(
        recipient=post.author,
        kind=Notification.LIKE,
        post=post,
    ).first()
    if notification is None or notification.actor != liker:
        return

    # ganti ke orang lain yang masih nge-like, atau hapus kalau sudah tidak ada
    other_liker = post.likes.exclude(id=post.author_id).first()
    if other_liker:
        notification.actor = other_liker
        notification.save(update_fields=["actor"])
    else:
        notification.delete()


def notify_follow(follower, followed):
    Notification.objects.create(recipient=followed, actor=follower, kind=Notification.FOLLOW)


def undo_follow(follower, followed):
    Notification.objects.filter(
        recipient=followed,
        actor=follower,
        kind=Notification.FOLLOW,
    ).delete()