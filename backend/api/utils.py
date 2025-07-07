from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe, Subscription


def create_object(request, pk, serializer_in, serializer_out, model):
    """
    Создаёт связь: добавляет в избранное, корзину или подписки.
    """
    if request.user.is_anonymous:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    user_id = request.user.id
    obj = get_object_or_404(model, id=pk)

    if model is Recipe:
        data = {'user': user_id, 'recipe': obj.id}
    else:
        data = {'user': user_id, 'author': obj.id}

    serializer = serializer_in(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Возвращаем данные уже сериализованные в нужном формате
    return serializer_out(obj, context={'request': request})


def delete_object(request, pk, model_object, delete_model):
    """
    Удаляет связь: из избранного, корзины или подписок.
    """
    user = request.user
    if user.is_anonymous:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if delete_model is Subscription:
        obj = get_object_or_404(delete_model, user=user, author=pk)
    else:
        recipe = get_object_or_404(model_object, id=pk)
        obj = get_object_or_404(delete_model, user=user, recipe=recipe)

    obj.delete()
