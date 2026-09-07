from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Assignment, Chore, Person
from .rotation import get_or_create_week_assignments, get_week_start


class AssignmentModelTests(TestCase):
    def test_str_and_defaults(self):
        person = Person.objects.create(name='Alex')
        chore = Chore.objects.create(name='Dishes')
        assignment = Assignment.objects.create(
            week_start=date(2024, 1, 1), person=person, chore=chore,
        )
        self.assertFalse(assignment.completed)
        self.assertIsNone(assignment.completed_at)
        self.assertIn('Alex', str(assignment))
        self.assertIn('Dishes', str(assignment))


class RotationTests(TestCase):
    def setUp(self):
        # Migrations seed placeholder people/chores; start from a clean slate.
        Person.objects.all().delete()
        Chore.objects.all().delete()
        self.people = [Person.objects.create(name=f'Person {i}') for i in range(1, 5)]
        self.chores = [Chore.objects.create(name=f'Chore {i}') for i in range(1, 9)]

    def test_get_week_start_returns_monday(self):
        # Wednesday, Jan 3 2024 -> Monday, Jan 1 2024
        self.assertEqual(get_week_start(date(2024, 1, 3)), date(2024, 1, 1))
        # Already a Monday -> unchanged
        self.assertEqual(get_week_start(date(2024, 1, 1)), date(2024, 1, 1))

    def test_creates_one_assignment_per_chore(self):
        week_start = date(2024, 1, 1)
        assignments = get_or_create_week_assignments(week_start)
        self.assertEqual(assignments.count(), 8)
        self.assertEqual(
            {a.chore_id for a in assignments}, {c.id for c in self.chores},
        )

    def test_each_person_gets_two_chores(self):
        week_start = date(2024, 1, 1)
        assignments = get_or_create_week_assignments(week_start)
        for person in self.people:
            self.assertEqual(assignments.filter(person=person).count(), 2)

    def test_idempotent_for_same_week(self):
        week_start = date(2024, 1, 1)
        get_or_create_week_assignments(week_start)
        get_or_create_week_assignments(week_start)
        self.assertEqual(Assignment.objects.filter(week_start=week_start).count(), 8)

    def test_different_weeks_rotate_mapping(self):
        week1 = date(2024, 1, 1)
        week2 = week1 + timedelta(weeks=1)
        assignments_week1 = get_or_create_week_assignments(week1)
        assignments_week2 = get_or_create_week_assignments(week2)
        mapping1 = {a.chore_id: a.person_id for a in assignments_week1}
        mapping2 = {a.chore_id: a.person_id for a in assignments_week2}
        self.assertNotEqual(mapping1, mapping2)

    def test_rotation_fairness_over_time(self):
        week_start = date(2024, 1, 1)
        history = {person.id: set() for person in self.people}
        for week_index in range(len(self.people)):
            assignments = get_or_create_week_assignments(
                week_start + timedelta(weeks=week_index),
            )
            for assignment in assignments:
                history[assignment.person_id].add(assignment.chore_id)
        all_chore_ids = {chore.id for chore in self.chores}
        for person_id, chore_ids in history.items():
            self.assertEqual(chore_ids, all_chore_ids)

    def test_no_people_or_chores_returns_empty(self):
        Person.objects.all().delete()
        Chore.objects.all().delete()
        assignments = get_or_create_week_assignments(date(2024, 1, 1))
        self.assertEqual(assignments.count(), 0)


class ViewTests(TestCase):
    def setUp(self):
        # Migrations seed placeholder people/chores; start from a clean slate.
        Person.objects.all().delete()
        Chore.objects.all().delete()
        self.people = [Person.objects.create(name=f'Person {i}') for i in range(1, 5)]
        self.chores = [Chore.objects.create(name=f'Chore {i}') for i in range(1, 9)]

    def test_current_week_view_creates_and_displays_assignments(self):
        response = self.client.get(reverse('current_week'))
        self.assertEqual(response.status_code, 200)
        week_start = get_week_start()
        self.assertEqual(Assignment.objects.filter(week_start=week_start).count(), 8)

    def test_mark_done_post_marks_completed(self):
        week_start = get_week_start()
        assignment = get_or_create_week_assignments(week_start).first()
        response = self.client.post(reverse('mark_done', args=[assignment.id]))
        self.assertRedirects(response, reverse('current_week'))
        assignment.refresh_from_db()
        self.assertTrue(assignment.completed)
        self.assertIsNotNone(assignment.completed_at)

    def test_mark_done_get_does_not_mark_completed(self):
        week_start = get_week_start()
        assignment = get_or_create_week_assignments(week_start).first()
        self.client.get(reverse('mark_done', args=[assignment.id]))
        assignment.refresh_from_db()
        self.assertFalse(assignment.completed)

    def test_history_view_lists_past_weeks_most_recent_first(self):
        week1 = date(2024, 1, 1)
        week2 = week1 + timedelta(weeks=1)
        get_or_create_week_assignments(week1)
        get_or_create_week_assignments(week2)

        response = self.client.get(reverse('history'))

        self.assertEqual(response.status_code, 200)
        weeks_in_order = [a.week_start for a in response.context['assignments']]
        self.assertEqual(weeks_in_order, sorted(weeks_in_order, reverse=True))
