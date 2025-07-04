from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Reservation
from .forms import ReservationForm
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

class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'booking/reservation_form.html'
    success_url = reverse_lazy('reservation_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'booking/reservation_form.html'
    success_url = reverse_lazy('reservation_list')

    def get_queryset(self):
        return super().get_queryset().filter(organizer=self.request.user)

class ReservationDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'booking/reservation_confirm_delete.html'
    success_url = reverse_lazy('reservation_list')

    def get_queryset(self):
        return super().get_queryset().filter(organizer=self.request.user)
