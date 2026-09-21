from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.config import get_settings
from backend.database import Database
from api.routers import auth, profiles, search, social

VERSION = "0.4.2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = Database(settings.database_url, settings.database_path)
    await db.init()
    app.state.settings = settings
    app.state.db = db

    # The API does not need a Telegram Bot instance for guest/browser mode.
    # Only create it when BOT_TOKEN is actually configured.
    app.state.bot = Bot(settings.bot_token) if settings.bot_token else None

    yield

    await db.close()
    if app.state.bot is not None:
        await app.state.bot.session.close()


settings = get_settings()
app = FastAPI(title="КУПИДОН API", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(social.router, prefix="/api")


@app.get("/media/{photo_path:path}", name="media")
async def media(photo_path: str):
    photo = await app.state.db.get_photo(photo_path)
    if not photo:
        return Response(status_code=404)
    return Response(
        content=bytes(photo["data"]),
        media_type=photo["content_type"],
    )


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": VERSION, "service": "kupidon-api"}
