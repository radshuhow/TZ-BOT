from aiogram import Router
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from typing import List

from keyboards import get_main_menu
from config_reader import config

common_router = Router()

class AdminFilter(BaseFilter):
    """
    Фильтр для проверки, что пользователь есть в списке разрешенных.
    """
    def __init__(self, allowed_users: List[int]):
        self.allowed_users = allowed_users

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.allowed_users

# Применяем фильтр ко всем хэндлерам в этом роутере,
# которые должны быть доступны только администраторам (баерам).
# Мы также можем применять его точечно к каждому хэндлеру.
# Здесь я применю его к /start.
@common_router.message(CommandStart(), AdminFilter(config.allowed_users))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    """
    await state.clear()
    await message.answer(
        "Здравствуйте! 👋\n\n"
        "Я бот для автоматизации постановки ТЗ на креативы. "
        "Выберите тип ТЗ, который хотите создать:",
        reply_markup=get_main_menu()
    )

@common_router.message(CommandStart())
async def cmd_start_restricted(message: Message):
    """
    Обработчик /start для пользователей, не входящих в список.
    """
    await message.answer("❌ У вас нет доступа к этому боту.")


@common_router.message(Command("cancel"))
@common_router.message(lambda msg: msg.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Обработчик отмены FSM-сценария.
    """
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Действие отменено. Вы возвращены в главное меню.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Вы и так в главном меню.",
            reply_markup=get_main_menu()
        )