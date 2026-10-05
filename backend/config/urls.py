from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def home(request):
    return render(request, 'auth_ui.html')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('questions/', include('questions.urls')),
    path('api/auth/', include('accounts.urls')),
]
