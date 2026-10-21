from django.test import TestCase

from accounts.models import User
from games.models import Game, Player, WaitingRoomEntry
from games.services import form_waiting_room_game, join_waiting_room


class WaitingRoomFormationTests(TestCase):
    def setUp(self):
        self.users = [
            User.objects.create_user(
                username=f'player_{index}',
                email=f'player_{index}@example.com',
                password='example-password',
            )
            for index in range(5)
        ]

    def test_five_waiting_users_create_game_and_leave_two_entries(self):
        for user in self.users:
            join_waiting_room(user)

        game = form_waiting_room_game()

        self.assertIsNotNone(game)
        self.assertEqual(game.status, Game.STATUS_WAITING)
        players = list(game.players.order_by('color'))
        self.assertEqual(len(players), 3)
        self.assertEqual({player.color for player in players}, {
            color for color, _ in Player.COLORS
        })
        self.assertTrue(all(player.score == 0 for player in players))
        self.assertEqual(
            WaitingRoomEntry.objects.count(),
            2,
        )
        self.assertEqual(
            set(WaitingRoomEntry.objects.values_list('user_id', flat=True)),
            {user.pk for user in self.users} - {player.user_id for player in players},
        )
        self.assertEqual(Game.objects.count(), 1)
        self.assertEqual(Player.objects.count(), 3)
        self.assertEqual(game.rounds.count(), 0)

    def test_two_waiting_users_do_not_change_database(self):
        for user in self.users[:2]:
            join_waiting_room(user)

        before = (
            Game.objects.count(),
            Player.objects.count(),
            WaitingRoomEntry.objects.count(),
            set(WaitingRoomEntry.objects.values_list('user_id', flat=True)),
        )

        result = form_waiting_room_game()

        after = (
            Game.objects.count(),
            Player.objects.count(),
            WaitingRoomEntry.objects.count(),
            set(WaitingRoomEntry.objects.values_list('user_id', flat=True)),
        )
        self.assertIsNone(result)
        self.assertEqual(after, before)

    def test_user_who_joins_an_ongoing_game_stays_queued_but_is_not_selected(self):
        for user in self.users[:4]:
            join_waiting_room(user)
        ongoing_game = Game.objects.create(status=Game.STATUS_WAITING)
        Player.objects.create(
            game=ongoing_game,
            user=self.users[0],
            color=Player.COLOR_RED,
        )

        game = form_waiting_room_game()

        selected_user_ids = set(game.players.values_list('user_id', flat=True))
        self.assertNotIn(self.users[0].pk, selected_user_ids)
        self.assertEqual(len(selected_user_ids), 3)
        self.assertTrue(
            WaitingRoomEntry.objects.filter(user=self.users[0]).exists(),
        )
        self.assertEqual(WaitingRoomEntry.objects.count(), 1)


class WaitingRoomApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='api_player',
            email='api_player@example.com',
            password='example-password',
        )

    def test_join_and_leave_endpoints_manage_only_authenticated_users_entry(self):
        self.client.force_login(self.user)

        join_response = self.client.post('/api/games/waiting-room/join/')
        self.assertEqual(join_response.status_code, 201)
        self.assertTrue(WaitingRoomEntry.objects.filter(user=self.user).exists())

        duplicate_response = self.client.post('/api/games/waiting-room/join/')
        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(WaitingRoomEntry.objects.filter(user=self.user).count(), 1)

        leave_response = self.client.post('/api/games/waiting-room/leave/')
        self.assertEqual(leave_response.status_code, 204)
        self.assertFalse(WaitingRoomEntry.objects.filter(user=self.user).exists())

        repeated_leave_response = self.client.post('/api/games/waiting-room/leave/')
        self.assertEqual(repeated_leave_response.status_code, 204)

    def test_user_in_waiting_or_active_game_cannot_join(self):
        self.client.force_login(self.user)
        for game_status in (Game.STATUS_WAITING, Game.STATUS_ACTIVE):
            Game.objects.all().delete()
            game = Game.objects.create(status=game_status)
            Player.objects.create(game=game, user=self.user, color=Player.COLOR_RED)

            response = self.client.post('/api/games/waiting-room/join/')

            self.assertEqual(response.status_code, 409)
            self.assertFalse(WaitingRoomEntry.objects.filter(user=self.user).exists())

    def test_completed_game_does_not_prevent_joining(self):
        game = Game.objects.create(status=Game.STATUS_COMPLETED)
        Player.objects.create(game=game, user=self.user, color=Player.COLOR_RED)
        self.client.force_login(self.user)

        response = self.client.post('/api/games/waiting-room/join/')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(WaitingRoomEntry.objects.filter(user=self.user).exists())
