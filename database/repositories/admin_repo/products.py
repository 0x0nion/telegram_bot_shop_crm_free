from sqlalchemy import select, delete

from database.models import LocaleText
from database.models.product import Product
from database.models.temp_models import TempProduct, TempLocaleText
from locales.units import DEFAULT_UNIT
from utils.logger import logger


class AdminProductsMixin:

    async def get_product_by_id(self, product_id: int, use_temp: bool = False,
                                admin_id: int = None) -> Product | TempProduct | None:
        model = TempProduct if use_temp else Product
        query = select(model).where(model.id == product_id)
        if use_temp:
            query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_products_by_category(self, category_id: int | None, use_temp: bool = False,
                                       admin_id: int = None) -> list:
        model = TempProduct if use_temp else Product
        query = select(model).where(model.category_id == category_id)
        if use_temp:
            query = query.where(model.admin_id == admin_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_product(
            self,
            name: str,
            description: str,
            price: float,
            category_id: int | None,
            image_id: str | None = None,
            unit: str = DEFAULT_UNIT.value,
            use_temp: bool = False,
            admin_id: int = None
    ) -> Product | TempProduct:
        logger.info(f"Creating product '{name}' (category_id={category_id}, use_temp={use_temp}, admin_id={admin_id})")
        model = TempProduct if use_temp else Product
        data = {
            "name": name,
            "description": description,
            "price": price,
            "category_id": category_id,
            "image_id": image_id,
            "unit": unit
        }
        if use_temp:
            data["admin_id"] = admin_id

        new_item = model(**data)
        self.session.add(new_item)
        await self.session.commit()
        return new_item

    async def delete_product(self, product_id: int, use_temp: bool = False, admin_id: int = None):
        logger.info(f"Deleting product id={product_id} (use_temp={use_temp}, admin_id={admin_id})")
        if use_temp:
            await self.session.execute(
                delete(TempProduct).where(TempProduct.id == product_id, TempProduct.admin_id == admin_id)
            )
            await self.session.execute(
                delete(TempLocaleText).where(
                    TempLocaleText.entity_id == product_id,
                    TempLocaleText.entity_type.like('%product%'),
                    TempLocaleText.admin_id == admin_id
                )
            )
        else:
            await self.session.execute(delete(Product).where(Product.id == product_id))
            await self.session.execute(
                delete(LocaleText).where(
                    LocaleText.entity_id == product_id,
                    LocaleText.entity_type.like('%product%')
                )
            )
        await self.session.commit()

    async def update_product_field(self, product_id: int, field: str, value: any, use_temp: bool = False,
                                   admin_id: int = None):
        logger.debug(f"Updating product id={product_id} field '{field}' to '{value}' (use_temp={use_temp}, admin_id={admin_id})")
        model = TempProduct if use_temp else Product
        query = select(model).where(model.id == product_id)
        if use_temp:
            query = query.where(model.admin_id == admin_id)

        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        if item:
            setattr(item, field, value)
            await self.session.commit()