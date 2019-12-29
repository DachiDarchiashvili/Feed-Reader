from django import forms

from apps.feeds.models import Comment, Feed

from django.db import models


class Gocha(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, blank=True)


class CreateGocha(forms.ModelForm):
    class Meta:
        model = Gocha
        fields = '__all__'


class CreateFeedForm(forms.ModelForm):
    class Meta:
        model = Feed
        fields = ('custom_title', 'link')


class UpdateFeedForm(forms.ModelForm):
    class Meta:
        model = Feed
        fields = ('custom_title',)


class UpdateCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class CommentCreationForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        feed_item_id = kwargs.pop('feed_item_id', None)
        author_id = kwargs.pop('author_id', None)
        super().__init__(*args, **kwargs)
        self.feed_item_id = feed_item_id
        self.author_id = author_id

    def save(self, commit=True):
        self.instance = super().save(commit=False)
        self.instance.feed_item_id = self.feed_item_id
        self.instance.author_id = self.author_id
        self.instance.save()
        return self.instance
