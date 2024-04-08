from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

head = "@Danil_Cataffs"
admins = ["m1i1ha", 'Viktoria_cataffs']
admin_ids = [1095610815, 6653984089]

TOKEN = "7059450347:AAFkpI7q1SAPPPjqXE738EfBhB0J7ByRJTs"
bot = Bot(token = TOKEN)
roles = ('Тимлид', 'Афф-менеджер', 'Кволити-менеджер')


storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)
dp.middleware.setup(LoggingMiddleware())