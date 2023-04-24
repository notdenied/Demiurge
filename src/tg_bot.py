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


class ContextGlobals:
    """
    Internal class for "unpacking" messages.
    """

    def __init__(self, message: aiogram.types.Message) -> None:
        self.user_id: int = message['from']['id']
        self.user: User = get_user(self.user_id)
        if not self.user:
            register_user(self.user_id)
            self.user: User = get_user(self.user_id)
        self.state: int = self.user.state
        self.text: str = message.text
        self.message: aiogram.types.Message = message
        if not self.text:
            try:
                self.text: str = message.caption
            except:
                pass
        self.link: str = get_link(self.text if self.text else "")


def register_user(id) -> None:
    with Session(engine) as session:
        session.add(User(id=id))
        session.commit()


def get_user(id) -> User:
    with Session(engine) as session:
        res = select(User).where(User.id == id)
        user = session.scalars(res).one_or_none()
    return user


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
            Demotivator.user_id == user_id).where(Demotivator.is_temp
                                                  == True)
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
            Demotivator.id == dem_id).where(Demotivator.is_temp
                                            == True)
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
                Demotivator.user_id == user_id).where(Demotivator.is_temp
                                                      == False) \
                .where(Demotivator.is_private == False).order_by(Demotivator.id)
        else:
            res = select(Demotivator).where(
                Demotivator.user_id == user_id).where(Demotivator.is_temp
                                                      == False) \
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
    name = f'images/{prefix}_{int(time.time())}'
    name += f'_{random.getrandbits(32)}{extension}'
    if is_upper:
        name = '../' + name
    return name


bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(text=MY_PICS)
async def my_pics(message):
    gl = ContextGlobals(message)
    user_dems = get_dems(gl.user_id)
    if not user_dems:
        await message.answer("У вас пока нет демотиваторов!",
                             reply_markup=MAIN_KB)
        return
    await message.answer("Загрузка...",
                         reply_markup=MAIN_KB)
    dem = user_dems[0]
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    gl.text = "Тип: приватный." if dem.is_private else "Тип: публичный."
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
    await bot.send_photo(gl.user_id, photo=open(dem.filename, 'rb'),
                         caption=gl.text, reply_markup=kb)


@dp.message_handler(text=BACK_TO_MENU)
async def back_to_menu(message):
    gl = ContextGlobals(message)
    set_state(gl.user_id, 0)
    await message.answer("Вы в главном меню.",
                         reply_markup=MAIN_KB)


@dp.message_handler(text=FRIENDS_PICS)
async def friends_pics(message):
    kb = [
        [aiogram.types.KeyboardButton(text=ADD_FRIEND),
         aiogram.types.KeyboardButton(text=SHOW_PICTURES)],
        [aiogram.types.KeyboardButton(text=BACK_TO_MENU)]
    ]
    kb = aiogram.types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Отправьте картинку или нажмите кнопку."
    )
    await message.answer(SEE_FRIENDS_PICS,
                         reply_markup=kb)


@dp.message_handler(text=SHOW_PICTURES)
async def show_pictures(message):
    gl = ContextGlobals(message)
    set_state(gl.user_id, 2)
    kb = [
        [aiogram.types.KeyboardButton(text=BACK_TO_MENU)]
    ]
    kb = aiogram.types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    frds = pickle.loads(gl.user.friends)
    if frds:
        friends = "\n\nВаши друзья:\n" + \
            '\n'.join(f'`{i}`' for i in frds)
    else:
        friends = ''
    await message.answer('Введите ID друга.'+friends,
                         reply_markup=kb, parse_mode="Markdown")


@dp.message_handler(text=ADD_FRIEND)
async def add_friend_handler(message):
    gl = ContextGlobals(message)
    set_state(gl.user_id, 3)
    kb = [
        [aiogram.types.KeyboardButton(text=BACK_TO_MENU)]
    ]
    kb = aiogram.types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    await message.answer('Введите ID друга:', reply_markup=kb)


@dp.message_handler(text=SETTINGS)
async def settings(message):
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Изменить способ генерации",
        callback_data=json.dumps({'action': 'change_create_mode'})))
    await message.answer(SETTINGS_TEXT, reply_markup=kb)
    return


@dp.message_handler(text=HELP_BUTTON)
async def on_message(message):
    await message.answer(HELP_MESSAGE, reply_markup=MAIN_KB)


async def create_dem(gl, text):
    dem = get_temp_dem(gl.user_id)
    await gl.message.answer("Генерирую...", reply_markup=MAIN_KB)
    if gl.user.create_mode == 0:
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
                base_photo=open(dem.filename, 'rb').read(),
                explanation=text2, title=text1, jpeg_quality=100)
        except:
            await gl.message.answer(ERROR_OCCURRED,
                                    reply_markup=MAIN_KB)
            return
        try:
            (await dem_.coroutine_download()).save(dem.filename)
        except:
            await gl.message.answer(ERROR_OCCURRED,
                                    reply_markup=MAIN_KB)
            return
    set_dem_temp(dem.id, is_temp=False)
    await bot.send_photo(gl.user_id, photo=open(dem.filename, 'rb'),
                         caption="Готово!",
                         reply_markup=DEM_CREATED_KB(dem.id))


