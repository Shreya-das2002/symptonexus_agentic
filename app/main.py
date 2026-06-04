from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal
from app.routes.chat import router as chat_router
from app.routes.doctors import router as doctor_router


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doctor_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {
            "success": True,
            "app": settings.app_name,
            "environment": settings.app_env,
            "database": "connected",
            "ollama_model": settings.ollama_model,
        }
    finally:
        db.close()
