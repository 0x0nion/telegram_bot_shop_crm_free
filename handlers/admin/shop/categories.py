# handlers/admin/shop/categories.py
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from handlers.admin.shop.render_shop_menu import render_shop_menu
from handlers.admin.utils import get_user_lang, parse_id
from keyboards.admin_inline import AdminInlineKb
from src.core.ui import UIManager
from state.admin_states import AdminState

categories_router = Router()


@categories_router.callback_query(F.data == "admin_shop")
@categories_router.callback_query(
    F.data.startswith("admin_shop_")
    & ~F.data.startswith("admin_shop_settings")
    & ~F.data.startswith("admin_shop_start")
)
async def route_shop_level(
    callback: CallbackQuery,
    admin_repo: AdminRepository,
    state: FSMContext,
    user: User,
):
    await state.clear()

    data_parts = callback.data.split("_")
    raw_id = data_parts[2] if len(data_parts) > 2 else "root"
    current_cat_id = parse_id(raw_id)

    # Синхронизация здесь намеренно отсутствует:
    # сессия инициализируется строго один раз при входе через "Редактировать каталог".

    await render_shop_menu(callback, admin_repo, current_cat_id, user=user)
    await callback.answer()


@categories_router.callback_query(F.data.startswith("admin_addcat_"))
async def route_add_category_start(
    callback: CallbackQuery, state: FSMContext, user: User
):
    data_parts = callback.data.split("_")
    raw_id = data_parts[2] if len(data_parts) > 2 else "root"
    parent_id = parse_id(raw_id)

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    await state.update_data(
        parent_id=parent_id, menu_message_id=callback.message.message_id
    )
    await state.set_state(AdminState.add_category)

    back_callback = f"admin_shop_{raw_id}"

    text = kb.get_text(
        "enter_category_name", "✍️ Введите **название** для новой категории:"
    )
    reply_markup = kb.get_cancel_add_category_kb(back_callback=back_callback)

    await UIManager.show(
        event=callback,
        text=text,
        reply_markup=reply_markup,
    )


@categories_router.message(AdminState.add_category, F.text)
async def process_add_category(
    message: Message,
    state: FSMContext,
    admin_repo: AdminRepository,
    user: User,
):
    category_name = message.text.strip()
    user_data = await state.get_data()
    parent_id = user_data.get("parent_id")
    menu_message_id = user_data.get("menu_message_id")

    await admin_repo.create_category(
        name=category_name,
        parent_id=parent_id,
        use_temp=True,
        admin_id=message.from_user.id,
    )
    await state.clear()

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if menu_message_id:
        await render_shop_menu(
            message,
            admin_repo,
            parent_id,
            user=user,
            message_id_to_edit=menu_message_id,
        )


@categories_router.callback_query(F.data.startswith("admin_del_cat_"))
async def route_delete_category(
    callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    category_id_to_del = int(callback.data.split("_")[3])

    target_category = await admin_repo.get_category_by_id(
        category_id=category_id_to_del,
        use_temp=True,
        admin_id=callback.from_user.id,
    )
    parent_id = target_category.parent_id if target_category else None

    await admin_repo.delete_category(
        category_id_to_del, use_temp=True, admin_id=callback.from_user.id
    )
    await render_shop_menu(callback, admin_repo, parent_id, user=user)
    await callback.answer()


@categories_router.callback_query(F.data.startswith("admin_add_tittle_"))
async def start_edit_category_description(
    callback: CallbackQuery, state: FSMContext, user: User
):
    data_parts = callback.data.split("_")
    raw_id = data_parts[3] if len(data_parts) > 3 else "root"
    category_id = parse_id(raw_id)

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    await state.update_data(
        category_id=category_id, menu_message_id=callback.message.message_id
    )
    await state.set_state(AdminState.edit_category_description)

    prompt_text = kb.get_text("prompts.category_desc", "✍️ Введите описание:")
    back_callback = f"admin_shop_{raw_id}"

    await UIManager.show(
        event=callback,
        text=prompt_text,
        reply_markup=kb.get_cancel_add_category_kb(back_callback=back_callback),
    )


@categories_router.message(
    AdminState.edit_category_description, F.text
)
async def process_edit_category_description(
    message: Message,
    state: FSMContext,
    admin_repo: AdminRepository,
    user: User,
):
    desc_text = message.text.strip()
    user_data = await state.get_data()
    category_id = user_data.get("category_id")
    menu_message_id = user_data.get("menu_message_id")

    target_entity_id = category_id if category_id is not None else 0

    await admin_repo.update_temp_locale_for_all_languages(
        entity_id=target_entity_id,
        entity_type="category_description",
        text=desc_text,
        admin_id=message.from_user.id,
    )

    await state.clear()

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if menu_message_id:
        await render_shop_menu(
            message,
            admin_repo,
            category_id,
            user=user,
            message_id_to_edit=menu_message_id,
        )


@categories_router.callback_query(F.data.startswith("admin_del_tittle_"))
async def route_delete_category_description(
    callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    data_parts = callback.data.split("_")
    raw_id = data_parts[3] if len(data_parts) > 3 else "root"
    category_id = parse_id(raw_id)

    target_entity_id = category_id if category_id is not None else 0

    await admin_repo.delete_temp_locale_for_all_languages(
        entity_id=target_entity_id,
        entity_type="category_description",
        admin_id=callback.from_user.id,
    )

    await render_shop_menu(callback, admin_repo, category_id, user=user)
    await callback.answer()