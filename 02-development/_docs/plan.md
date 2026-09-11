# Tennis Tournament Manager — Project Plan

## Overview
A web app for a single organizer to manage one-off, single-elimination tennis
tournaments. Player and match data persist in a database, enabling
rating-based seeding and historical performance analysis across tournaments.

## Tech Stack
- **Backend**: TBC
- **Frontend**: TBC
- **Database**: TBC
- **Auth**: TBC

Stack decisions will be made iteratively through conversation as the app is
rebuilt from scratch.

## Core Entities
- **Player**: name, rating (e.g., ELO-style), created date
- **Tournament**: name, date, location, surface (tournament-level)
- **Match**: tournament, round, player1, player2, winner, set scores, date,
  surface (inherited from tournament)
- **Bracket/Seed**: links players to a tournament with seed position

## Features

### 1. Tournament Setup
- Create a tournament with name, date, location, and surface.
- Add players to the tournament (select from existing player database or
  add new players).
- Seed players based on current rating/ranking.
- Auto-generate single-elimination bracket, including bye slots for
  non-power-of-two player counts, auto-assigned to top seeds.

### 2. Running the Tournament
- View the bracket.
- Enter match results: winner + full set scores (e.g., 6-4, 3-6, 6-2).
- Advance winners automatically to the next round.
- Mark tournament complete when final is recorded.

### 3. Player Database
- Persistent player records across tournaments.
- Rating updates after each recorded match (ELO-style system).

### 4. Historical Analysis (per player)
- Match win ratio (win/loss counts).
- Most recent tournament performance, including current win/loss streak.
- Rating trend over time (chart/list of rating changes).

## Out of Scope (for now)
- Player-facing views (organizer-only tool).
- Non-single-elimination formats (round-robin, ladder, etc.).
- CSV/file import of players (manual entry via UI only).
- Multi-user support / authentication.
- Head-to-head records, tournament win counts, or other stats beyond the
  three listed above.

## Open Questions / Future Considerations
- Exact rating algorithm details (e.g., ELO K-factor) — to be decided during
  implementation.
- Possible future: CSV import, multi-user auth, additional tournament
  formats, richer analytics.
