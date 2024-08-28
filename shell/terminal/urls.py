from django.urls import path
from .views import terminal_view

urlpatterns = [
    path('', terminal_view, name='terminal'),
    # other URL patterns
]
