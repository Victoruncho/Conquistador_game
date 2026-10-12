from django.contrib import admin

from .models import Game, Player, Round


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'players_count')
    list_filter = ('status',)
    search_fields = ('id',)

    @admin.display(description='Players')
    def players_count(self, obj):
        return obj.players.count()


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'color', 'score')
    list_filter = ('game', 'color')
    search_fields = ('user__username',)


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('game', 'number', 'type', 'status', 'winner', 'created_at', 'completed_at')
    list_filter = ('game', 'type', 'status')
    search_fields = ('game__id', 'winner__user__username')
