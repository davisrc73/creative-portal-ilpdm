import os
import cv2
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.models import Asset, AssetType
from app.config import settings

class FileIndexer:
    def __init__(self, db: Session):
        self.db = db
        self.nas_path = Path(settings.NAS_MOUNT_PATH)
        self.supported_extensions = (
            settings.SUPPORTED_VIDEO_EXTENSIONS + 
            settings.SUPPORTED_IMAGE_EXTENSIONS
        )
        # Garante que a pasta de thumbnails existe no NAS
        self.thumb_dir = self.nas_path / "thumbnails"
        self.thumb_dir.mkdir(exist_ok=True)

    def scan_directory(self, directory: Path = None) -> Dict[str, any]:
        if directory is None:
            directory = self.nas_path
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        results = {
            "total_files_found": 0,
            "new_assets_indexed": 0,
            "existing_assets_skipped": 0,
            "errors": []
        }
        
        for file_path in self._walk_directory(directory):
            results["total_files_found"] += 1
            
            try:
                if self._is_asset_indexed(str(file_path)):
                    results["existing_assets_skipped"] += 1
                    continue
                
                asset = self._create_asset_from_file(file_path)
                if asset:
                    self.db.add(asset)
                    self.db.commit()
                    results["new_assets_indexed"] += 1
            except Exception as e:
                self.db.rollback()
                error_msg = f"Error indexing {file_path}: {str(e)}"
                results["errors"].append(error_msg)
                print(error_msg)
        
        return results

    def _walk_directory(self, directory: Path):
        for root, dirs, files in os.walk(directory):
            # Ignora a própria pasta de thumbnails para não indexar as miniaturas
            if "thumbnails" in root:
                continue
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_extensions:
                    yield file_path

    def _is_asset_indexed(self, file_path: str) -> bool:
        return self.db.query(Asset).filter(Asset.file_path == file_path).first() is not None

    def _generate_video_thumbnail(self, video_path: Path) -> Optional[str]:
        """Extrai um frame do vídeo para usar como miniatura usando OpenCV."""
        thumb_name = f"{video_path.stem}_thumb.jpg"
        thumb_path = self.thumb_dir / thumb_name
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            # Tenta capturar o frame no segundo 1 para evitar ecrãs pretos no início
            cap.set(cv2.CAP_PROP_POS_MSEC, 1000) 
            success, frame = cap.read()
            
            if success:
                # Redimensiona para manter a miniatura leve
                height, width = frame.shape[:2]
                max_size = 640
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                cv2.imwrite(str(thumb_path), resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                cap.release()
                return str(thumb_path)
            
            cap.release()
        except Exception as e:
            print(f"Failed to generate thumbnail for {video_path}: {e}")
        
        return None

    def _create_asset_from_file(self, file_path: Path) -> Asset:
        file_extension = file_path.suffix.lower()
        
        if file_extension in settings.SUPPORTED_VIDEO_EXTENSIONS:
            asset_type = AssetType.VIDEO
        elif file_extension in settings.SUPPORTED_IMAGE_EXTENSIONS:
            asset_type = AssetType.IMAGE
        else:
            return None
        
        file_size = file_path.stat().st_size
        
        asset = Asset(
            filename=file_path.name,
            file_path=str(file_path),
            asset_type=asset_type,
            file_size=file_size
        )
        
        if asset_type == AssetType.IMAGE:
            try:
                with Image.open(file_path) as img:
                    asset.width, asset.height = img.size
            except Exception as e:
                print(f"Could not read image dimensions for {file_path}: {e}")
        
        elif asset_type == AssetType.VIDEO:
            try:
                # Gera miniatura e extrai metadados do vídeo
                asset.thumbnail_path = self._generate_video_thumbnail(file_path)
                
                cap = cv2.VideoCapture(str(file_path))
                if cap.isOpened():
                    asset.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    asset.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if fps > 0:
                        asset.duration = frame_count / fps
                cap.release()
            except Exception as e:
                print(f"Could not read video metadata for {file_path}: {e}")
        
        return asset

    def reindex_asset(self, asset_id: int) -> Asset:
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset with id {asset_id} not found")
        
        file_path = Path(asset.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        asset.file_size = file_path.stat().st_size
        
        if asset.asset_type == AssetType.IMAGE:
            try:
                with Image.open(file_path) as img:
                    asset.width, asset.height = img.size
            except Exception as e:
                print(f"Could not read image dimensions: {e}")
        
        elif asset.asset_type == AssetType.VIDEO:
            asset.thumbnail_path = self._generate_video_thumbnail(file_path)

        self.db.commit()
        self.db.refresh(asset)
        return asset