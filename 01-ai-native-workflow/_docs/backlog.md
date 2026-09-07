# Household Chore Manager — Backlog

## 1. Data Models
- [x] `Person` model: name.
- [x] `Chore` model: name, description.
- [x] `Assignment` model: week_start, person, chore, completed, completed_at.
- [x] Migrations + Django admin registration for all models.
- [x] Seed data: 4 people, 8 predefined chores.

## 2. Weekly Rotation
- [x] Compute current week (Monday-based) from calendar date.
- [x] Deterministic rotation assigning all 8 chores across 4 people
      (2 chores/person), auto-generated per week.
- [ ] Verify rotation fairness over a long run (each person eventually gets
      every chore an equal number of times).

## 3. Current Week View
- [x] Homepage showing this week's assignments grouped by person.
- [x] Mark-chore-done action (no login required).
- [ ] Group/display assignments by person more clearly (currently a flat
      list).

## 4. History
- [x] `history` view listing all past assignments with completion status.
- [ ] Filter history by person.
- [ ] Filter history by chore.
- [ ] Highlight missed chores (past week, still not completed).

## 5. Polish
- [ ] Basic navigation/layout shared across pages (currently minimal HTML).
- [ ] Rename seeded placeholder people (Person 1-4) to real household
      members.
- [ ] Basic styling (currently unstyled).

## 6. Testing
- [x] Model tests: `Assignment` string representation and field defaults.
- [x] Rotation tests: week-start calculation, one assignment per chore,
      2 chores per person, idempotency, rotation changes week-to-week,
      fairness over time, no people/chores edge case.
- [x] View tests: current week creates/displays assignments, mark-done
      (POST vs GET), history ordering.
