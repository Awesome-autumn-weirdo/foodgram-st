from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe
from users.models import Follow


def create_object(request, pk, input_serializer, output_serializer, base_model):
    """
    Универсальный метод добавления объекта:
    - в избранное
    - в корзину
    - в подписки
    """
    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    target = get_object_or_404(base_model, id=pk)

    payload = {
        "user": user.id,
        "recipe" if base_model is Recipe else "author": target.id
    }

    serializer = input_serializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    output_data = output_serializer(target, context={"request": request})
    return Response(output_data.data, status=status.HTTP_201_CREATED)


def delete_object(request, pk, target_model, relation_model):
    """
    Универсальное удаление из:
    - избранного
    - корзины
    - подписок
    """
    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if relation_model is Follow:
        link = get_object_or_404(relation_model, user=user, author_id=pk)
    else:
        recipe_instance = get_object_or_404(target_model, id=pk)
        link = get_object_or_404(relation_model, user=user, recipe=recipe_instance)

    link.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)