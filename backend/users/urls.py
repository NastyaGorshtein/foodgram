from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, AvatarView

router = DefaultRouter()

router.register('', UserViewSet, basename='users')

urlpatterns = [
    path(
        'me/avatar/',
        AvatarView.as_view(),
        name='avatar'
    ),
    path('', include(router.urls)),
]
