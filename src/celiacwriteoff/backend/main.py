from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import db
import storage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.items import router as items_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    storage.ensure_storage_dirs()
    db.init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(items_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}