"""Mock backend client.

Every call the frontend makes to "the backend" goes through this module.
Data is kept in-memory and shaped like what a real API/DB layer would
return (plain dicts/lists), so swapping this out for real HTTP or ORM
calls later shouldn't require changing any page code.
"""
from __future__ import annotations

import math
import random
from datetime import date
from itertools import count

SURFACES = ["Hard", "Clay", "Grass", "Indoor"]

_player_ids = count(1)
_tournament_ids = count(1)
_match_ids = count(1)

_players: dict[int, dict] = {}
_tournaments: dict[int, dict] = {}
_matches: dict[int, dict] = {}


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def create_player(name: str, rating: float = 1200.0) -> dict:
    player_id = next(_player_ids)
    player = {
        "id": player_id,
        "name": name,
        "rating": rating,
        "created": date.today().isoformat(),
        "rating_history": [{"date": date.today().isoformat(), "rating": rating}],
        "match_history": [],  # [{tournament_id, opponent_id, won, score}]
    }
    _players[player_id] = player
    return player


def list_players() -> list[dict]:
    return sorted(_players.values(), key=lambda p: p["name"])


def get_player(player_id: int) -> dict | None:
    return _players.get(player_id)


def get_player_stats(player_id: int) -> dict:
    history = _players[player_id]["match_history"]
    wins = sum(1 for m in history if m["won"])
    total = len(history)

    streak, streak_won = 0, None
    for m in reversed(history):
        if streak_won is None:
            streak_won = m["won"]
        if m["won"] != streak_won:
            break
        streak += 1

    return {
        "wins": wins,
        "losses": total - wins,
        "win_ratio": wins / total if total else 0.0,
        "streak": streak,
        "streak_type": None if streak_won is None else ("W" if streak_won else "L"),
        "rating_history": _players[player_id]["rating_history"],
    }


# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------

def create_tournament(name: str, tournament_date, location: str, surface: str, player_ids: list[int]) -> dict:
    tournament_id = next(_tournament_ids)
    tournament = {
        "id": tournament_id,
        "name": name,
        "date": tournament_date.isoformat() if hasattr(tournament_date, "isoformat") else tournament_date,
        "location": location,
        "surface": surface,
        "player_ids": list(player_ids),
        "status": "setup",  # setup -> in_progress -> complete
        "rounds": [],  # list of rounds, each a list of match ids
    }
    _tournaments[tournament_id] = tournament
    return tournament


def list_tournaments() -> list[dict]:
    return sorted(_tournaments.values(), key=lambda t: t["date"], reverse=True)


def get_tournament(tournament_id: int) -> dict | None:
    return _tournaments.get(tournament_id)


def get_bracket(tournament_id: int) -> list[list[dict]]:
    tournament = _tournaments[tournament_id]
    return [[_matches[mid] for mid in round_ids] for round_ids in tournament["rounds"]]


def _next_power_of_two(n: int) -> int:
    return 1 if n <= 1 else 2 ** math.ceil(math.log2(n))


def _seed_order(bracket_size: int) -> list[int]:
    """Standard single-elimination seeding order, e.g. size 8 -> [1,8,4,5,2,7,3,6]."""
    order = [1, 2]
    while len(order) < bracket_size:
        size = len(order) * 2
        order = [s for seed in order for s in (seed, size + 1 - seed)]
    return order


def generate_bracket(tournament_id: int) -> dict:
    tournament = _tournaments[tournament_id]
    players = sorted(
        (_players[pid] for pid in tournament["player_ids"]),
        key=lambda p: p["rating"],
        reverse=True,
    )
    n = len(players)
    bracket_size = _next_power_of_two(n)

    seed_to_player = {i + 1: player for i, player in enumerate(players)}
    for seed in range(n + 1, bracket_size + 1):
        seed_to_player[seed] = None  # bye slot

    order = _seed_order(bracket_size)
    round1_matchups = [
        (seed_to_player[order[i]], seed_to_player[order[i + 1]])
        for i in range(0, bracket_size, 2)
    ]

    rounds: list[list[int]] = []
    round1_ids = [_create_match(tournament_id, 1, a, b) for a, b in round1_matchups]
    rounds.append(round1_ids)

    remaining = bracket_size // 2
    round_num = 1
    while remaining > 1:
        remaining //= 2
        round_num += 1
        rounds.append([_create_match(tournament_id, round_num, None, None) for _ in range(remaining)])

    tournament["rounds"] = rounds
    tournament["status"] = "in_progress"
    _advance_all_byes(tournament_id)
    return tournament


