from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField
from datetime import timedelta

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام")
    capacity = models.PositiveIntegerField(verbose_name="ظرفیت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    color = models.CharField(max_length=7, default='#808080', help_text='کد رنگ هگزادسیمال را وارد کنید، مثال: #FF5733', verbose_name="رنگ")

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

class Attendee(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='attendees')
    email = models.EmailField(blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rsvp_status = models.CharField(
        max_length=20,
        choices=[
            ('NEEDS_ACTION', 'Needs Action'),
            ('ACCEPTED', 'Accepted'),
            ('DECLINED', 'Declined'),
            ('TENTATIVE', 'Tentative'),
        ],
        default='NEEDS_ACTION'
    )

    class Meta:
        unique_together = ('reservation', 'email')

    def __str__(self):
        return f"{self.email} for reservation '{self.reservation.title}'"
