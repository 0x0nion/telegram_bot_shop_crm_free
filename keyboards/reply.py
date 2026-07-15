from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Клавиатура с кнопкой отправки гео
def get_address_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить мою геолокацию", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True # Скроется после одного использования
    )