def _create_match(tournament_id: int, round_num: int, player_a: dict | None, player_b: dict | None) -> int:
    match_id = next(_match_ids)
    match = {
        "id": match_id,
        "tournament_id": tournament_id,
        "round": round_num,
        "player_a_id": player_a["id"] if player_a else None,
        "player_b_id": player_b["id"] if player_b else None,
        "is_bye": (player_a is None) != (player_b is None),
        "winner_id": None,
        "score": None,
    }
    if match["is_bye"]:
        match["winner_id"] = match["player_a_id"] or match["player_b_id"]
    _matches[match_id] = match
    return match_id


def _advance_all_byes(tournament_id: int) -> None:
    tournament = _tournaments[tournament_id]
    for match_id in tournament["rounds"][0]:
        match = _matches[match_id]
        if match["is_bye"]:
            _advance_winner(tournament_id, match)


def record_match_result(match_id: int, winner_id: int, score: str) -> dict:
    match = _matches[match_id]
    match["winner_id"] = winner_id
    match["score"] = score

    loser_id = match["player_a_id"] if winner_id == match["player_b_id"] else match["player_b_id"]
    _update_ratings(match["tournament_id"], winner_id, loser_id, score)
    _advance_winner(match["tournament_id"], match)
    _maybe_complete_tournament(match["tournament_id"])
    return match


def _advance_winner(tournament_id: int, match: dict) -> None:
    rounds = _tournaments[tournament_id]["rounds"]
    round_idx = match["round"] - 1
    if round_idx + 1 >= len(rounds):
        return  # final round played, nothing further to advance to

    position = rounds[round_idx].index(match["id"])
    next_match = _matches[rounds[round_idx + 1][position // 2]]
    slot = "player_a_id" if position % 2 == 0 else "player_b_id"
    next_match[slot] = match["winner_id"]


def _update_ratings(tournament_id: int, winner_id: int, loser_id: int, score: str) -> None:
    k = 32
    winner, loser = _players[winner_id], _players[loser_id]
    expected_winner = 1 / (1 + 10 ** ((loser["rating"] - winner["rating"]) / 400))
    winner["rating"] = round(winner["rating"] + k * (1 - expected_winner), 1)
    loser["rating"] = round(loser["rating"] + k * (0 - (1 - expected_winner)), 1)

    today = date.today().isoformat()
    winner["rating_history"].append({"date": today, "rating": winner["rating"]})
    loser["rating_history"].append({"date": today, "rating": loser["rating"]})
    winner["match_history"].append({"tournament_id": tournament_id, "opponent_id": loser_id, "won": True, "score": score})
    loser["match_history"].append({"tournament_id": tournament_id, "opponent_id": winner_id, "won": False, "score": score})


def _maybe_complete_tournament(tournament_id: int) -> None:
    tournament = _tournaments[tournament_id]
    final_match = _matches[tournament["rounds"][-1][0]]
    if final_match["winner_id"]:
        tournament["status"] = "complete"


def _seed_demo_data() -> None:
    names = [
        "Alice Chen", "Ben Osei", "Carla Diaz", "Dmitri Volkov",
        "Elena Petrova", "Farid Khan", "Grace Kim", "Hugo Silva",
        "Ivy Nakamura", "Jack Murphy",
    ]
    rng = random.Random(42)
    for name in names:
        create_player(name, rating=round(rng.uniform(1200, 1800), 1))


_seed_demo_data()
