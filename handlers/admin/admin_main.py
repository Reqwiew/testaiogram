from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from loader import *

router = Router()


@router.message(Command('admin'), flags={"is_admin": True})
async def admin_panel(message: Message, **kwargs):
    await bot.send_message(
        chat_id=message.chat.id,
        text="<b>Admin panel is open</b>",
    )
