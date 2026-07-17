import asyncio
import logging
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.repositories.admin_repo import AdminRepository
from keyboards.admin_inline import AdminInlineKb
from state.admin_states import EditProduct
from database.models.user import User

editor_router = Router()
logger = logging.getLogger(__name__)


async def self_destruct(message: Message, seconds: int = 3):
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def show_product_card(chat_id: int, product_id: int, admin_repo: AdminRepository, bot: Bot,
                            old_message_id: int = None, lang: str = "en"):
    product = await admin_repo.get_product_by_id(product_id, use_temp=True, admin_id=chat_id)
    if not product:
        return

    kb = AdminInlineKb(lang=lang)

    desc_val = product.description or kb.get_text("no_description", "Описание отсутствует")
    unit_val = product.unit or kb.get_text("default_unit", "шт.")

    text = kb.get_text("product_card_template",
                       "📦 <b>{name}</b>\n\n📝 <i>{description}</i>\n\n💰 <b>Цена:</b> {price} {unit}")
    formatted_text = text.format(name=product.name, description=desc_val, price=product.price, unit=unit_val)

    category_id = product.category_id if product.category_id else "root"
    reply_markup = kb.get_product_editor_kb(product_id=product_id, category_id=category_id)

    if old_message_id:
        try:
            await bot.delete_message(chat_id, old_message_id)
        except TelegramBadRequest:
            pass

    if product.image_id:
        await bot.send_photo(chat_id, photo=product.image_id, caption=formatted_text, reply_markup=reply_markup,
                             parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text=formatted_text, reply_markup=reply_markup, parse_mode="HTML")


@editor_router.callback_query(F.data.startswith("admin_item_"))
async def route_product_card(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    product_id = int(callback.data.split("_")[2])
    lang = user.language if user.language in ["ru", "en", "es"] else "en"

    await show_product_card(callback.message.chat.id, product_id, admin_repo, callback.bot, callback.message.message_id,
                            lang=lang)
    await callback.answer()


@editor_router.callback_query(F.data.startswith("admin_edit_p_"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext, user: User):
    action = callback.data.split("_")[3]
    product_id = int(callback.data.split("_")[4])
    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    state_mapping = {
        "name": EditProduct.name,
        "desc": EditProduct.description,
        "price": EditProduct.price,
        "unit": EditProduct.unit,
        "photo": EditProduct.photo
    }

    target_state = state_mapping.get(action)
    if not target_state:
        err_field_text = kb.get_text("errors.selection_field", "Ошибка выбора поля")
        await callback.answer(err_field_text, show_alert=True)
        return

    await state.set_state(target_state)

    prompt_text = kb.get_text(f"prompts.{action}") or kb.get_text("prompts.default", "Введите данные:")

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
async def process_edit_input(message: Message, state: FSMContext, admin_repo: AdminRepository, user: User):
    data = await state.get_data()
    pid = data['product_id']
    old_msg_id = data.get('message_id')
    curr_state = await state.get_state()

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if "photo" in curr_state and not message.photo:
        err_msg = kb.get_text("errors.not_photo", "❌ Пожалуйста, пришлите изображение.")
        err = await message.answer(err_msg)
        asyncio.create_task(self_destruct(err))
        return

    if "price" in curr_state:
        clean_text = message.text.strip().replace(',', '.', 1)
        if not clean_text.replace('.', '', 1).isdigit():
            err_msg = kb.get_text("errors.invalid_price", "❌ Ошибка! Введите корректное число.")
            err = await message.answer(err_msg)
            asyncio.create_task(self_destruct(err))
            return
        await admin_repo.update_product_field(pid, "price", float(clean_text), use_temp=True,
                                              admin_id=message.from_user.id)

    elif "photo" in curr_state:
        await admin_repo.update_product_field(pid, "image_id", message.photo[-1].file_id, use_temp=True,
                                              admin_id=message.from_user.id)
    else:
        field = "name" if "name" in curr_state else "description" if "description" in curr_state else "unit"
        await admin_repo.update_product_field(pid, field, message.text.strip(), use_temp=True,
                                              admin_id=message.from_user.id)

    await state.clear()
    await show_product_card(message.chat.id, pid, admin_repo, message.bot, old_msg_id, lang=lang)