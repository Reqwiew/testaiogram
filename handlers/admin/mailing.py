import asyncio
import time
import traceback

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select

from loader import *
from tables import Users
from utils.user_input import Input

router = Router()


@router.callback_query(F.data == AdminButtons.mailing.name, flags={"is_admin": True})
async def run_mailing(call: CallbackQuery, state: FSMContext):
    mailing_message = await Input(
        chat_id=call.message.chat.id,
        text="<b>Введите сообщение:\n️</b>",
        state=state,
    ).reply_markup(
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="backToAdmin")],
            ]
        )
    ).hide_keyboard_after().edit(
        message_id=call.message.message_id
    )

    await state.update_data(mailing_message=[mailing_message.message.message_id]
    if type(mailing_message.message) is not list
    else [item.message_id for item in mailing_message.message])

    await bot.copy_messages(
        chat_id=call.message.chat.id,
        from_chat_id=call.message.chat.id,
        message_ids=[mailing_message.message.message_id]
        if type(mailing_message.message) is not list
        else [item.message_id for item in mailing_message.message],
    )
    await bot.send_message(
        chat_id=call.message.chat.id,
        text="<b>Отправить?</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅️ Отправить", callback_data=f"send-mail"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel-mail")
                ]
            ]
        )
    )


@router.callback_query(F.data.startswith("send-mail"), flags={"is_admin": True})
async def start_mailing(call: CallbackQuery, state: FSMContext):
    try:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.send_message(chat_id=call.message.chat.id, text="<b>Рассылка начата</b>")
        async with (async_session() as session):
            state_data = await state.get_data()
            mailing_message = state_data.get("mailing_message")

            await state.clear()
            if mailing_message is None:
                return
            users = (await session.execute(select(Users.id))).all()
            list_of_not_received_msg_users = []
            t0 = time.time()

            for future in asyncio.as_completed(
                    map(mailer, [
                        {
                            "msg_ids": mailing_message,
                            "from_chat": call.message.chat.id,
                            "user": user[0],
                            "iteration": i // 20,
                        } for i, user in enumerate(users, 0)])):
                if not await future:
                    list_of_not_received_msg_users.append(future)
            await bot.send_message(chat_id=call.message.chat.id, text=f"<b>Рассылка завершена\n"
                                                                      f"Всего пользователей <code>{len(users)}</code>\n"
                                                                      f"Сообщения дошли до <code>{len(users) - len(list_of_not_received_msg_users)}</code> пользователей\n"
                                                                      f"Затрачено: {round(time.time() - t0, 2)} сек.</b>")
    except Exception:
        print(traceback.format_exc())


@router.callback_query(lambda call: call.data == "cancel-mail", flags={"is_admin": True})
async def cancel_mail(call):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]]))
    await call.answer("✅ Canceled")


async def mailer(data):
    try:
        await asyncio.sleep(data["iteration"])
        if len(data["msg_ids"]) == 1:
            await bot.copy_message(
                chat_id=data["user"],
                from_chat_id=data["from_chat"],
                message_id=data["msg_ids"][0],
            )
        else:
            await bot.copy_messages(
                chat_id=data["user"],
                from_chat_id=data["from_chat"],
                message_ids=data["msg_ids"]
            )
        return True
    except Exception:
        print(traceback.format_exc())
        return False
