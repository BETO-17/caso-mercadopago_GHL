import os, requests
from .models import MPClient

MP_CLIENT_ID = os.getenv("MP_CLIENT_ID")
MP_CLIENT_SECRET = os.getenv("MP_CLIENT_SECRET")

def refresh_mp_token(client: MPClient):
    url = "https://api.mercadopago.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": MP_CLIENT_ID,
        "client_secret": MP_CLIENT_SECRET,
        "refresh_token": client.refresh_token
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}

    res = requests.post(url, data=payload, headers=headers)
    if res.status_code == 200:
        data = res.json()
        client.access_token = data.get("access_token")
        client.refresh_token = data.get("refresh_token")
        client.save()
        return True
    return False
