#ContactsCreate/models.py
from django.db import models
from ghlmp_updates.ghl_client import add_tag_to_contact, set_custom_field


class Contact(models.Model):
    """Representa un contacto creado o sincronizado desde GoHighLevel."""

    ghl_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # ID de GHL
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    location_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        nombre = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return nombre or f"Contacto sin nombre ({self.email or 'sin email'})"

    def mark_paid(self, payment_id):
        if not self.payment_id:
            self.payment_id = payment_id
            self.status = "paid"
            self.save()

        # 🔹 Sincronizar con GoHighLevel
        try:
            add_tag_to_contact(self.contact_id, "pago_confirmado")
            set_custom_field(self.contact_id, "payment_status", "paid")
            print(f"[GHL] Contacto {self.contact_id} actualizado correctamente.")
        except Exception as e:
            print(f"[ERROR GHL Sync] {e}")

