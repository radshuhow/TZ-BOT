from aiogram import Router
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from typing import List

from keyboards import get_main_menu
from config_reader import config
from sent_tz_store import sent_tz_store

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


def _is_main_creator(message: Message) -> bool:
    creator_username = (config.creator_username or "").lstrip("@").lower()
    username = (message.from_user.username if message.from_user else "") or ""
    return bool(creator_username and username.lower() == creator_username)


@common_router.message(Command("tz"))
@common_router.message(Command("find_tz"))
async def find_tz(message: Message):
    """Return a previously sent TZ to the main creator by its ID."""
    if not _is_main_creator(message):
        await message.answer("❌ Эта команда доступна только главному креатору.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /tz <ID ТЗ>\nНапример: /tz 1a2b3c4d")
        return

    tz_id = parts[1].strip().lstrip("#")
    if not tz_id or any(char.isspace() for char in tz_id):
        await message.answer("Укажите корректный ID ТЗ, например: /tz 1a2b3c4d")
        return

    item = await sent_tz_store.get_by_id(tz_id)
    if not item:
        await message.answer(f"ТЗ #{tz_id} не найдено.")
        return

    from handlers.tz_form_handler import _build_send_text, _split_text_for_telegram, _strip_html_tags

    data = item.get("data", {})
    tz_text = f"🆔 <b>ID ТЗ: #{tz_id}</b>\n\n{_build_send_text(data)}"
    if len(tz_text) <= 4096:
        await message.answer(tz_text, parse_mode="HTML")
    else:
        for part in _split_text_for_telegram(_strip_html_tags(tz_text), max_len=4096):
            await message.answer(part)

    for media in data.get("media", []):
        caption = media.get("caption")
        if media.get("type") == "photo":
            await message.answer_photo(media["file_id"], caption=caption)
        elif media.get("type") == "video":
            await message.answer_video(media["file_id"], caption=caption)


@common_router.message(Command("cancel"))
@common_router.message(lambda msg: msg.text is not None and msg.text.lower() == "отмена")
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