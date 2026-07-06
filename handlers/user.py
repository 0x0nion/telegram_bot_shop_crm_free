# handlers/user.py
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
# ИЗМЕНЕНО: Импортируем из нового места
from database.repositories.user_repo import UserRepository
from keyboards.inline import get_language_keyboard

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, user_repo: UserRepository):
    user = await user_repo.get_user(message.from_user.id)

    if user and user.language:
        welcome_msg = (
            f"Привет, {message.from_user.full_name}! Рад видеть тебя снова."
            if user.language == "ru" else
            f"Hello, {message.from_user.full_name}! Glad to see you again."
        )
        await message.answer(welcome_msg)
    else:
        if not user:
            await user_repo.create_user(user_id=message.from_user.id, username=message.from_user.username)

        await message.answer(
            "Добро пожаловать! Пожалуйста, выберите язык:\n"
            "Welcome! Please select a language:",
            reply_markup=get_language_keyboard()
        )

    print(message.from_user.id)

@user_router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, user_repo: UserRepository):
    lang = callback.data.split("_")[1]
    await user_repo.update_language(callback.from_user.id, lang)

    welcome_text = "Вы успешно выбрали русский язык! Приветствуем." if lang == "ru" else "You have successfully selected English! Welcome."

    await callback.message.edit_text(welcome_text)
    await callback.answer()