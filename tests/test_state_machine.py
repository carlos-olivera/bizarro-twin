from datetime import datetime, timezone
import types

import pytest

from src.modules.state_machine import InteractionStateMachine
import src.modules.state_machine as sm_mod


def make_tweet(attrs: dict):
    """Crea un objeto sencillo con atributos arbitrarios para pruebas."""
    return types.SimpleNamespace(**attrs)


def test_should_quote_high_engagement(monkeypatch):
    sm = InteractionStateMachine()
    tweet = make_tweet({"favorite_count": 3, "retweet_count": 0})
    monkeypatch.setattr(sm_mod.random, "random", lambda: 0.5)
    assert sm._should_quote(tweet) is True  # probabilidad 0.7, 0.5 < 0.7


def test_should_quote_low_engagement(monkeypatch):
    sm = InteractionStateMachine()
    tweet = make_tweet({"favorite_count": 1, "retweet_count": 1})
    monkeypatch.setattr(sm_mod.random, "random", lambda: 0.6)
    assert sm._should_quote(tweet) is False  # probabilidad 0.5, 0.6 >= 0.5


def test_should_quote_dict_metrics(monkeypatch):
    sm = InteractionStateMachine()
    tweet = {"like_count": 5, "repost_count": 0}
    monkeypatch.setattr(sm_mod.random, "random", lambda: 0.2)
    assert sm._should_quote(tweet) is True


def test_decide_action_priorities_host_first():
    sm = InteractionStateMachine()
    host = make_tweet({"id": "1", "text": "host tweet"})
    plan = sm.decide_action(host_tweet=host, mentions=[], allow_daily=False, current_time=datetime.now(timezone.utc))
    assert plan.action_type == "host"
    assert plan.target_tweet == host


def test_decide_action_daily_when_allowed():
    sm = InteractionStateMachine()
    now = datetime(2024, 1, 1, 21, 0, tzinfo=timezone.utc)
    plan = sm.decide_action(host_tweet=None, mentions=[], allow_daily=True, current_time=now)
    assert plan.action_type == "daily"
    assert plan.target_tweet is None


def test_decide_action_no_daily_after_limit():
    sm = InteractionStateMachine()
    now = datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc)
    plan = sm.decide_action(host_tweet=None, mentions=[], allow_daily=True, current_time=now)
    assert plan is None


def test_decide_action_mentions_when_no_host_or_daily():
    sm = InteractionStateMachine()
    mention = make_tweet({"id": "m1", "text": "hola"})
    now = datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc)
    plan = sm.decide_action(host_tweet=None, mentions=[mention], allow_daily=False, current_time=now)
    assert plan.action_type == "mention"
    assert plan.target_tweet == mention


def test_ignore_short_tweet_host():
    sm = InteractionStateMachine()
    host = make_tweet({"id": "1", "text": "muy corto"})
    plan = sm.decide_action(host_tweet=host, mentions=[], allow_daily=False, current_time=datetime.now(timezone.utc))
    assert plan is None


def test_ignore_media_short_text():
    sm = InteractionStateMachine()
    host = make_tweet({"id": "1", "text": "texto con media", "media": ["img"], "favorite_count": 10})
    plan = sm.decide_action(host_tweet=host, mentions=[], allow_daily=False, current_time=datetime.now(timezone.utc))
    assert plan is None
