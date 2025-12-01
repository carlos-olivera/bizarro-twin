from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, DateTime, Float, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from src.core.database import Base

class SemanticMemory(Base):
    __tablename__ = "semantic_memory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector de 1536 dimensiones (Estándar DeepSeek/OpenAI)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536))
    
    # Metadatos flexibles para filtros (ej. autor, fecha original)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, server_default='{}')
    
    source_type: Mapped[str] = mapped_column(String(50)) # 'host_tweet', 'reflection', etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Memory(id={self.id}, source={self.source_type}, content='{self.content[:30]}...')>"


class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tweet_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50)) # 'tweet', 'reply', 'like'
    
    input_context: Mapped[Optional[str]] = mapped_column(Text)
    generated_content: Mapped[Optional[str]] = mapped_column(Text)
    
    # Snapshot del estado emocional al momento de la acción
    mood_state: Mapped[Dict[str, float]] = mapped_column(JSONB)
    
    # Métricas futuras (se actualizan 24h después)
    metrics_at_24h: Mapped[Dict[str, int]] = mapped_column(JSONB, server_default='{}')
    reward_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Action(id={self.id}, type={self.action_type}, reward={self.reward_score})>"


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    arousal: Mapped[float] = mapped_column(Float, nullable=False)
    
    stimulus_type: Mapped[str] = mapped_column(String(100)) # Qué causó el cambio
    description: Mapped[Optional[str]] = mapped_column(Text) # Descripción legible
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Mood(V={self.valence}, A={self.arousal}, stimulus={self.stimulus_type})>"