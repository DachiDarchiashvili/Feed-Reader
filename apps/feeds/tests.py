import uuid

from django.db.utils import IntegrityError
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from apps.feeds.models import Feed, FeedItem, Comment
from apps.feeds.forms import (
    CreateFeedForm, UpdateFeedForm, UpdateCommentForm, CommentCreationForm
)


class FeedTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )

    def test_terminated_false_logic(self):
        self.assertFalse(self.feed.terminated)

    def test_toggle_terminated_logic(self):
        self.feed.toggle_terminated()
        self.feed.refresh_from_db()
        self.assertTrue(self.feed.terminated)

    def test_pull_now_logic(self):
        scan_after = self.feed.scan_after
        self.feed.pull_now()
        self.feed.refresh_from_db()
        self.assertNotEqual(scan_after, self.feed.scan_after)
        self.assertLess(scan_after, self.feed.scan_after)


class FeedItemCreationTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )
        self.feed_item = FeedItem.objects.create(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )

    def test_none_creator_is_represented_as_empty_string(self):
        feed_item = FeedItem(
            title='Feed Item Title',
            description='Feed Item Description',
            creator=None,
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )
        feed_item.save()
        feed_item.refresh_from_db()
        self.assertEqual(feed_item.creator, None)

    def test_allow_two_feed_items_without_author(self):
        for x in range(2):
            FeedItem.objects.create(
                title=f'Feed Item Title {x}',
                description=f'Feed Item Description {x}',
                guid=uuid.uuid4(),
                author=None,
                feed=self.feed,
                user=self.test_user,
                category=['Category 1'],
                pub_date=timezone.now()
            )

    def test_feed_item_mark_as_read(self):
        feed_item = FeedItem(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )
        feed_item.mark_as_read()
        feed_item.refresh_from_db()
        self.assertTrue(feed_item.read)

    def test_feed_item_mark_as_unread(self):
        feed_item = FeedItem(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )
        feed_item.mark_as_unread()
        feed_item.refresh_from_db()
        self.assertFalse(feed_item.read)

    def test_feed_item_mark_as_favourite(self):
        feed_item = FeedItem(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )
        feed_item.toggle_favorite()
        feed_item.refresh_from_db()
        self.assertTrue(feed_item.favorite)

    def test_feed_item_inherit_fields(self):
        self.assertEqual(
            'http://www.nu.nl/rss/Algemeen', self.feed_item.feed.link
        )
        self.assertEqual(None, self.feed_item.feed.title)
        self.assertEqual(False, self.feed_item.feed.terminated)


class CommentCreationTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )
        self.feed_item = FeedItem.objects.create(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )

    def test_create_comment(self):
        Comment.objects.create(
            text=f'{self.feed_item} first comment',
            author=self.test_user,
            feed_item=self.feed_item
        )


class CreateFeedFormTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )

    def test_form_fields(self):
        form = CreateFeedForm()
        self.assertEqual(len(form.fields), 2)
        self.assertTrue('custom_title' in form.fields)
        self.assertTrue('link' in form.fields)

    def test_form_save(self):
        form = CreateFeedForm(data={
            'custom_title': 'My NF',
            'link': 'http://www.dachi.me/rss/news'
        })
        self.assertTrue(form.is_valid())
        form.instance.user = self.test_user
        form.save()
        feed = Feed.objects.filter(link='http://www.dachi.me/rss/news')
        self.assertTrue(feed.exists())


class UpdateFeedFormTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )

    def test_form_fields(self):
        form = UpdateFeedForm()
        self.assertEqual(len(form.fields), 1)
        self.assertTrue('custom_title' in form.fields)

    def test_form_update(self):
        form = UpdateFeedForm(data={
            'custom_title': 'My NF',
        }, instance=self.feed)
        self.assertTrue(form.is_valid())
        form.save()
        feed = Feed.objects.filter(link=self.feed.link)
        self.assertTrue(feed.exists())
        self.assertEqual(feed.first().custom_title, 'My NF')


class CommentCreationFormTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )
        self.feed_item = FeedItem.objects.create(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )

    def test_form_fields(self):
        form = CommentCreationForm()
        self.assertEqual(len(form.fields), 1)
        self.assertTrue('text' in form.fields)

    def test_form_save(self):
        form = CommentCreationForm(data={
            'text': 'Dummy Comment'
        }, feed_item_id=self.feed_item.pk, author_id=self.test_user.pk)
        self.assertTrue(form.is_valid())
        form.save()
        comment = Comment.objects.filter(feed_item=self.feed_item,
                                         author=self.test_user)
        self.assertTrue(comment.exists())

    def test_form_save_without_kwargs(self):
        form = CommentCreationForm(data={
            'text': 'Dummy Comment'
        })
        self.assertTrue(form.is_valid())
        self.assertRaises(IntegrityError, form.save)


class UpdateCommentFormTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        self.feed, _ = Feed.objects.get_or_create(
            link='http://www.nu.nl/rss/Algemeen',
            ttl=60,
            user=self.test_user
        )
        self.feed_item = FeedItem.objects.create(
            title='Feed Item Title',
            description='Feed Item Description',
            guid=uuid.uuid4(),
            feed=self.feed,
            user=self.test_user,
            category=['Category 1'],
            pub_date=timezone.now()
        )
        self.comment = Comment.objects.create(
            text='Dummy Comment',
            author=self.test_user,
            feed_item=self.feed_item
        )

    def test_form_fields(self):
        form = UpdateCommentForm()
        self.assertEqual(len(form.fields), 1)
        self.assertTrue('text' in form.fields)

    def test_form_update(self):
        form = UpdateCommentForm(data={
            'text': 'Dummy Text',
        }, instance=self.comment)
        self.assertTrue(form.is_valid())
        form.save()
        comm = Comment.objects.filter(author=self.test_user,
                                      text='Dummy Text',
                                      feed_item=self.feed_item)
        self.assertTrue(comm.exists())
        self.assertEqual(comm.first().text, 'Dummy Text')


class FeedsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create_user(
            username='testuser1', password='qwerty2019'
        )
        user2 = User.objects.create_user(
            username='testuser2', password='qwerty2019'
        )
        for x in range(5):
            if x % 2:
                user = user1
            else:
                user = user2
            feed = Feed.objects.create(
                link=f'http://dachi.me/rss/news/{x}',
                ttl=60,
                user=user
            )
            for y in range(10):
                feed_item = FeedItem.objects.create(
                    title=f'Feed Item {y}',
                    description='Feed Item Description',
                    guid=uuid.uuid4(),
                    feed=feed,
                    user=user,
                    category=['Category 1'],
                    pub_date=timezone.now(),
                    favorite=(y % 3 == 0),
                    read=(y % 4 == 0)
                )
                for z in range(2):
                    Comment.objects.create(
                        text=f'Dummy Comment {z}',
                        author=user,
                        feed_item=feed_item
                    )

    def setUp(self):
        self.user = User.objects.get(username='testuser1')
        self.client = Client()


class DashboardTests(FeedsTestCase):
    def test_dashboard_unauth_redirect_ok(self):
        url = reverse('index')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_dashboard_ok(self):
        self.client.login(username=self.user.username,
                          password='qwerty2019')
        url = reverse('index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.context['fav_feed_items'].count(), 0)
        self.assertEqual(resp.context['current_page'], 'dashboard')

    def test_dashboard_only_owns(self):
        self.client.login(username=self.user.username,
                          password='qwerty2019')
        url = reverse('index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['fav_feed_items']
        ]))


