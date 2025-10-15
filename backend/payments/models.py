# payments/models.py
from django.db import models
from ghlmp_updates.ghl_client import add_tag_to_contact, set_custom_field

class PaymentPreference(models.Model):
    '''Model to store payment preferences for appointments.'''

    appointment_id = models.CharField(max_length=128)
    contact_id = models.CharField(max_length=128)
    preference_id = models.CharField(max_length=128, unique=True)
    init_point = models.URLField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=32, default="pending")  # pending | paid | failed
    payment_id = models.CharField(max_length=128, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
