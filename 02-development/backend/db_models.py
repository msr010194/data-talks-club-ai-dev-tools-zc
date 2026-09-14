"""SQLAlchemy ORM models."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

tournament_players = Table(
    "tournament_players",
    Base.metadata,
    Column("tournament_id", ForeignKey("tournaments.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    rating: Mapped[float] = mapped_column(default=1200.0)
    created: Mapped[date] = mapped_column(default=date.today)

    rating_history: Mapped[list["RatingHistory"]] = relationship(
        back_populates="player", cascade="all, delete-orphan", order_by="RatingHistory.id"
    )


class RatingHistory(Base):
    __tablename__ = "rating_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    date: Mapped[date] = mapped_column(default=date.today)
    rating: Mapped[float]

    player: Mapped["Player"] = relationship(back_populates="rating_history")


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    date: Mapped[date]
    location: Mapped[str]
    surface: Mapped[str]
    status: Mapped[str] = mapped_column(default="setup")

    players: Mapped[list["Player"]] = relationship(secondary=tournament_players)
    matches: Mapped[list["Match"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))
    round: Mapped[int]
    position: Mapped[int]  # index within the round, used to compute bracket advancement
    player_a_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    player_b_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    is_bye: Mapped[bool] = mapped_column(default=False)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), default=None)
    score: Mapped[str | None] = mapped_column(default=None)
    decided_at: Mapped[datetime | None] = mapped_column(default=None)

    tournament: Mapped["Tournament"] = relationship(back_populates="matches")
