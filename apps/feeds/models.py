from django.contrib.auth.models import User
from django.contrib.postgres import fields
from django.db import models
from django.utils import timezone
from django.conf import settings


class Feed(models.Model):
    custom_title = models.CharField(verbose_name='Title', max_length=100,
                                    null=True, blank=True)
    title = models.CharField(verbose_name='Title', max_length=200, null=True,
                             blank=True)
    description = models.TextField(verbose_name='Description', max_length=1000,
                                   null=True, blank=True)
    link = models.URLField(verbose_name='Link', max_length=200)
    ttl = models.PositiveIntegerField(verbose_name='TTL', blank=True,
                                      default=settings.FEED_SCAN_INTERVAL)
    language = models.CharField(verbose_name='Language', max_length=20,
                                null=True, blank=True)
    last_build_date = models.DateTimeField(verbose_name='Last Build Date',
                                           null=True, blank=True)
    copyright = models.CharField(verbose_name='Copyright', max_length=200,
                                 null=True, blank=True)
    image = models.URLField(verbose_name='Image', max_length=200, null=True,
                            blank=True)
    docs = models.URLField(verbose_name='Docs', max_length=200, null=True,
                           blank=True)
    web_master = models.EmailField(verbose_name='Web Master', max_length=100,
                                   null=True, blank=True)
    pub_date = models.DateTimeField(verbose_name='Pub. Date', null=True,
                                    blank=True)
    scan_after = models.DateTimeField(verbose_name='Scan After DT', blank=True,
                                      auto_now_add=True)
    terminated = models.BooleanField(verbose_name='Terminated', default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="feeds")

    class Meta:
        db_table = 'feed'
        ordering = ['-last_build_date']
        unique_together = [['link', 'user']]

    def __str__(self):
        return self.title or self.link

    def toggle_terminated(self):
        self.terminated = not self.terminated
        self.save()

    def pull_now(self):
        self.scan_after = timezone.now()
        self.save()


class FeedItem(models.Model):
    title = models.CharField(verbose_name='Title', max_length=200)
    description = models.TextField(verbose_name='Description', max_length=1000)
    link = models.URLField(verbose_name='Link', max_length=200)
    category = fields.ArrayField(models.CharField(max_length=100),
                                 verbose_name='Categories', size=50)
    guid = models.CharField(verbose_name='Globally Unique Identifier',
                            max_length=200)
    pub_date = models.DateTimeField(verbose_name='Pub. Date')
    author = models.CharField(verbose_name='Author', max_length=100, null=True,
                              blank=True)
    creator = models.CharField(verbose_name='Creator', max_length=100,
                               null=True, blank=True)
    rights = models.CharField(verbose_name='Rights', max_length=200, null=True,
                              blank=True)
    enclosure = models.URLField(verbose_name='Cover Image', max_length=500,
                                null=True, blank=True)
    related_links = fields.ArrayField(
        fields.ArrayField(models.CharField(max_length=200), size=2),
        verbose_name='Related URLs Representation', size=30, null=True,
        blank=True)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE,
                             related_name="items")
    create_date = models.DateTimeField(verbose_name="Creation Date",
                                       auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="feed_items")
    favorite = models.BooleanField(verbose_name="Favorite", default=False)
    read = models.BooleanField(verbose_name="Read", default=False)

    class Meta:
        db_table = 'feed_item'
        ordering = ['-pub_date']
        unique_together = [['guid', 'user']]

    def __str__(self):
        return self.title

    def mark_as_read(self):
        self.read = True
        self.save()

    def mark_as_unread(self):
        self.read = False
        self.save()

    def toggle_favorite(self):
        self.favorite = not self.favorite
        self.save()


class Comment(models.Model):
    date_created = models.DateTimeField(verbose_name='Creation Date',
                                        auto_now_add=True)
    text = models.TextField(verbose_name='Text', max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    feed_item = models.ForeignKey(FeedItem, on_delete=models.CASCADE,
                                  related_name="comments")

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f'{self.author.username} - {self.feed_item.title}'
