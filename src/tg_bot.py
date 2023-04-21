import aiogram
import json
import aiofiles
import random
import time
import aiohttp
import re
import os
import demapi

from aiogram import Bot, Dispatcher
from sqlalchemy.orm import Session
from sqlalchemy import select
from PIL import Image

from .generator import Generator
from .settings import TG_TOKEN
from .constants import *
from .database import *


def register_user(id) -> None:
    with Session(engine) as session:
        session.add(User(id=id))
        session.commit()


def get_user(id) -> User:
    with Session(engine) as session:
        res = select(User).where(User.id == id)
        return session.scalars(res).one_or_none()


def get_dem(id) -> Demotivator:
    with Session(engine) as session:
        res = select(Demotivator).where(Demotivator.id == id)
        return session.scalars(res).one_or_none()


def get_link(url) -> str:
    res = [i[0] for i in re.findall(URL_RE, url)]
    if res:
        return res[0]


def set_state(id, state) -> None:
    with Session(engine) as session:
        res = select(User).where(User.id == id)
        user = session.scalars(res).one_or_none()
        user.state = state
        session.commit()


def add_dem(filename, user_id) -> None:
    with Session(engine) as session:
        session.add(Demotivator(filename=filename, user_id=user_id))
        session.commit()


def get_temp_dem(user_id) -> Demotivator:
    with Session(engine, expire_on_commit=False) as session:
        res = select(Demotivator).where(
            Demotivator.user_id == user_id).where(Demotivator.is_temp == True)
        output = None
        for dem in session.scalars(res):
            if not output or output.id < dem.id:
                if output:
                    session.delete(output)
                output = dem
            else:
                session.delete(dem)
        session.commit()
        return output


def set_dem_temp(dem_id, is_temp):
    with Session(engine) as session:
        res = select(Demotivator).where(
            Demotivator.id == dem_id).where(Demotivator.is_temp == True)
        dem = session.scalars(res).one()
        dem.is_temp = is_temp
        session.commit()


def set_dem_privacy(dem_id, value):
    with Session(engine) as session:
        res = select(Demotivator).where(
            Demotivator.id == dem_id)
        dem = session.scalars(res).one()
        dem.is_private = value
        session.commit()


def change_create_mode(user_id):
    with Session(engine) as session:
        res = select(User).where(User.id == user_id)
        user = session.scalars(res).one_or_none()
        user.create_mode = 1 - user.create_mode
        session.commit()


def get_dems(user_id, only_public=False):
    with Session(engine) as session:
        if only_public:
            res = select(Demotivator).where(
                Demotivator.user_id == user_id).where(Demotivator.is_temp == False) \
                .where(Demotivator.is_private == False).order_by(Demotivator.id)
        else:
            res = select(Demotivator).where(
                Demotivator.user_id == user_id).where(Demotivator.is_temp == False) \
                .order_by(Demotivator.id)
        return session.scalars(res).all()


def add_friend(from_id, to_id):
    with Session(engine) as session:
        res = select(User).where(User.id == from_id)
        user = session.scalars(res).one()
        user.friends = pickle.dumps(pickle.loads(user.friends) + [to_id])
        session.commit()


def del_dem(dem_id):
    with Session(engine) as session:
        res = select(Demotivator).where(
            Demotivator.id == dem_id)
        dem = session.scalars(res).one()
        session.delete(dem)
        session.commit()


def get_filename(prefix='file', extension='.png', is_upper=False):
    if not os.path.exists('images'):
        os.mkdir('images')
    name = f'images/{prefix}_{int(time.time())}_{random.getrandbits(32)}{extension}'
    if is_upper:
        name = '../' + name
    return name


bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(content_types=['document'])
@dp.message_handler(content_types=['photo'])
@dp.message_handler()
async def on_message(message):
    user_id = message['from']['id']
    user = get_user(user_id)
    if not user:
        register_user(user_id)
        await message.answer(MAIN_MESSAGE, reply_markup=MAIN_KB)
        return
    state = user.state
    text = message.text
    if not text:
        try:
            text = message.caption
        except:
            pass
    link = get_link(text if text else "")
    '''
    0 - default
    1 - waiting for text
    2 - waiting for friend id
    3 - waiting for adding friend
    '''
    if text == MY_PICS:
        user_dems = get_dems(user_id)
        if not user_dems:
            await message.answer("У вас пока нет демотиваторов!",
                                 reply_markup=MAIN_KB)
            return
        await message.answer("Загрузка...",
                             reply_markup=MAIN_KB)
        dem = user_dems[0]
        kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        text = "Тип: приватный." if dem.is_private else "Тип: публичный."
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Дальше",
            callback_data=json.dumps({'action': 'next', 'value': 1})))
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Сделать приватным",
            callback_data=json.dumps({'action': 'make_private',
                                      'value': True, 'id': dem.id})),
               aiogram.types.InlineKeyboardButton(
            text="Сделать публичным",
            callback_data=json.dumps({'action': 'make_private',
                                      'value': False, 'id': dem.id}))
               )
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Удалить",
            callback_data=json.dumps({'action': 'delete_dem', 'id': dem.id})))
        await bot.send_photo(user_id, photo=open(dem.filename, 'rb'), caption=text,
                             reply_markup=kb)
        return

    elif text == BACK_TO_MENU:
        set_state(user_id, 0)
        await message.answer("Вы в главном меню.",
                             reply_markup=MAIN_KB)
        return

    elif text == FRIENDS_PICS:
        kb = [
            [
                aiogram.types.KeyboardButton(text=ADD_FRIEND),
                aiogram.types.KeyboardButton(text=SHOW_PICTURES)
            ],
            [
                aiogram.types.KeyboardButton(text=BACK_TO_MENU)
            ]
        ]
        kb = aiogram.types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Отправьте картинку или нажмите кнопку."
        )
        await message.answer('Тут вы можете добавить друга и посмотреть его работы.',
                             reply_markup=kb)
        return

    elif text == SHOW_PICTURES:
        set_state(user_id, 2)
        kb = [
            [
                aiogram.types.KeyboardButton(text=BACK_TO_MENU)
            ]
        ]
        kb = aiogram.types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )
        frds = pickle.loads(user.friends)
        if frds:
            friends = "\n\nВаши друзья:\n" + \
                '\n'.join(f'`{i}`' for i in frds)
        else:
            friends = ''
        await message.answer('Введите ID друга.'+friends, reply_markup=kb,
                             parse_mode="Markdown")
        return

    elif text == ADD_FRIEND:
        set_state(user_id, 3)
        kb = [
            [
                aiogram.types.KeyboardButton(text=BACK_TO_MENU)
            ]
        ]
        kb = aiogram.types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )
        await message.answer('Введите ID друга:', reply_markup=kb)
        return

    elif text == SETTINGS:
        kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Изменить способ генерации",
            callback_data=json.dumps({'action': 'change_create_mode'})))
        await message.answer(SETTINGS_TEXT, reply_markup=kb)
        return

    elif text == HELP_BUTTON:
        await message.answer(HELP_MESSAGE, reply_markup=MAIN_KB)
        return

    if state == 0:
        if message.photo or link or message.document:
            name = get_filename()
            await message.answer("Скачиваю...", reply_markup=MAIN_KB)
            try:
                if link:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link) as resp:
                            if resp.status == 200:
                                f = await aiofiles.open(name, mode='wb')
                                await f.write(await resp.read())
                                await f.close()
                            else:
                                raise ValueError()
                else:
                    if message.photo:
                        await message.photo[-1].download(name)
                    else:
                        await message.document.download(name)
            except:
                await message.answer(LOAD_ERROR, reply_markup=MAIN_KB)
                return
            add_dem(name, user_id)
            if not text or link:
                kb = [
                    [
                        aiogram.types.KeyboardButton(text=RANDOM_TEXT)
                    ],
                    [
                        aiogram.types.KeyboardButton(text=BACK_TO_MENU)
                    ]
                ]
                kb = aiogram.types.ReplyKeyboardMarkup(
                    keyboard=kb,
                    resize_keyboard=True
                )
                await message.answer(WAITING_TEXT, reply_markup=kb)
                set_state(user_id, 1)
                return
            dem = get_temp_dem(user_id)
            await message.answer("Генерирую...", reply_markup=MAIN_KB)
            if user.create_mode == 0:
                Generator(text, dem.filename, dem.filename).generate()
            else:
                texts = text.split('\n')
                if len(texts) > 1:
                    text1, text2 = texts[0], texts[1]
                else:
                    text1, text2 = text, ""
                try:
                    Image.open(dem.filename).convert('RGB').save(dem.filename)
                    dem_ = demapi.Configure(
                        base_photo=open(dem.filename, 'rb').read(), explanation=text2,
                        title=text1, jpeg_quality=100)
                except:
                    await message.answer("Произошла ошибка, попробуйте другую картинку.",
                                         reply_markup=MAIN_KB)
                    return
                try:
                    with open(dem.filename, 'wb') as f:
                        (await dem_.coroutine_download()).save(dem.filename)
                except:
                    await message.answer("Произошла ошибка, попробуйте другую картинку.",
                                         reply_markup=MAIN_KB)
                    return
            set_dem_temp(dem.id, is_temp=False)
            await bot.send_photo(user_id, photo=open(dem.filename, 'rb'), caption="Готово!",
                                 reply_markup=DEM_CREATED_KB(dem.id))
        else:
            await message.answer(HELP_MESSAGE, reply_markup=MAIN_KB)

    elif state == 1:
        if not text or text == RANDOM_TEXT:
            text = random.choice(MESSAGES)
        dem = get_temp_dem(user_id)
        set_state(user_id, 0)
        if not dem:
            await message.answer(HELP_MESSAGE, reply_markup=MAIN_KB)
            return
        await message.answer("Генерирую...", reply_markup=MAIN_KB)
        if user.create_mode == 0:
            Generator(text, dem.filename, dem.filename).generate()
        else:
            texts = text.split('\n')
            if len(texts) > 1:
                text1, text2 = texts[0], texts[1]
            else:
                text1, text2 = text, ""
            try:
                Image.open(dem.filename).convert('RGB').save(dem.filename)
                dem_ = demapi.Configure(
                    base_photo=open(dem.filename, 'rb').read(), explanation=text2,
                    title=text1, jpeg_quality=100)
            except:
                await message.answer("Произошла ошибка, попробуйте другую картинку.",
                                     reply_markup=MAIN_KB)
                return
            try:
                with open(dem.filename, 'wb') as f:
                    (await dem_.coroutine_download()).save(dem.filename)
            except:
                await message.answer("Произошла ошибка, попробуйте другую картинку.",
                                     reply_markup=MAIN_KB)
                return
        set_dem_temp(dem.id, is_temp=False)
        await bot.send_photo(user_id, photo=open(dem.filename, 'rb'), caption="Готово!",
                             reply_markup=DEM_CREATED_KB(dem.id))

    elif state == 2:
        set_state(user_id, 0)
        try:
            friend_id = int(text)
        except:
            await message.answer("Вы прислали не число!", reply_markup=MAIN_KB)
            return
        friends = pickle.loads(user.friends)
        if friend_id not in friends:
            await message.answer("Пользователя нет в друзьях!",
                                 reply_markup=MAIN_KB)
            return
        user_dems = get_dems(friend_id, only_public=True)
        if not user_dems:
            await message.answer("У друга пока нет демотиваторов!",
                                 reply_markup=MAIN_KB)
            return
        dem = user_dems[0]
        kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Дальше",
            callback_data=json.dumps({'action': 'friend_next', 'value': 1,
                                      'friend_id': friend_id})))
        await bot.send_photo(user_id, photo=open(dem.filename, 'rb'),
                             reply_markup=kb)

    elif state == 3:
        set_state(user_id, 0)
        try:
            friend_id = int(text)
            if friend_id == user_id:
                await message.answer("Вы не можете добавить себя!",
                                     reply_markup=MAIN_KB)
                return
            await bot.send_message(friend_id, INVITATION(user_id),
                                   reply_markup=INV_KB(user_id))
            await message.answer("Запрос отправлен.", reply_markup=MAIN_KB)
        except:
            await message.answer("Запрос отправить не удалось!",
                                 reply_markup=MAIN_KB)


