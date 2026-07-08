from aiomost import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
