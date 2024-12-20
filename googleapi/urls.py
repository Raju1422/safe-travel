from django.urls import path
from . import views

urlpatterns = [
    path('get-coordinates/', views.CoordinatesView.as_view(), name='get_coordinates'),
]
