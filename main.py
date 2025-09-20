from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Request, status
from sqlalchemy import text
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.api import contacts, utils, auth, users
from src.database.db import sessionmanager

scheduler = AsyncIOScheduler()


async def cleanup_expired_tokens():
    async with sessionmanager.session() as db:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        stmt = text(
            "DELETE FROM refresh_tokens WHERE expired_at < :now OR revoked_at IS NOT NULL AND revoked_at < :cutoff"
        )
        await db.execute(stmt, {"now": now, "cutoff": cutoff})
        await db.commit()
        print(f"Expired tokens cleaned up [{now.strftime('%Y-%m-%d %H:%M:%S')}]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(cleanup_expired_tokens, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Contacts Application",
    description="Contacts Application",
    version="v1.1",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
def read_root(request: Request):
    return {"message": "Contacts Application v1.1"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
