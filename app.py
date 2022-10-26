import logging

from vkbottle import Keyboard, Text
from vkbottle.bot import Bot, Message

logging.getLogger("vkbottle").setLevel(logging.ERROR)
from helpers import ctx, NoBotMiddleware, MenuState
from settings import Setting
token = ""

bot = Bot(token)
bot.labeler.message_view.register_middleware(NoBotMiddleware)
settings = Setting()

async def clear_session(peer_id):
    """ для очистки сессии """
    try:
        ctx.clear(peer_id)
    except KeyError:
        pass
    await bot.state_dispenser.set(peer_id, MenuState.START)


async def start_handler(message: Message):
    await message.answer(settings.commands.text['message'])
    if message.text.lower() == settings.commands.text['cmd_start']:
        await text_handler(message)
    else:
        await bot.state_dispenser.set(message.peer_id, MenuState.START)
        await info_handler(message)

async def info_handler(message: Message):
    await message.answer(
        settings.commands.info['message'],
        keyboard=(
            Keyboard(inline=True)
            .add(Text(settings.commands.info['cmd_start'],
            {"cmd": "start"}))
            .get_json()
        ),
    )


async def text_handler(message: Message):
    await message.answer(
        settings.commands.text['message_1'],
    )
    await bot.state_dispenser.set(message.peer_id, MenuState.TEXT)


async def add_text_handler(message: Message):
    ctx.add_text(message.peer_id, message.text)
    await message.answer(
        settings.commands.text['message_2'],
        keyboard=(
            Keyboard(inline=True)
            .add(Text("отправить новость редакции", {"item": "send"})).row()
            .add(Text("Загрузить фото", {"item": "add_photo"}))
            .add(Text("Изменить текст", {"item": "text_change"}))
            .add(Text("Отменить новость", {"item": "undo"}))
            .get_json()
        ),
    )


async def swith_handler(message: Message):
    payload: dict = message.get_payload_json()  # type: ignore
    cmd = payload['item']
    if cmd == 'send':
        await bot.state_dispenser.set(message.peer_id, MenuState.FINISH)
        return await finish_handler(message)
    if cmd == 'add_photo':
        await message.answer(
           settings.commands.swith['add_photo'],
        )
        await bot.state_dispenser.set(message.peer_id, MenuState.MEDIA)
    elif cmd == 'text_change':
        return await text_handler(message)
    elif cmd == 'undo':
        await clear_session(message.peer_id)
        await bot.state_dispenser.set(message.peer_id, MenuState.START)
        await message.answer(settings.commands.swith['undo'])
        return await info_handler(message)


async def media_handler(message: Message):
    media = ctx.get_media(message.peer_id)
    try:
        assert len(message.attachments)
        # генерирем список из фото с ссылками
        photo_list = []
        for attachment in message.attachments:
            photo_list.append(attachment.photo.sizes[0].url)

        if media:
            # в случае если есть данные.
            photo_list += media
        ctx.add_media(message.peer_id, photo_list)

        await message.answer(settings.commands.media['message_1'])
        await message.answer(settings.commands.media['message_2'],
                             keyboard=Keyboard(inline=True)
                             .add(Text("Отправит", {"item": "send"})).row()
                             .add(Text("Загрузить ещё", {"item": "upload"}))
                             .add(Text("Отменить", {"item": "undo"}))
                             )
        await bot.state_dispenser.set(message.peer_id, MenuState.FINISH)
    except:
        return settings.commands.media['message_3']


async def finish_handler(message: Message):
    payload: dict = message.get_payload_json()  # type: ignore
    cmd = payload['item']
    if cmd == 'upload':
        await bot.state_dispenser.set(message.peer_id, MenuState.MEDIA)
        return settings.commands.finish['message_1']
    await ctx.send_data(message)
    await clear_session(message.peer_id)
    if cmd == 'send':
        text = settings.commands.finish['message_2']
    else:
        text = settings.commands.finish['message_3']
    await message.answer(text)
    await bot.state_dispenser.set(message.peer_id, MenuState.START)
    await info_handler(message)

# Init message
bot.on.private_message(state=None)(start_handler)
# For start create news
bot.on.private_message(state=MenuState.START, payload={"cmd": "start"})(text_handler)
# For wait start create news
bot.on.private_message(state=MenuState.START)(info_handler)
# Add media
bot.on.private_message(state=MenuState.MEDIA, )(media_handler)
# Route wait message send | add media | undo
bot.on.private_message(state=MenuState.TEXT, payload_map=[("item", str)])(swith_handler)
# Add text
bot.on.private_message(state=MenuState.TEXT)(add_text_handler)
# Route wait message send and reload
bot.on.private_message(state=MenuState.FINISH)(finish_handler)
bot.run_forever()
