import logging

from vkbottle import Keyboard, Text
from vkbottle.bot import Bot, Message

logging.getLogger("vkbottle").setLevel(logging.ERROR)
from helpers import ctx, NoBotMiddleware, MenuState

token = ""

bot = Bot(token)
bot.labeler.message_view.register_middleware(NoBotMiddleware)


async def clear_session(peer_id):
    """ для очистки сессии """
    try:
        ctx.clear(peer_id)
    except KeyError:
        pass
    await bot.state_dispenser.set(peer_id, MenuState.START)


async def log_handler(message: Message):
    data = await bot.state_dispenser.get(message.peer_id)
    await message.answer(f'state :{data}')


async def start_handler(message: Message):
    await message.answer(
        "Привет это стартовое меню.",
        keyboard=(
            Keyboard(inline=True)
            .add(Text("Создать заявку?", {"cmd": "start"}))
            .get_json()
        ),
    )
    await bot.state_dispenser.set(message.peer_id, MenuState.START)


async def info_handler(message: Message):
    await message.answer(
        "Ведите текст",
    )
    await bot.state_dispenser.set(message.peer_id, MenuState.TEXT)


async def add_text_handler(message: Message):
    ctx.add_text(message.peer_id, message.text)
    await message.answer(
        "Выберите из списка",
        keyboard=(
            Keyboard(inline=True)
            .add(Text("Отправит", {"item": "send"}))
            .add(Text("Загрузить фото", {"item": "add_photo"}))
            .add(Text("Отменить", {"item": "undo"}))
            .get_json()
        ),
    )
    await bot.state_dispenser.set(message.peer_id, MenuState.WAIT)


async def swith_handler(message: Message):
    payload: dict = message.get_payload_json()  # type: ignore
    cmd = payload['item']
    if cmd == 'send':
        await bot.state_dispenser.set(message.peer_id, MenuState.FINISH)
        return await finish_handler(message)
    if cmd == 'add_photo':
        await message.answer(
            "Загрузите изображения",
        )
        await bot.state_dispenser.set(message.peer_id, MenuState.MEDIA)
    elif cmd == 'undo':
        await clear_session(message.peer_id)
        await message.answer(
            "Успешно отменина",
            keyboard=(
                Keyboard(inline=False)
                .add(Text("Создать заявку?", {"cmd": "start"}))
                .get_json()
            ),
        )


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

        await message.answer('Успешно загруженно')
        await message.answer('Можете загрузить ещё или',
                             keyboard=Keyboard(inline=True)
                             .add(Text("Отправит", {"item": "send"}))
                             .add(Text("Загрузить ещё", {"item": "upload"}))
                             .add(Text("Отменить", {"item": "undo"}))
                             )
        await bot.state_dispenser.set(message.peer_id, MenuState.FINISH)
    except:
        return "Загружать нужно фото"


async def finish_handler(message: Message):
    payload: dict = message.get_payload_json()  # type: ignore
    cmd = payload['item']
    if cmd == 'upload':
        await bot.state_dispenser.set(message.peer_id, MenuState.MEDIA)
        return "Загрузите изображения"
    ctx.send_data(message)
    await clear_session(message.peer_id)
    await message.answer("Успешно исполнено",
                         keyboard=(
                             Keyboard(inline=True)
                             .add(Text("Создать заявку", {"cmd": "start"}))
                             .get_json()
                         ),
                         )


bot.on.private_message(blocking=False)(log_handler)
bot.on.private_message(state=None)(start_handler)
bot.on.private_message(state=MenuState.MEDIA, )(media_handler)
bot.on.private_message(state=MenuState.TEXT)(add_text_handler)
bot.on.private_message(state=MenuState.START, payload={"cmd": "start"})(info_handler)
bot.on.private_message(state=MenuState.WAIT, payload_map=[("item", str)])(swith_handler)
bot.on.private_message(state=MenuState.FINISH)(finish_handler)
bot.run_forever()
