import re
from django.core.exceptions import ValidationError


def is_username_ok(value):
    # "me" — зарезервированное имя, использовать нельзя
    if value.lower() == 'me':
        raise ValidationError('Имя "me" нельзя использовать.')

    # Имя должно начинаться с буквы и содержать только буквы, цифры, "-", "_" или "."
    pattern = r'^[a-zA-Z][a-zA-Z0-9\-_.]{1,20}$'
    if not re.match(pattern, value):
        raise ValidationError(f'Имя пользователя содержит недопустимые символы: {value}')