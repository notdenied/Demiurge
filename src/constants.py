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
RANDOM_TEXT = "Случайная подпись"


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

MAIN_MESSAGE = """Привет!

Этот бот позволяет генерировать демотиваторы из присланных тобой картинок.
Чтобы получить демотиватор, отправь картинку или ссылку на неё."""
HELP_MESSAGE = """Чтобы сгенерировать картинку, отправь её в этот чат. Ссылки также поддерживаются.
Другие команды ты можешь найти на клавиатуре."""
LOAD_ERROR = "Произошла ошибка при загрузке картинки, проверьте вложение и повторите попытку."
WAITING_TEXT = "Введите текст демотиватора (до двух строк):"
SETTINGS_TEXT = """Тут вы можете изменить настройки бота.

На данный момент можно выбрать один из двух способов генерации. Нажмите кнопку, чтобы поменять его."""


def INVITATION(x):
    return f'Пользователь {x} хочет добавить вас в друзья.'


def INV_KB(user_id):
    kb = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
    kb.add(aiogram.types.InlineKeyboardButton(
        text="Добавить",
        callback_data=json.dumps({'action': 'add_friend',
                                  'id': user_id})))
    return kb


TEMPLATE_PATH = 'src/template.png'
FONT = "src/times.ttf"
FONT_SIZE = 45*2
SECOND_FONT_SIZE = 35*2
FIRST_TEXT_Y = 390*2
SECOND_TEXT_PADDING = 30
SECOND_TEXT_Y = FIRST_TEXT_Y + 55*2
PADDING = 10*2
FRAME_BOX = (2*75, 2*45, 2*499, 2*373)


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


MESSAGES = ["Ситуация, знакомая многим.", "Ладно.", "Вставить текст",
            "Его идеи\nБудут актуальны всегда", "Его идеи\nПолная фигня",
            "Умные мысли часто преследуют его\nНо он быстрее.",
            "После этих слов\nВ украинском поезде начался сущий кошмар",
            "Жак Фреско про быдло", "Кошка Жака Фреско про быдло",
            "Жак Быдло про фрески",
            "Ахахахахахахаха\nЧё его так скосило?", "Инвалид он.\nТогда извиняюсь",
            "Гуси флиф флап", "Мыслант гигысли\nРусец отсосской кратодемии",
            "Кто?\nА ты не подглядывай!", "Она без хиджаба . . .",
            "Новонiколаiвка, милiция.",
            "Лее, куда прёшь, эээ?\nНе видишь, таджик идёт.",
            "Алло, ну как там\nс деньгами обстоит вопрос?", "Кiт, ты маму мав?\nМав",
            "Увидите такого в переулке – бегите.\nЭта тварь никого не пощадит!",
            "Сумасшедший\nОтбитый идиот", "Нет, спасибо, я не голодный",
            "А в чём прикол?\nЯ реально не шарю", "Ачё\nВсмысле",
            "Как его зовут?\nЕго не зовут, он сам приходит.",
            "Вот это мужик!\nА вы и дальше любите своих эмобоев, они же такие крутые!",
            "Шах и мат, либералы!!!", "Ооо\nЛибераху порвало", "Ошибка молодости",
            "Биба и Боба",
            "Такое мог придумать только русский человек\nУ других бы смекалочки не хватило!",
            "Вот тут пендосы явно обосрались...", "Роися вперде!",
            "Вместе с девочкой\nПлакала половина маршрутки!",
            "Смирись\nТы никогда не станешь настолько же крутым",
            "А пятый где?\nБез пятого не начнём.", "Поддержим?", "Жумайсынба.",
            "Остановите эту планету, я сойду",
            "Может хватит\nБухтеть и дестабилизировать ситуацию в стране?",
            "Че несёт этот сумасшедший?\nУвозим его, мужики!", "Ты как из палаты выбрался?",
            "Он в своём познании\nнастолько преисполнился...", "Либералы, вы довольны?",
            "Ммм, вкус детства", "Узнал\nСогласен", " Советы бывалых",
            "Детство без интернета.", "Школоте не понять\nвсю эпичность этого фото.",
            "Уважаю.", "Хохла спросить забыли.", "Где мы свернули не туда?",
            "Повезло повезло.", "Ломай, ломай\nМы же миллионеры, ещё купим.", "Суета...",
            "чин чан чон чи чича чочи\nчинчазанжи удын тан тун фуама агычи чина чан чон.",
            "Как вы думаете, он реально умер\nИли просто хайпит на своей смерти?",
            "И это главное достижение укропов?",
            "Он ещё мало изучен\nПотому что от него получают больше люлей, чем информации.",
            "У профессионалов\nесть стандарты.",
            "Гении\nзачастую становятся отвергнутыми обществом.", 'Ну и в чём он неправ?',
            'Назови их всех.\nДокажи, что у тебя нет личной жизни.',
            'Казалось бы,\nпричём тут Украина?',
            'В мире много языков,\nно этот парень выбрал язык фактов.',
            'Что не так с этим обществом?', 'Мужики,\nнеужели вам сложно быть такими же?',
            'Добрый чел.\nПозитивный.', 'Злой чел.\nНегативный.', 'Виктор Корнеплод.',
            'Гигант мысли,\nотец русской демократии.',
            'Как мы и предполагали,\nдогадки оказались правдивы.', 'Есть только два гендера.',
            'Умные мысли\nвообще не преследуют его.',
            'Умные мысли часто преследуют его\nи наконец-то догнали!', 'Смешно.\nСмеëмся.',
            'Не смешно.\nНе смеëмся.', 'Индифферентно.\nВ полной мере.', 'Здоровья погибшим.',
            'О Мультивселенной\nмало что известно.', 'А говорили,\nЕГЭ не будет сложным.',
            'Хочется стереть себе память\nи забыть эту парашу.',
            'Наврядли ты так сможешь.\nДа оно тебе и не надо, сигареты и ВКонтакте — вся твоя жизнь.',
            'Literally 1984.', 'По таким сюжетам снимают фильмы,\nно не выпускают.',
            'ДАВАЙ!! ДАВАААЙ УРААА\nДАВААЙ ДАААВАААЙ', 'СТОЙ!! СТОООЙ НЕЕЕТ\nНЕ НАДО ХВАТИТ',
            'Поколение не потеряно.\nГордимся!', 'Миллионы лет эволюции...\nНа кой чëрт?',
            'Его боялись даже...\nДа даже я боюсь.', 'Выводы делайте сами...',
            'Их боялись даже чеченцы!\nСамая отмороженная ОПГ за всю историю России.',
            'Этого мобилизуем.', 'Призывается в первую очередь.',
            'Ты бездушная скотина,\nЕсли не плакал на этом моменте..']