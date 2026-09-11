from fastapi import APIRouter, HTTPException

from ..schemas import Player, PlayerCreate, PlayerStats
from ..store import NotFoundError, store

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[Player])
def list_players():
    return store.list_players()


@router.post("", response_model=Player, status_code=201)
def create_player(payload: PlayerCreate):
    return store.create_player(payload.name, payload.rating)


@router.get("/{player_id}", response_model=Player)
def get_player(player_id: int):
    try:
        return store.get_player(player_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{player_id}/stats", response_model=PlayerStats)
def get_player_stats(player_id: int):
    try:
        return store.get_player_stats(player_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
