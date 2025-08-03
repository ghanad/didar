from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Reservation, Room, Attendee
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
import json
import logging
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .utils import is_booking_manager

logger = logging.getLogger(__name__)

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'booking/calendar_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.filter(is_active=True)
        context['business_hours_start'] = settings.BUSINESS_HOURS_START
        context['business_hours_end'] = settings.BUSINESS_HOURS_END
        context['is_manager'] = is_booking_manager(self.request.user) # Pass manager status to template
        return context

def reservation_api(request):
    start_param = request.GET.get('start')
    end_param = request.GET.get('end')

    start_date = parse_datetime(start_param) if start_param else timezone.now() - timedelta(days=30)
    end_date = parse_datetime(end_param) if end_param else timezone.now() + timedelta(days=30)

    reservations = Reservation.objects.all()
    room_id = request.GET.get('room_id')
    if room_id:
        reservations = reservations.filter(room__id=room_id)
    events = []

    for reservation in reservations:
        # Determine if the current user is the organizer or a manager
        is_organizer_or_manager = (reservation.organizer == request.user) or is_booking_manager(request.user)

        # Prepare extendedProps, redacting sensitive info if not authorized
        extended_props = {
            'pk': reservation.pk,
        }

        if is_organizer_or_manager:
            extended_props['organizer_username'] = reservation.organizer.username
            extended_props['room_name'] = reservation.room.name
            extended_props['it_support'] = 'Yes' if reservation.it_support_needed else 'No'
            extended_props['description'] = reservation.description
            extended_props['attendee_list'] = [{'name': attendee.user.get_full_name() if attendee.user else attendee.email, 'value': attendee.email} for attendee in reservation.attendees.all()]
        else:
            # Redact all sensitive information for unauthorized users
            extended_props['organizer_username'] = 'کاربر دیگر' # Other User
            extended_props['room_name'] = 'اتاق خصوصی' # Private Room
            extended_props['it_support'] = 'نامشخص' # Unknown
            extended_props['description'] = 'اطلاعات خصوصی' # Private Information
            extended_props['attendee_list'] = [] # Empty list

        if reservation.recurrence_rule:
            if not reservation.start_time:
                continue

            for occurrence in reservation.recurrence_rule.between(start_date, end_date, inc=True):
                if timezone.is_aware(reservation.start_time) and timezone.is_naive(occurrence):
                    occurrence = timezone.make_aware(occurrence, timezone.get_current_timezone())
                elif timezone.is_naive(reservation.start_time) and timezone.is_aware(occurrence):
                    occurrence = timezone.make_naive(occurrence)

                event_start = occurrence
                event_end = occurrence + reservation.duration if reservation.duration else occurrence + timedelta(hours=1)

                events.append({
                    'title': reservation.title,
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                    'url': reverse('booking:reservation_detail', args=[reservation.pk]),
                    'allDay': False,
                    'color': reservation.room.color,
                    'extendedProps': extended_props # Use the prepared extended_props
                })
        else:
            if reservation.start_time and reservation.end_time:
                events.append({
                    'title': reservation.title,
                    'start': reservation.start_time.isoformat(),
                    'end': reservation.end_time.isoformat(),
                    'allDay': False,
                    'color': reservation.room.color,
                    'extendedProps': extended_props # Use the prepared extended_props
                })
    return JsonResponse(events, safe=False)



def manage_attendees(reservation, new_attendee_emails):
    """
    Manages Attendee objects for a given reservation.
    Removes old attendees, adds new ones, and links to User objects if found.
    """
    existing_attendee_emails = {a.email for a in reservation.attendees.all()}
    new_attendee_emails_set = set(new_attendee_emails)

    # Remove old attendees
    emails_to_remove = existing_attendee_emails - new_attendee_emails_set
    for email in emails_to_remove:
        reservation.attendees.filter(email=email).delete()

    # Add new attendees
    emails_to_add = new_attendee_emails_set - existing_attendee_emails
    for email in emails_to_add:
        attendee = Attendee(reservation=reservation, email=email)
        try:
            user = User.objects.get(email=email)
            attendee.user = user
        except User.DoesNotExist:
            pass  # Leave user as None if not found
        attendee.save()
        
