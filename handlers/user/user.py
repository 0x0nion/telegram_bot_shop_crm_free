# handlers/user.py
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.repositories.user_repo import UserRepository
from keyboards.inline import get_language_keyboard, InlineKb
from locales.locales import Locale

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, user_repo: UserRepository, state: FSMContext):
    await state.clear()
    user = await user_repo.get_user(message.from_user.id)
    if user and user.language:
        await message.answer(
            text=Locale(user.language).get_text('user_main'),
            reply_markup=InlineKb(user.language).get_kb('user_main_menu')
        )
    else:
        if not user:
            await user_repo.create_user(user_id=message.from_user.id)
        await message.answer(
            text="👇 👇 👇 👇",
            reply_markup=get_language_keyboard()
        )


@user_router.callback_query(F.data.startswith("client_main"))
async def open_main_menu(callback: CallbackQuery, user_repo: UserRepository):
    await callback.answer()
    user = await user_repo.get_user(callback.from_user.id)
    await callback.message.edit_text(
        text=Locale(user.language).get_text('user_main'),
        reply_markup=InlineKb(user.language).get_kb('user_main_menu')
    )


@user_router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, user_repo: UserRepository):
    await callback.answer()
    await user_repo.update_language(user_id=callback.from_user.id, language=callback.data.split('_')[-1])
    user = await user_repo.get_user(callback.from_user.id)
    await callback.message.edit_text(
        text=Locale(user.language).get_text('user_main'),
        reply_markup=InlineKb(user.language).get_kb('user_main_menu')
    )
