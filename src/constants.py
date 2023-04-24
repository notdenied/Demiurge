import aiogram
import json
import re

MY_PICS = "Мои картинки"
FRIENDS_PICS = "Картинки друзей"
SETTINGS = "Настройки"
HELP_BUTTON = "Помощь"
ADD_FRIEND = "Добавить друга"
SHOW_PICTURES = "Посмотреть картинки друга"
BACK_TO_MENU = "Обратно в меню"

SYSTEM_TEXTS = set([MY_PICS, BACK_TO_MENU, FRIENDS_PICS, SHOW_PICTURES,
                    ADD_FRIEND, SETTINGS, HELP_BUTTON])

RANDOM_TEXT = "Случайная подпись"
SEE_FRIENDS_PICS = 'Тут вы можете добавить друга и посмотреть его работы.'
ERROR_OCCURRED = "Произошла ошибка, попробуйте другую картинку."


TEMPLATE_PATH = 'resources/template.png'
FONT = "resources/times.ttf"
FONT_SIZE = 45*2
SECOND_FONT_SIZE = 35*2
FIRST_TEXT_Y = 390*2
SECOND_TEXT_PADDING = 30
SECOND_TEXT_Y = FIRST_TEXT_Y + 55*2
PADDING = 10*2
FRAME_BOX = (2*75, 2*45, 2*499, 2*373)


with open('resources/texts.json', 'r') as f:
    data = json.loads(f.read())
    MESSAGES = data['MESSAGES']
    MAIN_MESSAGE = data['MAIN_MESSAGE']
    HELP_MESSAGE = data['HELP_MESSAGE']
    LOAD_ERROR = data['LOAD_ERROR']
    WAITING_TEXT = data['WAITING_TEXT']
    SETTINGS_TEXT = data['SETTINGS_TEXT']


URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+"
    "|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)"
    "|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

KB_ = [
    [
        aiogram.types.KeyboardButton(text=MY_PICS),
        aiogram.types.KeyboardButton(text=FRIENDS_PICS)
    ],
    [
        aiogram.types.KeyboardButton(text=SETTINGS),
        aiogram.types.KeyboardButton(text=HELP_BUTTON)
    ]
]

MAIN_KB = aiogram.types.ReplyKeyboardMarkup(
    keyboard=KB_,
    resize_keyboard=True,
    input_field_placeholder="Отправьте картинку или нажмите кнопку."
)


def DEM_CREATED_KB(dem_id):
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Сделать приватным",
        callback_data=json.dumps({'action': 'make_private',
                                  'value': True, 'id': dem_id})))
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Сделать публичным",
        callback_data=json.dumps({'action': 'make_private',
                                  'value': False, 'id': dem_id}))
           )
    return kb


def INVITATION(x):
    return f'Пользователь {x} хочет добавить вас в друзья.'


def INV_KB(user_id):
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Добавить",
        callback_data=json.dumps({'action': 'add_friend',
                                  'id': user_id})))
    return kb