async def handle_default(gl):
    if gl.message.photo or gl.link or gl.message.document:
        name = get_filename()
        await gl.message.answer("Скачиваю...", reply_markup=MAIN_KB)
        try:
            if gl.link:
                async with aiohttp.ClientSession() as session:
                    async with session.get(gl.link) as resp:
                        f = await aiofiles.open(name, mode='wb')
                        await f.write(await resp.read())
                        await f.close()
            else:
                if gl.message.photo:
                    await gl.message.photo[-1].download(name)
                else:
                    await gl.message.document.download(name)
        except:
            await gl.message.answer(LOAD_ERROR, reply_markup=MAIN_KB)
            return
        add_dem(name, gl.user_id)
        if not gl.text or gl.link:
            kb = [
                [aiogram.types.KeyboardButton(text=RANDOM_TEXT)],
                [aiogram.types.KeyboardButton(text=BACK_TO_MENU)]
            ]
            kb = aiogram.types.ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True
            )
            await gl.message.answer(WAITING_TEXT, reply_markup=kb)
            set_state(gl.user_id, 1)
            return
        else:
            await create_dem(gl, gl.text)
    else:
        await gl.message.answer(MAIN_MESSAGE, reply_markup=MAIN_KB)


async def send_invitation(gl):
    try:
        friend_id = int(gl.text)
        if friend_id == gl.user_id:
            await gl.message.answer("Вы не можете добавить себя!",
                                    reply_markup=MAIN_KB)
            return
        await bot.send_message(friend_id, INVITATION(gl.user_id),
                               reply_markup=INV_KB(gl.user_id))
        await gl.message.answer("Запрос отправлен.",
                                reply_markup=MAIN_KB)
    except:
        await gl.message.answer("Запрос отправить не удалось!",
                                reply_markup=MAIN_KB)


async def start_watching_dems(gl):
    try:
        friend_id = int(gl.text)
    except:
        await gl.message.answer("Вы прислали не число!",
                                reply_markup=MAIN_KB)
        return
    friends = pickle.loads(gl.user.friends)
    if friend_id not in friends:
        await gl.message.answer("Пользователя нет в друзьях!",
                                reply_markup=MAIN_KB)
        return
    user_dems = get_dems(friend_id, only_public=True)
    if not user_dems:
        await gl.message.answer("У друга пока нет демотиваторов!",
                                reply_markup=MAIN_KB)
        return
    dem = user_dems[0]
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Дальше",
        callback_data=json.dumps({'action': 'friend_next', 'value': 1,
                                  'friend_id': friend_id})))
    await bot.send_photo(gl.user_id, photo=open(dem.filename, 'rb'),
                         reply_markup=kb)


'''
States:
0 - default
1 - waiting for text
2 - waiting for friend id
3 - waiting for adding friend
'''


@dp.message_handler(content_types=['document', 'photo'])
@dp.message_handler()
async def states_handler(message):
    gl = ContextGlobals(message)

    if gl.text in SYSTEM_TEXTS:
        return

    if gl.state == 0:
        await handle_default(gl)

    elif gl.state == 1:
        set_state(gl.user_id, 0)
        if not gl.text or gl.text == RANDOM_TEXT:
            gl.text = random.choice(MESSAGES)
        await create_dem(gl, gl.text)

    elif gl.state == 2:
        set_state(gl.user_id, 0)
        await start_watching_dems(gl)

    elif gl.state == 3:
        set_state(gl.user_id, 0)
        await send_invitation(gl)


async def send_next_dem(user_id, data):
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
        callback_data=json.dumps({'action': 'next', 'value':
                                  data['value']+1})))
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Сделать приватным",
        callback_data=json.dumps({'action': 'make_private',
                                  'value': True, 'id': dem.id})),
           aiogram.types.InlineKeyboardButton(
        text="Сделать публичным",
        callback_data=json.dumps({'action': 'make_private',
                                  'value': False, 'id': dem.id})))
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Удалить",
        callback_data=json.dumps({'action': 'delete_dem', 'id':
                                  dem.id})))
    await bot.send_photo(user_id, photo=open(dem.filename, 'rb'),
                         caption=text, reply_markup=kb)


async def send_next_friend_dem(message, data, user_id):
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
        callback_data=json.dumps({'action': 'friend_next', 'value':
                                  data['value']+1, 'friend_id':
                                  friend_id})))
    await bot.send_photo(user_id, photo=open(dem.filename, 'rb'),
                         reply_markup=kb)


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
        await send_next_dem(user_id, data)

    elif action == 'friend_next':
        await send_next_friend_dem(message, data, user_id)

    elif action == 'add_friend':
        friend_id = data['id']
        add_friend(user_id, friend_id)
        add_friend(friend_id, user_id)
        await message.answer('Друг добавлен!')

    elif action == "delete_dem":
        dem_id = data['id']
        del_dem(dem_id)
        await message.answer('Демотиватор удалён!')
