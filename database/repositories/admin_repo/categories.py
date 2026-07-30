from sqlalchemy import select, delete

from database.models import LocaleText
from database.models.category import Category
from database.models.product import Product
from database.models.temp_models import TempCategory, TempProduct, TempLocaleText
from locales.units import DEFAULT_UNIT
from utils.logger import logger


class AdminCategoriesMixin:

    async def get_category_by_id(self, category_id: int, use_temp: bool = False,
                                 admin_id: int = None) -> Category | TempCategory | None:
        model = TempCategory if use_temp else Category
        query = select(model).where(model.id == category_id)
        if use_temp:
            query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_categories_by_parent(self, parent_id: int | None = None, use_temp: bool = False,
                                       admin_id: int = None) -> list:
        model = TempCategory if use_temp else Category
        query = select(model).where(model.parent_id == parent_id)
        if use_temp:
            query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_category(
            self,
            name: str,
            parent_id: int | None = None,
            use_temp: bool = False,
            admin_id: int = None
    ) -> Category | TempCategory:
        logger.info(f"Creating category '{name}' (parent_id={parent_id}, use_temp={use_temp}, admin_id={admin_id})")
        model = TempCategory if use_temp else Category
        data = {"name": name, "parent_id": parent_id}
        if use_temp:
            data["admin_id"] = admin_id

        new_category = model(**data)
        self.session.add(new_category)
        await self.session.flush()

        for lang_code in self.SUPPORTED_LANGUAGES:
            if use_temp:
                self.session.add(TempLocaleText(
                    entity_id=new_category.id,
                    entity_type="category_name",
                    language_code=lang_code,
                    text=name,
                    admin_id=admin_id
                ))
            else:
                self.session.add(LocaleText(
                    entity_id=new_category.id,
                    entity_type="category_name",
                    language_code=lang_code,
                    text=name
                ))

        await self.session.commit()
        return new_category

    async def _get_temp_subcategory_ids(self, parent_id: int, admin_id: int, accumulated: list):
        res = await self.session.execute(
            select(TempCategory.id).where(TempCategory.parent_id == parent_id, TempCategory.admin_id == admin_id)
        )
        sub_ids = res.scalars().all()
        for s_id in sub_ids:
            accumulated.append(s_id)
            await self._get_temp_subcategory_ids(s_id, admin_id, accumulated)

    async def _get_real_subcategory_ids(self, parent_id: int, accumulated: list):
        res = await self.session.execute(select(Category.id).where(Category.parent_id == parent_id))
        sub_ids = res.scalars().all()
        for s_id in sub_ids:
            accumulated.append(s_id)
            await self._get_real_subcategory_ids(s_id, accumulated)

    async def delete_category(self, category_id: int, use_temp: bool = False, admin_id: int = None):
        logger.info(f"Deleting category id={category_id} (use_temp={use_temp}, admin_id={admin_id})")
        if use_temp:
            all_cat_ids = [category_id]
            await self._get_temp_subcategory_ids(category_id, admin_id, all_cat_ids)

            await self.session.execute(
                delete(TempProduct).where(TempProduct.category_id.in_(all_cat_ids), TempProduct.admin_id == admin_id)
            )
            await self.session.execute(
                delete(TempCategory).where(TempCategory.id.in_(all_cat_ids), TempCategory.admin_id == admin_id)
            )
            await self.session.execute(
                delete(TempLocaleText).where(
                    TempLocaleText.entity_id.in_(all_cat_ids),
                    TempLocaleText.entity_type.like('%category%'),
                    TempLocaleText.admin_id == admin_id
                )
            )
        else:
            all_cat_ids = [category_id]
            await self._get_real_subcategory_ids(category_id, all_cat_ids)

            await self.session.execute(delete(Product).where(Product.category_id.in_(all_cat_ids)))
            await self.session.execute(delete(Category).where(Category.id.in_(all_cat_ids)))
            await self.session.execute(
                delete(LocaleText).where(
                    LocaleText.entity_id.in_(all_cat_ids),
                    LocaleText.entity_type.like('%category%')
                )
            )

        await self.session.commit()