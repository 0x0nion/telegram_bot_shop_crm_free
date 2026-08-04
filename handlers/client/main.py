from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models import User
from database.repositories.user_repo import UserRepository
from keyboards.inline import get_language_keyboard, InlineKb
from src.core.ui import UIManager

client_main_router = Router()


async def show_client_main_menu(
    event: Message | CallbackQuery,
    user_repo: UserRepository,
    user: User,
    message_id_to_edit: int | None = None,
) -> None:
    """
    Единая точка отображения главного меню пользователя
    с подтягиванием текста и фото приветствия из БД через user_repo.
    """
    lang = user.language if user and user.language else "ru"

    # Динамическая подгрузка текста и фото приветствия из БД
    text, photo_id = await user_repo.get_welcome_card(lang_code=lang)

    orders_count = len(user.orders) if user.orders else 0
    cart_count = len(user.cart) if user.cart else 0

    reply_markup = InlineKb(lang).get_main_kb(orders=orders_count, cart=cart_count)

    await UIManager.show(
        event=event,
        text=text,
        reply_markup=reply_markup,
        photo=photo_id,
        message_id_to_edit=message_id_to_edit,
    )


@client_main_router.message(CommandStart())
async def cmd_start(
    message: Message,
    user_repo: UserRepository,
    state: FSMContext,
    user: User,
) -> None:
    await state.clear()

    if user and user.language:
        await show_client_main_menu(event=message, user_repo=user_repo, user=user)
    else:
        if not user:
            await user_repo.create_user(user_id=message.from_user.id)

        await UIManager.show(
            event=message,
            text="👇 👇 👇 👇",
            reply_markup=get_language_keyboard(),
        )


@client_main_router.callback_query(F.data.startswith("client_main"))
async def open_main_menu(
    callback: CallbackQuery,
    user_repo: UserRepository,
    user: User,
) -> None:
    await callback.answer()
    await show_client_main_menu(
        event=callback,
        user_repo=user_repo,
        user=user,
        message_id_to_edit=callback.message.message_id,
    )


@client_main_router.callback_query(F.data.startswith("client_settings"))
async def open_settings(
    callback: CallbackQuery,
) -> None:
    await callback.answer()
    await UIManager.show(
        event=callback,
        text="👇 👇 👇 👇",
        reply_markup=get_language_keyboard(),
        message_id_to_edit=callback.message.message_id,
    )


@client_main_router.callback_query(F.data.startswith("lang_"))
async def select_language(
    callback: CallbackQuery,
    user_repo: UserRepository,
) -> None:
    await callback.answer()
    lang_code = callback.data.split("_")[-1]

    await user_repo.update_language(user_id=callback.from_user.id, language=lang_code)
    user = await user_repo.get_or_create_user(callback.from_user)

    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass

    await show_client_main_menu(
        event=callback,
        user_repo=user_repo,
        user=user,
        message_id_to_edit=None,
    )