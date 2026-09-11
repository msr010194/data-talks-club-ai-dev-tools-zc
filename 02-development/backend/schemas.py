"""Pydantic schemas for the Tennis Tournament Manager API.

Mirrors the shapes defined in openapi.yaml.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Surface = Literal["Hard", "Clay", "Grass", "Indoor"]


class PlayerCreate(BaseModel):
    name: str
    rating: float = 1200.0


class Player(BaseModel):
    id: int
    name: str
    rating: float
    created: date


class RatingPoint(BaseModel):
    date: date
    rating: float


class PlayerStats(BaseModel):
    wins: int
    losses: int
    win_ratio: float
    streak: int
    streak_type: Literal["W", "L"] | None
    rating_history: list[RatingPoint]


class TournamentCreate(BaseModel):
    name: str
    date: date
    location: str
    surface: Surface
    player_ids: list[int] = Field(min_length=2)


class Tournament(BaseModel):
    id: int
    name: str
    date: date
    location: str
    surface: Surface
    player_ids: list[int]
    status: Literal["setup", "in_progress", "complete"]


class Match(BaseModel):
    id: int
    tournament_id: int
    round: int
    player_a_id: int | None
    player_b_id: int | None
    is_bye: bool
    winner_id: int | None
    score: str | None


class Bracket(BaseModel):
    tournament_id: int
    rounds: list[list[Match]]


class MatchResultIn(BaseModel):
    winner_id: int
    score: str
