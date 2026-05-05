from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ilpdm_user:ilpdm_password@localhost:5432/ilpdm_dam"
    OPENROUTER_API_KEY: str = ""
    NAS_MOUNT_PATH: str = "/nas_assets"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    SUPPORTED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    SUPPORTED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff"]
    
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    VISION_MODEL: str = "google/gemini-2.5-flash"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
