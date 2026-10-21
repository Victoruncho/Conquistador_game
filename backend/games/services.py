import random

from django.db import transaction
from django.db.models import Exists, OuterRef

from .models import Game, Player, WaitingRoomEntry


class WaitingRoomError(Exception):
    pass


class AlreadyWaitingError(WaitingRoomError):
    pass


class IneligiblePlayerError(WaitingRoomError):
    pass


def _has_ongoing_game(user_id):
    return Player.objects.filter(
        user_id=user_id,
        game__status__in=[Game.STATUS_WAITING, Game.STATUS_ACTIVE],
    )


@transaction.atomic
def join_waiting_room(user):
    if WaitingRoomEntry.objects.filter(user=user).exists():
        raise AlreadyWaitingError

    if _has_ongoing_game(user.pk).exists():
        raise IneligiblePlayerError

    return WaitingRoomEntry.objects.create(user=user)


@transaction.atomic
def leave_waiting_room(user):
    WaitingRoomEntry.objects.filter(user=user).delete()


@transaction.atomic
def form_waiting_room_game():
    ongoing_games = Player.objects.filter(
        user_id=OuterRef('user_id'),
        game__status__in=[Game.STATUS_WAITING, Game.STATUS_ACTIVE],
    )
    eligible_entries = list(
        WaitingRoomEntry.objects.annotate(
            has_ongoing_game=Exists(ongoing_games),
        )
        .filter(has_ongoing_game=False)
        .select_related('user')
    )

    if len(eligible_entries) < 3:
        return None

    selected_entries = random.sample(eligible_entries, 3)
    game = Game.objects.create(status=Game.STATUS_WAITING)
    Player.objects.bulk_create(
        [
            Player(
                user=entry.user,
                game=game,
                color=color,
                score=0,
            )
            for entry, (color, _) in zip(selected_entries, Player.COLORS)
        ]
    )
    WaitingRoomEntry.objects.filter(
        pk__in=[entry.pk for entry in selected_entries],
    ).delete()

    return game
