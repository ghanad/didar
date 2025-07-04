from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Reservation
from django.utils import timezone

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
