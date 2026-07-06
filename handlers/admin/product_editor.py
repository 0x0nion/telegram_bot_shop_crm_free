# handlers/admin/product_editor.py
import asyncio
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from database.repositories.admin_repo import AdminRepository
from state.admin_states import EditProduct

editor_router = Router()


def format_product_text(product) -> str:
    return (f"📦 <b>{product.name}</b>\n\n"
            f"📝 <i>{product.description or 'Описание отсутствует'}</i>\n\n"
            f"💰 <b>Цена:</b> {product.price} руб. / {product.unit or 'шт.'}")


async def self_destruct(message: Message, seconds: int = 3):
    """Безопасно удаляет сообщение с ошибкой через заданное время."""
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def show_product_card(chat_id: int, product_id: int, admin_repo: AdminRepository, bot: Bot,
                            old_message_id: int = None):
    """Универсальная функция для отрисовки карточки (из черновика)."""
    product = await admin_repo.get_product_by_id(product_id, use_temp=True, admin_id=chat_id)
    if not product:
        return

    text = format_product_text(product)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Название", callback_data=f"admin_edit_p_name_{product_id}"),
        InlineKeyboardButton(text="⚖️ Ед. изм.", callback_data=f"admin_edit_p_unit_{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Описание", callback_data=f"admin_edit_p_desc_{product_id}"),
        InlineKeyboardButton(text="💰 Цена", callback_data=f"admin_edit_p_price_{product_id}")
    )
    builder.row(InlineKeyboardButton(text="📸 Фото", callback_data=f"admin_edit_p_photo_{product_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_shop_{product.category_id or 'root'}"))

    if old_message_id:
        try:
            await bot.delete_message(chat_id, old_message_id)
        except TelegramBadRequest:
            pass

    if product.image_id:
        await bot.send_photo(chat_id, photo=product.image_id, caption=text, reply_markup=builder.as_markup(),
                             parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text=text, reply_markup=builder.as_markup(), parse_mode="HTML")


@editor_router.callback_query(F.data.startswith("admin_item_"))
async def route_product_card(callback: CallbackQuery, admin_repo: AdminRepository):
    product_id = int(callback.data.split("_")[2])
    await show_product_card(callback.message.chat.id, product_id, admin_repo, callback.bot, callback.message.message_id)
    await callback.answer()


@editor_router.callback_query(F.data.startswith("admin_edit_p_"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[3]
    product_id = int(callback.data.split("_")[4])

    prompts = {
        "name": "✍️ Введите новое название:",
        "desc": "✍️ Введите новое описание:",
        "price": "💰 Введите новую цену (число):",
        "unit": "⚖️ Введите ед. измерения (например: шт, кг):",
        "photo": "📸 Пришлите новую фотографию товара:"
    }

    state_mapping = {
        "name": EditProduct.name,
        "desc": EditProduct.description,
        "price": EditProduct.price,
        "unit": EditProduct.unit,
        "photo": EditProduct.photo
    }

    target_state = state_mapping.get(action)
    if not target_state:
        await callback.answer("Ошибка выбора поля", show_alert=True)
        return

    await state.set_state(target_state)
    prompt_text = prompts.get(action, "Введите данные:")

    # ИСПРАВЛЕНО: Карточка с фото не может быть отредактирована через edit_message_text.
    # Если у сообщения есть фото, удаляем его и отправляем чистый текст, обновляя message_id в FSM.
    if callback.message.photo:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        new_msg = await callback.message.answer(prompt_text, reply_markup=None)
        await state.update_data(product_id=product_id, message_id=new_msg.message_id)
    else:
        await state.update_data(product_id=product_id, message_id=callback.message.message_id)
        await callback.message.edit_text(prompt_text, reply_markup=None)

    await callback.answer()


@editor_router.message(EditProduct.name, F.text)
@editor_router.message(EditProduct.description, F.text)
@editor_router.message(EditProduct.unit, F.text)
@editor_router.message(EditProduct.price, F.text)
@editor_router.message(EditProduct.photo)
async def process_edit_input(message: Message, state: FSMContext, admin_repo: AdminRepository):
    data = await state.get_data()
    pid = data['product_id']
    old_msg_id = data.get('message_id')
    curr_state = await state.get_state()

    # Защита от удаления сообщения пользователя (например, в группах или при сбоях)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if "photo" in curr_state and not message.photo:
        err = await message.answer("❌ Пожалуйста, пришлите изображение.")
        asyncio.create_task(self_destruct(err))
        return

    if "price" in curr_state:
        clean_text = message.text.strip().replace(',', '.', 1)
        if not clean_text.replace('.', '', 1).isdigit():
            err = await message.answer("❌ Ошибка! Введите корректное число.")
            asyncio.create_task(self_destruct(err))
            return
        await admin_repo.update_product_field(pid, "price", float(clean_text), use_temp=True,
                                              admin_id=message.from_user.id)

    elif "photo" in curr_state:
        await admin_repo.update_product_field(pid, "image_id", message.photo[-1].file_id, use_temp=True,
                                              admin_id=message.from_user.id)
    else:
        # ИСПРАВЛЕНО: Строка состояния содержит "description", а не "desc".
        # Проверка "desc" in curr_state всегда была False, из-за чего описание записывалось в поле "unit".
        field = "name" if "name" in curr_state else "description" if "description" in curr_state else "unit"
        await admin_repo.update_product_field(pid, field, message.text.strip(), use_temp=True,
                                              admin_id=message.from_user.id)

    await state.clear()
    await show_product_card(message.chat.id, pid, admin_repo, message.bot, old_msg_id)