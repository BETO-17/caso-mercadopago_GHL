# backend/ghl_oauth/views.py
from django.shortcuts import render
import os, requests
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from .models import GHLClient


# Lee variables desde settings.py (o .env)
GHL_CLIENT_ID = os.getenv("GHL_CLIENT_ID")
GHL_CLIENT_SECRET = os.getenv("GHL_CLIENT_SECRET")
GHL_REDIRECT_URI = os.getenv("GHL_REDIRECT_URI")


def install_link(request):
    """Devuelve el link de instalación privada de GHL"""

    link = (
        f"https://marketplace.gohighlevel.com/oauth/chooselocation?"
        f"response_type=code&client_id={GHL_CLIENT_ID}"
        f"&redirect_uri={GHL_REDIRECT_URI}"
        f"&scope=contacts.read,contacts.write,locations.readonly,users.readonly")
    return JsonResponse({"install_link": link})

def ghl_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "missing_code"}, status=400)

    # Paso 1: Intercambiar authorization_code por access_token
    token_url = "https://api.msgsndr.com/oauth/token"
    payload = {
        "client_id": settings.GHL_CLIENT_ID,
        "client_secret": settings.GHL_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.GHL_REDIRECT_URI,
    }

    # ✅ IMPORTANTE: usar files= para multipart/form-data
    token_res = requests.post(token_url, data=payload)

    try:
        token_data = token_res.json()
    except Exception as e:
        return JsonResponse({
            "error": "invalid_json_response",
            "details": token_res.text,
            "exception": str(e)
        }, status=400)

    if "access_token" not in token_data:
        print("Error en token response:", token_data)
        return JsonResponse({"error": "invalid_token_response", "details": token_data}, status=400)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # --- Obtener el location_id ---
    location_id = token_data.get("locationId")
    # Paso 2: Obtener información del usuario para extraer location_id
    #https://services.leadconnectorhq.com/users/:userId
    #https://services.leadconnectorhq.com/api/v2/users/me
    if not location_id:
    # fallback a llamada de API si no viene en el token
        me_url = "https://services.leadconnectorhq.com/users/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Version": "2021-07-28",   # 👈 obligatorio
            "Accept": "application/json"
            }
        me_res = requests.get(me_url, headers=headers)
        me_data = me_res.json()
        locations = me_data.get("company", {}).get("locations", [])
        location_id = locations[0].get("id") if locations else None
    '''
    me_url = "https://services.leadconnectorhq.com/users/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": "2021-07-28",   # 👈 obligatorio
        "Accept": "application/json"
        }
    me_res = requests.get(me_url, headers=headers)
    me_data = me_res.json()

    # Algunos usuarios tienen más de una location; toma la principal
    locations = me_data.get("company", {}).get("locations", [])
    location_id = locations[0].get("id") if locations else None
    '''
    if not location_id:
        print("Error: no se pudo obtener location_id:", me_data)
        return JsonResponse({"error": "missing_location_id", "details": me_data}, status=400)

    # Paso 3: Guardar en la base de datos
    client, created = GHLClient.objects.get_or_create(
        location_id=location_id,
        defaults={
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    )

    if not created:
        client.access_token = access_token
        client.refresh_token = refresh_token
        client.save()

    return JsonResponse({
        "status": "ok",
        "location_id": location_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    })