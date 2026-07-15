# handlers/admin/categories.py
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.repositories.admin_repo import AdminRepository
from state.admin_states import AdminState
from .common import render_shop_menu

categories_router = Router()


@categories_router.callback_query(F.data == "admin_shop")
@categories_router.callback_query(F.data.startswith("admin_shop_"))
async def route_shop_level(callback: CallbackQuery, admin_repo: AdminRepository, state: FSMContext):
    # Сбрасываем состояние при перемещении по меню, чтобы не было утечек FSM
    await state.clear()

    data_parts = callback.data.split("_")
    current_cat_id = None

    if len(data_parts) > 2 and data_parts[2] != "root":
        current_cat_id = int(data_parts[2])

    await render_shop_menu(callback, admin_repo, current_cat_id)
    await callback.answer()


@categories_router.callback_query(F.data.startswith("admin_addcat_"))
async def route_add_category_start(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    parent_id = None

    if len(data_parts) > 2 and data_parts[2] != "root":
        parent_id = int(data_parts[2])

    await state.update_data(parent_id=parent_id, menu_message_id=callback.message.message_id)
    await state.set_state(AdminState.add_category)

    back_callback = f"admin_shop_{parent_id}" if parent_id else "admin_shop_root"

    builder = InlineKeyboardBuilder()
    builder.button(text='📥 Отмена', callback_data=back_callback, style='danger')

    await callback.message.edit_text(
        text="✍️ Введите **название** для новой категории:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@categories_router.message(AdminState.add_category, F.text)
async def process_add_category(message: Message, state: FSMContext, admin_repo: AdminRepository):
    category_name = message.text.strip()
    user_data = await state.get_data()
    parent_id = user_data.get("parent_id")
    menu_message_id = user_data.get("menu_message_id")

    await admin_repo.create_category(
        name=category_name,
        parent_id=parent_id,
        use_temp=True,
        admin_id=message.from_user.id
    )
    await state.clear()

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if menu_message_id:
        await render_shop_menu(message, admin_repo, parent_id, message_id_to_edit=menu_message_id)


@categories_router.callback_query(F.data.startswith("admin_del_cat_"))
async def route_delete_category(callback: CallbackQuery, admin_repo: AdminRepository):
    category_id_to_del = int(callback.data.split("_")[3])

    # Запрос категории идет из temp-таблицы с указанием admin_id,
    # чтобы не падало, если категория создана в этой сессии и еще не в основной БД
    target_category = await admin_repo.get_category_by_id(
        category_id=category_id_to_del,
        use_temp=True,
        admin_id=callback.from_user.id
    )
    parent_id = target_category.parent_id if target_category else None

    await admin_repo.delete_category(category_id_to_del, use_temp=True, admin_id=callback.from_user.id)
    await render_shop_menu(callback, admin_repo, parent_id)
    await callback.answer()