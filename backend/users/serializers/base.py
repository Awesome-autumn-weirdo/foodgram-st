import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""
    ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png')

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, b64data = data.split(';base64,')
                ext = header.split('/')[-1].lower().replace('jpeg', 'jpg')
                if ext not in self.ALLOWED_EXTENSIONS:
                    raise serializers.ValidationError(
                        f"Недопустимый формат '{ext}'. Разрешено: {', '.join(self.ALLOWED_EXTENSIONS)}"
                    )
                file_name = f"{uuid.uuid4().hex[:12]}.{ext}"
                decoded_file = base64.b64decode(b64data)
                data = ContentFile(decoded_file, name=file_name)
            except Exception:
                raise serializers.ValidationError('Ошибка чтения изображения')
        return super().to_internal_value(data)
