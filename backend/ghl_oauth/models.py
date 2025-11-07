# ghl_oauth/models.py
from django.db import models
import uuid  # Solo para state UUID, no para id

class GHLClient(models.Model):
    """Modelo para guardar tokens y metadata de GHL OAuth por location."""
    location_id = models.CharField(max_length=100, unique=True)  # ID único de location en GHL
    access_token = models.TextField()  # Token de acceso (caduca ~1h)
    refresh_token = models.TextField()  # Token para refresh (largo plazo)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GHL Client for location {self.location_id}"

    class Meta:
        verbose_name = "GHL Client"
        verbose_name_plural = "GHL Clients"

class FlowState(models.Model):
    """Modelo temporal para trackear flow GHL → MP (state + location_id)."""
    # QUITADO: id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) – Usa default AutoField
    state = models.CharField(max_length=255, unique=True)  # UUID string para CSRF y chain
    ghl_location_id = models.CharField(max_length=100, null=True, blank=True)  # Permite None inicial
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FlowState {self.state} for location {self.ghl_location_id or 'pending'}"

    class Meta:
        verbose_name = "Flow State"
        verbose_name_plural = "Flow States"
        indexes = [models.Index(fields=['state'])]  # Para queries rápidas