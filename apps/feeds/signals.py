from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete)
def delete_usubscribed_feed(sender, instance, using):
    if not instance.feed.subscriptions.count():
        instance.feed.delete()
