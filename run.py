import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.memory import MemoryStorage
from motor.motor_asyncio import AsyncIOMotorClient

from config_reader import config
from handlers import common, tz_form_handler

async def main():

    # Настройка логирования
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Инициализация бота
    bot = Bot(token=config.bot_token.get_secret_value())

    # Инициализация клиента MongoDB и хранилища FSM с фолбэком на память
    mongo_client = None
    try:
        mongo_client = AsyncIOMotorClient(
            config.mongo_dsn.get_secret_value(),
            serverSelectionTimeoutMS=2000,
            socketTimeoutMS=2000,
            connectTimeoutMS=2000,
        )
        # Проверяем доступность Mongo
        await mongo_client.admin.command("ping")
        storage = MongoStorage(mongo_client, db_name="tz_bot_fsm_storage")
        logging.info("FSM storage: MongoDB")
    except Exception as e:
        logging.warning("MongoDB недоступна, переключаюсь на MemoryStorage: %s", e)
        if mongo_client:
            try:
                mongo_client.close()
            except Exception:
                pass
        mongo_client = None
        storage = MemoryStorage()

    # Инициализация Диспетчера
    dp = Dispatcher(storage=storage)

    # Подключение роутеров
    dp.include_router(common.common_router)
    dp.include_router(tz_form_handler.tz_router)

    # Перед запуском polling'а удаляем вебхук, если он был
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Бот запускается...")
    # Запуск polling'а
    try:
        await dp.start_polling(bot)
    finally:
        # Корректное закрытие сессии бота и клиента MongoDB (если есть)
        await bot.session.close()
        if mongo_client is not None:
            mongo_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")