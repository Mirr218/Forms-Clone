from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import create_tables
from app.models import User, Form, Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Forms API",
    description="Clone of Yandex Forms",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Welcome to Forms API"}