from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Возвращает главную клавиатуру с выбором типа ТЗ.
    """
    buttons = [
        [KeyboardButton(text="Обычное ТЗ"), KeyboardButton(text="Уник")],
        [KeyboardButton(text="Адапт"), KeyboardButton(text="Рерайт")],
        [KeyboardButton(text="ДИЗАЙН КАРТИНОК PWA")],
        [KeyboardButton(text="Изменить отправленное ТЗ")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите тип ТЗ для создания"
    )

def get_cancel_kb() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для отмены FSM-сценария.
    """
    buttons = [
        [KeyboardButton(text="Отмена")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def get_confirm_inline_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_nav_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Назад"), KeyboardButton(text="Редактировать ТЗ")],
        [KeyboardButton(text="Отмена")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def get_edit_steps_kb(flow: str) -> InlineKeyboardMarkup:
    mapping = {
        "standard": [
            ("Заказчик", "customer"),
            ("Гео", "geo"),
            ("Подход", "approach"),
            ("Прила", "app"),
            ("Язык", "language"),
            ("Референс", "reference"),
            ("Селеба", "celebrity"),
            ("Формат крео", "format"),
            ("Слот(-ы)", "slot"),
            ("Вводные/Футажи/Доп.", "extras"),
            ("Сценарий", "scenario"),
        ],
        "uniq": [
            ("Заказчик", "customer"),
            ("Гео", "geo"),
            ("Прила", "app"),
            ("Название крео", "creative_name"),
        ],
        "adapt": [
            ("Заказчик", "customer"),
            ("Гео", "geo"),
            ("Новая прила", "new_app"),
            ("Креатив", "creative_name"),
        ],
        "rewrite": [
            ("Заказчик", "customer"),
            ("Гео", "geo"),
            ("Язык", "language"),
            ("Креатив(реф)", "creative_reference"),
            ("Дополнительно", "additional"),
        ],
        "pwa": [
            ("Заказчик", "customer"),
            ("Формат", "format"),
            ("Бренд", "brand"),
            ("Логотипы", "logos"),
            ("Слот", "slot"),
            ("Гео", "geo"),
            ("Доп. элементы", "extra_elements"),
            ("Предложения", "offers"),
            ("Текст", "text"),
        ],
    }
    items = mapping.get(flow, [])
    rows = []
    row = []
    for title, key in items:
        row.append(InlineKeyboardButton(text=title, callback_data=f"edit:{flow}:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_next_step_inline_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➡️ Следующий этап", callback_data="next_step")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skip_preferred_creative_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➡️ Следующий этап", callback_data="skip_preferred_creative")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_edit_media_kb(flow: str, step_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🗑 Удалить медиа этого этапа", callback_data=f"delete_media:{flow}:{step_key}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_after_delete_media_kb(flow: str, step_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📤 Загрузить новое медиа", callback_data=f"reupload_media_hint:{flow}:{step_key}")],
        [InlineKeyboardButton(text="👀 К предпросмотру ТЗ", callback_data="back_to_preview")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)