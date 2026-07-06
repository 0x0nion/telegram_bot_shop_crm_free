# database/repositories/admin_repo.py
from sqlalchemy import select, delete
from database.repositories.base_repo import BaseRepository
from database.models.category import Category
from database.models.product import Product
from database.models.temp_models import TempCategory, TempProduct


class AdminRepository(BaseRepository):

    # --- Методы синхронизации ---

    async def sync_to_temp(self, admin_id: int):
        # Очищаем временные данные текущего админа
        await self.session.execute(delete(TempCategory).where(TempCategory.admin_id == admin_id))
        await self.session.execute(delete(TempProduct).where(TempProduct.admin_id == admin_id))

        # Получаем свежие данные из основы
        cats_res = await self.session.execute(select(Category))
        cats = cats_res.scalars().all()

        real_to_temp_cat_id = {}
        temp_cats_pairs = []

        # Шаг 1: Создаем временные категории без parent_id, чтобы сгенерировать их ID
        for cat in cats:
            tc = TempCategory(
                original_id=cat.id, name=cat.name, parent_id=None, admin_id=admin_id
            )
            self.session.add(tc)
            temp_cats_pairs.append((cat, tc))

        await self.session.flush()

        # Шаг 2: Строим маппинг real_id -> temp_id
        for cat, tc in temp_cats_pairs:
            real_to_temp_cat_id[cat.id] = tc.id

        # Шаг 3: Проставляем правильные parent_id, указывающие на temp-записи
        for cat, tc in temp_cats_pairs:
            if cat.parent_id is not None:
                tc.parent_id = real_to_temp_cat_id.get(cat.parent_id)

        # Шаг 4: Копируем продукты с привязкой к temp_category_id
        prods_res = await self.session.execute(select(Product))
        for p in prods_res.scalars().all():
            self.session.add(TempProduct(
                original_id=p.id, name=p.name, description=p.description,
                price=p.price, unit=p.unit, image_id=p.image_id,
                category_id=real_to_temp_cat_id.get(p.category_id), admin_id=admin_id
            ))
        await self.session.commit()

    async def commit_changes(self, admin_id: int):
        # 1. Получаем все временные данные админа
        temp_cats = (
            await self.session.execute(select(TempCategory).where(TempCategory.admin_id == admin_id))).scalars().all()
        temp_prods = (
            await self.session.execute(select(TempProduct).where(TempProduct.admin_id == admin_id))).scalars().all()

        alive_cat_ids = [tc.original_id for tc in temp_cats if tc.original_id is not None]
        alive_prod_ids = [tp.original_id for tp in temp_prods if tp.original_id is not None]

        # 2. УДАЛЕНИЕ: Сначала продукты, затем категории (избегаем конфликтов Foreign Key)
        if alive_prod_ids:
            await self.session.execute(delete(Product).where(~Product.id.in_(alive_prod_ids)))
        else:
            await self.session.execute(delete(Product))

        if alive_cat_ids:
            await self.session.execute(delete(Category).where(~Category.id.in_(alive_cat_ids)))
        else:
            await self.session.execute(delete(Category))

        # 3. ПЕРЕНОС И ОБНОВЛЕНИЕ (Оптимизировано: без UPDATE в цикле)
        # Подгружаем выжившие боевые категории для прямого обновления объектов
        real_cats_res = await self.session.execute(select(Category).where(Category.id.in_(alive_cat_ids)))
        real_cats_dict = {c.id: c for c in real_cats_res.scalars().all()}

        temp_to_real_cat_id = {}
        new_cats_pairs = []

        # Обновляем существующие и готовим новые категории
        for tc in temp_cats:
            if tc.original_id is not None:
                temp_to_real_cat_id[tc.id] = tc.original_id
                real_cat = real_cats_dict.get(tc.original_id)
                if real_cat:
                    real_cat.name = tc.name
            else:
                new_cat = Category(name=tc.name, parent_id=None)
                self.session.add(new_cat)
                new_cats_pairs.append((tc, new_cat))

        if new_cats_pairs:
            await self.session.flush()
            for tc, new_cat in new_cats_pairs:
                temp_to_real_cat_id[tc.id] = new_cat.id

        # Выставляем корректные parent_id для всех боевых категорий
        for tc in temp_cats:
            real_cat_id = temp_to_real_cat_id[tc.id]
            real_cat = real_cats_dict.get(real_cat_id) or next(
                (pair[1] for pair in new_cats_pairs if pair[1].id == real_cat_id), None)
            if real_cat:
                real_cat.parent_id = temp_to_real_cat_id.get(tc.parent_id) if tc.parent_id is not None else None

        # Подгружаем выжившие боевые продукты для прямого обновления
        real_prods_res = await self.session.execute(select(Product).where(Product.id.in_(alive_prod_ids)))
        real_prods_dict = {p.id: p for p in real_prods_res.scalars().all()}

        # Синхронизируем продукты
        for tp in temp_prods:
            real_category_id = temp_to_real_cat_id.get(tp.category_id) if tp.category_id is not None else None
            if tp.original_id is not None:
                real_prod = real_prods_dict.get(tp.original_id)
                if real_prod:
                    real_prod.name = tp.name
                    real_prod.description = tp.description
                    real_prod.price = tp.price
                    real_prod.unit = tp.unit
                    real_prod.image_id = tp.image_id
                    real_prod.category_id = real_category_id
            else:
                self.session.add(Product(
                    name=tp.name, description=tp.description, price=tp.price,
                    unit=tp.unit, image_id=tp.image_id, category_id=real_category_id
                ))

        # 4. Очищаем временные таблицы админа
        await self.session.execute(delete(TempCategory).where(TempCategory.admin_id == admin_id))
        await self.session.execute(delete(TempProduct).where(TempProduct.admin_id == admin_id))

        await self.session.commit()

    # --- Чтение ---

    async def get_category_by_id(self, category_id: int, use_temp: bool = False,
                                 admin_id: int = None) -> Category | TempCategory | None:
        model = TempCategory if use_temp else Category
        query = select(model).where(model.id == category_id)
        if use_temp: query = query.where(model.admin_id == admin_id)
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
        if use_temp: data["admin_id"] = admin_id

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
        if use_temp: data["admin_id"] = admin_id

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