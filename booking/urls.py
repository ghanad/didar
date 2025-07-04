from django.urls import path
from .views import reservation_api, CalendarView, reservation_quick_create_api, reservation_update_api, reservation_delete_api

app_name = 'booking'

urlpatterns = [
    # The calendar is now the main view
    path('', CalendarView.as_view(), name='calendar_view'),
    
    # API Endpoints
    path('api/reservations/', reservation_api, name='reservation_api'),
    path('api/reservations/quick_create/', reservation_quick_create_api, name='reservation_quick_create_api'),
    path('api/reservations/<int:pk>/update/', reservation_update_api, name='reservation_update_api'),
    path('api/reservations/<int:pk>/delete/', reservation_delete_api, name='reservation_delete_api'),
]