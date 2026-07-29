# handlers/admin/shop/products.py
import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from filters.admin import IsAdminFilter
from handlers.admin.shop.render_shop_menu import render_shop_menu
from handlers.admin.utils import get_user_lang, parse_id
from keyboards.admin_inline import AdminInlineKb
from locales.units import DEFAULT_UNIT

products_router = Router()
products_router.message.filter(IsAdminFilter())
products_router.callback_query.filter(IsAdminFilter())

logger = logging.getLogger(__name__)


@products_router.callback_query(F.data.startswith("admin_add_item_"))
async def create_default_product(
    callback: CallbackQuery,
    admin_repo: AdminRepository,
    state: FSMContext,
    user: User,
):
    await state.clear()

    data_parts = callback.data.split("_")
    raw_id = data_parts[3] if len(data_parts) > 3 else "root"
    category_id = parse_id(raw_id)

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    default_name = kb.get_text("default_product_name", "Новый товар")
    default_desc = kb.get_text("default_product_desc", "Описание отсутствует")

    await admin_repo.create_product(
        name=default_name,
        description=default_desc,
        price=0.0,
        category_id=category_id,
        image_id=None,
        unit=DEFAULT_UNIT.value,
        use_temp=True,
        admin_id=callback.from_user.id,
    )

    await render_shop_menu(callback, admin_repo, category_id, user=user)

    alert_text = kb.get_text(
        "alerts.product_created", "✨ Заготовка товара создана!"
    )
    await callback.answer(alert_text)


@products_router.callback_query(F.data.startswith("admin_del_item_"))
async def route_delete_product(
    callback: CallbackQuery,
    admin_repo: AdminRepository,
    state: FSMContext,
    user: User,
):
    await state.clear()

    data_parts = callback.data.split("_")
    product_id_to_del = int(data_parts[3]) if len(data_parts) > 3 else 0

    product = await admin_repo.get_product_by_id(
        product_id=product_id_to_del,
        use_temp=True,
        admin_id=callback.from_user.id,
    )
    category_id = product.category_id if product else None

    await admin_repo.delete_product(
        product_id_to_del, use_temp=True, admin_id=callback.from_user.id
    )

    await render_shop_menu(callback, admin_repo, category_id, user=user)

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    alert_text = kb.get_text("alerts.product_deleted", "🗑 Товар удален")
    await callback.answer(alert_text)