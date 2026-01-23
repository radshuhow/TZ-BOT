from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo

from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hcode, hbold, hitalic
import logging
from html import escape as html_escape
from typing import List

from states import StandardTZ, UniqTZ, AdaptTZ, RewriteTZ, PwaTZ, ConfirmSend
from keyboards import get_cancel_kb, get_main_menu, get_confirm_inline_kb, get_nav_kb, get_edit_steps_kb, get_next_step_inline_kb, get_edit_media_kb, get_after_delete_media_kb, get_skip_preferred_creative_kb

from config_reader import config
from handlers.common import AdminFilter # Импортируем фильтр

# Создаем роутер для FSM
tz_router = Router()

# -----------------------------------------------------------------------
# Вспомогательные функции для форматирования ТЗ
# -----------------------------------------------------------------------

def _safe_html_value(value) -> str:
    if value is None:
        return ""
    return html_escape(str(value))

def _strip_html_tags(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("<b>", "")
        .replace("</b>", "")
        .replace("<i>", "")
        .replace("</i>", "")
        .replace("<code>", "")
        .replace("</code>", "")
    )

def _split_text_for_telegram(text: str, max_len: int = 4096) -> List[str]:
    if not text:
        return [""]
    if len(text) <= max_len:
        return [text]

    parts: List[str] = []
    remaining = text
    while remaining:
        chunk = remaining[:max_len]
        cut = chunk.rfind("\n")
        if cut <= 0:
            cut = max_len
        parts.append(remaining[:cut])
        remaining = remaining[cut:]
        if remaining.startswith("\n"):
            remaining = remaining[1:]
    return parts

def _format_standard_tz(data: dict) -> str:
    return (
        f"📝 {hbold('НОВОЕ ТЗ (Обычное)')}\n\n"
        f"👤 {hbold('Заказчик:')} {_safe_html_value(data.get('customer'))}\n"
        f"🎨 {hbold('Предпочитаемый креативщик:')} {_safe_html_value(data.get('preferred_creative'))}\n"
        f"🌍 {hbold('Гео:')} {_safe_html_value(data.get('geo'))}\n"
        f"🎯 {hbold('Подход:')} {_safe_html_value(data.get('approach'))}\n"
        f"📱 {hbold('Прила:')} {_safe_html_value(data.get('app'))}\n"
        f"🗣️ {hbold('Язык:')} {_safe_html_value(data.get('language'))}\n"
        f"🔗 {hbold('Референс/исходник:')} {_safe_html_value(data.get('reference'))}\n"
        f"⭐ {hbold('Селеба:')} {_safe_html_value(data.get('celebrity'))}\n"
        f"📐 {hbold('Формат крео:')} {_safe_html_value(data.get('format'))}\n"
        f"🎰 {hbold('Слот(-ы):')} {_safe_html_value(data.get('slot'))}\n"
        f"💡 {hbold('Футажи/Дополнительно:')} {_safe_html_value(data.get('extras'))}\n\n"
        f"🧾 {hbold('Сценарий (Текст):')}\n{_safe_html_value(data.get('scenario'))}"
    )

def _format_uniq_tz(data: dict) -> str:
    return (
        f"📝 {hbold('НОВОЕ ТЗ (Уник)')}\n\n"
        f"👤 {hbold('Заказчик:')} {_safe_html_value(data.get('customer'))}\n"
        f"🎨 {hbold('Предпочитаемый креативщик:')} {_safe_html_value(data.get('preferred_creative'))}\n"
        f"🌍 {hbold('Гео:')} {_safe_html_value(data.get('geo'))}\n"
        f"📱 {hbold('Прила (если заменить):')} {_safe_html_value(data.get('app'))}\n"
        f"🎬 {hbold('Название креатива:')} {_safe_html_value(data.get('creative_name'))}"
    )

def _format_adapt_tz(data: dict) -> str:
    return (
        f"📝 {hbold('НОВОЕ ТЗ (Адапт)')}\n\n"
        f"👤 {hbold('Заказчик:')} {_safe_html_value(data.get('customer'))}\n"
        f"🎨 {hbold('Предпочитаемый креативщик:')} {_safe_html_value(data.get('preferred_creative'))}\n"
        f"🌍 {hbold('Гео:')} {_safe_html_value(data.get('geo'))}\n"
        f"📱 {hbold('Новая прила:')} {_safe_html_value(data.get('new_app'))}\n"
        f"🎬 {hbold('Креатив:')} {_safe_html_value(data.get('creative_name'))}"
    )

def _format_rewrite_tz(data: dict) -> str:
    return (
        f"📝 {hbold('НОВОЕ ТЗ (Рерайт)')}\n\n"
        f"👤 {hbold('Заказчик:')} {_safe_html_value(data.get('customer'))}\n"
        f"🎨 {hbold('Предпочитаемый креативщик:')} {_safe_html_value(data.get('preferred_creative'))}\n"
        f"🌍 {hbold('Гео:')} {_safe_html_value(data.get('geo'))}\n"
        f"🗣️ {hbold('Язык:')} {_safe_html_value(data.get('language'))}\n"
        f"🎬 {hbold('Креатив (референс):')} {_safe_html_value(data.get('creative_reference'))}\n"
        f"💡 {hbold('Дополнительно:')} {_safe_html_value(data.get('additional'))}"
    )

