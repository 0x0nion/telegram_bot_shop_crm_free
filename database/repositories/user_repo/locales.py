from typing import Optional
from sqlalchemy import select
from database.models.locales import LocaleText


class UserLocaleMixin:
    """Миксин для работы с локалями и динамическими текстами/медиа на стороне пользователя."""

    async def get_locale_text(
            self,
            entity_type: str,
            entity_id: int = 0,
            lang_code: str = "ru",
            default_lang: str = "ru"
    ) -> Optional[str]:
        """
        Универсальный подгрузчик локалей с фолбэком на язык по умолчанию.

        :param entity_type: Тип сущности ("welcome_message", "welcome_photo", "category_name" и т.д.)
        :param entity_id: ID сущности (0 для глобальных системных системных параметров)
        :param lang_code: Основной язык пользователя
        :param default_lang: Резервный язык при отсутствии перевода
        """
        # 1. Поиск по запрошенному языку
        stmt = select(LocaleText.text).where(
            LocaleText.entity_type == entity_type,
            LocaleText.entity_id == entity_id,
            LocaleText.language_code == lang_code
        )
        result = await self.session.execute(stmt)
        text = result.scalar_one_or_none()

        # 2. Фолбэк на дефолтный язык (если основного перевода нет в БД)
        if text is None and lang_code != default_lang:
            fallback_stmt = select(LocaleText.text).where(
                LocaleText.entity_type == entity_type,
                LocaleText.entity_id == entity_id,
                LocaleText.language_code == default_lang
            )
            fallback_res = await self.session.execute(fallback_stmt)
            text = fallback_res.scalar_one_or_none()

        return text

    async def get_welcome_card(self, lang_code: str = "ru") -> tuple[str, Optional[str]]:
        """
        Получение приветственного текста и обложки для стартового меню.
        """
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