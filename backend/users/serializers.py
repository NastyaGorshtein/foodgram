from django.contrib.auth import get_user_model
from rest_framework import serializers

from djoser.serializers import UserCreateSerializer

from recipes.serializers import Base64ImageField


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_is_subscribed(self, obj):

        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        return request.user.subscriptions.filter(
            author=obj
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
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

    def get_recipes(self, obj):
        from recipes.serializers import RecipeShortSerializer

        request = self.context.get('request')

        recipes = obj.recipes.all()

        recipes_limit = None

        if request:
            recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
