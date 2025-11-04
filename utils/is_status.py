from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.types import Update

from loader import ADMINS


class AdminMiddleware(BaseMiddleware):
    def __init__(self):
        super(AdminMiddleware, self).__init__()

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        real_handler: HandlerObject = data.get("handler")
        admin_key = real_handler.flags.get("is_admin")
        if admin_key is not None:
            if event.from_user.id in ADMINS:
                return await handler(event, data)
            return
        return await handler(event, data)