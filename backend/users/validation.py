import re
from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError('Имя "me" использовать нельзя.')

    pattern = r'^[a-zA-Z][a-zA-Z0-9\-_.]{1,20}$'
    if not re.match(pattern, value):
        raise ValidationError(f'Недопустимые символы в имени: {value}')
