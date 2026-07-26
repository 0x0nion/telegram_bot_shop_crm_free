from sqlalchemy import select, delete

from database.models import LocaleText
from database.models.temp_models import TempLocaleText
from utils.logger import logger


class AdminLocalesMixin:

    async def get_locale_text(
            self,
            entity_id: int,
            entity_type: str,
            language_code: str,
            use_temp: bool = False,
            admin_id: int = None
    ) -> str | None:
        if use_temp:
            query = select(TempLocaleText.text).where(
                TempLocaleText.entity_id == entity_id,
                TempLocaleText.entity_type == entity_type,
                TempLocaleText.language_code == language_code,
                TempLocaleText.admin_id == admin_id
            )
        else:
            query = select(LocaleText.text).where(
                LocaleText.entity_id == entity_id,
                LocaleText.entity_type == entity_type,
                LocaleText.language_code == language_code
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_temp_locales(self, entity_id: int, entity_type: str, admin_id: int):
        result = await self.session.execute(
            select(TempLocaleText).where(
                TempLocaleText.entity_id == entity_id,
                TempLocaleText.entity_type == entity_type,
                TempLocaleText.admin_id == admin_id
            )
        )
        return result.scalars().all()

    async def update_temp_locale(self, entity_id: int, entity_type: str,
                                 language_code: str, text: str, admin_id: int):
        logger.debug(f"Updating temp locale for entity_id={entity_id}, type='{entity_type}', lang='{language_code}', admin_id={admin_id}")
        result = await self.session.execute(
            select(TempLocaleText).where(
                TempLocaleText.entity_id == entity_id,
                TempLocaleText.entity_type == entity_type,
                TempLocaleText.language_code == language_code,
                TempLocaleText.admin_id == admin_id
            )
        )
        locale = result.scalar_one_or_none()

        if locale:
            locale.text = text
        else:
            new_locale = TempLocaleText(
                entity_id=entity_id,
                entity_type=entity_type,
                language_code=language_code,
                text=text,
                admin_id=admin_id
            )
            self.session.add(new_locale)

        await self.session.commit()

    async def update_temp_locale_for_all_languages(
            self,
            entity_id: int,
            entity_type: str,
            text: str,
            admin_id: int
    ):
        for lang_code in self.SUPPORTED_LANGUAGES:
            await self.update_temp_locale(
                entity_id=entity_id,
                entity_type=entity_type,
                language_code=lang_code,
                text=text,
                admin_id=admin_id
            )

    async def delete_temp_locale_for_all_languages(
            self,
            entity_id: int,
            entity_type: str,
            admin_id: int
    ):
        logger.info(f"Deleting temp locales for entity_id={entity_id}, type='{entity_type}', admin_id={admin_id}")
        await self.session.execute(
            delete(TempLocaleText).where(
                TempLocaleText.entity_id == entity_id,
                TempLocaleText.entity_type == entity_type,
                TempLocaleText.admin_id == admin_id
            )
        )
        await self.session.commit()