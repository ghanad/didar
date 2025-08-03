from django import template

from booking.utils import is_booking_manager


register = template.Library()


@register.filter(name="is_booking_manager")
def is_booking_manager_filter(user):
    """Return True if the user is listed as a booking manager."""
    return is_booking_manager(user)

