from django.urls import path

from apps.feeds.views import FeedListView, CreateFeedFormView, \
    UpdateFeedFormView, DeleteFeedFormView, ToggleTerminatedFeedView, \
    PullNowFeedView, FeedFavFeedItemListView, FeedUnreadFeedItemListView, \
    FeedFeedItemListView, FeedItemDetailView, FeedItemListView, \
    FeedItemUnreadListView, FeedItemFavListView, ToggleFavoriteFeedItemView, \
    FeedItemMarkUnreadView, CommentCreateView, CommentUpdateView, \
    CommentDeleteView

app_name = 'feeds'
urlpatterns = [
    path('', FeedListView.as_view(), name='list'),
    path('create/', CreateFeedFormView.as_view(), name='create'),
    path('<int:pk>/edit/', UpdateFeedFormView.as_view(), name='edit'),
    path('<int:pk>/delete/', DeleteFeedFormView.as_view(), name='delete'),
    path('<int:pk>/pull_now/', PullNowFeedView.as_view(), name='pull_now'),
    path('<int:pk>/toggle_term/',
         ToggleTerminatedFeedView.as_view(), name='tgl_term'),
    path('<int:fid>/items/<int:pk>/',
         FeedItemDetailView.as_view(), name='feed_item_detail'),
    path('<int:fid>/items/<int:pk>/favorite',
         ToggleFavoriteFeedItemView.as_view(), name='feed_item_fav'),
    path('<int:fid>/items/<int:pk>/mark_as_unread',
         FeedItemMarkUnreadView.as_view(), name='feed_item_mark_unread'),
    path('<int:pk>/items/favorites/',
         FeedFavFeedItemListView.as_view(), name='feed_feed_items_fav'),
    path('<int:pk>/items/unread/',
         FeedUnreadFeedItemListView.as_view(), name='feed_feed_items_unread'),
    path('<int:pk>/items/all/',
         FeedFeedItemListView.as_view(), name='feed_feed_items_list'),
    path('items/',
         FeedItemListView.as_view(), name='feed_item_list'),
    path('items/unread/',
         FeedItemUnreadListView.as_view(), name='feed_items_unread'),
    path('items/favorite/',
         FeedItemFavListView.as_view(), name='feed_items_fav'),
    path('<int:fid>/items/<int:iid>/comments/create/',
         CommentCreateView.as_view(), name='comment_create'),
    path('<int:fid>/items/<int:iid>/comments/<int:pk>/edit/',
         CommentUpdateView.as_view(), name='comment_edit'),
    path('<int:fid>/items/<int:iid>/comments/<int:pk>/delete/',
         CommentDeleteView.as_view(), name='comment_delete'),
]
