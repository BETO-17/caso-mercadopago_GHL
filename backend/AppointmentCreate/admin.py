# AppointmentCreate/admin.py
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'appointment_status', 'contact', 'ghl_id']
    list_filter = ['appointment_status', 'start_time']
    search_fields = ['title', 'notes']
    raw_id_fields = ['contact']  # Para FK grande