import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import src.modules.x_client as x_mod


class FakeQuoteTweetClient:
    def __init__(self, *args, **kwargs):
        self.called = None

    async def create_tweet(self, text, quote_tweet_id):
        self.called = ("quote_tweet_id", quote_tweet_id, text)
        return {"text": text}


class FakeQuoteClient:
    def __init__(self, *args, **kwargs):
        self.called = None

    async def create_tweet(self, text, quote):
        self.called = ("quote", quote, text)
        return {"text": text}


class FakeAttachmentClient:
    def __init__(self, *args, **kwargs):
        self.called = None

    async def create_tweet(self, text, attachment_url):
        self.called = ("attachment_url", attachment_url, text)
        return {"text": text}


class FakeReplyClient:
    def __init__(self, *args, **kwargs):
        self.called = None

    async def create_tweet(self, text, reply_to):
        self.called = ("reply_to", reply_to, text)
        return {"text": text}


class FakeReplyIdClient:
    def __init__(self, *args, **kwargs):
        self.called = None

    async def create_tweet(self, text, reply_to_tweet_id):
        self.called = ("reply_to_tweet_id", reply_to_tweet_id, text)
        return {"text": text}


@pytest.mark.asyncio
async def test_quote_prefers_quote_tweet_id(monkeypatch):
    monkeypatch.setattr(x_mod, "Client", FakeQuoteTweetClient)
    bot = x_mod.XClient()
    await bot._create_with_quote("hola", "123")
    assert bot.client.called == ("quote_tweet_id", "123", "hola")


@pytest.mark.asyncio
async def test_quote_fallback_to_quote(monkeypatch):
    monkeypatch.setattr(x_mod, "Client", FakeQuoteClient)
    bot = x_mod.XClient()
    await bot._create_with_quote("hola", "123")
    assert bot.client.called == ("quote", "123", "hola")


@pytest.mark.asyncio
async def test_quote_fallback_to_attachment_url(monkeypatch):
    monkeypatch.setattr(x_mod, "Client", FakeAttachmentClient)
    bot = x_mod.XClient()
    await bot._create_with_quote("hola", "123")
    assert bot.client.called[0] == "attachment_url"
    assert "123" in bot.client.called[1]


@pytest.mark.asyncio
async def test_reply_prefers_reply_to(monkeypatch):
    monkeypatch.setattr(x_mod, "Client", FakeReplyClient)
    bot = x_mod.XClient()
    await bot._create_with_reply("hola", "321")
    assert bot.client.called == ("reply_to", "321", "hola")


@pytest.mark.asyncio
async def test_reply_fallback_reply_to_tweet_id(monkeypatch):
    monkeypatch.setattr(x_mod, "Client", FakeReplyIdClient)
    bot = x_mod.XClient()
    await bot._create_with_reply("hola", "321")
    assert bot.client.called == ("reply_to_tweet_id", "321", "hola")
