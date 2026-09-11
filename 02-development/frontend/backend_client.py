"""HTTP client for the Tennis Tournament Manager FastAPI backend.

Every call the frontend makes to the backend goes through this module, so
pages never talk to `httpx` directly. Configure the backend location via
the `BACKEND_URL` environment variable (defaults to localhost:8000).
"""
from __future__ import annotations

import os

import httpx

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

SURFACES = ["Hard", "Clay", "Grass", "Indoor"]


class BackendError(Exception):
    """Raised when the backend is unreachable or returns an error response."""


def _request(method: str, path: str, **kwargs) -> dict | list:
    try:
        response = httpx.request(method, f"{BASE_URL}{path}", timeout=10, **kwargs)
    except httpx.RequestError as exc:
        raise BackendError(f"Could not reach backend at {BASE_URL}: {exc}") from exc

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise BackendError(detail)

    return response.json()


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def create_player(name: str, rating: float = 1200.0) -> dict:
    return _request("POST", "/players", json={"name": name, "rating": rating})


def list_players() -> list[dict]:
    return _request("GET", "/players")


def get_player(player_id: int) -> dict:
    return _request("GET", f"/players/{player_id}")


def get_player_stats(player_id: int) -> dict:
    return _request("GET", f"/players/{player_id}/stats")


# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------

def create_tournament(name: str, tournament_date, location: str, surface: str, player_ids: list[int]) -> dict:
    payload = {
        "name": name,
        "date": tournament_date.isoformat() if hasattr(tournament_date, "isoformat") else tournament_date,
        "location": location,
        "surface": surface,
        "player_ids": list(player_ids),
    }
    return _request("POST", "/tournaments", json=payload)


def list_tournaments() -> list[dict]:
    return _request("GET", "/tournaments")


def get_tournament(tournament_id: int) -> dict:
    return _request("GET", f"/tournaments/{tournament_id}")


def get_bracket(tournament_id: int) -> list[list[dict]]:
    return _request("GET", f"/tournaments/{tournament_id}/bracket")["rounds"]


def generate_bracket(tournament_id: int) -> dict:
    return _request("POST", f"/tournaments/{tournament_id}/bracket")


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def record_match_result(match_id: int, winner_id: int, score: str) -> dict:
    return _request("POST", f"/matches/{match_id}/result", json={"winner_id": winner_id, "score": score})
