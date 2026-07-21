# state/admin_states.py
from aiogram.fsm.state import StatesGroup, State


class AdminState(StatesGroup):
    add_category = State()
    edit_category_description = State()


class EditProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    unit = State()
    photo = State()