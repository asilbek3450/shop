import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings
from redis.asyncio import Redis

from telegrambot.handlers.common import router


logger = logging.getLogger(__name__)


async def start_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not configured.")

    # Storage configuration
    redis_url = getattr(settings, "REDIS_URL", None)
    if redis_url:
        logger.info("Using RedisStorage for FSM")
        storage = RedisStorage(Redis.from_url(redis_url))
    else:
        logger.info("Using MemoryStorage for FSM")
        storage = MemoryStorage()

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)

    logger.info("Starting Telegram bot polling")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def run_bot():
    asyncio.run(start_bot())
