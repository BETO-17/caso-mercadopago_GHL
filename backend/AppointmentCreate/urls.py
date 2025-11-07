# AppointmentCreate/urls.py
from django.urls import path
from . import views  # Importa todas las funciones de views

urlpatterns = [
    path('create/', views.create_appointment, name="create_appointment"),
    path("webhooks/appointments/", views.appointment_webhook, name="appointment_webhook"),
    path("webhooks/ghl/appointments/", views.appointment_webhook, name="ghl_appointment_webhook"),  # Usa la misma función
]