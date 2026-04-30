import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database import init_db
from init_db import create_default_admin, create_default_menus
from api import auth, users, dashboard, menus
from jobs.a_share_basic_sync import run_a_share_stock_basic_sync_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await create_default_admin()
    await create_default_menus()
    sync_task: asyncio.Task[None] | None = None
    if settings.a_share_basic_sync_enabled:
        sync_task = asyncio.create_task(
            run_a_share_stock_basic_sync_loop(
                settings.a_share_basic_sync_interval_seconds
            )
        )
    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                pass

app = FastAPI(
    title="Admin Dashboard API",
    description="Backend API for Admin Dashboard with user authentication and management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(menus.router)

@app.get("/")
async def root():
    return {"message": "Admin Dashboard API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
