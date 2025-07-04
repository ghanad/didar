Project Chronos: Meeting Room Booking System
1. Project Vision
Project Chronos is an internal, web-based application designed to streamline and manage the reservation of company meeting rooms. The primary goal is to optimize the use of company resources, prevent scheduling conflicts, and provide a transparent, user-friendly interface for all employees to book meeting spaces.
2. Technology Stack
This project will be built using a reliable and rapid-development-focused stack, ideal for a solo developer.
Backend: Python 3.10+ with Django 4.x
Database:
Development (MVP): SQLite (Default with Django, zero setup required)
Production: PostgreSQL (Recommended for future deployment)
Frontend (MVP): Plain HTML, CSS, and minimal JavaScript, styled with Bootstrap 5 for a clean, responsive UI without the complexity of a JS framework.
Key Libraries:
django-auth-ldap: For Active Directory integration (Post-MVP core).
Pillow: For any potential image/file uploads.
3. MVP Scope: The Core Deliverable
The Minimum Viable Product (MVP) will focus on delivering the essential functionality to make the system usable. All other features will be built upon this stable foundation.
User Authentication: Initial login will use Django's built-in user system for development speed. LDAP will be the first major feature post-MVP.
Room Management (Admin Only):
Admins can Create, Update, and De-activate rooms via the Django Admin Panel.
Each room will have a name, capacity, and an is_active status.
Reservation Management (For Authenticated Users):
Users can create a new reservation for an active room.
Users can view a list of all upcoming reservations.
Users can only edit or cancel reservations they have created.
Conflict Detection: The system will strictly prevent double-booking a room for the same time slot.
Basic Notifications: An automatic email will be sent to a predefined IT support address if the "IT Support Required" checkbox is ticked during booking.
4. MVP Development Roadmap
This roadmap is broken down into small, sequential, and achievable steps. Each step represents a clear task you can work on with your LLM assistant.
Step 0: Project Initialization
Create a new Django project (django-admin startproject project_chronos).
Create a new Django app for the core logic (python manage.py startapp booking).
Add the new app to INSTALLED_APPS in settings.py.
Initialize a Git repository (git init) and make your first commit.
Step 1: Data Modeling (models.py)
Define the Room model with fields: name (CharField), capacity (PositiveIntegerField), is_active (BooleanField, default=True).
Define the Reservation model with fields:
title (CharField)
room (ForeignKey to Room)
organizer (ForeignKey to Django's User model)
start_time (DateTimeField)
end_time (DateTimeField)
it_support_needed (BooleanField, default=False)
description (TextField, optional)
Run makemigrations and migrate.
Step 2: The Admin Panel (admin.py)
Register the Room and Reservation models in the booking/admin.py file.
Use list_display to customize the admin view for rooms, showing name, capacity, and is_active status.
This provides a fully functional UI for the System Admin role instantly.
Step 3: User-Facing Views - Read-Only (views.py & Templates)
Create a ReservationListView (using Django's ListView) to display a list of all upcoming reservations in a simple table.
Create a ReservationDetailView (using Django's DetailView) to show the details of a single reservation.
Create the corresponding HTML templates using Bootstrap 5 for styling.
Step 4: Create Reservation Form & Logic (forms.py, views.py)
Create a ReservationForm using Django's ModelForm.
Create a ReservationCreateView (using Django's CreateView) to display the form.
Implement Conflict Detection: In the form's clean() method or the view's form_valid() method, add the logic to check if the selected room has any other reservations that overlap with the requested start_time and end_time. If there is a conflict, raise a ValidationError.
Step 5: Edit & Delete Views (views.py & Templates)
Create an ReservationUpdateView and ReservationDeleteView.
Implement Permissions: Crucially, ensure these views check that request.user is the organizer of the reservation before allowing any changes.
Step 6: Basic Email Notification
Configure SMTP settings in settings.py for sending emails.
Use a Django Signal (post_save on the Reservation model) to check if it_support_needed is True and, if so, send a basic email to the IT department.
5. Post-MVP & Future Goals (The Roadmap Ahead)
Once the MVP is stable and deployed internally, we will proceed with the features from the original proposal.
Phase 2: Integration & Enhancements
LDAP/Active Directory Integration using django-auth-ldap.
Calendar View: Implement a full-featured calendar (e.g., using FullCalendar.js) with day/week/month views.
Recurring Reservations: Add functionality to create daily, weekly, or monthly bookings.
Advanced Notifications: Comprehensive email system for confirmations, reminders, and cancellations.
Catering & IT Roles: Create specific views and notification systems for these teams.
Phase 3: Advanced Features
Reporting Dashboard: A view for admins to see statistics on room usage.
Outlook/Google Calendar Integration: Automatically create events in attendees' calendars.
Enhanced Mobile-Friendly (Responsive) Design.
6. Getting Started (Setup Instructions)
Generated bash
# 1. Clone the repository (once it's created on GitHub/GitLab)
git clone <your-repo-url>
cd project-chronos

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt  # You will create this file

# 4. Apply database migrations
python manage.py migrate

# 5. Create a superuser to access the admin panel
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver

# 7. Access the application at http://127.0.0.1:8000
#    Access the admin panel at http://127.0.0.1:8000/admin