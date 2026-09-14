"""Data store backed by SQLAlchemy.

All lookups/mutations for players, tournaments, and matches happen here so
routers and schemas stay agnostic to how data is persisted. Every function
takes a `Session` and returns plain dicts shaped like the API schemas.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from . import db_models as models


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""


class ValidationError(Exception):
    """Raised when an operation is invalid given the current state."""


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _player_dict(player: models.Player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "rating": player.rating,
        "created": player.created,
    }


def _rating_history(player: models.Player) -> list[dict]:
    return [{"date": rh.date, "rating": rh.rating} for rh in player.rating_history]


def _tournament_dict(tournament: models.Tournament) -> dict:
    return {
        "id": tournament.id,
        "name": tournament.name,
        "date": tournament.date,
        "location": tournament.location,
        "surface": tournament.surface,
        "player_ids": [p.id for p in tournament.players],
        "status": tournament.status,
    }


def _match_dict(match: models.Match) -> dict:
    return {
        "id": match.id,
        "tournament_id": match.tournament_id,
        "round": match.round,
        "player_a_id": match.player_a_id,
        "player_b_id": match.player_b_id,
        "is_bye": match.is_bye,
        "winner_id": match.winner_id,
        "score": match.score,
    }


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def create_player(db: Session, name: str, rating: float = 1200.0) -> dict:
    player = models.Player(name=name, rating=rating, created=date.today())
    db.add(player)
    db.flush()
    db.add(models.RatingHistory(player_id=player.id, date=date.today(), rating=rating))
    db.commit()
    db.refresh(player)
    return _player_dict(player)


def list_players(db: Session) -> list[dict]:
    players = db.query(models.Player).order_by(models.Player.name).all()
    return [_player_dict(p) for p in players]


def _get_player_or_404(db: Session, player_id: int) -> models.Player:
    player = db.get(models.Player, player_id)
    if player is None:
        raise NotFoundError(f"Player {player_id} not found")
    return player


def get_player(db: Session, player_id: int) -> dict:
    return _player_dict(_get_player_or_404(db, player_id))


def get_player_stats(db: Session, player_id: int) -> dict:
    player = _get_player_or_404(db, player_id)

    matches = (
        db.query(models.Match)
        .filter(
            models.Match.winner_id.isnot(None),
            models.Match.is_bye.is_(False),
            (models.Match.player_a_id == player_id) | (models.Match.player_b_id == player_id),
        )
        .order_by(models.Match.decided_at, models.Match.id)
        .all()
    )

    results = [m.winner_id == player_id for m in matches]
    wins = sum(results)
    total = len(results)

    streak, streak_won = 0, None
    for won in reversed(results):
        if streak_won is None:
            streak_won = won
        if won != streak_won:
            break
        streak += 1

    return {
        "wins": wins,
        "losses": total - wins,
        "win_ratio": wins / total if total else 0.0,
        "streak": streak,
        "streak_type": None if streak_won is None else ("W" if streak_won else "L"),
        "rating_history": _rating_history(player),
    }


# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------

def create_tournament(
    db: Session, name: str, tournament_date, location: str, surface: str, player_ids: list[int]
) -> dict:
    if len(player_ids) < 2:
        raise ValidationError("A tournament needs at least 2 players")

    players = db.query(models.Player).filter(models.Player.id.in_(player_ids)).all()
    found_ids = {p.id for p in players}
    for player_id in player_ids:
        if player_id not in found_ids:
            raise ValidationError(f"Unknown player id: {player_id}")

    date_value = tournament_date if isinstance(tournament_date, date) else date.fromisoformat(tournament_date)
    tournament = models.Tournament(
        name=name, date=date_value, location=location, surface=surface, status="setup", players=players
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return _tournament_dict(tournament)


def list_tournaments(db: Session) -> list[dict]:
    tournaments = db.query(models.Tournament).order_by(models.Tournament.date.desc()).all()
    return [_tournament_dict(t) for t in tournaments]


def _get_tournament_or_404(db: Session, tournament_id: int) -> models.Tournament:
    tournament = db.get(models.Tournament, tournament_id)
    if tournament is None:
        raise NotFoundError(f"Tournament {tournament_id} not found")
    return tournament


def get_tournament(db: Session, tournament_id: int) -> dict:
    return _tournament_dict(_get_tournament_or_404(db, tournament_id))


def get_bracket(db: Session, tournament_id: int) -> dict:
    tournament = _get_tournament_or_404(db, tournament_id)
    if tournament.status == "setup":
        raise ValidationError("Bracket has not been generated yet")

    matches = (
        db.query(models.Match)
        .filter(models.Match.tournament_id == tournament_id)
        .order_by(models.Match.round, models.Match.position)
        .all()
    )
    rounds: list[list[dict]] = []
    for match in matches:
        round_idx = match.round - 1
        while len(rounds) <= round_idx:
            rounds.append([])
        rounds[round_idx].append(_match_dict(match))
    return {"tournament_id": tournament_id, "rounds": rounds}


def _next_power_of_two(n: int) -> int:
    return 1 if n <= 1 else 2 ** math.ceil(math.log2(n))


def _seed_order(bracket_size: int) -> list[int]:
    """Standard single-elimination seeding order, e.g. size 8 -> [1,8,4,5,2,7,3,6]."""
    order = [1, 2]
    while len(order) < bracket_size:
        size = len(order) * 2
        order = [s for seed in order for s in (seed, size + 1 - seed)]
    return order


def generate_bracket(db: Session, tournament_id: int) -> dict:
    tournament = _get_tournament_or_404(db, tournament_id)
    if tournament.status != "setup":
        raise ValidationError("Bracket already generated for this tournament")

    players = sorted(tournament.players, key=lambda p: p.rating, reverse=True)
    n = len(players)
    bracket_size = _next_power_of_two(n)

    seed_to_player: dict[int, models.Player | None] = {i + 1: player for i, player in enumerate(players)}
    for seed in range(n + 1, bracket_size + 1):
        seed_to_player[seed] = None

    order = _seed_order(bracket_size)
    round1_matchups = [
        (seed_to_player[order[i]], seed_to_player[order[i + 1]])
        for i in range(0, bracket_size, 2)
    ]

    for position, (player_a, player_b) in enumerate(round1_matchups):
        db.add(_build_match(tournament_id, 1, position, player_a, player_b))

    remaining = bracket_size // 2
    round_num = 1
    while remaining > 1:
        remaining //= 2
        round_num += 1
        for position in range(remaining):
            db.add(_build_match(tournament_id, round_num, position, None, None))

    tournament.status = "in_progress"
    db.flush()  # assign match ids before wiring up bye advancement

    _advance_all_byes(db, tournament_id)
    db.commit()
    return get_bracket(db, tournament_id)


def _build_match(
    tournament_id: int, round_num: int, position: int, player_a: models.Player | None, player_b: models.Player | None
) -> models.Match:
    is_bye = (player_a is None) != (player_b is None)
    winner_id = None
    if is_bye:
        winner_id = player_a.id if player_a else player_b.id
    return models.Match(
        tournament_id=tournament_id,
        round=round_num,
        position=position,
        player_a_id=player_a.id if player_a else None,
        player_b_id=player_b.id if player_b else None,
        is_bye=is_bye,
        winner_id=winner_id,
    )


def _advance_all_byes(db: Session, tournament_id: int) -> None:
    round1_matches = (
        db.query(models.Match)
        .filter(models.Match.tournament_id == tournament_id, models.Match.round == 1)
        .order_by(models.Match.position)
        .all()
    )
    for match in round1_matches:
        if match.is_bye:
            _advance_winner(db, tournament_id, match)


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def _get_match_or_404(db: Session, match_id: int) -> models.Match:
    match = db.get(models.Match, match_id)
    if match is None:
        raise NotFoundError(f"Match {match_id} not found")
    return match


def get_match(db: Session, match_id: int) -> dict:
    return _match_dict(_get_match_or_404(db, match_id))


def record_match_result(db: Session, match_id: int, winner_id: int, score: str) -> dict:
    match = _get_match_or_404(db, match_id)
    if match.is_bye:
        raise ValidationError("Cannot record a result for a bye")
    if match.winner_id is not None:
        raise ValidationError("This match has already been decided")
    if match.player_a_id is None or match.player_b_id is None:
        raise ValidationError("This match is still waiting for an opponent")
    if winner_id not in (match.player_a_id, match.player_b_id):
        raise ValidationError("Winner must be one of the match's players")

    match.winner_id = winner_id
    match.score = score
    match.decided_at = datetime.now(timezone.utc)

    loser_id = match.player_a_id if winner_id == match.player_b_id else match.player_b_id
    _update_ratings(db, winner_id, loser_id)
    _advance_winner(db, match.tournament_id, match)
    _maybe_complete_tournament(db, match.tournament_id)

    db.commit()
    db.refresh(match)
    return _match_dict(match)


def _advance_winner(db: Session, tournament_id: int, match: models.Match) -> None:
    next_match = (
        db.query(models.Match)
        .filter(
            models.Match.tournament_id == tournament_id,
            models.Match.round == match.round + 1,
            models.Match.position == match.position // 2,
        )
        .one_or_none()
    )
    if next_match is None:
        return  # final round played, nothing further to advance to

    slot = "player_a_id" if match.position % 2 == 0 else "player_b_id"
    setattr(next_match, slot, match.winner_id)


def _update_ratings(db: Session, winner_id: int, loser_id: int) -> None:
    k = 32
    winner = db.get(models.Player, winner_id)
    loser = db.get(models.Player, loser_id)
    expected_winner = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400))
    winner.rating = round(winner.rating + k * (1 - expected_winner), 1)
    loser.rating = round(loser.rating + k * (0 - (1 - expected_winner)), 1)

    today = date.today()
    db.add(models.RatingHistory(player_id=winner.id, date=today, rating=winner.rating))
    db.add(models.RatingHistory(player_id=loser.id, date=today, rating=loser.rating))


def _maybe_complete_tournament(db: Session, tournament_id: int) -> None:
    tournament = db.get(models.Tournament, tournament_id)
    final_match = (
        db.query(models.Match)
        .filter(models.Match.tournament_id == tournament_id)
        .order_by(models.Match.round.desc())
        .first()
    )
    if final_match is not None and final_match.winner_id:
        tournament.status = "complete"
