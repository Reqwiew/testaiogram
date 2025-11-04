import pickle
import traceback

from aiogram import F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from numpy import arange

from loader import bot, dp
from utils.singleton import Singleton

package = {}


class Paginator(object, metaclass=Singleton):
    def __init__(
        self,
        save_to: str = "pagination.pkl",
    ):
        self.save_to = save_to

    def importer(self):
        global package
        try:
            with open(self.save_to, "rb") as fp:
                package = pickle.load(fp)
        except Exception:
            package = {}
            with open(self.save_to, "wb") as fw:
                pickle.dump(package, fw)

    @staticmethod
    async def adder(user_id, item_id, array):
        global package
        if user_id not in package.keys():
            package[user_id] = {item_id: array}
        else:
            package[user_id].update({item_id: array})

    @staticmethod
    async def remover(user_id, item_id):
        global package
        package[user_id].pop(item_id)

    @staticmethod
    async def getter(user_id, item_id):
        global package
        return package[user_id][item_id] if item_id in package[user_id].keys() else None

    def exporter(self):
        global package
        try:
            with open(self.save_to, "wb") as fp:
                pickle.dump(package, fp)
        except Exception:
            print(traceback.format_exc())


__PAGINATOR = Paginator()


async def paginator(
    user_id: int,
    identifier: str,
    add_down=InlineKeyboardMarkup(inline_keyboard=[[]]),
    add_up=InlineKeyboardMarkup(inline_keyboard=[[]]),
    old_keyboard=InlineKeyboardMarkup(inline_keyboard=[[]]),
    page=1,
    array=None,
    row=2,
    call_data="",
    spliter="|",
):
    try:
        keyboard = []
        await __PAGINATOR.adder(
            user_id=user_id,
            item_id=str(identifier),
            array={
                "add_up": add_up,
                "pages": array,
                "add_down": add_down,
                "call_data": call_data,
                "spliter": spliter,
                "row": row,
                "page": page,
            },
        )
        if len(array) > page - 1 >= 0:
            for item in add_up.inline_keyboard:
                keyboard.append(item)

            for i in arange(0, len(array[page - 1]), row):
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=item["text"], callback_data=f"{call_data}{spliter}{item['callback_data']}"
                        )
                        for item in array[page - 1][i : i + row]
                    ]
                )

            keyboard.append(
                [
                    InlineKeyboardButton(text="⬅️", callback_data=f"pageBack|{identifier}|{page}"),
                    InlineKeyboardButton(text=f"{page}", callback_data=f"pageNow|{identifier}|{page}"),
                    InlineKeyboardButton(text="➡️", callback_data=f"pageNext|{identifier}|{page}"),
                ]
            )

            for item in add_down.inline_keyboard:
                keyboard.append(item)

            return InlineKeyboardMarkup(inline_keyboard=keyboard)
        else:
            raise Exception
    except Exception:
        return old_keyboard



@dp.callback_query(F.data.startswith("pageBack"))
async def pagination_back(call):
    try:
        _, identifier, page = call.data.split("_")
        data = await __PAGINATOR.getter(user_id=str(call.message.chat.id), item_id=identifier)
        return await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=(
                await paginator(
                    page=int(page) - 1
                    if 0 < int(page) - 1
                    else len(data["pages"]),
                    old_keyboard=call.message.reply_markup.inline_keyboard,
                    identifier=identifier,
                    user_id=str(call.message.chat.id),
                    add_up=data["add_up"],
                    add_down=data["add_down"],
                    array=data["pages"],
                    call_data=data["call_data"],
                    spliter=data["spliter"],
                    row=data["row"],
                )
            ),
        )
    except Exception:
        return None

@dp.callback_query(F.data.startswith("pageNext"))
async def pagination_next(call):
    try:
        _, identifier, page = call.data.split("_")
        data = await __PAGINATOR.getter(user_id=str(call.message.chat.id), item_id=identifier)
        return await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=(
                await paginator(
                    page=int(page) + 1
                    if len(data["pages"]) >= int(page) + 1
                    else 1,
                    old_keyboard=call.message.reply_markup.inline_keyboard,
                    identifier=identifier,
                    user_id=str(call.message.chat.id),
                    add_up=data["add_up"],
                    add_down=data["add_down"],
                    array=data["pages"],
                    call_data=data["call_data"],
                    spliter=data["spliter"],
                    row=data["row"],
                )
            ),
        )
    except Exception:
        return None
