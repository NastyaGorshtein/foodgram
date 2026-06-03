from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .models import Recipe


class RecipeRedirectView(View):

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)

        return redirect(f'/recipes/{recipe.pk}/')
