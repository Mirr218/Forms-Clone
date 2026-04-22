from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_router, forms_router, submissions_router
from app.core.config import api_config, cors_config
from app.db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title=api_config.title,
    description=api_config.description,
    version=api_config.version,
    contact={
        "name": api_config.contact_name,
        "email": str(api_config.contact_email),
        "url": str(api_config.contact_url),
    },
    lifespan=lifespan,
)

if cors_config.origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in cors_config.origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(forms_router)
app.include_router(submissions_router)


@app.get("/")
async def root():
    return {"message": f"{api_config.title} is running"}
