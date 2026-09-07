from datetime import date, timedelta

from .models import Chore, Person, Assignment

EPOCH = date(2024, 1, 1)  # Monday, used as a stable reference point for rotation


def get_week_start(today=None):
    """Return the Monday of the week containing `today` (defaults to today)."""
    today = today or date.today()
    return today - timedelta(days=today.weekday())


def get_or_create_week_assignments(week_start):
    """Ensure Assignment rows exist for `week_start`, rotating chores across people."""
    people = list(Person.objects.order_by('id'))
    chores = list(Chore.objects.order_by('id'))
    if not people or not chores:
        return Assignment.objects.filter(week_start=week_start)

    if Assignment.objects.filter(week_start=week_start).exists():
        return Assignment.objects.filter(week_start=week_start)

    weeks_since_epoch = (week_start - EPOCH).days // 7
    offset = weeks_since_epoch % len(people)

    for index, chore in enumerate(chores):
        person = people[(index + offset) % len(people)]
        Assignment.objects.create(week_start=week_start, chore=chore, person=person)

    return Assignment.objects.filter(week_start=week_start)
