from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from app.api.routes import leads, managers
from app.bot.dispatcher import create_bot, create_dispatcher
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal

settings = get_settings()
bot = create_bot()
dispatcher = create_dispatcher()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await bot.session.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router, prefix="/api", tags=["leads"])
app.include_router(managers.router, prefix="/api", tags=["managers"])


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": settings.app_name})


@app.head("/")
async def root_head() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.head("/health")
async def health_head() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@app.get("/health/db")
async def health_db() -> dict[str, str]:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> dict[str, bool]:
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret and secret != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram secret",
        )
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}
