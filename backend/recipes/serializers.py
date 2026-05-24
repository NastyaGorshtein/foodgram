import base64

from django.core.files.base import ContentFile

from rest_framework import serializers

from .models import (Tag, Ingredient, RecipeIngredient,
                     Recipe, Favorite, ShoppingCart)

from django.contrib.auth import get_user_model

User = get_user_model()


class RecipeAuthorSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):

        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        return request.user.subscriptions.filter(
            author=obj
        ).exists()


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):

        if isinstance(data, str) and data.startswith('data:image'):

            format, imgstr = data.split(';base64,')

            ext = format.split('/')[-1]

            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        source='recipe_ingredients',
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    author = RecipeAuthorSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):

        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        return Favorite.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):

        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        allow_empty=False
    )

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        allow_empty=False
    )

    cooking_time = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            **validated_data
        )

        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):

        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:

            RecipeIngredient.objects.filter(recipe=instance).delete()

            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=instance,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients_data
            ])

        return super().update(instance, validated_data)

    def validate(self, data):

        request = self.context.get('request')

        if request and request.method in ('PATCH', 'PUT'):

            if 'ingredients' not in self.initial_data:
                raise serializers.ValidationError({
                    'ingredients': 'Обязательное поле'
                })

            if 'tags' not in self.initial_data:
                raise serializers.ValidationError({
                    'tags': 'Обязательное поле'
                })

        tags = data.get('tags')
        ingredients = data.get('ingredients')

        if tags is not None:
            if len(tags) != len(set(tags)):
                raise serializers.ValidationError(
                    {'tags': 'Теги не должны повторяться'}
                )

        if ingredients is not None:

            ingredient_ids = []

            for ingredient in ingredients:

                ingredient_id = ingredient['id']

                if not Ingredient.objects.filter(id=ingredient_id).exists():
                    raise serializers.ValidationError(
                        {'ingredients': 'Ингредиент не существует'}
                    )

                ingredient_ids.append(ingredient_id)

            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться'}
                )

        return data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
