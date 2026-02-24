from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    start_scheduler()
    yield
    # 关闭时
    stop_scheduler()


app = FastAPI(title="Stock Trade API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Stock Trade API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
