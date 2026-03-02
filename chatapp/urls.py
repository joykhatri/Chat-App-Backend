from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path

router = DefaultRouter()
router.register('register', UserViewSet, basename="register")
router.register('users', UserViewSet, basename="users")
router.register('login', LoginViewSet, basename="login")
router.register('profile', ProfileViewSet, basename="profile")
router.register('chat/start', ChatViewSet, basename="start_chat")
router.register('chat', ChatViewSet, basename="view_chat")
urlpatterns = [
    path('logout/', LogoutViewSet.as_view(), name="logout")
]

urlpatterns += router.urls