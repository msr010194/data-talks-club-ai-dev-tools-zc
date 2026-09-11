from fastapi import FastAPI

from .routers import matches, players, tournaments

app = FastAPI(title="Tennis Tournament Manager API", version="0.1.0")

app.include_router(players.router)
app.include_router(tournaments.router)
app.include_router(matches.router)


@app.get("/health")
def health():
    return {"status": "ok"}
