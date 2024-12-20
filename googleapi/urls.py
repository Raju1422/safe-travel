from django.urls import path
from . import views

urlpatterns = [
    path('get-coordinates/', views.CoordinatesView.as_view(), name='get_coordinates'),
    path('generate-multi-path-risk/',views.MultiPathRiskView.as_view(), name='generate-multi-path-risk'),
    path('get-best-path-details/', views.BestPathDetailsView.as_view(), name='get-best-path-details'),
]

