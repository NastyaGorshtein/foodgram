from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated,
                                        AllowAny
                                        )
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .models import (Tag, Ingredient, Recipe,
                     Favorite, ShoppingCart, RecipeIngredient)
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          RecipeShortSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
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
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
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
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):

        recipe = self.get_object()

        if request.method == 'POST':

            if Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():

                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Favorite.objects.create(
                user=request.user,
                recipe=recipe
            )

            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        favorite = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        )

        if not favorite.exists():
            return Response(
                {'errors': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):

        recipe = self.get_object()

        if request.method == 'POST':

            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():

                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(
                user=request.user,
                recipe=recipe
            )

            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        shopping_cart = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        )

        if not shopping_cart.exists():
            return Response(
                {'errors': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_cart.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
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

        shopping_list = []

        for item in ingredients:
            shopping_list.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )

        response = HttpResponse(
            '\n'.join(shopping_list),
            content_type='text/plain'
        )

        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):

        recipe = self.get_object()

        short_link = request.build_absolute_uri(
            f'/recipes/{recipe.id}/'
        )

        return Response({
            'short-link': short_link
        })
