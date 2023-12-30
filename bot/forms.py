from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class RegistrationForm(StatesGroup):
    name = State()

class GetKilled(StatesGroup):
    player_id = State()
