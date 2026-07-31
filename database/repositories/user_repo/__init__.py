from database.repositories.base_repo import BaseRepository
from database.repositories.user_repo.account import UserAccountMixin
from database.repositories.user_repo.cart import UserCartMixin
from database.repositories.user_repo.orders import UserOrderMixin


class UserRepository(
    UserAccountMixin,
    UserCartMixin,
    UserOrderMixin,
    BaseRepository
):
    pass