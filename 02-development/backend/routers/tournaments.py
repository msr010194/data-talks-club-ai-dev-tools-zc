from fastapi import APIRouter, HTTPException

from ..schemas import Bracket, Tournament, TournamentCreate
from ..store import NotFoundError, ValidationError, store

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.get("", response_model=list[Tournament])
def list_tournaments():
    return store.list_tournaments()


@router.post("", response_model=Tournament, status_code=201)
def create_tournament(payload: TournamentCreate):
    try:
        return store.create_tournament(
            payload.name, payload.date, payload.location, payload.surface, payload.player_ids
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{tournament_id}", response_model=Tournament)
def get_tournament(tournament_id: int):
    try:
        return store.get_tournament(tournament_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{tournament_id}/bracket", response_model=Bracket)
def get_bracket(tournament_id: int):
    try:
        return store.get_bracket(tournament_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{tournament_id}/bracket", response_model=Bracket, status_code=201)
def generate_bracket(tournament_id: int):
    try:
        return store.generate_bracket(tournament_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
