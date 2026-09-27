from django.test import TestCase

from accounts.models import User


class AuthApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='player_one',
            email='player@example.com',
            password='example-password',
        )
        self.user.profile.nickname = 'MountainKnight'
        self.user.profile.avatar_key = 'knight-1'
        self.user.profile.save()

    def test_csrf_endpoint_returns_204(self):
        response = self.client.get('/api/auth/csrf/')

        self.assertEqual(response.status_code, 204)

    def test_register_endpoint_creates_user_and_profile(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'player_two',
                'email': 'player2@example.com',
                'nickname': 'NewKnight',
                'password': 'example-password',
                'password_confirm': 'example-password',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'player_two')
        self.assertEqual(response.json()['profile']['nickname'], 'NewKnight')
        self.assertTrue(User.objects.filter(username='player_two').exists())

    def test_login_creates_session_and_me_access(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'player_one', 'password': 'example-password'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'player_one')
        self.assertIn('sessionid', self.client.cookies)

        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()['username'], 'player_one')

    def test_logout_clears_session(self):
        self.client.login(username='player_one', password='example-password')

        response = self.client.post('/api/auth/logout/')

        self.assertEqual(response.status_code, 204)
        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 403)

    def test_anonymous_users_cannot_access_protected_routes(self):
        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 403)

        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, 403)

    def test_profile_patch_updates_only_allowed_fields(self):
        self.client.login(username='player_one', password='example-password')

        response = self.client.patch(
            '/api/auth/me/',
            {'nickname': 'NewKnight', 'avatar_key': 'knight-3'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile']['nickname'], 'NewKnight')
        self.assertEqual(response.json()['profile']['avatar_key'], 'knight-3')

    def test_csrf_cookie_is_set_and_unsafe_requests_require_csrf_token(self):
        csrf_response = self.client.get('/api/auth/csrf/')
        self.assertEqual(csrf_response.status_code, 204)
        self.assertIn('csrftoken', self.client.cookies)

        csrf_token = self.client.cookies['csrftoken'].value

        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'player_two',
                'email': 'player2@example.com',
                'nickname': 'KnightTwo',
                'password': 'example-password',
                'password_confirm': 'example-password',
            },
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 201)

    def test_invalid_credentials_return_400(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'player_one', 'password': 'wrong-password'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
