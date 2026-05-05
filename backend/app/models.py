from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Float, Boolean
from sqlalchemy.sql import func
from app.database import Base
import enum

class AssetType(str, enum.Enum):
    VIDEO = "video"
    IMAGE = "image"

class EmotionalSentiment(str, enum.Enum):
    NOSTALGIA = "nostalgia"
    RESILIENCE = "resilience"
    CALM = "calm"
    JOY = "joy"
    MELANCHOLY = "melancholy"

class Seasonality(str, enum.Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL_SEASONS = "all_seasons"

class TargetAudience(str, enum.Enum):
    DIASPORA = "diaspora"
    LOCAL_COMMUNITY = "local_community"
    GENERAL = "general"
    YOUTH = "youth"
    ELDERS = "elders"

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    file_size = Column(Integer)
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    cultural_context = Column(String, nullable=True)
    social_copy = Column(Text, nullable=True)
    emotional_sentiment = Column(Enum(EmotionalSentiment), nullable=True)
    seasonality = Column(Enum(Seasonality), nullable=True)
    target_audience = Column(Enum(TargetAudience), nullable=True)
    
    ai_tags = Column(JSON, default=list)
    ai_description = Column(Text, nullable=True)
    ai_analyzed = Column(Boolean, default=False)
    
    custom_tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    thumbnail_path = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Asset(id={self.id}, filename={self.filename}, type={self.asset_type})>"
