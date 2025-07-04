from django.urls import path
from .views import ReservationListView, ReservationDetailView, ReservationCreateView, ReservationUpdateView, ReservationDeleteView, reservation_api, CalendarView

app_name = 'booking'

urlpatterns = [
    path('', CalendarView.as_view(), name='reservation_list'),
    path('<int:pk>/', ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservations/new/', ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/<int:pk>/edit/', ReservationUpdateView.as_view(), name='reservation_edit'),
    path('reservations/<int:pk>/delete/', ReservationDeleteView.as_view(), name='reservation_delete'),
    path('api/reservations/', reservation_api, name='reservation_api'),
]