@require_POST
@login_required
def reservation_quick_create_api(request):
    try:
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description', '')  # Default to empty string if not provided
        it_support_needed = data.get('it_support_needed', False) # Default to False if not provided
        attendees_emails = data.get('attendees', []) # Get attendees emails
        start_str = data.get('start')
        end_str = data.get('end')
        room_id = data.get('room_id')

        if not all([title, start_str, end_str]):
            return JsonResponse({'error': 'Missing required fields (title, start, end).'}, status=400)

        if not room_id:
            return JsonResponse({'error': 'Room ID is required.'}, status=400)

        try:
            start_time = parse_datetime(start_str)
            end_time = parse_datetime(end_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date/time format.'}, status=400)

        if not start_time or not end_time:
            return JsonResponse({'error': 'Invalid date/time values.'}, status=400)

        if start_time >= end_time:
            return JsonResponse({'error': 'Start time must be before end time.'}, status=400)

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found.'}, status=400)

        # Conflict Detection
        conflicting_reservations = Reservation.objects.filter(
            room=room,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if conflicting_reservations.exists():
            return JsonResponse({'error': 'This time slot conflicts with an existing reservation.'}, status=400)

        reservation = Reservation.objects.create(
            title=title,
            description=description,
            it_support_needed=it_support_needed,
            start_time=start_time,
            end_time=end_time,
            room=room,
            organizer=request.user,
            duration=end_time - start_time
        )
        
        manage_attendees(reservation, attendees_emails)

        return JsonResponse({'message': 'Reservation created successfully!', 'id': reservation.id}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
    except Exception as e:
        logger.error("Error creating quick reservation: %s", e, exc_info=True)
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)


from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

@require_http_methods(["PUT"]) # This view only accepts PUT requests
@login_required
def reservation_update_api(request, pk):
    try:
        reservation = get_object_or_404(Reservation, pk=pk)

        # Security Check: Ensure the user owns this reservation or is a manager
        if reservation.organizer != request.user and not is_booking_manager(request.user):
            return JsonResponse({'error': 'شما فقط می‌توانید رزروهای خود را ویرایش کنید.'}, status=403)

        data = json.loads(request.body)
        
        # --- Data Extraction and Validation ---
        title = data.get('title')
        room_id = data.get('room_id')
        start_str = data.get('start')
        end_str = data.get('end')
        attendees_emails = data.get('attendees', []) # Get attendees emails

        if not all([title, room_id, start_str, end_str]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        try:
            room = Room.objects.get(id=room_id)
            start_time = parse_datetime(start_str)
            end_time = parse_datetime(end_str)
        except (Room.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid room ID or date/time format.'}, status=400)
        
        if start_time >= end_time:
            return JsonResponse({'error': 'Start time must be before end time.'}, status=400)

        # --- Conflict Detection (excluding the current reservation) ---
        conflicting = Reservation.objects.filter(
            room=room,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(pk=pk) # Exclude the reservation we are currently editing

        if conflicting.exists():
            return JsonResponse({'error': 'This time slot conflicts with another reservation.'}, status=400)

        # --- Update the reservation object ---
        reservation.title = title
        reservation.room = room
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.description = data.get('description', '')
        reservation.it_support_needed = data.get('it_support_needed', False)
        reservation.duration = end_time - start_time
        # Note: Recurrence editing is not handled in this simplified API.
        reservation.recurrence_rule = None

        reservation.save()
        manage_attendees(reservation, attendees_emails)

        return JsonResponse({'message': 'Reservation updated successfully!', 'id': reservation.id})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        logger.error(f"Error updating reservation {pk}: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)
# --- END OF CHANGES - Step 1 ---

@require_http_methods(["DELETE"]) # This view only accepts DELETE requests
@login_required
def reservation_delete_api(request, pk):
    try:
        reservation = get_object_or_404(Reservation, pk=pk)

        # Security Check: User must be the organizer or a manager to delete
        if reservation.organizer != request.user and not is_booking_manager(request.user):
            return JsonResponse({'error': 'You do not have permission to delete this reservation.'}, status=403)

        reservation.delete()

        return JsonResponse({'message': 'Reservation deleted successfully.'}, status=200)

    except Exception as e:
        logger.error(f"Error deleting reservation {pk}: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)
@login_required
def user_search_api(request):
    search_term = request.GET.get('q', '')

    if len(search_term) < 2:
        return JsonResponse([], safe=False)

    users = User.objects.filter(
        Q(username__icontains=search_term) |
        Q(first_name__icontains=search_term) |
        Q(last_name__icontains=search_term) |
        Q(email__icontains=search_term)
    ).distinct()[:10]

    results = []
    for user in users:
        full_name = user.get_full_name()
        display_name = full_name if full_name else user.username
        results.append({
            'value': user.email,
            'name': display_name,
            'email': user.email,
        })
    return JsonResponse(results, safe=False)

@require_http_methods(["PATCH"])
@login_required
def reservation_drag_update_api(request, pk):
    try:
        reservation = get_object_or_404(Reservation, pk=pk)

        if reservation.organizer != request.user and not is_booking_manager(request.user):
            return JsonResponse({'error': 'شما فقط می‌توانید رزروهای خود را ویرایش کنید.'}, status=403)

        data = json.loads(request.body)
        start_str = data.get('start')
        end_str = data.get('end')

        if not start_str or not end_str:
            return JsonResponse({'error': 'Start and end times are required.'}, status=400)

        try:
            start_time = parse_datetime(start_str)
            end_time = parse_datetime(end_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date/time format.'}, status=400)

        if start_time >= end_time:
            return JsonResponse({'error': 'Start time must be before end time.'}, status=400)

        # Conflict Detection
        conflicting = Reservation.objects.filter(
            room=reservation.room,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(pk=pk)

        if conflicting.exists():
            return JsonResponse({'error': 'This time slot conflicts with another reservation.'}, status=400)

        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.duration = end_time - start_time
        reservation.save(update_fields=['start_time', 'end_time', 'duration'])

        return JsonResponse({'message': 'Reservation updated successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        logger.error(f"Error updating reservation {pk} via drag: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)