from django.contrib import admin
from .models import Room, Reservation, Attendee

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_active', 'color')
    list_filter = ('is_active',)
    search_fields = ('name',)

class AttendeeInline(admin.TabularInline):
    model = Attendee
    fields = ('email', 'user')
    extra = 1

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'organizer', 'start_time', 'end_time', 'recurrence_rule', 'duration')
    fields = ('title', 'room', 'organizer', 'start_time', 'end_time', 'recurrence_rule', 'duration', 'it_support_needed', 'description')
    list_filter = ('room',)
    date_hierarchy = 'start_time'
    search_fields = ('title', 'organizer__username')
    inlines = [AttendeeInline]
