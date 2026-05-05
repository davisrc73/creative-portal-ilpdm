from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import AssetType, EmotionalSentiment, Seasonality, TargetAudience

class AssetBase(BaseModel):
    filename: str
    file_path: str
    asset_type: AssetType
    cultural_context: Optional[str] = None
    social_copy: Optional[str] = None
    emotional_sentiment: Optional[EmotionalSentiment] = None
    seasonality: Optional[Seasonality] = None
    target_audience: Optional[TargetAudience] = None
    custom_tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    cultural_context: Optional[str] = None
    social_copy: Optional[str] = None
    emotional_sentiment: Optional[EmotionalSentiment] = None
    seasonality: Optional[Seasonality] = None
    target_audience: Optional[TargetAudience] = None
    custom_tags: Optional[List[str]] = None
    notes: Optional[str] = None

class AssetResponse(AssetBase):
    id: int
    file_size: Optional[int] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    ai_tags: List[str] = Field(default_factory=list)
    ai_description: Optional[str] = None
    social_copy: Optional[str] = None
    ai_analyzed: bool = False
    thumbnail_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    indexed_at: datetime

    class Config:
        from_attributes = True

class IndexingStatus(BaseModel):
    total_files_found: int
    new_assets_indexed: int
    existing_assets_skipped: int
    errors: List[str] = Field(default_factory=list)

class SearchQuery(BaseModel):
    query: str
    asset_type: Optional[AssetType] = None
    emotional_sentiment: Optional[EmotionalSentiment] = None
    seasonality: Optional[Seasonality] = None
    target_audience: Optional[TargetAudience] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    results: List[AssetResponse]
    total: int
    limit: int
    offset: int
