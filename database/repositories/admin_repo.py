# database/repositories/admin_repo.py
from sqlalchemy import select, delete

from database.models import LocaleText
from database.repositories.base_repo import BaseRepository
from database.models.category import Category
from database.models.product import Product
from database.models.temp_models import TempCategory, TempProduct, TempLocaleText


class AdminRepository(BaseRepository):

    # --- Методы синхронизации ---

    async def sync_to_temp(self, admin_id: int):
        # 1. Очистка временных данных
        await self.session.execute(delete(TempCategory).where(TempCategory.admin_id == admin_id))
        await self.session.execute(delete(TempProduct).where(TempProduct.admin_id == admin_id))
        await self.session.execute(delete(TempLocaleText).where(TempLocaleText.admin_id == admin_id))

        # 2. Синхронизация категорий
        cats_res = await self.session.execute(select(Category))
        cats = cats_res.scalars().all()

        real_to_temp_cat_id = {}
        temp_cats_pairs = []

        for cat in cats:
            tc = TempCategory(
                original_id=cat.id, name=cat.name, parent_id=None, admin_id=admin_id
            )
            self.session.add(tc)
            temp_cats_pairs.append((cat, tc))

        await self.session.flush()

        for cat, tc in temp_cats_pairs:
            real_to_temp_cat_id[cat.id] = tc.id

        for cat, tc in temp_cats_pairs:
            if cat.parent_id is not None:
                tc.parent_id = real_to_temp_cat_id.get(cat.parent_id)

        # 3. Синхронизация продуктов
        prods_res = await self.session.execute(select(Product))
        temp_prods_pairs = []
        for p in prods_res.scalars().all():
            tp = TempProduct(
                original_id=p.id, name=p.name, description=p.description,
                price=p.price, unit=p.unit, image_id=p.image_id,
                category_id=real_to_temp_cat_id.get(p.category_id), admin_id=admin_id
            )
            self.session.add(tp)
            temp_prods_pairs.append((p, tp))

        await self.session.flush()

        # 4. Синхронизация локалей (включая корневое меню с entity_id = 0)
        locales_res = await self.session.execute(select(LocaleText))
        for loc in locales_res.scalars().all():
            target_id = None
            if loc.entity_id == 0:
                target_id = 0
            elif loc.entity_type == 'category':
                target_id = real_to_temp_cat_id.get(loc.entity_id)
            elif loc.entity_type == 'product':
                temp_p = next((tp for p, tp in temp_prods_pairs if p.id == loc.entity_id), None)
                if temp_p:
                    target_id = temp_p.id

            if target_id is not None:
                self.session.add(TempLocaleText(
                    temp_entity_id=target_id,
                    entity_type=loc.entity_type,  # Сохраняем исходный тип ('category', 'product')
                    language_code=loc.language_code,
                    text=loc.text,
                    admin_id=admin_id
                ))

        await self.session.commit()

    async def commit_changes(self, admin_id: int):
        temp_cats = (
            await self.session.execute(select(TempCategory).where(TempCategory.admin_id == admin_id))).scalars().all()
        temp_prods = (
            await self.session.execute(select(TempProduct).where(TempProduct.admin_id == admin_id))).scalars().all()
        temp_locales = (await self.session.execute(
            select(TempLocaleText).where(TempLocaleText.admin_id == admin_id))).scalars().all()

        alive_cat_ids = [tc.original_id for tc in temp_cats if tc.original_id is not None]
        alive_prod_ids = [tp.original_id for tp in temp_prods if tp.original_id is not None]

        # 1. Удаление старых данных
        if alive_prod_ids:
            await self.session.execute(delete(Product).where(~Product.id.in_(alive_prod_ids)))
        else:
            await self.session.execute(delete(Product))

        if alive_cat_ids:
            await self.session.execute(delete(Category).where(~Category.id.in_(alive_cat_ids)))
        else:
            await self.session.execute(delete(Category))

        # Очистка старых локалей для удаленных сущностей (сохраняем корневые с entity_id = 0)
        await self.session.execute(delete(LocaleText).where(
            ~((LocaleText.entity_id.in_(alive_prod_ids) & (LocaleText.entity_type == 'product')) |
              (LocaleText.entity_id.in_(alive_cat_ids) & (LocaleText.entity_type == 'category')) |
              (LocaleText.entity_id == 0))
        ))

        # 2. Обновление и создание категорий
        real_cats_res = await self.session.execute(select(Category).where(Category.id.in_(alive_cat_ids)))
        real_cats_dict = {c.id: c for c in real_cats_res.scalars().all()}

        temp_to_real_id = {}
        new_cats_pairs = []

        for tc in temp_cats:
            if tc.original_id is not None:
                temp_to_real_id[tc.id] = tc.original_id
                if real_cats_dict.get(tc.original_id):
                    real_cats_dict[tc.original_id].name = tc.name
            else:
                new_cat = Category(name=tc.name)
                self.session.add(new_cat)
                new_cats_pairs.append((tc, new_cat))

        await self.session.flush()
        for tc, new_cat in new_cats_pairs:
            temp_to_real_id[tc.id] = new_cat.id

        # 2.1 Обновление parent_id для категорий
        real_cats_all = await self.session.execute(select(Category))
        real_cats_all_dict = {c.id: c for c in real_cats_all.scalars().all()}
        for tc in temp_cats:
            real_cat_id = temp_to_real_id.get(tc.id)
            if real_cat_id and real_cat_id in real_cats_all_dict:
                real_cats_all_dict[real_cat_id].parent_id = temp_to_real_id.get(tc.parent_id)

        # 3. Обновление продуктов
        real_prods_res = await self.session.execute(select(Product).where(Product.id.in_(alive_prod_ids)))
        real_prods_dict = {p.id: p for p in real_prods_res.scalars().all()}
        temp_to_real_prod_id = {}
        new_prods_pairs = []

        for tp in temp_prods:
            real_cat_id = temp_to_real_id.get(tp.category_id)
            if tp.original_id is not None:
                temp_to_real_prod_id[tp.id] = tp.original_id
                real_prod = real_prods_dict.get(tp.original_id)
                if real_prod:
                    real_prod.name, real_prod.description = tp.name, tp.description
                    real_prod.price, real_prod.unit = tp.price, tp.unit
                    real_prod.image_id, real_prod.category_id = tp.image_id, real_cat_id
            else:
                new_prod = Product(
                    name=tp.name, description=tp.description, price=tp.price,
                    unit=tp.unit, image_id=tp.image_id, category_id=real_cat_id
                )
                self.session.add(new_prod)
                new_prods_pairs.append((tp, new_prod))

        await self.session.flush()
        for tp, new_prod in new_prods_pairs:
            temp_to_real_prod_id[tp.id] = new_prod.id

        # 4. Финализация локалей (поддержка temp_entity_id = 0)
        for tl in temp_locales:
            if tl.temp_entity_id == 0:
                real_id = 0
                real_type = tl.entity_type
            elif "category" in tl.entity_type:
                real_id = temp_to_real_id.get(tl.temp_entity_id)
                real_type = "category"
            elif "product" in tl.entity_type:
                real_id = temp_to_real_prod_id.get(tl.temp_entity_id)
                real_type = "product"
            else:
                continue

            if real_id is not None:
                existing_locale_res = await self.session.execute(
                    select(LocaleText).where(
                        LocaleText.entity_id == real_id,
                        LocaleText.entity_type == real_type,
                        LocaleText.language_code == tl.language_code
                    )
                )
                existing_locale = existing_locale_res.scalar_one_or_none()

                if existing_locale:
                    existing_locale.text = tl.text
                else:
                    self.session.add(LocaleText(
                        entity_id=real_id,
                        entity_type=real_type,
                        language_code=tl.language_code,
                        text=tl.text
                    ))

        # 5. Очистка временных
        await self.session.execute(delete(TempCategory).where(TempCategory.admin_id == admin_id))
        await self.session.execute(delete(TempProduct).where(TempProduct.admin_id == admin_id))
        await self.session.execute(delete(TempLocaleText).where(TempLocaleText.admin_id == admin_id))
        await self.session.commit()

    async def get_locale_text(
            self,
            entity_id: int,
            entity_type: str,
            language_code: str,
            use_temp: bool = False,
            admin_id: int = None
    ) -> str | None:
        """
        Универсальный метод получения перевода для сущности (боевой или временной).
        """
        if use_temp:
            query = select(TempLocaleText.text).where(
                TempLocaleText.temp_entity_id == entity_id,
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

    # --- Чтение ---

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
        if use_temp: query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_product_by_id(self, product_id: int, use_temp: bool = False,
                                admin_id: int = None) -> Product | TempProduct | None:
        model = TempProduct if use_temp else Product
        query = select(model).where(model.id == product_id)
        if use_temp: query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_products_by_category(self, category_id: int | None, use_temp: bool = False,
                                       admin_id: int = None) -> list:
        model = TempProduct if use_temp else Product
        query = select(model).where(model.category_id == category_id)
        if use_temp: query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # --- Создание ---

    async def create_category(self, name: str, parent_id: int | None = None, use_temp: bool = False,
                              admin_id: int = None):
        model = TempCategory if use_temp else Category
        data = {"name": name, "parent_id": parent_id}
        if use_temp:
            data["admin_id"] = admin_id

        new_item = model(**data)
        self.session.add(new_item)
        await self.session.commit()
        return new_item

    async def create_product(self, name: str, description: str, price: float, category_id: int | None,
                             image_id: str | None = None, unit: str = "шт.", use_temp: bool = False,
                             admin_id: int = None):
        model = TempProduct if use_temp else Product
        data = {"name": name, "description": description, "price": price, "category_id": category_id,
                "image_id": image_id, "unit": unit}
        if use_temp:
            data["admin_id"] = admin_id

        new_item = model(**data)
        self.session.add(new_item)
        await self.session.commit()
        return new_item

    # --- Удаление и Обновление ---

    async def _get_temp_subcategory_ids(self, parent_id: int, admin_id: int, accumulated: list):
        """Вспомогательный метод для рекурсивного сбора ID всех подкатегорий в Temp."""
        res = await self.session.execute(
            select(TempCategory.id).where(TempCategory.parent_id == parent_id, TempCategory.admin_id == admin_id)
        )
        sub_ids = res.scalars().all()
        for s_id in sub_ids:
            accumulated.append(s_id)
            await self._get_temp_subcategory_ids(s_id, admin_id, accumulated)

    async def _get_real_subcategory_ids(self, parent_id: int, accumulated: list):
        """Вспомогательный метод для рекурсивного сбора ID всех подкатегорий в Prod."""
        res = await self.session.execute(select(Category.id).where(Category.parent_id == parent_id))
        sub_ids = res.scalars().all()
        for s_id in sub_ids:
            accumulated.append(s_id)
            await self._get_real_subcategory_ids(s_id, accumulated)

    async def delete_category(self, category_id: int, use_temp: bool = False, admin_id: int = None):
        """Удаление категории с каскадным рекурсивным удалением всех подкатегорий и их товаров."""
        if use_temp:
            all_cat_ids = [category_id]
            await self._get_temp_subcategory_ids(category_id, admin_id, all_cat_ids)

            await self.session.execute(
                delete(TempProduct).where(TempProduct.category_id.in_(all_cat_ids), TempProduct.admin_id == admin_id))
            await self.session.execute(
                delete(TempCategory).where(TempCategory.id.in_(all_cat_ids), TempCategory.admin_id == admin_id))
        else:
            all_cat_ids = [category_id]
            await self._get_real_subcategory_ids(category_id, all_cat_ids)

            await self.session.execute(delete(Product).where(Product.category_id.in_(all_cat_ids)))
            await self.session.execute(delete(Category).where(Category.id.in_(all_cat_ids)))

        await self.session.commit()

    async def delete_product(self, product_id: int, use_temp: bool = False, admin_id: int = None):
        model = TempProduct if use_temp else Product
        query = delete(model).where(model.id == product_id)
        if use_temp: query = query.where(model.admin_id == admin_id)
        await self.session.execute(query)
        await self.session.commit()

    async def update_product_field(self, product_id: int, field: str, value: any, use_temp: bool = False,
                                   admin_id: int = None):
        model = TempProduct if use_temp else Product
        query = select(model).where(model.id == product_id)
        if use_temp: query = query.where(model.admin_id == admin_id)

        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        if item:
            setattr(item, field, value)
            await self.session.commit()

    # --- Работа с локалями (Temp) ---

    async def get_temp_locales(self, entity_id: int, entity_type: str, admin_id: int):
        """Получает список всех локалей для временной сущности."""
        result = await self.session.execute(
            select(TempLocaleText).where(
                TempLocaleText.temp_entity_id == entity_id,
                TempLocaleText.entity_type == entity_type,
                TempLocaleText.admin_id == admin_id
            )
        )
        return result.scalars().all()

    async def update_temp_locale(self, entity_id: int, entity_type: str,
                                 language_code: str, text: str, admin_id: int):
        """Обновляет или создает запись локали во временной таблице."""
        # Пытаемся найти существующую
        result = await self.session.execute(
            select(TempLocaleText).where(
                TempLocaleText.temp_entity_id == entity_id,
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
                temp_entity_id=entity_id,
                entity_type=entity_type,
                language_code=language_code,
                text=text,
                admin_id=admin_id
            )
            self.session.add(new_locale)

        await self.session.commit()