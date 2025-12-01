from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, List, Optional
import random


@dataclass
class ActionPlan:
    action_type: str                     # 'host', 'mention', 'daily'
    target_tweet: Optional[Any] = None   # Objeto Twikit u otro contenedor con id/text
    should_quote: bool = False           # True = quote, False = reply/post
    reason: str = ""                     # Breve explicación para logs
    target_text: str = ""                # Texto base cuando no hay tweet origen (daily)


class InteractionStateMachine:
    """
    Encapsula reglas de interacción:
    - Responder al host cuando replica.
    - Daily post antes de las 22:00, 1 vez al día.
    - Responder menciones de otros usuarios con el mismo tono.
    - Preferir quote si el tweet tiene engagement (>2 likes o >2 RTs).
    """

    def decide_action(
        self,
        host_tweet: Optional[Any],
        mentions: List[Any],
        allow_daily: bool,
        current_time: datetime,
    ) -> Optional[ActionPlan]:
        """Devuelve un plan de acción o None si no hay nada que hacer."""

        # 1. Prioridad: Responder al host si hay tweet pendiente
        if host_tweet and not self._should_ignore(host_tweet):
            should_quote = self._should_quote(host_tweet)
            return ActionPlan(
                action_type="host",
                target_tweet=host_tweet,
                should_quote=should_quote,
                reason="Reply al host pendiente",
            )

        # 2. Daily post (solo antes de las 22:00)
        if allow_daily and current_time.time() < time(22, 0):
            return ActionPlan(
                action_type="daily",
                target_tweet=None,
                should_quote=False,
                reason="Publicación diaria antes de las 22:00",
                target_text="Genera una reflexión bizarra diaria sin tweet de referencia.",
            )

        # 3. Responder menciones (tono bizarro)
        if mentions:
            mention = mentions[0]  # Estrategia simple: primera mención pendiente
            if not self._should_ignore(mention):
                should_quote = self._should_quote(mention)
                return ActionPlan(
                    action_type="mention",
                    target_tweet=mention,
                    should_quote=should_quote,
                    reason="Responder mención pendiente",
                )

        # Nada que hacer
        return None

    def _should_ignore(self, tweet: Any) -> bool:
        """
        Reglas de descarte:
        - Texto muy corto (<40 caracteres).
        - Tiene media (imagen/video) y texto <150.
        """
        text = self._get_text(tweet)
        if len(text.strip()) < 40:
            return True
        if self._has_media(tweet) and len(text.strip()) < 150:
            return True
        return False

    def _should_quote(self, tweet: Any) -> bool:
        """
        Determina si es más probable hacer quote que reply basado en engagement.
        Si likes>2 o retweets>2 aumenta probabilidad de quote (70%).
        Si no, usa probabilidad base 50%.
        """
        likes = self._get_metric(tweet, ["favorite_count", "favourites_count", "like_count"])
        rts = self._get_metric(tweet, ["retweet_count", "repost_count"])

        high_engagement = (likes is not None and likes > 2) or (rts is not None and rts > 2)
        prob_quote = 0.7 if high_engagement else 0.5
        return random.random() < prob_quote

    @staticmethod
    def _get_metric(tweet: Any, possible_attrs: List[str]) -> Optional[int]:
        """Lee de forma segura una métrica de likes/RTs si existe."""
        for attr in possible_attrs:
            if hasattr(tweet, attr):
                try:
                    return int(getattr(tweet, attr))
                except (TypeError, ValueError):
                    continue
            # Si viene como dict
            if isinstance(tweet, dict) and attr in tweet:
                try:
                    return int(tweet[attr])
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _get_text(tweet: Any) -> str:
        """Extrae texto del tweet compatible con objeto o dict."""
        if tweet is None:
            return ""
        if hasattr(tweet, "text"):
            return getattr(tweet, "text", "") or ""
        if isinstance(tweet, dict):
            return str(tweet.get("text", ""))
        return str(tweet)

    @staticmethod
    def _has_media(tweet: Any) -> bool:
        """Detecta presencia de imágenes o video en atributos comunes."""
        media_fields = ["media", "photos", "photo", "video", "videos", "media_keys"]
        for field in media_fields:
            if hasattr(tweet, field):
                val = getattr(tweet, field, None)
                if val:
                    return True
            if isinstance(tweet, dict) and field in tweet and tweet[field]:
                return True
        return False


# Instancia global
state_machine = InteractionStateMachine()
