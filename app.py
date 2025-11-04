import asyncio
import datetime

from colorama import Fore, Style

from handlers import user, admin, core
from loader import *
from tables import init_models


async def on_startup():
    await init_models()
    bot_info = await dp.get("bot").get_me()
    print(
        f"{Style.BRIGHT}{Fore.CYAN}https://t.me/{bot_info.username} запущен успешно! "
        f"({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        Style.RESET_ALL
    )


async def main():
    try:
        from handlers import dp
        await on_startup()
        from utils.is_status import AdminMiddleware
        dp.message.middleware(AdminMiddleware())
        dp.callback_query.middleware(AdminMiddleware())

        dp.include_routers(
            user.user_main.router,

            admin.admin_main.router,
            admin.mailing.router,

            core.core.router,
        )
        await bot.delete_webhook()
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("окончание работы")
