from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LinkPreviewOptions, Message

from config import ADMIN_ID, GITHUB_LINK, USEFUL_LINKS
from keyboards import schedule_kb, settings_kb
from services import welcome

# /help and /github
router = Router(name=__name__)


class FeedBackCommands(StatesGroup):
    waiting_for_message = State()


@router.message(Command("help", ignore_case=True))
@router.message(CommandStart())
@router.message(Command("начать", "изменитьмоюгруппу", ignore_case=True))
@router.message(F.text.replace(" ", "").upper().in_({"СТАРТ", "НАЧАТЬ", "ИЗМЕНИТЬМОЮГРУППУ"}))
async def say_hello(message: Message, state: FSMContext) -> None:
    await welcome(message, state)


@router.message(Command("info", ignore_case=True))
@router.message(Command("about", ignore_case=True))
@router.message(F.text.replace(" ", "").upper().in_({"ОНАС"}))
async def info(message: Message) -> None:
    await message.answer(
        f"""Некоммерческий Open Source проект, созданный силами студентов для улучшения качества образовательной среды.
\nИсходный код и документация доступны на GitHub:\n{GITHUB_LINK}

Проект улучшается по мере увеличения наших сил и возможностей
        """
    )


@router.message(Command("commands", ignore_case=True))
async def commands(message: Message) -> None:
    await message.answer(
        """/start начать
/commands список команд
/info и /about информация о проекте

/week расписание на неделю
/today расписание на день
/tomorrow расписание на завтра
/nextweek расписание следующей недели
/settings настройки
        """
    )


@router.message(F.text.replace(" ", "").upper().in_({"НАСТРОЙКИ"}))
async def settings(message: Message) -> None:
    await message.answer(
        "Выберите действие", reply_markup=settings_kb.as_markup(resize_keyboard=True)
    )


@router.message(F.text.replace(" ", "").upper().in_({"ВЕРНУТЬСЯ"}))
async def getback_button(message: Message) -> None:
    await message.answer(
        "Выберите действие", reply_markup=schedule_kb.as_markup(resize_keyboard=True)
    )


@router.message(FeedBackCommands.waiting_for_message)
async def recive_feedback_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text == "exit":
        await message.answer("Отменено", reply_markup=schedule_kb.as_markup(resize_keyboard=True))
        await state.clear()
        return
    elif message.text == "Вернуться":
        await state.clear()
        return
    if message.text:
        msg = message.text + f"\n{message.chat.id}"
        await bot.send_message(ADMIN_ID, msg)
        await message.answer("Отправлено")
        await state.clear()


@router.message(Command("feedback", ignore_case=True))
@router.message(
    F.text.func(lambda t: t and t.replace(" ", "").upper() in {"ОСТАВИТЬОТЗЫВ|ПОЖЕЛАНИЯ"})
)
async def feedback(message: Message, state: FSMContext) -> None:
    await message.answer("Введите сообщение...\n\nЛибо напрямую @Zeufo.\n(exit для отмены)")
    await state.set_state(FeedBackCommands.waiting_for_message)


@router.message(F.text.func(lambda t: t and t.replace(" ", "").upper() in {"ПОЛЕЗНЫЕССЫЛКИ"}))
async def useful_links(message: Message) -> None:
    # Собираем текст сообщения
    lines = ["🔗 <b>Полезные ссылки:</b>\n"]

    for url, description in USEFUL_LINKS.items():
        lines.append(f"🌐 <a href='{url}'>{url}</a>\n💬 {description}\n")

    response_text = "\n".join(lines)

    await message.answer(
        text=response_text,
        parse_mode="HTML",
        # Отключает тяжелые превью страниц, чтобы сообщение выглядело аккуратно
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        # Если нужна еще и клавиатура снизу — раскомментируй:
        # reply_markup=settings_kb.as_markup(resize_keyboard=True),
    )
