from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Game(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_WAITING, 'Waiting'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Game {self.pk}'

    def clean(self):
        super().clean()
        if self.status == self.STATUS_ACTIVE and self.players.count() != 3:
            raise ValidationError({'status': 'An active game must have exactly three players.'})

    def get_current_round(self):
        return self.rounds.order_by('-number').first()

    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    def is_completed(self):
        return self.status == self.STATUS_COMPLETED


class Player(models.Model):
    COLOR_RED = 'red'
    COLOR_GREEN = 'green'
    COLOR_BLUE = 'blue'

    COLORS = [
        (COLOR_RED, 'Red'),
        (COLOR_GREEN, 'Green'),
        (COLOR_BLUE, 'Blue'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    score = models.IntegerField(default=0)
    color = models.CharField(max_length=20, choices=COLORS)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'], name='unique_user_per_game'),
            models.UniqueConstraint(fields=['game', 'color'], name='unique_color_per_game'),
            models.CheckConstraint(condition=models.Q(score__gte=0), name='player_score_gte_0'),
        ]

    def clean(self):
        super().clean()
        if self.score < 0:
            raise ValidationError({'score': 'Score cannot be negative.'})

    def __str__(self):
        return f'{self.user.username} ({self.color})'


class WaitingRoomEntry(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='waiting_room_entry',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} (waiting)'


class Round(models.Model):
    TYPE_CITY_CAPTURE = 'city_capture'
    TYPE_BATTLE = 'battle'
    TYPE_CAPITAL_ATTACK = 'capital_attack'
    TYPE_BONUS = 'bonus'

    TYPE_CHOICES = [
        (TYPE_CITY_CAPTURE, 'City Capture'),
        (TYPE_BATTLE, 'Battle'),
        (TYPE_CAPITAL_ATTACK, 'Capital Attack'),
        (TYPE_BONUS, 'Bonus'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['game', 'number'], name='unique_round_number_per_game'),
            models.UniqueConstraint(
                fields=['game'],
                condition=models.Q(status='active'),
                name='unique_active_round_per_game',
            ),
        ]

    def clean(self):
        super().clean()
        if self.winner and self.winner.game_id != self.game_id:
            raise ValidationError({'winner': 'Winner must belong to the same game as the round.'})

        if self.status == self.STATUS_COMPLETED:
            if self.winner is None:
                raise ValidationError({'winner': 'Completed rounds must have a winner.'})
            if self.completed_at is None:
                raise ValidationError({'completed_at': 'Completed rounds must include a completion timestamp.'})
        elif self.completed_at is not None:
            raise ValidationError({'completed_at': 'Only completed rounds may include a completion timestamp.'})

    def __str__(self):
        return f'Round {self.number} ({self.type})'
