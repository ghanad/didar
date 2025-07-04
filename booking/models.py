from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField
from datetime import timedelta

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    title = models.CharField(max_length=200)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    recurrence_rule = RecurrenceField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    it_support_needed = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation for '{self.title}' in '{self.room.name}' on {self.start_time}"
