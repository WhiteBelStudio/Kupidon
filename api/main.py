import asyncio
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.config import get_settings
from backend.database import Database
from api.routers import auth, profiles, search, social

VERSION = "0.4.3"

# Vercel's Python ASGI adapter may serve requests without running FastAPI's
# lifespan hooks. Keep the shared application state available at import time,
# then lazily initialize the database on the first request.
settings = get_settings()
db = Database(settings.database_url, settings.database_path)
init_lock = asyncio.Lock()
initialized = False


async def ensure_initialized() -> None:
    global initialized
    if initialized:
        return
    async with init_lock:
        if initialized:
            return
        await db.init()
        initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_initialized()
    yield
    await db.close()


app = FastAPI(title="КУПИДОН API", version=VERSION, lifespan=lifespan)

# Make state available even when the platform skips the lifespan event.
app.state.settings = settings
app.state.db = db
app.state.bot = Bot(settings.bot_token) if settings.bot_token else None


@app.middleware("http")
async def initialize_before_request(request: Request, call_next):
    await ensure_initialized()
    return await call_next(request)


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