def _format_pwa_tz(data: dict) -> str:
    return (
        f"📝 {hbold('НОВОЕ ТЗ (PWA/Прилка)')} \n\n"
        f"👤 {hbold('Заказчик:')} {_safe_html_value(data.get('customer'))}\n"
        f"🎨 {hbold('Предпочитаемый креативщик:')} {_safe_html_value(data.get('preferred_creative'))}\n"
        f"📐 {hbold('Формат:')} {_safe_html_value(data.get('format'))}\n"
        f"🏷️ {hbold('Бренд Казино:')} {_safe_html_value(data.get('brand'))}\n"
        f"🧩 {hbold('Лого брендов:')} {_safe_html_value(data.get('logos'))}\n"
        f"🎰 {hbold('Слот:')} {_safe_html_value(data.get('slot'))}\n"
        f"🌍 {hbold('Гео:')} {_safe_html_value(data.get('geo'))}\n"
        f"✨ {hbold('Доп. элементы:')} {_safe_html_value(data.get('extra_elements'))}\n"
        f"🎁 {hbold('Спец. предложения:')} {_safe_html_value(data.get('offers'))}\n"
        f"📝 {hbold('Текст на картинке:')} {_safe_html_value(data.get('text'))}"
    )

def _build_send_text(data: dict) -> str:
    flow = data.get("flow")
    if flow == "standard":
        return _format_standard_tz(data)
    if flow == "uniq":
        return _format_uniq_tz(data)
    if flow == "adapt":
        return _format_adapt_tz(data)
    if flow == "rewrite":
        return _format_rewrite_tz(data)
    if flow == "pwa":
        return _format_pwa_tz(data)
    return ""

def _build_preview_text(data: dict) -> str:
    base = _build_send_text(data)
    footer = f"\n\n⚠️ {hitalic('Проверьте, всё ли указано точно, перед отправкой ТЗ. Если нужно — нажмите «Редактировать ТЗ».')}"
    return base + footer

async def _show_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    tz_text = _build_preview_text(data)

    await state.update_data(preview=tz_text)
    await state.set_state(ConfirmSend.waiting)
    await message.answer("Предпросмотр ТЗ. Проверьте и подтвердите отправку:", parse_mode="HTML")
    try:
        if len(tz_text) <= 4096:
            await message.answer(tz_text, parse_mode="HTML", reply_markup=get_confirm_inline_kb())
        else:
            plain = _strip_html_tags(tz_text)
            parts = _split_text_for_telegram(plain, max_len=4096)
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await message.answer(part, reply_markup=get_confirm_inline_kb())
                else:
                    await message.answer(part)
    except Exception as e:
        logging.exception(f"Failed to send TZ preview with HTML, falling back to plain text: {e}")
        plain = _strip_html_tags(tz_text)
        parts = _split_text_for_telegram(plain, max_len=4096)
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await message.answer(part, reply_markup=get_confirm_inline_kb())
            else:
                await message.answer(part)
    media = data.get("media", [])
    if media:
        by_step = {}
        for m in media:
            step = m.get("step") or "unknown"
            by_step.setdefault(step, []).append(m)
        for step, items in by_step.items():
            label = None
            flow = data.get("flow")
            if flow and flow in FLOW_LABELS and step in FLOW_LABELS[flow]:
                label = FLOW_LABELS[flow][step]
            header = f"Медиа для этапа: {label or step}"
            await message.answer(header)
            group = []
            for m in items:
                if m.get("type") == "photo":
                    group.append(InputMediaPhoto(media=m["file_id"], caption=m.get("caption")))
                elif m.get("type") == "video":
                    group.append(InputMediaVideo(media=m["file_id"], caption=m.get("caption")))
            if group:
                if len(group) == 1:
                    item = group[0]
                    if isinstance(item, InputMediaPhoto):
                        await message.answer_photo(item.media, caption=item.caption)
                    else:
                        await message.answer_video(item.media, caption=item.caption)
                else:
                    await message.answer_media_group(media=group)

# -----------------------------------------------------------------------
# Навигация по шагам: порядок, лейблы и соответствие состояниям
# -----------------------------------------------------------------------

FLOW_ORDERS = {
    "standard": [
        "customer", "geo", "approach", "app", "language", "reference",
        "celebrity", "format", "slot", "extras", "scenario",
    ],
    "uniq": ["customer", "geo", "app", "creative_name"],
    "adapt": ["customer", "geo", "new_app", "creative_name"],
    "rewrite": ["customer", "geo", "language", "creative_reference", "additional"],
    "pwa": [
        "customer", "format", "brand", "logos", "slot", "geo",
        "extra_elements", "offers", "text",
    ],
}

