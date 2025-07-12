from django.contrib.auth.models import AbstractUser, Permission, Group
from django.db import models

from users.validation import validate_username


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True
    )
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        validators=[validate_username]
    )
    email = models.EmailField(
        'Email',
        max_length=254,
        unique=True
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        verbose_name='Группы',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        verbose_name='Права доступа',
        blank=True,
        help_text='Конкретные разрешения для этого пользователя.'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',  # пользователь подписан на авторов
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',  # у автора есть подписчики
        verbose_name='Автор'
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
