from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    AlreadyWaitingError,
    IneligiblePlayerError,
    join_waiting_room,
    leave_waiting_room,
)


class WaitingRoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            entry = join_waiting_room(request.user)
        except AlreadyWaitingError:
            return Response(
                {'detail': 'You already have a waiting room request.'},
                status=status.HTTP_409_CONFLICT,
            )
        except IneligiblePlayerError:
            return Response(
                {'detail': 'You are already in a waiting or active game.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {'created_at': entry.created_at},
            status=status.HTTP_201_CREATED,
        )


class WaitingRoomLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        leave_waiting_room(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
