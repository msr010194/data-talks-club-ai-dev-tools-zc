from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import store
from ..database import get_db
from ..schemas import Player, PlayerCreate, PlayerStats

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[Player])
def list_players(db: Session = Depends(get_db)):
    return store.list_players(db)


@router.post("", response_model=Player, status_code=201)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    return store.create_player(db, payload.name, payload.rating)


@router.get("/{player_id}", response_model=Player)
def get_player(player_id: int, db: Session = Depends(get_db)):
    try:
        return store.get_player(db, player_id)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{player_id}/stats", response_model=PlayerStats)
def get_player_stats(player_id: int, db: Session = Depends(get_db)):
    try:
        return store.get_player_stats(db, player_id)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
