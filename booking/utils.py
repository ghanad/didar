from django.conf import settings


def is_booking_manager(user):
    """Check if user has manager privileges for reservations."""
    if not user or not user.is_authenticated:
        return False
    manager_usernames = getattr(settings, 'BOOKING_MANAGERS', [])
    return user.username in manager_usernames
