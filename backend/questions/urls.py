from django.urls import path

from .views import question_ui

urlpatterns = [
    path('', question_ui, name='question_ui'),
]
