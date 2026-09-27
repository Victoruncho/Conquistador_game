from django.test import TestCase


class AuthApiTests(TestCase):
    def test_csrf_endpoint_returns_204(self):
        response = self.client.get('/api/auth/csrf/')

        self.assertEqual(response.status_code, 204)

    def test_register_endpoint_creates_user(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'player_one',
                'email': 'player@example.com',
                'nickname': 'MountainKnight',
                'password': 'example-password',
                'password_confirm': 'example-password',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'player_one')
        self.assertEqual(response.json()['profile']['nickname'], 'MountainKnight')
