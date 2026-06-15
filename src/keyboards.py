import asyncio
from decimal import HAVE_THREADS
import requests
import json
import aiogram
import aiosqlite
from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, state 
import html

from aiogram.types import InlineKeyboardButton, KeyboardButton, Message, ReplyKeyboardRemove, TelegramObject, update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F
import sys
from aiogram.fsm.state import State, StatesGroup 
from aiogram.fsm.context import FSMContext
from aiogram import types
from enum import Enum




schedule_kb = ReplyKeyboardBuilder()
admit_decline_kb = ReplyKeyboardBuilder()

schedule_kb.add(KeyboardButton(text="На сегодня"))
schedule_kb.add(KeyboardButton(text="На завтра"))
schedule_kb.add(KeyboardButton(text="На неделю"))
schedule_kb.add(KeyboardButton(text="На след. неделю"))
schedule_kb.add(KeyboardButton(text="Изменить мою группу"))
schedule_kb.adjust(2, 2, 1)

admit_decline_kb.add(KeyboardButton(text="Да"))
admit_decline_kb.add(KeyboardButton(text="Нет"))


#admit_decline_kb.as_markup(resize_keyboard=True)
#schedule_kb.as_markup(resize_keyboard=True)
