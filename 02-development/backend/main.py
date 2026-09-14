from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routers import matches, players, tournaments


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tennis Tournament Manager API", version="0.1.0", lifespan=lifespan)

app.include_router(players.router)
app.include_router(tournaments.router)
app.include_router(matches.router)


@app.get("/health")
def health():
    return {"status": "ok"}
