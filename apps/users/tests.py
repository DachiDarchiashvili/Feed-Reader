from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class UserTestCase(TestCase):
    databases = {'default'}

    def setUp(self):
        # Create test user
        User.objects.create_user(username='testuser1',
                                 password='qwerty2019')
        self.client = Client()

    def test_register_url_ok(self):
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)

    def test_login_ok(self):
        resp = self.client.get('/users/login/')
        self.assertEqual(resp.status_code, 200)

    def test_profile_unauth_redirect_ok(self):
        url = reverse('users:profile')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_profile_edit_unauth_redirect_ok(self):
        url = reverse('users:update')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_profile_set_passwd_unauth_redirect_ok(self):
        url = reverse('users:set_passwd')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_profile_delete_unauth_redirect_ok(self):
        url = reverse('users:delete')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')

    def test_user_register_ok(self):
        data = dict(
            username='cool_t_gang',
            password1='qwerty2019',
            password2='qwerty2019'
        )
        url = reverse('register')
        profile_url = reverse('users:login')
        resp = self.client.post(url, data=data)
        self.assertRedirects(resp, profile_url)
        status = self.client.login(username=data['username'],
                                   password=data['password1'])
        self.assertTrue(status)

    def test_register_rejects_invalid_username(self):
        data = dict(
            username='cool t',
            password1='qwerty2019',
            password2='qwerty2019'
        )
        url = reverse('register')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'username',
            ('Enter a valid username. This value may contain only letters, '
             'numbers, and @/./+/-/_ characters.')
        )

    def test_register_validates_passwd_fields(self):
        data = dict(
            username='cool_t_gang',
            password1='qwerty2019',
            password2='qwerty2020'
        )
        url = reverse('register')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'password2',
            'The two password fields didn’t match.'
        )

    def test_user_profile_ok(self):
        self.client.login(username='testuser1',
                          password='qwerty2019')
        url = reverse('users:profile')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['user'].username, 'testuser1')

    def test_user_edit_profile_ok(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        user = User.objects.get(username='testuser1')
        data = dict(first_name='T_first',
                    last_name='last_T',
                    email='test@example.com',
                    username=user.username,
                    date_joined=user.date_joined.strftime('%Y-%m-%d %H:%M:%S'))
        url = reverse('users:update')
        profile_url = reverse('users:profile')
        resp = self.client.post(url, data=data)
        self.assertRedirects(resp, profile_url)
        user = User.objects.get(username='testuser1')
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])

    def test_user_edit_rejects_invalid_username(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        user = User.objects.get(username='testuser1')
        data = dict(
            username="test user 1",
            last_name='last_T',
            email='test@example.com',
            date_joined=user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        )
        url = reverse('users:update')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'username',
            ('Enter a valid username. This value may contain only letters, '
             'numbers, and @/./+/-/_ characters.')
        )

    def test_user_set_password(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            old_password='qwerty2019',
            new_password1='qwerty2020',
            new_password2='qwerty2020'
        )
        url = reverse('users:set_passwd')
        profile_url = reverse('users:profile')
        resp = self.client.post(url, data=data)
        self.assertRedirects(resp, profile_url)
        user = User.objects.get(username='testuser1')
        self.assertTrue(user.check_password(data['new_password1']))

    def test_user_set_password_validates_old_password(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            old_password='qwerty2020',
            new_password1='qwerty2019',
            new_password2='qwerty2019'
        )
        url = reverse('users:set_passwd')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'old_password',
            'Your old password was entered incorrectly. Please enter it again.'
        )

    def test_user_set_password_vaidates_all_numeric_password(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            old_password='qwerty2019',
            new_password1='123456789',
            new_password2='123456789'
        )
        url = reverse('users:set_passwd')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'new_password2',
            'This password is entirely numeric.'
        )

    def test_user_set_password_validates_new_passwd_fields(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            old_password='qwerty2019',
            new_password1='qwerty2020',
            new_password2='qwerty2021'
        )
        url = reverse('users:set_passwd')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'new_password2',
            'The two password fields didn’t match.'
        )

    def test_user_set_password_validates_new_passwd_length(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        data = dict(
            old_password='qwerty2019',
            new_password1='qwrty20',
            new_password2='qwrty20'
        )
        url = reverse('users:set_passwd')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp, 'form', 'new_password2',
            ('This password is too short. It must contain at least 8 '
             'characters.')
        )

    def test_user_deletion(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        url = reverse('users:delete')
        url_index = reverse('users:login')
        resp = self.client.post(url, follow=True)
        self.assertRedirects(resp, url_index)

    def test_user_logout(self):
        login = self.client.login(username='testuser1',
                                  password='qwerty2019')
        self.assertTrue(login)
        url = reverse('users:logout')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        url = reverse('users:profile')
        resp = self.client.get(url)
        self.assertRedirects(resp, f'/users/login/?next={url}')
