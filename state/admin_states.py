# state/admin_states.py (Примерный вид твоего файла состояний)
from aiogram.fsm.state import StatesGroup, State


class AdminState(StatesGroup):
    add_category = State()  # Это у тебя уже есть


class EditProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    unit = State()
    photo = State()