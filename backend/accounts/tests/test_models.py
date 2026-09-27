from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Profile, User


class UserProfileModelTests(TestCase):
    def test_user_email_is_unique(self):
        User.objects.create_user(username='player_one', email='player@example.com', password='secret123')

        with self.assertRaises(IntegrityError):
            User.objects.create_user(username='player_two', email='player@example.com', password='secret123')

    def test_profile_created_for_user(self):
        user = User.objects.create_user(username='player_one', email='player@example.com', password='secret123')

        profile = Profile.objects.get(user=user)

        self.assertEqual(profile.nickname, 'player_one')
        self.assertEqual(profile.avatar_key, 'knight-1')
