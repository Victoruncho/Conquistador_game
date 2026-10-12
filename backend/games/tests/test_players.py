from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User
from games.models import Game, Player


class PlayerModelTests(TestCase):
    def test_player_color_must_be_valid_choice(self):
        game = Game.objects.create()
        user = User.objects.create_user(username='player', email='player@example.com', password='pass123')

        with self.assertRaises(ValidationError):
            player = Player(game=game, user=user, color='yellow', score=0)
            player.full_clean()

    def test_player_requires_unique_user_per_game(self):
        game = Game.objects.create()
        user = User.objects.create_user(username='duplicateuser', email='duplicate@example.com', password='pass123')
        Player.objects.create(game=game, user=user, color='green')

        with self.assertRaises(IntegrityError):
            Player.objects.create(game=game, user=user, color='blue')

    def test_player_score_defaults_to_zero(self):
        game = Game.objects.create()
        user = User.objects.create_user(username='defaultscore', email='defaultscore@example.com', password='pass123')
        player = Player.objects.create(game=game, user=user, color='red')

        self.assertEqual(player.score, 0)
