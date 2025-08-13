from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from users.models import CustomUser, Follow
from .base import Base64ImageField

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)

class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return (
            user.is_authenticated and
            Follow.objects.filter(subscriber=user, author=obj).exists()
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get('avatar'):
            request = self.context.get('request')
            default_path = 'recipes/images/default.jpg'
            data['avatar'] = (
                request.build_absolute_uri(f'/media/{default_path}')
                if request else f'/media/{default_path}'
            )
        return data
