from database.repositories.base_repo import BaseRepository
from database.repositories.admin_repo.categories import AdminCategoriesMixin
from database.repositories.admin_repo.products import AdminProductsMixin
from database.repositories.admin_repo.locales import AdminLocalesMixin
from database.repositories.admin_repo.sync import AdminSyncMixin


class AdminRepository(
    AdminCategoriesMixin,
    AdminProductsMixin,
    AdminLocalesMixin,
    AdminSyncMixin,
    BaseRepository
):
    SUPPORTED_LANGUAGES = ["ru", "en", "es"]