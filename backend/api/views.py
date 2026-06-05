from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.urls import reverse

from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated,
                                        AllowAny
                                        )
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import RecipeFilter
from .pagination import RecipesPagination
from .permissions import IsAuthorOrReadOnly
from recipes.models import (Tag, Ingredient, Recipe,
                            RecipeIngredient)
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          RecipeShortSerializer, FavoriteSerializer,
                          ShoppingCartSerializer, UserSerializer,
                          SubscriptionSerializer,
                          SubscriptionCreateSerializer,
                          AvatarSerializer, FavoriteDeleteSerializer,
                          ShoppingCartDeleteSerializer,
                          SubscriptionDeleteSerializer
                          )

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):

        queryset = Ingredient.objects.all()

        name = self.request.query_params.get('name')

        if name:
            queryset = queryset.filter(
                name__istartswith=name
            )

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,)
    pagination_class = RecipesPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save(
            author=request.user
        )

        read_serializer = RecipeReadSerializer(
            recipe,
            context={'request': request}
        )

        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)

        recipe = serializer.save()

        read_serializer = RecipeReadSerializer(
            recipe,
            context={'request': request}
        )

        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(
            request,
            *args,
            partial=True,
            **kwargs
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):

        recipe = self.get_object()

        if request.method == 'POST':

            serializer = FavoriteSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id,
                }
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer = FavoriteDeleteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id,
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):

        recipe = self.get_object()

        if request.method == 'POST':

            serializer = ShoppingCartSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id,
                }
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer = ShoppingCartDeleteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id,
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = '\n'.join(
            (
                f'{ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]}) — '
                f'{ingredient["total_amount"]}'
            )
            for ingredient in ingredients
        )

        response = HttpResponse(
            shopping_list,
            content_type='text/plain'
        )

        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response

    @action(
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_link(self, request, pk=None):

        recipe = self.get_object()

        short_path = reverse(
            'recipe-short-link',
            kwargs={'pk': recipe.pk}
        )

        short_link = request.build_absolute_uri(short_path)

        return Response({
            'short-link': short_link
        })


class UserViewSet(DjoserUserViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = RecipesPagination

    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_permissions(self):

        if self.action in {'list', 'retrieve', 'create'}:
            return [AllowAny()]

        return [IsAuthenticated()]

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):

        author = self.get_object()

        if request.method == 'POST':

            serializer = SubscriptionCreateSerializer(
                data={
                    'user': request.user.id,
                    'author': author.id,
                }
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer = SubscriptionDeleteSerializer(
            data={
                'user': request.user.id,
                'author': author.id,
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):

        authors = User.objects.filter(
            subscribers__user=request.user
        ).annotate(
            recipes_count=Count('recipes')
        ).order_by('id').prefetch_related('recipes')

        page = self.paginate_queryset(authors)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            authors,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)


class AvatarView(APIView):

    permission_classes = (IsAuthenticated,)

    def put(self, request):

        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)

    def delete(self, request):

        request.user.avatar.delete()

        request.user.avatar = None
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
