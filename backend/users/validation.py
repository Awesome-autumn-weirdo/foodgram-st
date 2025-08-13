import re
from django.core.exceptions import ValidationError


def is_username_ok(value):
    """
    Проверяет валидность имени пользователя.

    Правила:
    - Имя не может быть 'me' (регистр не важен).
    - Имя должно начинаться с буквы.
    - Допустимые символы: буквы, цифры, дефис, подчеркивание и точка.
    - Длина от 2 до 21 символа включительно.
    """

    normalized = value.lower()
    if normalized == 'me':
        raise ValidationError('Имя "me" зарезервировано и не может использоваться.')

    # Регулярное выражение проверяет:
    # первый символ — буква,
    # остальные 1–20 символов — буквы, цифры, -, _, .
    username_regex = r'^[a-zA-Z][a-zA-Z0-9._-]{1,20}$'

    if not re.fullmatch(username_regex, value):
        raise ValidationError(f'Недопустимое имя пользователя: "{value}". Проверьте формат.')
