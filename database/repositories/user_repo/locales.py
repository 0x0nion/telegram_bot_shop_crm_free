from typing import Optional
from database.models.locales import LocaleText
from database.repositories.base_repo import BaseRepository


class UserLocaleMixin:
    """Миксин для работы с локалями и динамическими текстами/медиа на стороне пользователя."""

    @property
    def _locale_repo(self) -> BaseRepository[LocaleText]:
        return BaseRepository(LocaleText, self.session)

    async def get_locale_text(
            self,
            entity_type: str,
            entity_id: int = 0,
            lang_code: str = "ru",
            default_lang: str = "ru"
    ) -> Optional[str]:
        # 1. Поиск по основному языку
        locale = await self._locale_repo.get_one(
            LocaleText.entity_type == entity_type,
            LocaleText.entity_id == entity_id,
            LocaleText.language_code == lang_code
        )
        if locale and locale.text:
            return locale.text

        # 2. Фолбэк на дефолтный язык
        if lang_code != default_lang:
            fallback_locale = await self._locale_repo.get_one(
                LocaleText.entity_type == entity_type,
                LocaleText.entity_id == entity_id,
                LocaleText.language_code == default_lang
            )
            if fallback_locale:
                return fallback_locale.text

        return None

    async def get_welcome_card(self, lang_code: str = "ru") -> tuple[str, Optional[str]]:
        text = await self.get_locale_text(
            entity_type="welcome_message",
            entity_id=0,
            lang_code=lang_code
        )
        if not text:
            text = "👋 Добро пожаловать в наш магазин!"

        photo_id = await self.get_locale_text(
            entity_type="welcome_photo",
            entity_id=0,
            lang_code=lang_code
        )

        if photo_id and (not photo_id.startswith("http") and len(photo_id) < 10):
            photo_id = None

        return text, photo_id