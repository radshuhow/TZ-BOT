from aiogram.fsm.state import State, StatesGroup

class StandardTZ(StatesGroup):
    customer = State()
    geo = State()
    approach = State()
    app = State()
    language = State()
    reference = State()
    celebrity = State()
    format = State()
    slot = State()
    extras = State()
    scenario = State()

class UniqTZ(StatesGroup):
    customer = State()
    geo = State()
    app = State()
    creative_name = State()

class AdaptTZ(StatesGroup):
    customer = State()
    geo = State()
    new_app = State()
    creative_name = State()

class RewriteTZ(StatesGroup):
    customer = State()
    geo = State()
    language = State()
    creative_reference = State()
    additional = State()
    confirm_send = State()

class PwaTZ(StatesGroup):
    customer = State()
    format = State()
    brand = State()
    logos = State()
    slot = State()
    geo = State()
    extra_elements = State()
    offers = State()
    text = State()

class ConfirmSend(StatesGroup):
    preferred_creative = State()
    waiting = State()