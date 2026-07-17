# state/admin_states.py
from aiogram.fsm.state import StatesGroup, State


class AdminState(StatesGroup):
    add_category = State()


class EditProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    unit = State()
    photo = State()