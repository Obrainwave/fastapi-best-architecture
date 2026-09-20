import os

from app.routers.api import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.helpers import app_exception_handler

IS_PROD = settings.APP_ENV == "production"

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if not IS_PROD else None,
    redoc_url="/redoc" if not IS_PROD else None,
    openapi_url="/openapi.json" if not IS_PROD else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

os.makedirs("storage/uploads/logos", exist_ok=True)
app.mount("/storage/uploads", StaticFiles(directory="storage"), name="storage")

app.add_exception_handler(
    AppException,
    app_exception_handler,
)