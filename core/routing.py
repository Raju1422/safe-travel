# your_app_name/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/predict-risk/", consumers.RiskPredictionConsumer.as_asgi()),
]