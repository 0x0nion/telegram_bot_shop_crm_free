# src/core/ui.py
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, BufferedInputFile


class UIManager:
    """
    Глобальный менеджер интерфейса (Single Message UI).
    Управляет отрисовкой экранов в рамках одного сообщения, исключая спам в чате.
    """

    @staticmethod
    async def show(
            event: Message | CallbackQuery,
            text: str,
            reply_markup: InlineKeyboardMarkup | None = None,
            parse_mode: str = "HTML",
            photo: str | BufferedInputFile | None = None,
            message_id_to_edit: int | None = None,
    ) -> Message:
        """
        Универсальный метод отрисовки интерфейса в одно сообщение.
        """
        bot: Bot = event.bot
        chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id

        msg_id = message_id_to_edit
        if not msg_id and isinstance(event, CallbackQuery):
            msg_id = event.message.message_id

        try:
            if photo:
                if msg_id:
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except TelegramBadRequest:
                        pass

                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )

            else:
                if msg_id:
                    try:
                        return await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=msg_id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode,
                        )
                    except TelegramBadRequest as e:
                        if "message is not modified" in str(e):
                            return event.message if isinstance(event, CallbackQuery) else event

                        try:
                            await bot.delete_message(chat_id, msg_id)
                        except TelegramBadRequest:
                            pass
                        return await bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode,
                        )
                else:
                    return await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode,
                    )

        finally:
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer()
                except TelegramBadRequest:
                    pass
