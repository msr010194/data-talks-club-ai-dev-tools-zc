# Household Chore Manager — Project Plan

## Overview
A web app for a household of 4 people to manage shared chores. Chores are
assigned on a weekly rotation so that everyone eventually does every chore,
with completion history tracked over time.

## Tech Stack
- **Backend**: Django
- **Frontend**: Django templates (server-rendered)
- **Database**: SQLite
- **Auth**: None — single shared view, no login required

## Core Entities
- **Person**: name (one of the 4 household members)
- **Chore**: name, description (predefined list of 8)
- **Week**: identified by start date, computed/derived automatically from
  the current calendar date
- **Assignment**: links a person, chore, and week; tracks completion status
  and completed date/time

## Features

### 1. Chore & Person Setup
- Predefined list of 8 chores (seeded via fixture/migration, not user-editable
  through the UI for now).
- Predefined list of 4 household members.

### 2. Weekly Rotation
- Each week, all 8 chores are assigned across the 4 people (2 chores per
  person).
- Rotation advances automatically based on the calendar date (new week ==
  new rotation), so that over time everyone cycles through every chore.
- Rotation order/logic is deterministic (e.g., fixed offset per week) —
  exact algorithm to be finalized during implementation.

### 3. Current Week View
- Shared homepage showing this week's assignments: each person and their
  2 chores.
- Mark a chore as done (no login — anyone can mark any chore complete).

### 4. History
- Persistent record of past weeks' assignments and completion status
  (done / missed, and when completed).
- View history per person or per chore (e.g., "did Alex do trash last
  week?").

## Testing
- Unit tests for rotation logic (week calculation, assignment generation,
  fairness/idempotency) and views (current week, mark-done, history).

## Out of Scope (for now)
- User accounts / authentication.
- Editing the chore list or person list via the UI (predefined only).
- Notifications/reminders (email, push, etc.) — webpage-check only.
- Swapping/trading chores between people, or manual reassignment.
- Non-weekly cadences (daily, custom per-chore frequency).

## Open Questions / Future Considerations
- Exact rotation algorithm (how chores map to people week-to-week) — to be
  decided during implementation.
- Possible future: user accounts, chore swapping, reminders, custom chore
  list management.
