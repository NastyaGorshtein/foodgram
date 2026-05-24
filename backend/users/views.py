from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.views import APIView

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from recipes.pagination import CustomPagination
from .models import Subscription, User
from .serializers import UserSerializer, SubscriptionSerializer, AvatarSerializer


class UserViewSet(DjoserUserViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):

        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]

        return [IsAuthenticated()]

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):

        author = get_object_or_404(User, id=id)

        if request.user == author:

            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':

            if Subscription.objects.filter(
                user=request.user,
                author=author
            ).exists():

                return Response(
                    {'errors': 'Уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(
                user=request.user,
                author=author
            )

            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        subscription = Subscription.objects.filter(
            user=request.user,
            author=author
        )

        if not subscription.exists():
            return Response(
                {'errors': 'Подписки не существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):

        authors = User.objects.filter(
            subscribers__user=request.user
        ).annotate(
            recipes_count=Count('recipes')
        ).prefetch_related('recipes')

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

    permission_classes = [IsAuthenticated]

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