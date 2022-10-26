from vkbottle import CtxStorage
from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle import BaseStateGroup
from pydantic import BaseModel
from typing import Union

class FeedbackForm(BaseModel):
    user_id:str
    username:str = ''
    text:str
    source: str
    media: Union[list[str], None] = []
    link:str

class Store(CtxStorage):
    """ Хронилище данных пользователя."""
    
    def token(self, v1, v2):
        return hash(hash(v1) + hash(v2))

    def _get(self, name):
        """ Получает данные из хранилищя с помощью ключа"""
        def _func(peer_id):
            return self.get(self.token(peer_id, name))
        return _func

    def _add(self, name):
        def _func(peer_id, data):
            self.set(self.token(peer_id, name), data)
        return _func

    def __getattr__(self, item):
        """ 
        Реализация обертки вызовов для хранилищя с помощью
        формирования уникального ключа на 
        основе id и названия метода
        - add 
        - get
        > ctx.add_data(id, 12)

        > ctx.get_data(id)
        12
        """

        method, name = item.split("_")
        method = '_' + method
        return getattr(self, method, None)(name)

    def get_data(self, peer_id):
        data = {
                'user_id': peer_id,
                'username': self.get_username(peer_id),
                'source': 'vk',
                'text': self.get_text(peer_id),
                'media': self.get_media(peer_id),
                'link': self.get_link(peer_id),

        }
        return FeedbackForm(**data).json()

    async def send_data(self, message: Message):
        with pika.BlockingConnection(pika.URLParameters(self.rabbitmq)) as connection:
            with connection.channel() as channel:
                    # отправка данных в очередь
                    queue = os.getenv('QNAME', "form_push")
                    channel.queue_declare(queue=queue,
                                          auto_delete=False,
                                          exclusive=False)
                    channel.basic_publish(
                        exchange='',
                        body=self.get_data(message.peer_id),
                        routing_key=queue
                    )


    def clear(self, peer_id):
        self.add_text(peer_id, None)
        self.add_media(peer_id, None)


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

