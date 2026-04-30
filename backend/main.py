from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from init_db import create_default_admin, create_default_menus
from api import auth, users, dashboard, menus, stocks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await create_default_admin()
    await create_default_menus()
    try:
        yield
    finally:
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
app.include_router(stocks.router)

@app.get("/")
async def root():
    return {"message": "Admin Dashboard API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
