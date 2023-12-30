from aiogram import Bot, Dispatcher, F
import asyncio
import config
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import logging
from user_handlers import start_handler, register_player, messages_handler,try_to_kill
from forms import RegistrationForm, GetKilled


async def on_startup():
    pass

async def main():
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.message.register(start_handler,Command(commands='start'))
    dp.message.register(register_player,RegistrationForm.name)
    dp.message.register(try_to_kill,GetKilled.player_id)
    dp.message.register(messages_handler)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
