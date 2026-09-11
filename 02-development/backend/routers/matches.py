from fastapi import APIRouter, HTTPException

from ..schemas import Match, MatchResultIn
from ..store import NotFoundError, ValidationError, store

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/{match_id}/result", response_model=Match)
def record_match_result(match_id: int, payload: MatchResultIn):
    try:
        return store.record_match_result(match_id, payload.winner_id, payload.score)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
