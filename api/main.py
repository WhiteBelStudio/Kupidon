from contextlib import asynccontextmanager
from pathlib import Path
from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import get_settings
from backend.database import Database
from api.routers import auth,profiles,search,social

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings=get_settings()
    db=Database(settings.database_path)
    await db.init()
    Path(settings.upload_dir).mkdir(parents=True,exist_ok=True)
    app.state.settings=settings
    app.state.db=db
    app.state.bot=Bot(settings.bot_token)
    yield
    await app.state.bot.session.close()

settings=get_settings()
app=FastAPI(title="КУПИДОН API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(auth.router,prefix="/api")
app.include_router(profiles.router,prefix="/api")
app.include_router(search.router,prefix="/api")
app.include_router(social.router,prefix="/api")
Path(settings.upload_dir).mkdir(parents=True,exist_ok=True)
app.mount("/media",StaticFiles(directory=settings.upload_dir),name="media")

@app.get("/health")
async def health():
    return {"status":"ok","version":"0.1.0"}

