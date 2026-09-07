# Tennis Tournament Manager — Backlog

## 1. Data Models
- [x] `Player` model: name, rating, created date.
- [ ] `Tournament` model: name, date, location, surface.
- [ ] `Match` model: tournament, round, player1, player2, winner, set scores,
      date (surface inherited from tournament).
- [ ] `Seed` model: links a player to a tournament with a seed position.
- [ ] Migrations + Django admin registration for all models.

## 2. Rating System
- [ ] Implement ELO-style rating calculation.
- [ ] Update player rating after each recorded match result.

## 3. Tournament Setup
- [ ] Create tournament form (name, date, location, surface).
- [ ] Add players to a tournament (from existing player DB or new player).
- [ ] Seed players by current rating.
- [ ] Generate single-elimination bracket, including bye slots for
      non-power-of-two player counts, auto-assigned to top seeds.

## 4. Running a Tournament
- [ ] Bracket view (rounds, matchups, byes).
- [ ] Match result entry: winner + full set scores.
- [ ] Auto-advance winners to next round.
- [ ] Mark tournament complete when final is recorded.

## 5. Player Database
- [ ] Player list/detail views.
- [ ] Persist player records across tournaments.

## 6. Historical Analysis
- [ ] Match win ratio (win/loss counts) per player.
- [ ] Most recent tournament performance + current win/loss streak.
- [ ] Rating trend over time (list/chart).

## 7. Polish
- [ ] Basic navigation (players, tournaments, create tournament).
- [ ] Input validation (e.g., valid set scores, no duplicate players in a
      tournament).
- [ ] Seed/test data for manual testing.