@dp.callback_query_handler()
async def on_callback(message):
    try:
        data = json.loads(message['data'])
        action = data['action']
    except:
        return
    user_id = message['from']['id']

    if action == 'make_private':
        is_private = data['value']
        dem_id = data['id']
        set_dem_privacy(dem_id, value=is_private)
        await message.answer('Готово!')

    elif action == 'change_create_mode':
        change_create_mode(user_id)
        await message.answer('Готово!')

    elif action == 'next':
        user_dems = get_dems(user_id)
        if not user_dems:
            await bot.send_message(user_id, "У вас пока нет демотиваторов!",
                                   reply_markup=MAIN_KB)
            return
        if data['value'] >= len(user_dems):
            await bot.send_message(user_id, "Вы дошли до конца!",
                                   reply_markup=MAIN_KB)
            return
        dem = user_dems[data['value']]
        kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        text = "Тип: приватный." if dem.is_private else "Тип: публичный."
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Дальше",
            callback_data=json.dumps({'action': 'next', 'value': data['value']+1})))
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Сделать приватным",
            callback_data=json.dumps({'action': 'make_private',
                                      'value': True, 'id': dem.id})),
               aiogram.types.InlineKeyboardButton(
            text="Сделать публичным",
            callback_data=json.dumps({'action': 'make_private',
                                      'value': False, 'id': dem.id}))
               )
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Удалить",
            callback_data=json.dumps({'action': 'delete_dem', 'id': dem.id})))
        await bot.send_photo(user_id, photo=open(dem.filename, 'rb'), caption=text,
                             reply_markup=kb)

    elif action == 'friend_next':
        friend_id = data['friend_id']
        user_dems = get_dems(friend_id, only_public=True)
        if not user_dems:
            await message.answer("У друга пока нет демотиваторов!",
                                 reply_markup=MAIN_KB)
            return
        if data['value'] >= len(user_dems):
            await bot.send_message(user_id, "Вы дошли до конца!",
                                   reply_markup=MAIN_KB)
            return
        dem = user_dems[data['value']]
        kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        kb.add(aiogram.types.InlineKeyboardButton(
            text="Дальше",
            callback_data=json.dumps({'action': 'friend_next', 'value': data['value']+1,
                                      'friend_id': friend_id})))
        await bot.send_photo(user_id, photo=open(dem.filename, 'rb'),
                             reply_markup=kb)

    elif action == 'add_friend':
        friend_id = data['id']
        add_friend(user_id, friend_id)
        add_friend(friend_id, user_id)
        await message.answer('Друг добавлен!')

    elif action == "delete_dem":
        dem_id = data['id']
        del_dem(dem_id)
        await message.answer('Демотиватор удалён!')
