import asyncio
from types import SimpleNamespace

import pytest

import app
from helpers import MenuState, Store


def run(coro):
    return asyncio.run(coro)


class FakeStateDispenser:
    def __init__(self):
        self.calls = []

    async def set(self, peer_id, state):
        self.calls.append((peer_id, state))


class FakeUsersApi:
    async def get(self, user_id, fields):
        assert fields == ["domain"]
        return [
            SimpleNamespace(
                domain=f"user{user_id}",
                first_name="Test",
                last_name="User",
            )
        ]


class FakeBot:
    def __init__(self):
        self.api = SimpleNamespace(users=FakeUsersApi())
        self.state_dispenser = FakeStateDispenser()


class FakeMessage:
    def __init__(self, peer_id=100, from_id=200, text="", payload=None, attachments=None):
        self.peer_id = peer_id
        self.from_id = from_id
        self.text = text
        self._payload = payload or {}
        self.attachments = attachments or []
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))

    def get_payload_json(self):
        return self._payload


class FakePhotoAttachment:
    def __init__(self, url):
        self.photo = SimpleNamespace(sizes=[SimpleNamespace(url=url)])


@pytest.fixture()
def fake_runtime(monkeypatch):
    fake_bot = FakeBot()
    store = Store()
    monkeypatch.setattr(app, "bot", fake_bot)
    monkeypatch.setattr(app, "ctx", store)
    return fake_bot, store


def test_start_handler_collects_user_and_prompts_info(fake_runtime):
    fake_bot, store = fake_runtime
    message = FakeMessage(peer_id=1, from_id=7, text="hello")

    run(app.start_handler(message))

    assert store.get_link(1) == "https://vk.com/user7"
    assert store.get_username(1) == "Test User"
    assert message.answers[0][0] == app.settings.commands.text["message"]
    assert message.answers[-1][0] == app.settings.commands.info["message"]
    assert fake_bot.state_dispenser.calls == [(1, MenuState.START)]


def test_start_handler_enters_text_state_for_start_command(fake_runtime):
    fake_bot, store = fake_runtime
    message = FakeMessage(peer_id=2, from_id=8, text=app.settings.commands.text["cmd_start"])

    run(app.start_handler(message))

    assert store.get_link(2) == "https://vk.com/user8"
    assert message.answers[-1][0] == app.settings.commands.text["message_1"]
    assert fake_bot.state_dispenser.calls == [(2, MenuState.TEXT)]


def test_add_text_handler_saves_text_and_returns_switch_keyboard(fake_runtime):
    _, store = fake_runtime
    message = FakeMessage(peer_id=3, text="Important news")

    run(app.add_text_handler(message))

    assert store.get_text(3) == "Important news"
    assert message.answers[0][0] == app.settings.commands.text["message_2"]
    assert "keyboard" in message.answers[0][1]


def test_switch_handler_routes_photo_change_and_undo(fake_runtime):
    fake_bot, store = fake_runtime
    store.add_text(4, "draft")
    store.add_media(4, ["old"])

    add_photo = FakeMessage(peer_id=4, payload={"item": "add_photo"})
    run(app.swith_handler(add_photo))
    assert add_photo.answers == [(app.settings.commands.swith["add_photo"], {})]
    assert fake_bot.state_dispenser.calls[-1] == (4, MenuState.MEDIA)

    text_change = FakeMessage(peer_id=4, payload={"item": "text_change"})
    run(app.swith_handler(text_change))
    assert text_change.answers == [(app.settings.commands.text["message_1"], {})]
    assert fake_bot.state_dispenser.calls[-1] == (4, MenuState.TEXT)

    undo = FakeMessage(peer_id=4, payload={"item": "undo"})
    run(app.swith_handler(undo))
    assert store.get_text(4) is None
    assert store.get_media(4) is None
    assert undo.answers[0][0] == app.settings.commands.swith["undo"]
    assert undo.answers[1][0] == app.settings.commands.info["message"]
    assert fake_bot.state_dispenser.calls[-2:] == [
        (4, MenuState.START),
        (4, MenuState.START),
    ]


def test_media_handler_saves_photos_and_handles_invalid_upload(fake_runtime):
    fake_bot, store = fake_runtime
    store.add_media(5, ["https://old.example/photo.jpg"])
    message = FakeMessage(
        peer_id=5,
        attachments=[FakePhotoAttachment("https://new.example/photo.jpg")],
    )

    assert run(app.media_handler(message)) is None

    assert store.get_media(5) == [
        "https://new.example/photo.jpg",
        "https://old.example/photo.jpg",
    ]
    assert message.answers[0][0] == app.settings.commands.media["message_1"]
    assert message.answers[1][0] == app.settings.commands.media["message_2"]
    assert fake_bot.state_dispenser.calls == [(5, MenuState.FINISH)]

    invalid = FakeMessage(peer_id=6)
    assert run(app.media_handler(invalid)) == app.settings.commands.media["message_3"]


def test_finish_handler_upload_send_and_cancel_paths(fake_runtime, monkeypatch):
    fake_bot, store = fake_runtime
    sent_peer_ids = []

    async def fake_send_data(message):
        sent_peer_ids.append(message.peer_id)

    monkeypatch.setattr(store, "send_data", fake_send_data)

    upload = FakeMessage(peer_id=7, payload={"item": "upload"})
    assert run(app.finish_handler(upload)) == app.settings.commands.finish["message_1"]
    assert fake_bot.state_dispenser.calls[-1] == (7, MenuState.MEDIA)
    assert sent_peer_ids == []

    store.add_text(8, "ready")
    store.add_media(8, ["photo"])
    send = FakeMessage(peer_id=8, payload={"item": "send"})
    run(app.finish_handler(send))
    assert sent_peer_ids == [8]
    assert store.get_text(8) is None
    assert store.get_media(8) is None
    assert send.answers[0][0] == app.settings.commands.finish["message_2"]
    assert send.answers[1][0] == app.settings.commands.info["message"]
    assert fake_bot.state_dispenser.calls[-2:] == [
        (8, MenuState.START),
        (8, MenuState.START),
    ]

    cancel = FakeMessage(peer_id=9, payload={"item": "cancel"})
    run(app.finish_handler(cancel))
    assert sent_peer_ids == [8, 9]
    assert cancel.answers[0][0] == app.settings.commands.finish["message_3"]


def test_clear_session_ignores_missing_context(fake_runtime, monkeypatch):
    fake_bot, store = fake_runtime

    def missing_clear(peer_id):
        raise KeyError(peer_id)

    monkeypatch.setattr(store, "clear", missing_clear)

    run(app.clear_session(10))

    assert fake_bot.state_dispenser.calls == [(10, MenuState.START)]
