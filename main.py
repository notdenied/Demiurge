from src.tg_bot import dp
from aiogram import executor

executor.start_polling(dp, skip_updates=False)
