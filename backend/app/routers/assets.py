from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Asset, AssetType, EmotionalSentiment, Seasonality, TargetAudience
from app.schemas import AssetResponse, AssetUpdate, SearchQuery, SearchResponse
from app.services.ai_tagger import AITagger

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get("/", response_model=List[AssetResponse])
def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    asset_type: Optional[AssetType] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Asset)
    
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    
    assets = query.offset(skip).limit(limit).all()
    return assets

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully"}

@router.post("/{asset_id}/analyze")
async def analyze_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    tagger = AITagger()
    
    try:
        analysis = await tagger.analyze_asset(asset)
        
        asset.ai_tags = analysis.get("tags", [])
        asset.ai_description = analysis.get("description")
        asset.ai_analyzed = True

        if analysis.get("social_copy"):
            asset.social_copy = analysis["social_copy"]   
        
        if analysis.get("cultural_context"):
            asset.cultural_context = analysis["cultural_context"]

        if analysis.get("emotional_sentiment"):
            try:
                asset.emotional_sentiment = EmotionalSentiment(analysis["emotional_sentiment"])
            except ValueError:
                pass
        if analysis.get("seasonality"):
            try:
                asset.seasonality = Seasonality(analysis["seasonality"])
            except ValueError:
                pass
        if analysis.get("target_audience"):
            try:
                asset.target_audience = TargetAudience(analysis["target_audience"])
            except ValueError:
                pass
        
        db.commit()
        db.refresh(asset)
        
        return {
            "message": "Asset analyzed successfully",
            "analysis": analysis,
            "asset": asset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/search", response_model=SearchResponse)
def search_assets(search_query: SearchQuery, db: Session = Depends(get_db)):
    query = db.query(Asset)
    
    if search_query.asset_type:
        query = query.filter(Asset.asset_type == search_query.asset_type)
    
    if search_query.emotional_sentiment:
        query = query.filter(Asset.emotional_sentiment == search_query.emotional_sentiment)
    
    if search_query.seasonality:
        query = query.filter(Asset.seasonality == search_query.seasonality)
    
    if search_query.target_audience:
        query = query.filter(Asset.target_audience == search_query.target_audience)
    
    if search_query.query:
        search_term = f"%{search_query.query}%"
        query = query.filter(
            (Asset.filename.ilike(search_term)) |
            (Asset.cultural_context.ilike(search_term)) |
            (Asset.ai_description.ilike(search_term)) |
            (Asset.social_copy.ilike(search_term)) |
            (Asset.notes.ilike(search_term))
        )
    
    total = query.count()
    
    results = query.offset(search_query.offset).limit(search_query.limit).all()
    
    return SearchResponse(
        results=results,
        total=total,
        limit=search_query.limit,
        offset=search_query.offset
    )
