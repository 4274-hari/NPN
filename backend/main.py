from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import close_mongo_connection, connect_to_mongo, get_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    close_mongo_connection()


app = FastAPI(title="NPN Social Copilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    await get_database().command("ping")
    return {"status": "ok", "database": "connected"}
