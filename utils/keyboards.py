from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить задачу')],
        [KeyboardButton(text='Посмотреть список задач')],
        [KeyboardButton(text='Поиск задач')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню'
)
