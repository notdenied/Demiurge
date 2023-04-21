# Demiurge

Telegram-бот для создания и распространения демотиваторов.

Настройка и установка:

Склонируйте репозиторий:

```git clone git@github.com:notdenied/Demiurge.git
cd Demiurge
git checkout dev
```

- Установите MySQL (точнее, её fork - MariaDB):

```sudo apt update
sudo apt install mariadb-server
sudo mysql_secure_installation
```

- Пройдите процедуру установки БД: в частности, установите пароль для пользователя (по умолчанию ```root```) и укажите его в файле ```src/settings.py```.
По умолчанию используется пароль ```P@$$w0rd```.

- Установите Python 3.9 (!) и необходимые зависимости:

```sudo apt install python3.9
pip3 install -r requirements.txt
```

Запуск:

```python3 main.py```

Функционал:

- Cоздание демотиваторов из картинок пользоватей со случайной или заданной подписью (одна или две строки).
- Работа с БД, в частности, ведение статистики по созданным демотиваторам, хранение друзей, картинок и пр.
- Возможность добавлять пользователей в друзья и смотреть их публичные картинки.
- Базовые настройки (выбор способа генерации).
- Интеграция с <https://www.imgonline.com.ua/demotivational-poster.php>.
- Получение картинок по ссылке.
- Сохранение всех сгенерированных демотиваторов, разделение на публичные и приватные.

Иерархия проекта:

- ```screenshots``` - скриншоты проекта.
- ```src/tg_bot.py``` - приложение (бот).
- ```src/database.py``` - схема БД.
- ```src/settings.py``` - настройки проекта.
- ```src/generator.py``` - реализация генератора картинок.
- ```src/constants.py``` - константы проекта.

Ниже представлены несколько скриншотов работы проекта.

![Screen 1](images/screenshots/1.png "Шифрование с помощью Шифра Цезаря.")
![Screen 2](images/screenshots/2.png "Декодирование при помощи различных методов анализа.")
![Screen 3](images/screenshots/3.png "Декодирование при помощи различных методов анализа 2.")
![Screen 4](images/screenshots/4.png "Vernam Encoding.")
![Screen 5](images/screenshots/5.png "Vernam Decoding.")
![Screen 6](images/screenshots/6.png "Steganography Example: Encoding.")
![Screen 7](images/screenshots/7.png "Steganography Example: Decoding.")