FLOW_LABELS = {
    "standard": {
        "customer": "Заказчик",
        "geo": "Гео",
        "approach": "Подход",
        "app": "Прила",
        "language": "Язык",
        "reference": "Референс",
        "celebrity": "Селеба",
        "format": "Формат крео",
        "slot": "Слот(-ы)",
        "extras": "Футажи/Дополнительно",
        "scenario": "Сценарий",
    },
    "uniq": {
        "customer": "Заказчик",
        "geo": "Гео",
        "app": "Прила",
        "creative_name": "Название крео",
    },
    "adapt": {
        "customer": "Заказчик",
        "geo": "Гео",
        "new_app": "Новая прила",
        "creative_name": "Креатив",
    },
    "rewrite": {
        "customer": "Заказчик",
        "geo": "Гео",
        "language": "Язык",
        "creative_reference": "Креатив(реф)",
        "additional": "Дополнительно",
    },
    "pwa": {
        "customer": "Заказчик",
        "format": "Формат",
        "brand": "Бренд",
        "logos": "Логотипы",
        "slot": "Слот",
        "geo": "Гео",
        "extra_elements": "Доп. элементы",
        "offers": "Предложения",
        "text": "Текст",
    },
}

FLOW_STATES = {
    "standard": {
        "customer": StandardTZ.customer,
        "geo": StandardTZ.geo,
        "approach": StandardTZ.approach,
        "app": StandardTZ.app,
        "language": StandardTZ.language,
        "reference": StandardTZ.reference,
        "celebrity": StandardTZ.celebrity,
        "format": StandardTZ.format,
        "slot": StandardTZ.slot,
        "extras": StandardTZ.extras,
        "scenario": StandardTZ.scenario,
    },
    "uniq": {
        "customer": UniqTZ.customer,
        "geo": UniqTZ.geo,
        "app": UniqTZ.app,
        "creative_name": UniqTZ.creative_name,
    },
    "adapt": {
        "customer": AdaptTZ.customer,
        "geo": AdaptTZ.geo,
        "new_app": AdaptTZ.new_app,
        "creative_name": AdaptTZ.creative_name,
    },
    "rewrite": {
        "customer": RewriteTZ.customer,
        "geo": RewriteTZ.geo,
        "language": RewriteTZ.language,
        "creative_reference": RewriteTZ.creative_reference,
        "additional": RewriteTZ.additional,
    },
    "pwa": {
        "customer": PwaTZ.customer,
        "format": PwaTZ.format,
        "brand": PwaTZ.brand,
        "logos": PwaTZ.logos,
        "slot": PwaTZ.slot,
        "geo": PwaTZ.geo,
        "extra_elements": PwaTZ.extra_elements,
        "offers": PwaTZ.offers,
        "text": PwaTZ.text,
    },
}

GROUP_TO_FLOW = {
    "StandardTZ": "standard",
    "UniqTZ": "uniq",
    "AdaptTZ": "adapt",
    "RewriteTZ": "rewrite",
    "PwaTZ": "pwa",
    "ConfirmSend": "confirm",
}

@tz_router.message(F.text == "Назад", AdminFilter(config.allowed_users))
async def on_back(message: Message, state: FSMContext):
    current = await state.get_state()
    data = await state.get_data()
    flow = data.get("flow")
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    if not flow:
        await message.answer("Вы в главном меню.", reply_markup=get_main_menu())
        return
    prev_key = None
    if not current:
        await message.answer("Вы в главном меню.", reply_markup=get_main_menu())
        return
    try:
        group, name = current.split(":", 1)
    except ValueError:
        group, name = current, ""
    if group == "ConfirmSend":
        steps = FLOW_ORDERS.get(flow, [])
        if steps:
            prev_key = steps[-1]
    else:
        steps = FLOW_ORDERS.get(flow, [])
        if name in steps:
            idx = steps.index(name)
            if idx > 0:
                prev_key = steps[idx - 1]
    if not prev_key:
        await message.answer("Это первый этап. Назад недоступно.", reply_markup=get_nav_kb())
        return
    await state.set_state(FLOW_STATES[flow][prev_key])
    cur_val = data.get(prev_key, "—")
    label = FLOW_LABELS[flow][prev_key]
    await message.answer(f"{label}. Текущее значение: {cur_val}\nВведите новое значение:", reply_markup=get_nav_kb())

@tz_router.message(F.text == "Редактировать ТЗ", AdminFilter(config.allowed_users))
async def on_edit_any_step(message: Message, state: FSMContext):
    data = await state.get_data()
    flow = data.get("flow")
    if not flow:
        await message.answer("Сначала начните создание ТЗ.", reply_markup=get_main_menu())
        return
    await message.answer("Выберите этап для редактирования:", reply_markup=get_edit_steps_kb(flow))

