from django.urls import path

from apps.users.views import LogInFormView, LogOutView, UserDetailView, \
    UserUpdateView, UserSetPasswordView, UserDeleteView

app_name = 'users'
urlpatterns = [
    path('login/', LogInFormView.as_view(), name='login'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('profile/', UserDetailView.as_view(), name='profile'),
    path('profile/update/', UserUpdateView.as_view(), name='update'),
    path('profile/set_password/', UserSetPasswordView.as_view(),
         name='set_passwd'),
    path('profile/delete/', UserDeleteView.as_view(), name='delete'),
]
