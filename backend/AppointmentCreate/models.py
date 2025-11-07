# AppointmentCreate/models.py
import uuid
from django.db import models
from ContactsCreate.models import Contact
from ghlmp_updates.ghl_client import add_tag_to_contact, set_custom_field

class Appointment(models.Model):
    """Representa una cita creada o sincronizada desde GoHighLevel."""

    local_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ghl_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    location_id = models.CharField(max_length=100)
    calendar_id = models.CharField(max_length=100, null=True, blank=True)  # FIX: null=True, blank=True
    # 🔹 Relación directa con el modelo Contact
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="appointments")
    title = models.CharField(max_length=200, default="Cita", null=True, blank=True)  # FIX
    appointment_status = models.CharField(max_length=50, default="confirmed")
    assigned_user_id = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)  # FIX
    end_time = models.DateTimeField(null=True, blank=True)  # FIX
    source = models.CharField(max_length=50, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title or 'Cita'} ({self.ghl_id})"

    def mark_paid(self, payment_id):
        self.local_id = payment_id
        self.appointment_status = "paid"
        self.save()

        # 🔹 Sincronizar con GoHighLevel
        try:
            add_tag_to_contact(self.contact.ghl_id, "pago_confirmado")
            set_custom_field(self.contact.ghl_id, "payment_status", "paid")
            print(f"[GHL] Cita {self.ghl_id} actualizada correctamente.")
        except Exception as e:
            print(f"[ERROR GHL Sync] {e}")