@tz_router.callback_query(F.data.startswith("edit:"), AdminFilter(config.allowed_users))
async def on_edit_select(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Некорректный выбор")
        return
    _, flow, key = parts
    if flow not in FLOW_STATES or key not in FLOW_STATES[flow]:
        await callback.answer("Шаг недоступен")
        return
    await state.set_state(FLOW_STATES[flow][key])
    data = await state.get_data()
    await state.update_data(flow=flow, editing=True)
    cur_val = data.get(key, "—")
    label = FLOW_LABELS[flow][key]
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        media = data.get("media", [])
        step_media = [m for m in media if m.get("step") == key]
        if step_media:
            header = f"Медиа для этапа: {label}"
            await callback.message.answer(header)
            group = []
            for m in step_media:
                if m.get("type") == "photo":
                    group.append(InputMediaPhoto(media=m["file_id"], caption=m.get("caption")))
                elif m.get("type") == "video":
                    group.append(InputMediaVideo(media=m["file_id"], caption=m.get("caption")))
            if group:
                if len(group) == 1:
                    item = group[0]
                    if isinstance(item, InputMediaPhoto):
                        await callback.message.answer_photo(item.media, caption=item.caption)
                    else:
                        await callback.message.answer_video(item.media, caption=item.caption)
                else:
                    await callback.message.answer_media_group(media=group)
            await callback.message.answer(
                f"Редактируем: {label}.\nТекущее значение: {cur_val}\nВведите новое значение:",
                reply_markup=get_edit_media_kb(flow, key),
            )
        else:
            await callback.message.answer(
                f"Редактируем: {label}.\nТекущее значение: {cur_val}\nВведите новое значение:",
                reply_markup=get_nav_kb(),
            )
    await callback.answer("Выберите новое значение")

@tz_router.callback_query(F.data.startswith("delete_media:"), AdminFilter(config.allowed_users))
async def on_delete_media(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Некорректный запрос")
        return
    _, flow, key = parts
    data = await state.get_data()
    media = data.get("media", [])
    if not media:
        await callback.answer("Медиа не найдены")
        return
    filtered = [m for m in media if m.get("step") != key]
    await state.update_data(media=filtered)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        label = FLOW_LABELS.get(flow, {}).get(key, key)
        text = (
            f"Медиа для этапа '{label}' удалены.\n\n"
            f"{hbold('Загрузить новую картинку или видео для этого этапа?')}\n"
            f"{hitalic('Или нажмите кнопку ниже, чтобы вернуться к предпросмотру финальной версии ТЗ.') }"
        )
        await callback.message.answer(text, reply_markup=get_after_delete_media_kb(flow, key), parse_mode="HTML")
    await callback.answer("Удалено")

@tz_router.callback_query(F.data.startswith("reupload_media_hint:"), AdminFilter(config.allowed_users))
async def on_reupload_media_hint(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Некорректный запрос")
        return
    _, flow, key = parts
    data = await state.get_data()
    label = FLOW_LABELS.get(flow, {}).get(key, key)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        text = (
            f"{hbold('Загрузите новое медиа для этого этапа.')}\n\n"
            f"Этап: {label}. Просто отправьте фото или видео сообщением — бот автоматически привяжет его к этому этапу."
        )
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer("Ожидаю медиа")

@tz_router.callback_query(F.data == "back_to_preview", AdminFilter(config.allowed_users))
async def on_back_to_preview_after_delete(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing=False)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.error(f"Error editing reply markup: {e}")
        await _show_preview(callback.message, state)
    await callback.answer("Предпросмотр ТЗ")

@tz_router.message((F.photo | F.video), AdminFilter(config.allowed_users))
async def on_media(message: Message, state: FSMContext):
    data = await state.get_data()
    flow = data.get("flow")
    if not flow:
        return

    current = await state.get_state()
    if not current:
        return
    try:
        group, name = current.split(":", 1)
    except ValueError:
        group, name = current, ""
    if flow not in FLOW_STATES:
        return

    media_list = data.get("media", [])

    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
        media_list.append({
            "type": "photo",
            "file_id": file_id,
            "caption": message.caption,
            "step": name,
        })
    elif message.video:
        file_id = message.video.file_id
        media_list.append({
            "type": "video",
            "file_id": file_id,
            "caption": message.caption,
            "step": name,
        })
    if not file_id:
        return

    await state.update_data(media=media_list)

    # Если редактируем существующее ТЗ, после сохранения медиа
    # сразу показываем обновлённый предпросмотр.
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return

    step_label = None
    flow = data.get("flow")
    if flow and flow in FLOW_LABELS and name in FLOW_LABELS[flow]:
        step_label = FLOW_LABELS[flow][name]
    text = "Вложение сохранено. Оно будет приложено к финальному ТЗ."
    if step_label:
        text += f"\nЭтап: {step_label}. Если к этому этапу больше нечего добавить — переходи к следующему." 
    await message.answer(text, reply_markup=get_next_step_inline_kb())

@tz_router.callback_query(F.data == "next_step", AdminFilter(config.allowed_users))
async def on_next_step(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    data = await state.get_data()
    flow = data.get("flow")
    if not flow or not current:
        await callback.answer("Нет активного ТЗ")
        return
    try:
        group, name = current.split(":", 1)
    except ValueError:
        group, name = current, ""
    steps = FLOW_ORDERS.get(flow, [])
    if name not in steps:
        await callback.answer("Следующий этап не найден")
        return
    idx = steps.index(name)
    if idx == len(steps) - 1:
        await callback.answer("Это последний этап")
        return
    next_key = steps[idx + 1]
    await state.set_state(FLOW_STATES[flow][next_key])
    label = FLOW_LABELS[flow].get(next_key, next_key)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer(f"Следующий этап: {label}. Введите значение:", reply_markup=get_nav_kb())
    await callback.answer("Перешли к следующему этапу")

@tz_router.message(F.text == "Обычное ТЗ", AdminFilter(config.allowed_users))
async def start_standard_tz(message: Message, state: FSMContext):
    await state.update_data(flow="standard")

    username = message.from_user.username if message.from_user else None
    if username:
        await state.update_data(customer=f"@{username}")
        await state.set_state(StandardTZ.geo)
        await message.answer(
            f"Вы начали создание {hbold('Обычного ТЗ')}.\n\n"
            f"{hbold('Заказчик')}: @{username}\n\n"
            "Гео:\n\n"
            f"{hitalic('Пример: Камерун')}",
            parse_mode="HTML",
        )
        return

    await state.set_state(StandardTZ.customer)
    await message.answer(
                         f"Вы начали создание {hbold('Обычного ТЗ')}.\n\n"
                         f"Введите {hbold('Заказчика')}:\n\n"
                         f"{hitalic('Пример: @pupkin')}",
                         reply_markup=get_nav_kb(), parse_mode="HTML")

@tz_router.message(StandardTZ.customer)
async def handle_standard_customer(message: Message, state: FSMContext):
    await state.update_data(customer=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.geo)
    await message.answer("Гео:\n\n"
                         f"{hitalic('Пример: Камерун')}", parse_mode="HTML")

@tz_router.message(StandardTZ.geo)
async def handle_standard_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.approach)
    await message.answer("Подход:")

@tz_router.message(StandardTZ.approach)
async def handle_standard_approach(message: Message, state: FSMContext):
    await state.update_data(approach=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.app)
    await message.answer("Прила:\n\n"
                         f"{hitalic('Пример: https://fasgdsif.be-the-best-play.xyz/')}", parse_mode="HTML")

@tz_router.message(StandardTZ.app)
async def handle_standard_app(message: Message, state: FSMContext):
    await state.update_data(app=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.language)
    await message.answer("Язык:\n\n"
                         f"{hitalic('Пример: Французский')}", parse_mode="HTML")

@tz_router.message(StandardTZ.language)
async def handle_standard_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.reference)
    await message.answer("Референс, исходник (Если есть):\n\n"
                         f"{hitalic('Пример: [ссылки]')}", parse_mode="HTML")

@tz_router.message(StandardTZ.reference)
async def handle_standard_reference(message: Message, state: FSMContext):
    await state.update_data(reference=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.celebrity)
    await message.answer("Селеба:\n\n"
                         f"{hitalic('Пример: francis_ngannou')}", parse_mode="HTML")

@tz_router.message(StandardTZ.celebrity)
async def handle_standard_celebrity(message: Message, state: FSMContext):
    await state.update_data(celebrity=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.format)
    await message.answer("Формат крео:\n\n"
                         f"{hitalic('Пример: 1:1, 16:9, 9:16')}",
                         parse_mode="HTML")

@tz_router.message(StandardTZ.format)
async def handle_standard_format(message: Message, state: FSMContext):
    await state.update_data(format=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.slot)
    await message.answer("Слот(-ы):")

@tz_router.message(StandardTZ.slot)
async def handle_standard_slot(message: Message, state: FSMContext):
    await state.update_data(slot=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.extras)
    await message.answer(
        " Футажи/Дополнительно:\n\n"
        "Примеры:\n"
        "• Умеренные футажи богатой жизни (без особняков)\n"
        "• Акценты: авто, яхты, часы, путешествия\n"
        "• Избегать кадров с замками/особняками\n"
        "• Пожелания к графике/цветам/шрифтам\n"
        "• Ссылки/референсы, если есть",
        parse_mode="HTML",
    )

@tz_router.message(StandardTZ.extras)
async def handle_standard_extras(message: Message, state: FSMContext):
    await state.update_data(extras=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(StandardTZ.scenario)
    await message.answer(" Сценарий(Текст):\n\n"
                         f"{hitalic('Пример: Francis на тренировке: «Каждый день — это бой...»')}", parse_mode="HTML")


@tz_router.message(StandardTZ.scenario)
async def handle_standard_scenario(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(scenario=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(ConfirmSend.preferred_creative)
    await message.answer(
        "Кто ваш предпочитаемый креативщик для этого ТЗ?\n\n"
        "Вы можете указать имя или @ник из команды. Если не важно — нажмите кнопку 'Следующий этап' ниже.\n\n"
        "Примеры:\n"
        "Юрий - @russkishpion\n"
        "Семен - @supersk\n"
        "Влад - @nevladex\n"
        "Ефим - @XFiderson\n",
        reply_markup=get_skip_preferred_creative_kb(),
        parse_mode="HTML",
    )

# -----------------------------------------------------------------------
# FSM: 2. Уник (Uniq)
# -----------------------------------------------------------------------

@tz_router.message(F.text == "Уник", AdminFilter(config.allowed_users))
async def start_uniq_tz(message: Message, state: FSMContext):
    await state.update_data(flow="uniq")

    username = message.from_user.username if message.from_user else None
    if username:
        await state.update_data(customer=f"@{username}")
        await state.set_state(UniqTZ.geo)
        await message.answer(
            f"Вы начали создание {hbold('ТЗ на Уник')}.\n\n"
            f"{hbold('Заказчик')}: @{username}\n\n"
            "Гео:\n\n"
            f"{hitalic('Пример: Колумбия')}",
            parse_mode="HTML",
        )
        return

    await state.set_state(UniqTZ.customer)
    await message.answer(
                         f"Вы начали создание {hbold('ТЗ на Уник')}.\n\n"
                         f"Введите {hbold('Заказчика')}:\n\n"
                         f"{hitalic('Пример: @pupkin')}",
                         reply_markup=get_nav_kb(), parse_mode="HTML")

@tz_router.message(UniqTZ.customer)
async def handle_uniq_customer(message: Message, state: FSMContext):
    await state.update_data(customer=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(UniqTZ.geo)
    await message.answer("Гео:\n\n"
                         f"{hitalic('Пример: Колумбия')}", parse_mode="HTML")

@tz_router.message(UniqTZ.geo)
async def handle_uniq_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(UniqTZ.app)
    await message.answer("Прила (если нужно заменить):\n\n"
                         f"{hitalic('Пример: оставляем как в креативе')}", parse_mode="HTML")

@tz_router.message(UniqTZ.app)
async def handle_uniq_app(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(app=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(UniqTZ.creative_name)
    await message.answer("Название креатива (на который делаем уникализацию):\n\n"
                         f"{hitalic('Пример: F_CO2')}", parse_mode="HTML")

@tz_router.message(UniqTZ.creative_name)
async def handle_uniq_creative(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(creative_name=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(ConfirmSend.preferred_creative)
    await message.answer(
        "Кто ваш предпочитаемый креативщик для этого ТЗ?\n\n"
        "Вы можете указать имя или @ник из команды. Если не важно — нажмите кнопку 'Следующий этап' ниже.\n\n"
        "Примеры:\n"
        "Юрий - @russkishpion\n"
        "Семен - @supersk\n"
        "Влад - @nevladex\n"
        "Ефим - @XFiderson\n",
        reply_markup=get_skip_preferred_creative_kb(),
        parse_mode="HTML",
    )

# -----------------------------------------------------------------------
# FSM: 3. Адапт (Adapt)
# -----------------------------------------------------------------------

@tz_router.message(F.text == "Адапт", AdminFilter(config.allowed_users))
async def start_adapt_tz(message: Message, state: FSMContext):
    await state.update_data(flow="adapt")

    username = message.from_user.username if message.from_user else None
    if username:
        await state.update_data(customer=f"@{username}")
        await state.set_state(AdaptTZ.geo)
        await message.answer(
            f"Вы начали создание {hbold('ТЗ на Адапт')}.\n\n"
            f"{hbold('Заказчик')}: @{username}\n\n"
            "Гео:\n\n"
            f"{hitalic('Пример: Аргентина')}",
            parse_mode="HTML",
        )
        return

    await state.set_state(AdaptTZ.customer)
    await message.answer(
                         f"Вы начали создание {hbold('ТЗ на Адапт')}.\n\n"
                         f"Введите {hbold('Заказчика')}:\n\n"
                         f"{hitalic('Пример: @pupkin')}",
                         reply_markup=get_nav_kb(), parse_mode="HTML")

@tz_router.message(AdaptTZ.customer)
async def handle_adapt_customer(message: Message, state: FSMContext):
    await state.update_data(customer=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(AdaptTZ.geo)
    await message.answer("Гео:\n\n"
                         f"{hitalic('Пример: Аргентина')}", parse_mode="HTML")

@tz_router.message(AdaptTZ.geo)
async def handle_adapt_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(AdaptTZ.new_app)
    await message.answer("Новая прила:\n\n"
                         f"{hitalic('Пример: https://fasgdsif.be-the-best-play.xyz/')}", parse_mode="HTML")

@tz_router.message(AdaptTZ.new_app)
async def handle_adapt_app(message: Message, state: FSMContext):
    await state.update_data(new_app=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(AdaptTZ.creative_name)
    await message.answer("Креатив:\n\n"
                         f"{hitalic('Пример: S_AR2')}", parse_mode="HTML")

@tz_router.message(AdaptTZ.creative_name)
async def handle_adapt_creative(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(creative_name=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(ConfirmSend.preferred_creative)
    await message.answer(
        "Кто ваш предпочитаемый креативщик для этого ТЗ?\n\n"
        "Вы можете указать имя или @ник из команды. Если не важно — нажмите кнопку 'Следующий этап' ниже.\n\n"
        "Примеры:\n"
        "Юрий - @russkishpion\n"
        "Семен - @supersk\n"
        "Влад - @nevladex\n"
        "Ефим - @XFiderson\n",
        reply_markup=get_skip_preferred_creative_kb(),
        parse_mode="HTML",
    )

# -----------------------------------------------------------------------
# FSM: 4. Рерайт (Rewrite)
# -----------------------------------------------------------------------

@tz_router.message(F.text == "Рерайт", AdminFilter(config.allowed_users))
async def start_rewrite_tz(message: Message, state: FSMContext):
    await state.update_data(flow="rewrite")

    username = message.from_user.username if message.from_user else None
    if username:
        await state.update_data(customer=f"@{username}")
        await state.set_state(RewriteTZ.geo)
        await message.answer(
            f"Вы начали создание {hbold('ТЗ на Рерайт')}.\n\n"
            f"{hbold('Заказчик')}: @{username}\n\n"
            "Гео:\n\n"
            f"{hitalic('Пример: Пакистан')}",
            parse_mode="HTML",
        )
        return

    await state.set_state(RewriteTZ.customer)
    await message.answer(
                         f"Вы начали создание {hbold('ТЗ на Рерайт')}.\n\n"
                         f"Введите {hbold('Заказчика')}:\n\n"
                         f"{hitalic('Пример: @pupkin')}",
                         reply_markup=get_nav_kb(), parse_mode="HTML")

@tz_router.message(RewriteTZ.customer)
async def handle_rewrite_customer(message: Message, state: FSMContext):
    await state.update_data(customer=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(RewriteTZ.geo)
    await message.answer("Гео:\n\n"
                         f"{hitalic('Пример: Пакистан')}", parse_mode="HTML")

@tz_router.message(RewriteTZ.geo)
async def handle_rewrite_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(RewriteTZ.language)
    await message.answer("Язык:\n\n"
                         f"{hitalic('Пример: Урду')}", parse_mode="HTML")

@tz_router.message(RewriteTZ.language)
async def handle_rewrite_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(RewriteTZ.creative_reference)
    await message.answer("Креатив(референс):\n\n"
                         f"{hitalic('Пример: S_IN20')}", parse_mode="HTML")

@tz_router.message(RewriteTZ.creative_reference)
async def handle_rewrite_creative(message: Message, state: FSMContext):
    await state.update_data(creative_reference=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(RewriteTZ.additional)
    await message.answer("Дополнительно (Замена кадров, селебы, текста и т.д.):\n\n"
                         f"{hitalic('Пример: Меняем гео на Пакистан, селебу меняем на Alina Khan...')}", parse_mode="HTML")

@tz_router.message(RewriteTZ.additional)
async def handle_rewrite_additional(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(additional=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(ConfirmSend.preferred_creative)
    await message.answer(
        "Кто ваш предпочитаемый креативщик для этого ТЗ?\n\n"
        "Вы можете указать имя или @ник из команды. Если не важно — нажмите кнопку 'Следующий этап' ниже.\n\n"
        "Примеры:\n"
        "Юрий - @russkishpion\n"
        "Семен - @supersk\n"
        "Влад - @nevladex\n"
        "Ефим - @XFiderson\n",
        reply_markup=get_skip_preferred_creative_kb(),
        parse_mode="HTML",
    )

# -----------------------------------------------------------------------
# FSM: 5. PWA (Прилка)
# -----------------------------------------------------------------------

@tz_router.message(F.text == "ДИЗАЙН КАРТИНОК PWA", AdminFilter(config.allowed_users))
async def start_pwa_tz(message: Message, state: FSMContext):
    await state.update_data(flow="pwa")

    username = message.from_user.username if message.from_user else None
    if username:
        await state.update_data(customer=f"@{username}")
        await state.set_state(PwaTZ.format)
        await message.answer(
            f"Вы начали создание {hbold('ТЗ на PWA (Прилку)')}.\n\n"
            f"{hbold('Заказчик')}: @{username}\n\n"
            "Формат:\n\n"
            f"{hitalic('Пример: 1 картинка горизонтальная (1280 х 2880) - ...')}",
            parse_mode="HTML",
        )
        return

    await state.set_state(PwaTZ.customer)
    await message.answer(
                         f"Вы начали создание {hbold('ТЗ на PWA (Прилку)')}.\n\n"
                         f"Введите {hbold('Заказчика')}:\n\n"
                         f"{hitalic('Пример: @pupkin')}",
                         reply_markup=get_nav_kb(), parse_mode="HTML")

@tz_router.message(PwaTZ.customer)
async def handle_pwa_customer(message: Message, state: FSMContext):
    await state.update_data(customer=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.format)
    await message.answer("Формат:\n\n"
                         f"{hitalic('Пример: 1 картинка горизонтальная (1280 х 2880) - ...')}", parse_mode="HTML")

@tz_router.message(PwaTZ.format)
async def handle_pwa_format(message: Message, state: FSMContext):
    await state.update_data(format=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.brand)
    await message.answer("Бренд Казино:\n\n"
                         f"{hitalic('Пример: 1win')}", parse_mode="HTML")

@tz_router.message(PwaTZ.brand)
async def handle_pwa_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.logos)
    await message.answer("Лого брендов, если надо показать на прилке:")

@tz_router.message(PwaTZ.logos)
async def handle_pwa_logos(message: Message, state: FSMContext):
    await state.update_data(logos=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.slot)
    await message.answer("Слот:")

@tz_router.message(PwaTZ.slot)
async def handle_pwa_slot(message: Message, state: FSMContext):
    await state.update_data(slot=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.geo)
    await message.answer("Гео:")

@tz_router.message(PwaTZ.geo)
async def handle_pwa_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.extra_elements)
    await message.answer("Доп. элементы на картинке:\n\n"
                         f"{hitalic('Пример: смс, коэффиценты, телефон с рукой')}", parse_mode="HTML")

@tz_router.message(PwaTZ.extra_elements)
async def handle_pwa_elements(message: Message, state: FSMContext):
    await state.update_data(extra_elements=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.offers)
    await message.answer("Специальные предложения:\n\n"
                         f"{hitalic('Пример: Бонусы, условия')}", parse_mode="HTML")

@tz_router.message(PwaTZ.offers)
async def handle_pwa_offers(message: Message, state: FSMContext):
    await state.update_data(offers=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(PwaTZ.text)
    await message.answer("Текст на картинке (призыв к действию и т.д):\n\n"
                         f"{hitalic('Пример: First deposit 500 = Get 4000')}", parse_mode="HTML")

@tz_router.message(PwaTZ.text)
async def handle_pwa_text(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(text=message.text)
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await _show_preview(message, state)
        return
    await state.set_state(ConfirmSend.preferred_creative)
    await message.answer(
        "Кто ваш предпочитаемый креативщик для этого ТЗ?\n\n"
        "Вы можете указать имя или @ник из команды. Если не важно — нажмите кнопку 'Следующий этап' ниже.\n\n"
        "Примеры:\n"
        "Юрий - @russkishpion\n"
        "Семен - @supersk\n"
        "Влад - @nevladex\n"
        "Ефим - @XFiderson\n",
        reply_markup=get_skip_preferred_creative_kb(),
        parse_mode="HTML",
    )

@tz_router.message(ConfirmSend.preferred_creative)
async def handle_preferred_creative(message: Message, state: FSMContext):
    await state.update_data(preferred_creative=message.text or "—", editing=False)
    await _show_preview(message, state)

@tz_router.callback_query(F.data == "skip_preferred_creative", AdminFilter(config.allowed_users))
async def on_skip_preferred_creative(callback: CallbackQuery, state: FSMContext):
    await state.update_data(preferred_creative="—", editing=False)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await _show_preview(callback.message, state)
    await callback.answer("Креативщик не выбран")

@tz_router.callback_query(F.data == "confirm_send", AdminFilter(config.allowed_users))
async def on_confirm_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        send_text = _build_send_text(data)

        if send_text:
            try:
                if len(send_text) <= 4096:
                    await bot.send_message(config.target_chat_id, send_text, parse_mode="HTML")
                else:
                    plain = _strip_html_tags(send_text)
                    parts = _split_text_for_telegram(plain, max_len=4096)
                    for part in parts:
                        await bot.send_message(config.target_chat_id, part)
            except Exception as e:
                logging.exception(f"Failed to send TZ text to target chat, falling back to plain text: {e}")
                plain = _strip_html_tags(send_text)
                parts = _split_text_for_telegram(plain, max_len=4096)
                for part in parts:
                    await bot.send_message(config.target_chat_id, part)

        media = data.get("media", [])
        if media:
            by_step = {}
            for m in media:
                step = m.get("step") or "unknown"
                by_step.setdefault(step, []).append(m)
            for step, items in by_step.items():
                label = None
                flow = data.get("flow")
                if flow and flow in FLOW_LABELS and step in FLOW_LABELS[flow]:
                    label = FLOW_LABELS[flow][step]
                header = f"Медиа для этапа: {label or step}"
                await bot.send_message(config.target_chat_id, header)
                photos = [m for m in items if m.get("type") == "photo"]
                videos = [m for m in items if m.get("type") == "video"]
                grouped = []
                for m in photos:
                    grouped.append(InputMediaPhoto(media=m["file_id"], caption=m.get("caption")))
                for m in videos:
                    grouped.append(InputMediaVideo(media=m["file_id"], caption=m.get("caption")))
                if not grouped:
                    continue
                if len(grouped) == 1:
                    item = grouped[0]
                    if isinstance(item, InputMediaPhoto):
                        await bot.send_photo(config.target_chat_id, item.media, caption=item.caption)
                    else:
                        await bot.send_video(config.target_chat_id, item.media, caption=item.caption)
                else:
                    batch = []
                    for item in grouped:
                        batch.append(item)
                        if len(batch) == 10:
                            await bot.send_media_group(config.target_chat_id, media=batch)
                            batch = []
                    if batch:
                        await bot.send_media_group(config.target_chat_id, media=batch)

        await state.clear()

        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            await callback.message.answer(
                " ТЗ отправлено!\n\nВы можете создать новое ТЗ.",
                reply_markup=get_main_menu()
            )
    except Exception as e:
        logging.exception(f"Error while confirming TZ send: {e}")
        if callback.message:
            await callback.message.answer("Ошибка при отправке ТЗ. Попробуйте ещё раз.")
    finally:
        try:
            await callback.answer("Отправлено")
        except Exception:
            pass

@tz_router.callback_query(F.data == "cancel_send", AdminFilter(config.allowed_users))
async def on_cancel_send(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer(
            " Отправка отменена. Вы можете начать заново.",
            reply_markup=get_main_menu()
        )
    await callback.answer("Отменено")