from django.core.paginator import Paginator, InvalidPage
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from apps.feeds.forms import CreateFeedForm, UpdateFeedForm, \
    UpdateCommentForm, CommentCreationForm
from apps.feeds.mixins import AuthRequiredMixin
from apps.feeds.models import Feed, FeedItem, Comment


class DashboardView(AuthRequiredMixin, generic.TemplateView):
    template_name = 'feeds/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'dashboard'
        ctx['fav_feed_items'] = FeedItem.objects.filter(
            favorite=True, user=self.request.user)[:20]
        return ctx


class FeedListView(AuthRequiredMixin, generic.ListView):
    login_url = '/users/login/'
    model = Feed
    template_name = 'feeds/feed_list.html'
    paginate_by = 20
    context_object_name = 'feeds'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        unread_qty = Count('items', filter=Q(items__read=False))
        queryset = queryset.annotate(unread_qty=unread_qty)
        return queryset


class CreateFeedFormView(AuthRequiredMixin, generic.CreateView):
    template_name = 'feeds/feed_create.html'
    model = Feed
    form_class = CreateFeedForm
    success_url = reverse_lazy('feeds:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class UpdateFeedFormView(AuthRequiredMixin, generic.UpdateView):
    template_name = 'feeds/feed_update.html'
    form_class = UpdateFeedForm
    model = Feed
    success_url = reverse_lazy('feeds:list')

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class DeleteFeedFormView(AuthRequiredMixin, generic.DeleteView):
    template_name = 'feeds/feed_confirm_delete.html'
    model = Feed
    success_url = reverse_lazy('feeds:list')

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class ToggleTerminatedFeedView(AuthRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        feed = get_object_or_404(Feed, user=self.request.user, pk=pk)
        feed.toggle_terminated()
        return HttpResponseRedirect(reverse_lazy('feeds:list'))


class PullNowFeedView(AuthRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        feed = get_object_or_404(Feed, user=self.request.user, pk=pk)
        feed.pull_now()
        return HttpResponseRedirect(reverse_lazy('feeds:list'))


class FeedItemDetailView(AuthRequiredMixin, generic.DetailView):
    model = FeedItem
    template_name = "feeds/feed_item_detail.html"
    context_object_name = "feed_item"

    def get_queryset(self):
        return FeedItem.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.get_object().mark_as_read()
        ctx['current_page'] = 'feeds'
        comments_ctx = self.get_comments_ctx()
        ctx.update(comments_ctx)
        return ctx

    def get_comments_ctx(self):
        page_size = 10
        queryset = Comment.objects.filter(author=self.request.user,
                                          feed_item=self.get_object())
        comments_left = queryset.count() - page_size
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset, page_size)
        context = {
            'paginator': paginator,
            'page_obj': page,
            'is_paginated': is_paginated,
            'comments': queryset,
            'comments_qty': comments_left
        }
        return context

    def paginate_queryset(self, queryset, page_size):
        paginator = Paginator(queryset, page_size, orphans=0,
                              allow_empty_first_page=True)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(
                    'Page is not “last”, nor can it be converted to an int.')
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            raise Http404('Invalid page (%(page_number)s): %(message)s' % {
                'page_number': page_number,
                'message': str(e)
            })


class FeedFavFeedItemListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        pk = self.kwargs.get('pk', None)
        if not pk:
            return FeedItem.objects.none()
        return FeedItem.objects.filter(
            feed_id=pk, user=self.request.user, favorite=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class FeedUnreadFeedItemListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        pk = self.kwargs.get('pk', None)
        if not pk:
            return FeedItem.objects.none()
        return FeedItem.objects.filter(
            feed_id=pk, user=self.request.user, read=False)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class FeedFeedItemListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        pk = self.kwargs.get('pk', None)
        if not pk:
            return FeedItem.objects.none()
        return FeedItem.objects.filter(user=self.request.user, feed_id=pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class FeedItemListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        return FeedItem.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class FeedItemUnreadListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        return FeedItem.objects.filter(user=self.request.user, read=False)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class FeedItemFavListView(AuthRequiredMixin, generic.ListView):
    model = FeedItem
    template_name = 'feeds/feed_item_list.html'
    paginate_by = 20
    context_object_name = 'feed_items'

    def get_queryset(self):
        return FeedItem.objects.filter(user=self.request.user, favorite=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class ToggleFavoriteFeedItemView(AuthRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        if not pk:
            return JsonResponse({'success': False})
        feed_item = FeedItem.objects.get(user=self.request.user, pk=pk)
        feed_item.toggle_favorite()
        return JsonResponse({
            'success': feed_item.favorite
        })


class FeedItemMarkUnreadView(AuthRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        if not pk:
            return JsonResponse({'success': False})
        try:
            feed_item = FeedItem.objects.get(user=self.request.user, pk=pk)
            feed_item.mark_as_unread()
        except FeedItem.DoesNotExist:
            return JsonResponse({'success': False})
        return JsonResponse({'success': True})


class CommentUpdateView(AuthRequiredMixin, generic.UpdateView):
    template_name = 'feeds/comment_update.html'
    form_class = UpdateCommentForm
    model = Comment

    def get_success_url(self):
        return reverse_lazy('feeds:feed_item_detail',
                            kwargs={
                                'pk': self.kwargs.get('iid'),
                                'fid': self.kwargs.get('fid'),
                            })

    def get_queryset(self):
        return self.model.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class CommentDeleteView(AuthRequiredMixin, generic.DeleteView):
    template_name = 'feeds/comment_confirm_delete.html'
    model = Comment

    def get_success_url(self):
        return reverse_lazy('feeds:feed_item_detail',
                            kwargs={
                                'pk': self.kwargs.get('iid'),
                                'fid': self.kwargs.get('fid'),
                            })

    def get_queryset(self):
        return self.model.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'feeds'
        return ctx


class CommentCreateView(AuthRequiredMixin, generic.CreateView):
    template_name = 'feeds/comment_create.html'
    model = Comment
    form_class = CommentCreationForm

    def get_success_url(self):
        return reverse_lazy('feeds:feed_item_detail',
                            kwargs={
                                'pk': self.kwargs.get('iid'),
                                'fid': self.kwargs.get('fid'),
                            })

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['feed_item_id'] = self.kwargs.get('iid')
        kwargs['author_id'] = self.request.user.id
        return kwargs
