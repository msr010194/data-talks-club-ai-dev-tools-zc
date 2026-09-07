from django.contrib import admin

from .models import Assignment, Chore, Person

admin.site.register(Person)
admin.site.register(Chore)
admin.site.register(Assignment)
