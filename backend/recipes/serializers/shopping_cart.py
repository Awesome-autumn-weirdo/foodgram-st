from .favorite import BaseFavoriteShoppingSerializer
from recipes.models import ShoppingCart

class ShoppingCartSerializer(BaseFavoriteShoppingSerializer):
    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = ShoppingCart
