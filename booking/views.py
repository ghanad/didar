from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Reservation, Room
from .forms import ReservationForm
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta

# این کلاس دیگر استفاده نمی‌شود اما برای کامل بودن نگه می‌داریم
class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'booking/reservation_list.html'
    context_object_name = 'reservations'
    ordering = ['start_time']

    def get_queryset(self):
        return super().get_queryset().filter(start_time__gt=timezone.now())

class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = 'booking/reservation_detail.html'
    context_object_name = 'reservation'

class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'booking/reservation_form.html'
    # FIX: Add app_name 'booking' to the success_url
    success_url = reverse_lazy('booking:reservation_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        if form.instance.start_time and form.instance.end_time:
            form.instance.duration = form.instance.end_time - form.instance.start_time
        return super().form_valid(form)

class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'booking/reservation_form.html'
    # FIX: Add app_name 'booking' to the success_url
    success_url = reverse_lazy('booking:reservation_list')

    def get_queryset(self):
        # این متد برای امنیت ضروری است
        return self.model.objects.filter(organizer=self.request.user)

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'booking/calendar_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.filter(is_active=True)
        return context

class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'booking/reservation_confirm_delete.html'
    # FIX: Add app_name 'booking' to the success_url
    success_url = reverse_lazy('booking:reservation_list')

    def get_queryset(self):
        # این متد برای امنیت ضروری است
        return self.model.objects.filter(organizer=self.request.user)

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
                })
        else:
            if reservation.start_time and reservation.end_time:
                events.append({
                    'title': reservation.title,
                    'start': reservation.start_time.isoformat(),
                    'end': reservation.end_time.isoformat(),
                    'url': reverse('booking:reservation_detail', args=[reservation.pk]),
                    'allDay': False,
                })
    return JsonResponse(events, safe=False)