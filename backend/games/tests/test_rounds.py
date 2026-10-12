from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from games.models import Game, Player, Round


class RoundModelTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create()
        self.players = [
            User.objects.create_user(username='r1', email='r1@example.com', password='pass123'),
            User.objects.create_user(username='r2', email='r2@example.com', password='pass123'),
            User.objects.create_user(username='r3', email='r3@example.com', password='pass123'),
        ]
        self.player_objs = [
            Player.objects.create(game=self.game, user=self.players[0], color='red'),
            Player.objects.create(game=self.game, user=self.players[1], color='green'),
            Player.objects.create(game=self.game, user=self.players[2], color='blue'),
        ]

    def test_round_starts_pending(self):
        round_obj = Round.objects.create(game=self.game, number=1, type=Round.TYPE_CITY_CAPTURE)
        self.assertEqual(round_obj.status, Round.STATUS_PENDING)
        self.assertIsNone(round_obj.winner)

    def test_round_can_complete_with_winner_from_same_game(self):
        round_obj = Round.objects.create(
            game=self.game,
            number=1,
            type=Round.TYPE_BATTLE,
            status=Round.STATUS_COMPLETED,
            winner=self.player_objs[0],
            completed_at=timezone.now(),
        )

        self.assertEqual(round_obj.winner, self.player_objs[0])
        self.assertEqual(round_obj.status, Round.STATUS_COMPLETED)
        self.assertIsNotNone(round_obj.completed_at)

    def test_completed_round_requires_completion_timestamp(self):
        round_obj = Round(
            game=self.game,
            number=1,
            type=Round.TYPE_BATTLE,
            status=Round.STATUS_COMPLETED,
            winner=self.player_objs[0],
        )

        with self.assertRaises(ValidationError):
            round_obj.full_clean()

    def test_round_rejects_winner_from_other_game(self):
        other_game = Game.objects.create()
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pass123')
        other_player = Player.objects.create(game=other_game, user=other_user, color='red')

        round_obj = Round(game=self.game, number=1, type=Round.TYPE_BATTLE, winner=other_player)

        with self.assertRaises(ValidationError):
            round_obj.full_clean()

    def test_round_number_must_be_unique_per_game(self):
        Round.objects.create(game=self.game, number=1, type=Round.TYPE_CITY_CAPTURE)

        with self.assertRaises(IntegrityError):
            Round.objects.create(game=self.game, number=1, type=Round.TYPE_BATTLE)
