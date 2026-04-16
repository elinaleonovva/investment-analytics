from django.urls import path
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='auth_refresh'),
]