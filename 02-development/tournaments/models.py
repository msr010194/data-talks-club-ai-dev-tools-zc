from django.db import models


class Player(models.Model):
    name = models.CharField(max_length=100)
    rating = models.FloatField(default=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
