from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import store
from ..database import get_db
from ..schemas import Match, MatchResultIn

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/{match_id}/result", response_model=Match)
def record_match_result(match_id: int, payload: MatchResultIn, db: Session = Depends(get_db)):
    try:
        return store.record_match_result(db, match_id, payload.winner_id, payload.score)
    except store.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except store.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
