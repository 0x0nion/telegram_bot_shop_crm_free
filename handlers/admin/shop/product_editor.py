# handlers/admin/shop/product_editor.py
import asyncio
import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from handlers.admin.utils import get_user_lang, self_destruct
from keyboards.admin_inline import AdminInlineKb
from locales.currencies import get_currency_symbol
from locales.units import get_unit_label
from src.core.ui import UIManager
from state.admin_states import EditProduct

editor_router = Router()
logger = logging.getLogger(__name__)


async def show_product_card(
        event: Message | CallbackQuery,
        product_id: int,
        admin_repo: AdminRepository,
        lang: str = "en",
        message_id_to_edit: int | None = None,
):
    """Единый метод отображения карточки товара с использованием UIManager."""
    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id

    product = await admin_repo.get_product_by_id(
        product_id, use_temp=True, admin_id=chat_id
    )
    if not product:
        return

    kb = AdminInlineKb(lang=lang)

    desc_val = product.description or kb.get_text(
        "no_description", "Описание отсутствует"
    )
    unit_val = get_unit_label(product.unit, lang=lang)
    currency_val = get_currency_symbol(getattr(product, "currency", None))

    text = kb.get_text(
        "product_card_template",
        "📦 <b>{name}</b>\n\n📝 <i>{description}</i>\n\n💰 <b>Цена:</b> {price} {currency} / {unit}",
    )
    formatted_text = text.format(
        name=product.name,
        description=desc_val,
        price=product.price,
        currency=currency_val,
        unit=unit_val,
    )

    category_id = product.category_id if product.category_id else "root"
    reply_markup = kb.get_product_editor_kb(
        product_id=product_id, category_id=category_id
    )

    await UIManager.show(
        event=event,
        text=formatted_text,
        reply_markup=reply_markup,
        photo=product.image_id,
        message_id_to_edit=message_id_to_edit,
    )


@editor_router.callback_query(F.data.startswith("admin_item_"))
async def route_product_card(
        callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    data_parts = callback.data.split("_")
    product_id = int(data_parts[2]) if len(data_parts) > 2 else 0
    lang = get_user_lang(user)

    await show_product_card(
        event=callback,
        product_id=product_id,
        admin_repo=admin_repo,
        lang=lang,
    )


@editor_router.callback_query(F.data.startswith("admin_edit_p_"))
async def start_edit_product(
        callback: CallbackQuery, state: FSMContext, user: User
):
    data_parts = callback.data.split("_")
    action = data_parts[3] if len(data_parts) > 3 else ""
    product_id = int(data_parts[4]) if len(data_parts) > 4 else 0

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    # Если выбрано редактирование единицы измерения
    if action == "unit":
        prompt_text = kb.get_text(
            "prompts.unit", "⚖️ Выберите единицу измерения:"
        )
        reply_markup = kb.get_unit_selection_kb(product_id=product_id)

        await UIManager.show(
            event=callback,
            text=prompt_text,
            reply_markup=reply_markup,
        )
        return

    state_mapping = {
        "name": EditProduct.name,
        "desc": EditProduct.description,
        "price": EditProduct.price,
        "photo": EditProduct.photo,
    }

    target_state = state_mapping.get(action)
    if not target_state:
        err_field_text = kb.get_text(
            "errors.selection_field", "Ошибка выбора поля"
        )
        await callback.answer(err_field_text, show_alert=True)
        return

    await state.set_state(target_state)

    prompt_text = kb.get_text(f"prompts.{action}") or kb.get_text(
        "prompts.default", "Введите данные:"
    )

    # Запоминаем ID текущего сообщения, чтобы в дальнейшем заменить его обратно на карточку
    await state.update_data(
        product_id=product_id, menu_message_id=callback.message.message_id
    )

    await UIManager.show(
        event=callback,
        text=prompt_text,
        reply_markup=None,
    )


@editor_router.callback_query(F.data.startswith("admin_set_unit_"))
async def set_product_unit(
        callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    """Обработчик выбора конкретной единицы измерения из инлайн-кнопок."""
    parts = callback.data.split("_")
    product_id = int(parts[3]) if len(parts) > 3 else 0
    unit_code = parts[4] if len(parts) > 4 else ""
    lang = get_user_lang(user)

    await admin_repo.update_product_field(
        product_id,
        "unit",
        unit_code,
        use_temp=True,
        admin_id=callback.from_user.id,
    )

    await show_product_card(
        event=callback,
        product_id=product_id,
        admin_repo=admin_repo,
        lang=lang,
    )


@editor_router.message(EditProduct.name, F.text)
@editor_router.message(EditProduct.description, F.text)
@editor_router.message(EditProduct.price, F.text)
@editor_router.message(EditProduct.photo)
async def process_edit_input(
        message: Message,
        state: FSMContext,
        admin_repo: AdminRepository,
        user: User,
):
    data = await state.get_data()
    pid = data.get("product_id")
    menu_message_id = data.get("menu_message_id")
    curr_state = await state.get_state()

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if "photo" in curr_state and not message.photo:
        err_msg = kb.get_text(
            "errors.not_photo", "❌ Пожалуйста, пришлите изображение."
        )
        err = await message.answer(err_msg)
        asyncio.create_task(self_destruct(err))
        return

    if "price" in curr_state:
        clean_text = message.text.strip().replace(",", ".", 1)
        if not clean_text.replace(".", "", 1).isdigit():
            err_msg = kb.get_text(
                "errors.invalid_price", "❌ Ошибка! Введите корректное число."
            )
            err = await message.answer(err_msg)
            asyncio.create_task(self_destruct(err))
            return
        await admin_repo.update_product_field(
            pid,
            "price",
            float(clean_text),
            use_temp=True,
            admin_id=message.from_user.id,
        )

    elif "photo" in curr_state:
        await admin_repo.update_product_field(
            pid,
            "image_id",
            message.photo[-1].file_id,
            use_temp=True,
            admin_id=message.from_user.id,
        )
    else:
        field = "name" if "name" in curr_state else "description"
        await admin_repo.update_product_field(
            pid,
            field,
            message.text.strip(),
            use_temp=True,
            admin_id=message.from_user.id,
        )

    await state.clear()

    # Возвращаем пользователя обратно в карточку товара в то же исходное сообщение
    if menu_message_id:
        await show_product_card(
            event=message,
            product_id=pid,
            admin_repo=admin_repo,
            lang=lang,
            message_id_to_edit=menu_message_id,
        )