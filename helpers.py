from vkbottle import CtxStorage
from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle import BaseStateGroup


class Store(CtxStorage):
    def token(self, v1, v2):
        return hash(hash(v1) + hash(v2))

    def get_text(self, peer_id):
        return self.get(self.token(peer_id,'text'))

    def get_media(self, peer_id):
        return self.get(self.token(peer_id,'media'))

    def add_text(self, peer_id, data):
        self.set(self.token(peer_id, 'text'), data)

    def add_media(self, peer_id, data):
        self.set(self.token(peer_id, 'media'), data)

    def get_data(self, peer_id):
        return  {
            'text': self.get(self.token(peer_id, 'text')),
            'media': self.get(self.token(peer_id, 'media'))
                 }

    async def send_data(self, message: Message):
        data = self.get_data(message.peer_id)

    def clear(self, peer_id):
        self.set(self.token(peer_id, 'text'), None)
        self.set(self.token(peer_id, 'media'), None)



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




ctx = Store()
