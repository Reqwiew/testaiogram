from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm import state
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete, or_
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import selectinload
from html import escape

from utils import keyboards as kb
from loader import *
from tables import *

router = Router()


class Register(StatesGroup):
    name = State()
    phone_number = State()
    tg_id = State()


class AddTask(StatesGroup):
    task_name = State()
    description = State()


class SearchTask(StatesGroup):
    keyword = State()


@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.tg_id == message.chat.id)
        )
        user = result.scalar_one_or_none()

        if user:
            await message.answer(f"Добро пожаловать, {escape(user.username)}!\n", reply_markup=kb.main)
            return

    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')


@router.message(Register.name)
async def user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.phone_number)
    await message.answer('Введите ваш номер телефона', reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='отправить номер телефона', request_contact=True)],
        ],
        resize_keyboard=True,
    ))


@router.message(Register.phone_number, F.contact)
async def user_phone(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.contact.phone_number)
    await state.update_data(tg_id=message.chat.id)
    data = await state.get_data()
    async with async_session() as session:
        async with session.begin():
            user = Users(username=data['name'], phone_number=data['phone_number'], tg_id=data['tg_id'])
            session.add(user)
    await message.answer("Вы успешно зарегистрировались")
    await state.clear()


@router.message(F.text == 'Добавить задачу')
async def add_task(message: Message, state: FSMContext):
    await state.set_state(AddTask.task_name)
    await message.answer(text='Введите название таски')


@router.message(AddTask.task_name)
async def add_task_name(message: Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await state.set_state(AddTask.description)
    await message.answer('Введите описание таски')


@router.message(AddTask.description)
async def add_task_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    task_name = data['task_name']
    description = data['description']
    tg_id = message.chat.id
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Users).where(Users.tg_id == tg_id))
            user = result.scalar_one_or_none()
            if user:
                task = Tasks(
                    task_name=task_name,
                    description=description,
                    user_id=user.id
                )
                session.add(task)

    await message.answer("Задача успешно добавлена!")
    await state.clear()
    await message.answer(
        f"Добро пожаловать, {escape(user.username)}!\nВыберите действие:",
        reply_markup=kb.main
    )


@router.message(F.text == 'Посмотреть список задач')
async def check_all_task(message: Message):
    tg_id = message.chat.id
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.tg_id == tg_id).options(selectinload(Users.tasks))

        )
        user = result.scalar_one_or_none()
        if not user or not user.tasks:
            await message.answer('У вас нет задач')
            return
        for task in user.tasks:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Выполнено', callback_data=f"done_{task.id}")]
            ])
            await message.answer(
                text=f"Задача: {escape(task.task_name)}\nОписание: {escape(task.description)}",
                reply_markup=keyboard
            )


@router.callback_query(lambda c: c.data and c.data.startswith("done_"))
async def complete_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(Tasks).where(Tasks.id == task_id))

    await callback.answer("Задача выполнена и удалена!")
    await callback.message.delete()


@router.message(F.text == 'Поиск задач')
async def start_search(message: Message, state: FSMContext):
    await state.set_state(SearchTask.keyword)
    await message.answer("Введите ключевое слово для поиска задач:")


@router.message(SearchTask.keyword)
async def search_task(message: Message, state: FSMContext):
    keyword = message.text.strip()
    tg_id = message.chat.id

    async with async_session() as session:
        result = await session.execute(
            select(Tasks)
            .join(Users)
            .where(
                Users.tg_id == tg_id,
                or_(
                    Tasks.task_name.ilike(f"%{keyword}%"),
                    Tasks.description.ilike(f"%{keyword}%")
                )
            )
        )
        tasks = result.scalars().all()

    await state.clear()

    if not tasks:
        await message.answer(text='Задачи по этому ключевому слову не найдены.')
        return

    for task in tasks:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Выполнено', callback_data=f"done_{task.id}")]
        ])
        await message.answer(
            text=f"Задача: {escape(task.task_name)}\nОписание: {escape(task.description)}",
            reply_markup=keyboard
        )