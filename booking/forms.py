from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['title', 'room', 'start_time', 'end_time', 'it_support_needed', 'description']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not all([room, start_time, end_time]):
            # Not all fields are present, let Django's default validation handle it
            return cleaned_data

        # Check for overlapping reservations
        overlapping_reservations = Reservation.objects.filter(
            room=room,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        # If this is an update, exclude the current reservation from the overlap check
        if self.instance and self.instance.pk:
            overlapping_reservations = overlapping_reservations.exclude(pk=self.instance.pk)

        if overlapping_reservations.exists():
            raise forms.ValidationError(
                "This room is already booked for the selected time slot. Please choose a different time or room."
            )

        return cleaned_data