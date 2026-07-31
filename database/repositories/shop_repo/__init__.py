from database.repositories.base_repo import BaseRepository
from database.repositories.shop_repo.categories import ShopCategoriesMixin
from database.repositories.shop_repo.products import ShopProductsMixin


class ShopRepository(
    ShopCategoriesMixin,
    ShopProductsMixin,
    BaseRepository
):
    """Репозиторий для работы исключительно с витриной магазина (клиентская часть)"""
    pass