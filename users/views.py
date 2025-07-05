from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('booking:calendar_view')

class CustomLogoutView(LogoutView):
    next_page = '/login/'