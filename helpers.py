from vkbottle import CtxStorage
from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle import BaseStateGroup


class Store(CtxStorage):
    """ Хронилище данных пользователя."""
    
    def token(self, v1, v2):
        return hash(hash(v1) + hash(v2))

    def get(self, name):
        def _func(peer_id, data):
            return self.get(self.token(peer_id, name), data)
        return _func

    def add(self, name):
        def _func(peer_id, data):
            self.set(self.token(peer_id, name), data)
        return _func

    def __getattr__(self, item):
        method, name = item.split("_")
        return geattr(self, method, None)

    def get_data(self, peer_id):
        return  {
            'text': self.get_text(peer_id),
            'media': self.get_media(peer_id)
                 }

    async def send_data(self, message: Message):
        data = self.get_data(message.peer_id)
        users_info = (await bot.api.users.get(message.from_id, fields = ['domain', ]))[0]
        url = "https://vk.com/{}".format(users_info.domain) if users_info.domain else ""

    def clear(self, peer_id):
        self.set_text(peer_id, None)
        self.set_media(peer_id, None)


class NoBotMiddleware(BaseMiddleware[Message]):
    "Отсеиваeм все сообщения от ботов:"
    async def pre(self):
        if self.event.from_id < 0:
            self.stop("from_id меньше 0")

class MenuState(BaseStateGroup):
    START = 1
    TEXT = 2
    WAIT = 3
    MEDIA = 4
    FINISH = 5

class InfoMiddleware(BaseMiddleware[Message]):
    async def post(self):
        if not self.handlers:
            self.stop("Сообщение не было обработано")

        await self.event.answer(
            "Сообщение было обработано:\n\n"
        )


ctx = Store()
