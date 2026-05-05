from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.schemas import IndexingStatus
from app.services.file_indexer import FileIndexer

router = APIRouter(prefix="/indexing", tags=["indexing"])

@router.post("/scan", response_model=IndexingStatus)
def scan_nas_directory(
    directory: str = None,
    db: Session = Depends(get_db)
):
    indexer = FileIndexer(db)
    
    try:
        if directory:
            scan_path = Path(directory)
        else:
            scan_path = None
        
        results = indexer.scan_directory(scan_path)
        
        return IndexingStatus(**results)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/scan-async")
async def scan_nas_directory_async(
    background_tasks: BackgroundTasks,
    directory: str = None,
    db: Session = Depends(get_db)
):
    def run_scan():
        indexer = FileIndexer(db)
        try:
            if directory:
                scan_path = Path(directory)
            else:
                scan_path = None
            indexer.scan_directory(scan_path)
        except Exception as e:
            print(f"Background scan failed: {e}")
    
    background_tasks.add_task(run_scan)
    
    return {
        "message": "Indexing started in background",
        "directory": directory or "default NAS mount path"
    }

@router.post("/reindex/{asset_id}")
def reindex_asset(asset_id: int, db: Session = Depends(get_db)):
    indexer = FileIndexer(db)
    
    try:
        asset = indexer.reindex_asset(asset_id)
        return {
            "message": "Asset reindexed successfully",
            "asset": asset
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