class FeedViewTests(FeedsTestCase):
    def test_list_unauth_redirect_ok(self):
        url = reverse('feeds:list')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_list_ok(self):
        self.client.login(username=self.user.username,
                          password='qwerty2019')
        url = reverse('feeds:list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.context['feeds'].count(), 0)
        self.assertEqual(resp.context['current_page'], 'feeds')

    def test_list_only_owns(self):
        self.client.login(username=self.user.username,
                          password='qwerty2019')
        url = reverse('feeds:list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(any([
            feed.user != self.user
            for feed in resp.context['feeds']
        ]))

    def test_create_unauth_redirect_ok(self):
        url = reverse('feeds:create')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_edit_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:edit', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_delete_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:delete', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_enable_disable_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:tgl_term', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_pull_now_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:pull_now', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_create_ok(self):
        login = self.client.login(username=self.user,
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            custom_title='Test title',
            link='https://dachi.me/rss/unique'
        )
        url = reverse('feeds:create')
        list_url = reverse('feeds:list')
        resp = self.client.post(url, data=data)
        self.assertRedirects(resp, list_url)
        feed = Feed.objects.filter(link=data['link'])
        self.assertTrue(feed.exists())

    def test_edit_ok(self):
        login = self.client.login(username=self.user,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        data = dict(
            custom_title='Just title'
        )
        url = reverse('feeds:edit', kwargs={'pk': feed.pk})
        list_url = reverse('feeds:list')
        resp = self.client.post(url, data=data)
        self.assertRedirects(resp, list_url)
        old_title = feed.custom_title
        feed.refresh_from_db()
        self.assertNotEqual(old_title, feed.custom_title)

    def test_delete_ok(self):
        login = self.client.login(username=self.user,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:delete', kwargs={'pk': feed.pk})
        list_url = reverse('feeds:list')
        resp = self.client.post(url, follow=True)
        self.assertRedirects(resp, list_url)
        feed = Feed.objects.filter(pk=feed.pk)
        self.assertFalse(feed.exists())

    def test_enable_disable_ok(self):
        login = self.client.login(username=self.user,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:tgl_term', kwargs={'pk': feed.pk})
        list_url = reverse('feeds:list')
        resp = self.client.get(url)
        self.assertRedirects(resp, list_url)
        old_termianted = feed.terminated
        feed.refresh_from_db()
        self.assertNotEqual(old_termianted, feed.terminated)

    def test_pull_now_ok(self):
        login = self.client.login(username=self.user,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:pull_now', kwargs={'pk': feed.pk})
        list_url = reverse('feeds:list')
        resp = self.client.get(url)
        self.assertRedirects(resp, list_url)
        old_scan_after = feed.scan_after
        feed.refresh_from_db()
        self.assertNotEqual(old_scan_after, feed.scan_after)


class FeedItemViewTests(FeedsTestCase):
    def test_list_all_unauth_redirect_ok(self):
        url = reverse('feeds:feed_item_list')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_list_unread_unauth_redirect_ok(self):
        url = reverse('feeds:feed_items_unread')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_list_fav_unauth_redirect_ok(self):
        url = reverse('feeds:feed_items_fav')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_feed_list_all_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:feed_feed_items_list', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_feed_list_unread_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:feed_feed_items_unread', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_feed_list_fav_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        url = reverse('feeds:feed_feed_items_fav', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_list_all_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        url = reverse('feeds:feed_item_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))

    def test_list_unread_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        url = reverse('feeds:feed_items_unread')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))

    def test_list_fav_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        url = reverse('feeds:feed_items_fav')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))

    def test_feed_list_all_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:feed_feed_items_list', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))

    def test_feed_list_unread_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:feed_feed_items_unread', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))

    def test_feed_list_fav_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        url = reverse('feeds:feed_feed_items_fav', kwargs={'pk': feed.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['current_page'], 'feeds')
        self.assertTrue('feed_items' in resp.context)
        self.assertFalse(any([
            feed_item.user != self.user
            for feed_item in resp.context['feed_items']
        ]))


class FeedItemDetailViewTests(FeedsTestCase):
    def test_item_detail_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        feed_item = feed.items.first()
        url = reverse('feeds:feed_item_detail', kwargs={'pk': feed_item.pk,
                                                        'fid': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_item_detail_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        feed_item = feed.items.first()
        url = reverse('feeds:feed_item_detail', kwargs={'pk': feed_item.pk,
                                                        'fid': feed.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('feed_item' in resp.context)

    def test_item_comments_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        feed_item = feed.items.first()
        url = reverse('feeds:feed_item_detail', kwargs={'pk': feed_item.pk,
                                                        'fid': feed.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('comments' in resp.context)
        self.assertTrue('comments_qty' in resp.context)
        self.assertFalse(any([
            comm.author != self.user
            for comm in resp.context['comments']
        ]))


class CommentViewTests(FeedsTestCase):
    def test_coment_create_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        feed_item = feed.items.first()
        url = reverse('feeds:comment_create', kwargs={'iid': feed_item.pk,
                                                      'fid': feed.pk})
        resp = self.client.post(url, data={'text': 'Dummy Comment'})
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_comment_edit_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        feed_item = feed.items.first()
        comment = feed_item.comments.first()
        url = reverse('feeds:comment_edit', kwargs={'pk': comment.pk,
                                                    'iid': feed_item.pk,
                                                    'fid': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_comment_delete_unauth_redirect_ok(self):
        feed = Feed.objects.first()
        feed_item = feed.items.first()
        comment = feed_item.comments.first()
        url = reverse('feeds:comment_delete', kwargs={'pk': comment.pk,
                                                      'iid': feed_item.pk,
                                                      'fid': feed.pk})
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_comment_create_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        feed_item = feed.items.first()
        url = reverse('feeds:comment_create', kwargs={'iid': feed_item.pk,
                                                      'fid': feed.pk})
        redir_url = reverse('feeds:feed_item_detail', kwargs={
            'pk': feed_item.pk,
            'fid': feed.pk})
        resp = self.client.post(url, data={'text': 'Dummy Comment'})
        self.assertRedirects(resp, redir_url)
        comment = Comment.objects.filter(text='Dummy Comment')
        self.assertTrue(comment.exists())

    def test_comment_edit_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        feed_item = feed.items.first()
        comment = feed_item.comments.first()
        url = reverse('feeds:comment_edit', kwargs={'pk': comment.pk,
                                                    'iid': feed_item.pk,
                                                    'fid': feed.pk})
        redir_url = reverse('feeds:feed_item_detail', kwargs={
            'pk': feed_item.pk,
            'fid': feed.pk})
        resp = self.client.post(url, data={'text': 'Comment Dummy'})
        self.assertRedirects(resp, redir_url)
        old_text = comment.text
        comment.refresh_from_db()
        self.assertNotEqual(old_text, comment.text)

    def test_comment_delete_ok(self):
        login = self.client.login(username=self.user.username,
                                  password='qwerty2019')
        self.assertTrue(login)
        feed = Feed.objects.filter(user=self.user).first()
        feed_item = feed.items.first()
        comment = feed_item.comments.first()
        url = reverse('feeds:comment_delete', kwargs={'pk': comment.pk,
                                                      'iid': feed_item.pk,
                                                      'fid': feed.pk})
        redir_url = reverse('feeds:feed_item_detail', kwargs={
            'pk': feed_item.pk,
            'fid': feed.pk})
        resp = self.client.post(url, follow=True)
        self.assertRedirects(resp, redir_url)
        comm = Comment.objects.filter(pk=comment.pk)
        self.assertFalse(comm.exists())
