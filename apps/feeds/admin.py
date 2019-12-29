from django.contrib import admin

from .models import Feed, FeedItem, Comment

admin.site.register(Feed)
admin.site.register(FeedItem)
admin.site.register(Comment)
