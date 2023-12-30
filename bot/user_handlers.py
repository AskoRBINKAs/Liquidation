from aiogram import types, F, Router
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from forms import RegistrationForm, GetKilled
import aiogram.utils.markdown as md
import pyqrcode
from urllib.parse import unquote
import aiohttp
import config
import texts


builder = ReplyKeyboardBuilder()
builder.row(
    types.KeyboardButton(text='Профиль'),
)
builder.row(
    types.KeyboardButton(text='Ликвидировать'),
    types.KeyboardButton(text="Список выживших")
)


async def start_handler(msg:Message,state:FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(config.API_URL+"/players/"+str(msg.from_user.id)+"/") as request:
            if request.status == 404:
                await msg.answer(texts.greetings_text_name_require)
                await state.set_state(RegistrationForm.name)
            else:
                await msg.answer(texts.greetings_text_on_return, reply_markup=builder.as_markup(resize_keyboard=True))


async def register_player(msg:Message,state:FSMContext):
    await msg.answer(texts.greetings_text_registration_success+f", {msg.text} !!!")
    await state.update_data(name=msg.text)
    async with aiohttp.ClientSession() as session:
        async with session.post(config.API_URL+"/players/",params={"name":msg.text,"tg_id":msg.from_user.id,"tg_tag":msg.from_user.username}) as request:
            if request.status != 200:
                await msg.answer(texts.error_default_message)
    await state.clear()


async def messages_handler(msg:Message, state:FSMContext):
    if msg.text.lower()=="профиль":
        await get_profile(msg,state)
    if msg.text.lower()=="ликвидировать":
        await get_victim_code(msg,state)
    if msg.text.lower()=="список выживших":
        await getAlives(msg,state)

async def get_victim_code(msg:Message,state:FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(config.API_URL+"/game/status/") as request:
            if request.status != 200:
                await msg.answer(texts.error_default_message)
            data = await request.json()
            if data['status'] == False:
                await msg.answer(texts.error_game_not_started)
                return
        async with session.get(config.API_URL+"/players/"+str(msg.from_user.id)+"/") as request:
            if request.status != 200:
                await msg.answer(texts.error_default_message)
                return
            data = await request.json()
            if data['is_alive'] == False:
                await msg.answer(texts.error_player_is_dead)
                return
            await msg.answer(texts.kill_require_qrcode)
            await state.set_state(GetKilled.player_id)

async def getAlives(msg:Message,state:FSMContext):
    async with aiohttp.ClientSession() as sesssion:
        async with sesssion.get(config.API_URL+f'/players/') as r:
            if r.status != 200:
                return
            d = await r.json()
            response = "Выжившие игроки:\n\n"
            counter = 0
            for i in d:
                if i['is_alive']:
                    counter += 1
                    response += i['name'] + '\n'
            response += f'\nВсего живых игроков: {counter}'
            print(response)
            await msg.answer(response)
async def try_to_kill(msg:Message,state:FSMContext):
     async with aiohttp.ClientSession() as session:
        async with session.get(config.API_URL+f"/game/kill/{msg.from_user.id}/{msg.text}/") as r:
            if r.status==404 or r.status==500:
                await msg.answer(texts.kill_failure,reply_markup=builder.as_markup(resize_keyboard=True))
                await state.clear()
            else:
                await state.update_data(player_id = msg.text)
                await msg.answer(texts.kill_success,reply_markup=builder.as_markup(resize_keyboard=True))
                await state.clear()


async def get_profile(msg:Message,state:FSMContext):
    async with aiohttp.ClientSession() as session:
        # async with session.get(config.API_URL+"/game/status/") as request:
        #     if request.status != 200:
        #         await msg.answer(texts.error_default_message)
        #     data = await request.json()
        #     if data['status'] == False:
        #         await msg.answer(texts.error_default_message)
        #         return
            
        async with session.get(config.API_URL+"/players/"+str(msg.from_user.id)+"/") as request:
            if request.status != 200:
                await msg.answer(texts.error_default_message)
                return
            
            data = await request.json()
            qr_code = pyqrcode.create(str(data['qr_code']))
            fname = str(msg.from_user.id)+".png"
            qr_code.png("qrcodes/"+fname,scale=6)
            response = "Данные об игроке: \n\n"
            response += "🏷️ Имя:  " + md.bold(data['name']) + '\n\n'
            response += "💥 Ликвидировано:  " + str(data['kills']) + '\n\n'
            response += "🎯 Цель:  " + (md.bold(data['victim']) if data['victim']!="none" else md.bold("Не объявлена")) + '\n\n'
            response += "⚠ Эксомьюникадо: " + ("Да" if data['is_excomunnicado'] else "Нет") + "\n\n"
            response += "🩸 Охотник: " + ("Да" if data['is_hunter'] else "Нет") + "\n\n"
            response += "🌐 Ваш код (такой же и в QR): " + '`'+str(data['qr_code']) + '`\n\n'
            if data['is_alive']:
                response += '🟢 Статус: в игре\n'
            else:
                response += '🔴 Статус: ликвидирован'
            await msg.answer_photo(FSInputFile("qrcodes/"+fname),caption=response)
