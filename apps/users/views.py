from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout, \
    update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, \
    UserCreationForm
from django.contrib.auth.models import User

from apps.feeds.mixins import AuthRequiredMixin
from apps.users.forms import LogInForm, UserUpdateForm


class LogInFormView(generic.View):
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        ctx = {
            'next': request.GET.get('next', ''),
            'form': LogInForm(**kwargs)
        }
        return render(request, 'users/login.html', ctx)

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        form = LogInForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                if (form.cleaned_data['next']
                        and form.cleaned_data['next'] != '/users/logout/'):
                    return HttpResponseRedirect(form.cleaned_data['next'])
                return HttpResponseRedirect('/')
            else:
                form.errors['password'] = 'The password is wrong'
        context = {'form': form}
        return render(request, 'users/login.html', context)


class LogOutView(AuthRequiredMixin, generic.TemplateView):
    template_name = "users/login.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class UserDetailView(AuthRequiredMixin, generic.DetailView):
    model = User
    template_name = "users/profile.html"
    context_object_name = "user"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'profile'
        return ctx


class UserUpdateView(AuthRequiredMixin, generic.UpdateView):
    template_name = 'users/update.html'
    form_class = UserUpdateForm
    model = User
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'profile'
        return ctx


class UserSetPasswordView(AuthRequiredMixin, generic.FormView):
    template_name = 'users/set_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'profile'
        return ctx


class UserDeleteView(AuthRequiredMixin, generic.DeleteView):
    template_name = 'users/confirm_delete.html'
    model = User
    success_url = reverse_lazy('users:login')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_page'] = 'profile'
        return ctx


class UserCreateView(generic.CreateView):
    template_name = 'users/create.html'
    model = User
    form_class = UserCreationForm
    success_url = reverse_lazy('users:login')
