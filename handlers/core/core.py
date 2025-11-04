from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from loader import *

router = Router()

@router.callback_query(F.data == "cancel")
async def cancel_input(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]])
    )
    await bot.send_message(
        chat_id=call.message.chat.id,
        text="<b>Canceled</b>"
    )