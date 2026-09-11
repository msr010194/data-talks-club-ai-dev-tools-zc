"""In-memory mock data store.

Stands in for a real database. All lookups/mutations for players,
tournaments, and matches happen here so routers stay thin, and this file
is the only thing that needs to change when a real DB is introduced.
"""
from __future__ import annotations

import math
from datetime import date
from itertools import count


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""


class ValidationError(Exception):
    """Raised when an operation is invalid given the current state."""


class MockStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._player_ids = count(1)
        self._tournament_ids = count(1)
        self._match_ids = count(1)
        self._players: dict[int, dict] = {}
        self._tournaments: dict[int, dict] = {}
        self._matches: dict[int, dict] = {}

    # -- Players ----------------------------------------------------------

    def create_player(self, name: str, rating: float = 1200.0) -> dict:
        player_id = next(self._player_ids)
        player = {
            "id": player_id,
            "name": name,
            "rating": rating,
            "created": date.today().isoformat(),
            "rating_history": [{"date": date.today().isoformat(), "rating": rating}],
            "match_history": [],  # [{tournament_id, opponent_id, won, score}]
        }
        self._players[player_id] = player
        return player

    def list_players(self) -> list[dict]:
        return sorted(self._players.values(), key=lambda p: p["name"])

    def get_player(self, player_id: int) -> dict:
        try:
            return self._players[player_id]
        except KeyError:
            raise NotFoundError(f"Player {player_id} not found") from None

    def get_player_stats(self, player_id: int) -> dict:
        history = self.get_player(player_id)["match_history"]
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
            "rating_history": self._players[player_id]["rating_history"],
        }

    # -- Tournaments --------------------------------------------------------

    def create_tournament(
        self, name: str, tournament_date, location: str, surface: str, player_ids: list[int]
    ) -> dict:
        if len(player_ids) < 2:
            raise ValidationError("A tournament needs at least 2 players")
        for player_id in player_ids:
            try:
                self.get_player(player_id)
            except NotFoundError:
                raise ValidationError(f"Unknown player id: {player_id}") from None

        tournament_id = next(self._tournament_ids)
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
        self._tournaments[tournament_id] = tournament
        return tournament

    def list_tournaments(self) -> list[dict]:
        return sorted(self._tournaments.values(), key=lambda t: t["date"], reverse=True)

    def get_tournament(self, tournament_id: int) -> dict:
        try:
            return self._tournaments[tournament_id]
        except KeyError:
            raise NotFoundError(f"Tournament {tournament_id} not found") from None

    def get_bracket(self, tournament_id: int) -> dict:
        tournament = self.get_tournament(tournament_id)
        if tournament["status"] == "setup":
            raise ValidationError("Bracket has not been generated yet")
        rounds = [[self._matches[mid] for mid in round_ids] for round_ids in tournament["rounds"]]
        return {"tournament_id": tournament_id, "rounds": rounds}

    @staticmethod
    def _next_power_of_two(n: int) -> int:
        return 1 if n <= 1 else 2 ** math.ceil(math.log2(n))

    @staticmethod
    def _seed_order(bracket_size: int) -> list[int]:
        """Standard single-elimination seeding order, e.g. size 8 -> [1,8,4,5,2,7,3,6]."""
        order = [1, 2]
        while len(order) < bracket_size:
            size = len(order) * 2
            order = [s for seed in order for s in (seed, size + 1 - seed)]
        return order

    def generate_bracket(self, tournament_id: int) -> dict:
        tournament = self.get_tournament(tournament_id)
        if tournament["status"] != "setup":
            raise ValidationError("Bracket already generated for this tournament")

        players = sorted(
            (self._players[pid] for pid in tournament["player_ids"]),
            key=lambda p: p["rating"],
            reverse=True,
        )
        n = len(players)
        bracket_size = self._next_power_of_two(n)

        seed_to_player = {i + 1: player for i, player in enumerate(players)}
        for seed in range(n + 1, bracket_size + 1):
            seed_to_player[seed] = None  # bye slot

        order = self._seed_order(bracket_size)
        round1_matchups = [
            (seed_to_player[order[i]], seed_to_player[order[i + 1]])
            for i in range(0, bracket_size, 2)
        ]

        rounds: list[list[int]] = []
        round1_ids = [self._create_match(tournament_id, 1, a, b) for a, b in round1_matchups]
        rounds.append(round1_ids)

        remaining = bracket_size // 2
        round_num = 1
        while remaining > 1:
            remaining //= 2
            round_num += 1
            rounds.append([self._create_match(tournament_id, round_num, None, None) for _ in range(remaining)])

        tournament["rounds"] = rounds
        tournament["status"] = "in_progress"
        self._advance_all_byes(tournament_id)
        return self.get_bracket(tournament_id)

    def _create_match(self, tournament_id: int, round_num: int, player_a: dict | None, player_b: dict | None) -> int:
        match_id = next(self._match_ids)
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
        self._matches[match_id] = match
        return match_id

    def _advance_all_byes(self, tournament_id: int) -> None:
        tournament = self._tournaments[tournament_id]
        for match_id in tournament["rounds"][0]:
            match = self._matches[match_id]
            if match["is_bye"]:
                self._advance_winner(tournament_id, match)

    # -- Matches ------------------------------------------------------------

    def get_match(self, match_id: int) -> dict:
        try:
            return self._matches[match_id]
        except KeyError:
            raise NotFoundError(f"Match {match_id} not found") from None

    def record_match_result(self, match_id: int, winner_id: int, score: str) -> dict:
        match = self.get_match(match_id)
        if match["is_bye"]:
            raise ValidationError("Cannot record a result for a bye")
        if match["winner_id"] is not None:
            raise ValidationError("This match has already been decided")
        if match["player_a_id"] is None or match["player_b_id"] is None:
            raise ValidationError("This match is still waiting for an opponent")
        if winner_id not in (match["player_a_id"], match["player_b_id"]):
            raise ValidationError("Winner must be one of the match's players")

        match["winner_id"] = winner_id
        match["score"] = score

        loser_id = match["player_a_id"] if winner_id == match["player_b_id"] else match["player_b_id"]
        self._update_ratings(match["tournament_id"], winner_id, loser_id, score)
        self._advance_winner(match["tournament_id"], match)
        self._maybe_complete_tournament(match["tournament_id"])
        return match

    def _advance_winner(self, tournament_id: int, match: dict) -> None:
        rounds = self._tournaments[tournament_id]["rounds"]
        round_idx = match["round"] - 1
        if round_idx + 1 >= len(rounds):
            return  # final round played, nothing further to advance to

        position = rounds[round_idx].index(match["id"])
        next_match = self._matches[rounds[round_idx + 1][position // 2]]
        slot = "player_a_id" if position % 2 == 0 else "player_b_id"
        next_match[slot] = match["winner_id"]

    def _update_ratings(self, tournament_id: int, winner_id: int, loser_id: int, score: str) -> None:
        k = 32
        winner, loser = self._players[winner_id], self._players[loser_id]
        expected_winner = 1 / (1 + 10 ** ((loser["rating"] - winner["rating"]) / 400))
        winner["rating"] = round(winner["rating"] + k * (1 - expected_winner), 1)
        loser["rating"] = round(loser["rating"] + k * (0 - (1 - expected_winner)), 1)

        today = date.today().isoformat()
        winner["rating_history"].append({"date": today, "rating": winner["rating"]})
        loser["rating_history"].append({"date": today, "rating": loser["rating"]})
        winner["match_history"].append({"tournament_id": tournament_id, "opponent_id": loser_id, "won": True, "score": score})
        loser["match_history"].append({"tournament_id": tournament_id, "opponent_id": winner_id, "won": False, "score": score})

    def _maybe_complete_tournament(self, tournament_id: int) -> None:
        tournament = self._tournaments[tournament_id]
        final_match = self._matches[tournament["rounds"][-1][0]]
        if final_match["winner_id"]:
            tournament["status"] = "complete"


store = MockStore()
