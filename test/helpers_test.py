import asyncio
import json
from types import SimpleNamespace

import pytest

import helpers
from helpers import NoBotMiddleware, Store


def run(coro):
    return asyncio.run(coro)


def test_store_dynamic_methods_get_data_and_clear():
    store = Store()
    store.add_username(42, "News Bot")
    store.add_text(42, "Story text")
    store.add_media(42, ["https://example.test/photo.jpg"])
    store.add_link(42, "https://vk.com/news")

    payload = json.loads(store.get_data(42))

    assert payload == {
        "user_id": "42",
        "username": "News Bot",
        "source": "vk",
        "text": "Story text",
        "media": ["https://example.test/photo.jpg"],
        "link": "https://vk.com/news",
    }

    store.clear(42)
    assert store.get_text(42) is None
    assert store.get_media(42) is None
    assert store.get_username(42) == "News Bot"


def test_store_rejects_unknown_dynamic_attribute():
    store = Store()

    with pytest.raises(AttributeError):
        store.unknown

    with pytest.raises(AttributeError):
        store.remove_text


def test_no_bot_middleware_allows_users_and_stops_bots():
    user_middleware = NoBotMiddleware(SimpleNamespace(from_id=1))
    run(user_middleware.pre())
    assert user_middleware.error is None

    bot_middleware = NoBotMiddleware(SimpleNamespace(from_id=-1))
    run(bot_middleware.pre())
    assert "from_id" in str(bot_middleware.error)


def test_send_data_publishes_feedback_to_configured_queue(monkeypatch):
    store = Store()
    store.add_username(77, "Queue User")
    store.add_text(77, "Queued text")
    store.add_media(77, ["photo"])
    store.add_link(77, "https://vk.com/queue")
    captured = {}

    class FakeChannel:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def queue_declare(self, **kwargs):
            captured["queue_declare"] = kwargs

        def basic_publish(self, **kwargs):
            captured["basic_publish"] = kwargs

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def channel(self):
            return FakeChannel()

    def fake_url_parameters(url):
        captured["url"] = url
        return f"params:{url}"

    def fake_blocking_connection(params):
        captured["params"] = params
        return FakeConnection()

    monkeypatch.setenv("rabbitmq", "amqp://guest:guest@localhost:5672/%2F")
    monkeypatch.setenv("QNAME", "feedback")
    monkeypatch.setattr(helpers.pika, "URLParameters", fake_url_parameters)
    monkeypatch.setattr(helpers.pika, "BlockingConnection", fake_blocking_connection)

    run(store.send_data(SimpleNamespace(peer_id=77)))

    assert captured["url"] == "amqp://guest:guest@localhost:5672/%2F"
    assert captured["params"] == "params:amqp://guest:guest@localhost:5672/%2F"
    assert captured["queue_declare"] == {
        "queue": "feedback",
        "auto_delete": False,
        "exclusive": False,
    }
    assert captured["basic_publish"]["exchange"] == ""
    assert captured["basic_publish"]["routing_key"] == "feedback"
    assert json.loads(captured["basic_publish"]["body"])["text"] == "Queued text"
