import asyncio
import traceback
from enum import Enum
from typing import NamedTuple, List

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.types import Message
from aiogram_media_group import media_group_handler

from loader import *


class UserInput(StatesGroup):
    input_message = State()


class InputActions(Enum):
    edit = "edit"
    delete = "delete"


class OutputActions(Enum):
    hide_keyboard = "hide_keyboard"
    delete = "delete"


class Output(NamedTuple):
    message: Message
    to_return: object = None
    bot_msg: Message = None


class Result(object):
    def __init__(self, content_type=None, content=None):
        self.content_type = content_type
        self.content = content


class InputReturns(Enum):
    OK = Result
    Err = "err"
    NoResult = "noresult"


KEYBOARD_DATA = {}
INPUT_STATE = {}


class Input(object):
    def __init__(self, chat_id: int | str, text: str, state: FSMContext, ):
        self.chat_id: int | str = chat_id
        self.text: str = text
        self.state: FSMContext = state

        self.__message_id: int | None = None
        self.__reply_markup = None,
        self.__after_input: OutputActions | None = None

        self.__msg = None

    async def send_photo(self, photo: str) -> Output:
        with open(photo, "rb") as file:
            return await self.__send(
                await bot.send_photo(
                    chat_id=self.chat_id,
                    caption=self.text,
                    photo=file,
                    reply_markup=self.__reply_markup
                )
            )

    async def send_document(self, document: str) -> Output:
        with open(document, "rb") as file:
            return await self.__send(
                await bot.send_document(
                    chat_id=self.chat_id,
                    caption=self.text,
                    document=file,
                    reply_markup=self.__reply_markup
                )
            )

    async def send_message(self) -> Output:
        return await self.__send(
            await bot.send_message(
                chat_id=self.chat_id,
                text=self.text,
                reply_markup=self.__reply_markup
            )
        )

    async def edit(self, message_id: int) -> Output:
        self.__message_id = message_id
        return await self.__send(
            await bot.edit_message_text(
                chat_id=self.chat_id,
                text=self.text,
                message_id=message_id,
                reply_markup=self.__reply_markup
            )
        )

    async def delete(self, message_id: int) -> Output:
        self.__message_id = message_id
        await bot.delete_message(
            chat_id=self.chat_id,
            message_id=message_id
        )
        return await self.__send(
            await bot.send_message(
                chat_id=self.chat_id,
                text=self.text,
                reply_markup=self.__reply_markup
            )
        )

    def reply_markup(self, reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup):
        self.__reply_markup = reply_markup
        return self

    def __after(self, action: OutputActions):
        self.__after_input = action
        return self

    def hide_keyboard_after(self):
        self.__after_input = OutputActions.hide_keyboard
        return self

    def delete_message_after(self):
        self.__after_input = OutputActions.delete
        return self

    async def __send(self, msg) -> Output | None:
        try:
            await self.state.set_state(UserInput.input_message)

            self.__msg = msg

            __event = asyncio.Event()
            INPUT_STATE[str(self.chat_id)] = __event
            await __event.wait()
            data = await self.state.get_value("input_message")
            await self.state.update_data(input_message=None)

            if data is not None:
                INPUT_STATE.pop(str(self.chat_id)).clear()
                return Output(message=data, to_return=data, bot_msg=msg)

            if KEYBOARD_DATA.get(self.chat_id, None) is not None:
                INPUT_STATE.pop(str(self.chat_id)).clear()
                return KEYBOARD_DATA.get(self.chat_id)

        except Exception:
            print("TEXT_INPUT", traceback.format_exc())
        finally:
            await self.state.set_state()
            if self.__after_input == OutputActions.hide_keyboard:
                await bot.edit_message_reply_markup(
                    chat_id=self.chat_id,
                    message_id=self.__msg.message_id,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]])
                )
            elif self.__after_input == OutputActions.delete:
                await bot.delete_message(chat_id=self.chat_id, message_id=self.__msg.message_id)
            if KEYBOARD_DATA.get(self.chat_id, None) is not None:
                del KEYBOARD_DATA[self.chat_id]


@dp.message(F.media_group_id, StateFilter(UserInput.input_message))
@media_group_handler
async def get_input_msg_group(messages: List[Message], state: FSMContext):
    await state.update_data(input_message=messages)
    INPUT_STATE[str(messages[0].chat.id)].set()


@dp.message(StateFilter(UserInput.input_message))
async def get_input_msg(message, state: FSMContext):
    await state.update_data(input_message=message)
    INPUT_STATE[str(message.chat.id)].set()


def call_input(func):
    async def wrapper(*args, **kwargs):
        try:
            KEYBOARD_DATA[args[0].message.chat.id] = await func(*args, **kwargs)
            INPUT_STATE[str(args[0].message.chat.id)].set()
        except Exception:
            print("CALL_INPUT", traceback.format_exc())

    return wrapper
