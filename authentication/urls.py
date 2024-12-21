from django.urls import path
from .views import UserRegistrationView,LoginView,UserDetailsView,SendEmailView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path("login/",LoginView.as_view(),name="login"),
   path('user/details/', UserDetailsView.as_view(), name='user-details'),
    path('user/send-email/', SendEmailView.as_view(), name='send-email'),

]