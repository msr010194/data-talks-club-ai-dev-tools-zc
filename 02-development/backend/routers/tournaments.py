from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import store
from ..database import get_db
from ..schemas import Bracket, Tournament, TournamentCreate

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.get("", response_model=list[Tournament])
def list_tournaments(db: Session = Depends(get_db)):
    return store.list_tournaments(db)


@router.post("", response_model=Tournament, status_code=201)
def create_tournament(payload: TournamentCreate, db: Session = Depends(get_db)):
    try:
        return store.create_tournament(
            db, payload.name, payload.date, payload.location, payload.surface, payload.player_ids
        )
    except store.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{tournament_id}", response_model=Tournament)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return store.get_tournament(db, tournament_id)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{tournament_id}/bracket", response_model=Bracket)
def get_bracket(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return store.get_bracket(db, tournament_id)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except store.ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{tournament_id}/bracket", response_model=Bracket, status_code=201)
def generate_bracket(tournament_id: int, db: Session = Depends(get_db)):
    try:
        return store.generate_bracket(db, tournament_id)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except store.ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
