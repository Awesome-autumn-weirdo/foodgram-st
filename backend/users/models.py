from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from users.validation import is_username_ok


class CustomUser(AbstractUser):
    """
    Расширенная модель пользователя с использованием email в качестве логина,
    добавлением аватара и настройкой групп и прав.
    """
    email = models.EmailField(
        _('Электронная почта'),
        max_length=254,
        unique=True
    )
    username = models.CharField(
        _('Имя пользователя'),
        max_length=150,
        unique=True,
        validators=[is_username_ok]
    )
    first_name = models.CharField(_('Имя'), max_length=150)
    last_name = models.CharField(_('Фамилия'), max_length=150)
    avatar = models.ImageField(
        _('Аватар'),
        upload_to='profiles/avatars/',
        blank=True,
        null=True,
        default='recipes/images/default.jpg'
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('Группы пользователя'),
        blank=True,
        related_name='custom_users',
        related_query_name='custom_user',
        help_text=_('Группы, в которых состоит пользователь')
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('Права пользователя'),
        blank=True,
        related_name='custom_users_permissions',
        related_query_name='custom_user_permission',
        help_text=_('Права, назначенные напрямую')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'custom_users'
        ordering = ['username']
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return f"{self.username} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = 'recipes/images/default.jpg'
        super().save(*args, **kwargs)


class Follow(models.Model):
    """
    Модель для подписок между пользователями.
    Обеспечивает уникальность пары подписчик-автор.
    """
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Подписчик')
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=_('Автор')
    )
    created_at = models.DateTimeField(
        _('Дата подписки'),
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription'
            )
        ]
        ordering = ['-created_at']
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

    def __str__(self):
        return f"{self.subscriber.username} подписан на {self.author.username}"