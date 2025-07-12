from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe, Subscription


def create_object(request, pk, input_serializer, output_serializer, model):
    """
    Добавление в избранное, корзину или подписки.
    """
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    user = request.user
    obj = get_object_or_404(model, id=pk)

    if model == Recipe:
        data = {
            'user': user.id,
            'recipe': obj.id
        }
    else:
        data = {
            'user': user.id,
            'author': obj.id
        }

    serializer = input_serializer(data=data)
    if serializer.is_valid():
        serializer.save()
        result = output_serializer(obj, context={'request': request})
        return Response(result.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def delete_object(request, pk, model_obj, link_model):
    """
    Удаление из избранного, корзины или подписок.
    """
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    user = request.user

    if link_model == Subscription:
        obj = get_object_or_404(link_model, user=user, author=pk)
    else:
        recipe = get_object_or_404(model_obj, id=pk)
        obj = get_object_or_404(link_model, user=user, recipe=recipe)

    obj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
