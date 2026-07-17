import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database.repositories.admin_repo import AdminRepository
from filters.admin import IsAdminFilter
from keyboards.admin_inline import AdminInlineKb
from database.models.user import User
from .common import render_shop_menu

products_router = Router()
products_router.message.filter(IsAdminFilter())
products_router.callback_query.filter(IsAdminFilter())

logger = logging.getLogger(__name__)


@products_router.callback_query(F.data.startswith("admin_add_item_"))
async def create_default_product(callback: CallbackQuery, admin_repo: AdminRepository, state: FSMContext, user: User):
    await state.clear()

    data_parts = callback.data.split("_")
    category_id = int(data_parts[3]) if len(data_parts) > 3 and data_parts[3] != "root" else None

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    default_name = kb.get_text("default_product_name", "Новый товар")
    default_desc = kb.get_text("default_product_desc", "Описание отсутствует")
    default_unit = kb.get_text("default_unit", "шт.")

    await admin_repo.create_product(
        name=default_name,
        description=default_desc,
        price=0.0,
        category_id=category_id,
        image_id=None,
        unit=default_unit,
        use_temp=True,
        admin_id=callback.from_user.id
    )

    await render_shop_menu(callback, admin_repo, category_id, user=user)

    alert_text = kb.get_text("alerts.product_created", "✨ Заготовка товара создана!")
    await callback.answer(alert_text)


@products_router.callback_query(F.data.startswith("admin_del_item_"))
async def route_delete_product(callback: CallbackQuery, admin_repo: AdminRepository, state: FSMContext, user: User):
    await state.clear()

    product_id_to_del = int(callback.data.split("_")[3])

    product = await admin_repo.get_product_by_id(
        product_id=product_id_to_del,
        use_temp=True,
        admin_id=callback.from_user.id
    )
    category_id = product.category_id if product else None

    await admin_repo.delete_product(product_id_to_del, use_temp=True, admin_id=callback.from_user.id)

    await render_shop_menu(callback, admin_repo, category_id, user=user)

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    alert_text = kb.get_text("alerts.product_deleted", "🗑 Товар удален")
    await callback.answer(alert_text)