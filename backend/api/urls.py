from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    UserViewSet,
    AvatarView,
)

router = DefaultRouter()

router.register('tags', TagViewSet)
router.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredient'
)
router.register('recipes', RecipeViewSet)
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path(
        'users/me/avatar/',
        AvatarView.as_view(),
        name='avatar'
    ),

    path('', include(router.urls)),

    path('', include('djoser.urls')),
]
