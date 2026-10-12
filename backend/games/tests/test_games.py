from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User
from games.models import Game, Player, Round


class GameModelTests(TestCase):
    def setUp(self):
        self.users = [
            User.objects.create_user(username='p1', email='p1@example.com', password='pass123'),
            User.objects.create_user(username='p2', email='p2@example.com', password='pass123'),
            User.objects.create_user(username='p3', email='p3@example.com', password='pass123'),
        ]

    def test_game_starts_in_waiting_status(self):
        game = Game.objects.create()
        self.assertEqual(game.status, Game.STATUS_WAITING)
        self.assertIsNotNone(game.created_at)

    def test_game_can_start_when_it_has_three_players(self):
        game = Game.objects.create()
        for index, user in enumerate(self.users):
            Player.objects.create(game=game, user=user, color=Player.COLORS[index], score=0)

        self.assertEqual(game.players.count(), 3)
        game.status = Game.STATUS_ACTIVE
        game.save()
        self.assertEqual(game.status, Game.STATUS_ACTIVE)
        self.assertTrue(game.is_active())

    def test_game_is_completed_when_status_is_completed(self):
        game = Game.objects.create(status=Game.STATUS_COMPLETED)
        self.assertTrue(game.is_completed())

    def test_game_active_state_requires_exactly_three_players(self):
        game = Game.objects.create(status=Game.STATUS_ACTIVE)
        for index, user in enumerate(self.users[:2]):
            Player.objects.create(game=game, user=user, color=Player.COLORS[index][0], score=0)

        with self.assertRaises(ValidationError):
            game.full_clean()

    def test_get_current_round_returns_latest_round(self):
        game = Game.objects.create()
        round_1 = Round.objects.create(game=game, number=1, type=Round.TYPE_CITY_CAPTURE)
        round_2 = Round.objects.create(game=game, number=2, type=Round.TYPE_BATTLE)

        self.assertEqual(game.get_current_round(), round_2)


class GameConstraintTests(TestCase):
    def test_game_rejects_duplicate_user_in_same_game(self):
        game = Game.objects.create()
        user = User.objects.create_user(username='dupe', email='dupe@example.com', password='pass123')
        Player.objects.create(game=game, user=user, color='red')

        with self.assertRaises(IntegrityError):
            Player.objects.create(game=game, user=user, color='green')

    def test_game_rejects_duplicate_color_in_same_game(self):
        game = Game.objects.create()
        user_one = User.objects.create_user(username='one', email='one@example.com', password='pass123')
        user_two = User.objects.create_user(username='two', email='two@example.com', password='pass123')

        Player.objects.create(game=game, user=user_one, color='red')

        with self.assertRaises(IntegrityError):
            Player.objects.create(game=game, user=user_two, color='red')

    def test_player_score_cannot_be_negative(self):
        game = Game.objects.create()
        user = User.objects.create_user(username='score', email='score@example.com', password='pass123')

        with self.assertRaises(ValidationError):
            player = Player(game=game, user=user, color='blue', score=-1)
            player.full_clean()
