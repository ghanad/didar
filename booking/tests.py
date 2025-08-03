from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Attendee, Reservation, Room
from .utils import is_booking_manager
from .views import manage_attendees


class IsBookingManagerTests(TestCase):
    @override_settings(BOOKING_MANAGERS=["manager"])
    def test_is_booking_manager(self):
        manager = User.objects.create_user(username="manager")
        regular = User.objects.create_user(username="regular")
        self.assertTrue(is_booking_manager(manager))
        self.assertFalse(is_booking_manager(regular))
        self.assertFalse(is_booking_manager(AnonymousUser()))


class ManageAttendeesTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="org", email="org@example.com"
        )
        self.room = Room.objects.create(name="Room1", capacity=5)
        self.reservation = Reservation.objects.create(
            title="Test",
            room=self.room,
            organizer=self.organizer,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration=timedelta(hours=1),
        )

    def test_manage_attendees_updates_attendees(self):
        Attendee.objects.create(reservation=self.reservation, email="old@example.com")
        linked_user = User.objects.create_user(
            username="attendee", email="new@example.com"
        )

        manage_attendees(self.reservation, ["new@example.com"])

        emails = set(
            self.reservation.attendees.values_list("email", flat=True)
        )
        self.assertEqual(emails, {"new@example.com"})
        attendee = self.reservation.attendees.get(email="new@example.com")
        self.assertEqual(attendee.user, linked_user)
