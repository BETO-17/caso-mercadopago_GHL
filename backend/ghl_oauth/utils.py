from .models import GHLClient
import requests
from django.conf import settings
from datetime import datetime

def refresh_ghl_token(client: GHLClient):
    """
    Refresca el access_token de un cliente de GHL usando su refresh_token.
    """
    url = "https://services.leadconnectorhq.com/oauth/token"
    payload = {
        "client_id": settings.GHL_CLIENT_ID,
        "client_secret": settings.GHL_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": client.refresh_token,
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        client.access_token = data["access_token"]
        client.refresh_token = data.get("refresh_token", client.refresh_token)
        client.save()
        print(f"🔁 Token actualizado para {client.location_id}")
        return True
    else:
        print(f"⚠️ Error al refrescar token ({client.location_id}): {response.text}")
        return False
