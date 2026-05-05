from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import assets, indexing

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ILPDM Digital Asset Management API",
    description="API for managing digital assets for the @ilovepauldomar community project",
    version="1.0.0"
)

# Esta linha cria a rota http://localhost:8000/media/ que aponta para a pasta TESTES
app.mount("/media", StaticFiles(directory="/nas_assets"), name="media")

origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)
app.include_router(indexing.router)

@app.get("/")
def root():
    return {
        "message": "ILPDM Digital Asset Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
