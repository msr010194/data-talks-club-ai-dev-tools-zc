from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Chore(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Assignment(models.Model):
    week_start = models.DateField()
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='assignments')
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='assignments')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('week_start', 'chore')
        ordering = ['week_start', 'person']

    def __str__(self):
        return f'{self.week_start} - {self.person} - {self.chore}'
