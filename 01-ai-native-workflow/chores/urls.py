from django.urls import path

from . import views

urlpatterns = [
    path('', views.current_week, name='current_week'),
    path('history/', views.history, name='history'),
    path('assignments/<int:assignment_id>/done/', views.mark_done, name='mark_done'),
]
