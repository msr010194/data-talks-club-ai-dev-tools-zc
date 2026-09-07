from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Assignment
from .rotation import get_or_create_week_assignments, get_week_start


def current_week(request):
    week_start = get_week_start()
    assignments = get_or_create_week_assignments(week_start).select_related('person', 'chore')
    return render(request, 'chores/current_week.html', {
        'week_start': week_start,
        'assignments': assignments,
    })


def mark_done(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    if request.method == 'POST':
        assignment.completed = True
        assignment.completed_at = timezone.now()
        assignment.save()
    return redirect('current_week')


def history(request):
    assignments = Assignment.objects.select_related('person', 'chore').order_by('-week_start')
    return render(request, 'chores/history.html', {'assignments': assignments})
