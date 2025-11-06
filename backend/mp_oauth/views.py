# backend/mp_oauth/views.py
from django.shortcuts import render
import os, requests
from django.http import JsonResponse
from .models import MPClient

MP_CLIENT_ID = os.getenv("MP_CLIENT_ID")
MP_CLIENT_SECRET = os.getenv("MP_CLIENT_SECRET")
MP_REDIRECT_URI = os.getenv("MP_REDIRECT_URI")

def install_link_mp(request):
    """
    Devuelve el enlace para que el cliente autorice la app de Mercado Pago.
    """
    link = (
        f"https://auth.mercadopago.com/authorization?"
        f"response_type=code&client_id={MP_CLIENT_ID}&"
        f"redirect_uri={MP_REDIRECT_URI}"
    )
    return JsonResponse({"install_link": link})


def mp_callback(request):
    """
    Recibe el authorization_code desde Mercado Pago y obtiene los tokens.
    """
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No se recibió authorization_code"}, status=400)

    token_url = "https://api.mercadopago.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": MP_CLIENT_ID,
        "client_secret": MP_CLIENT_SECRET,
        "code": code,
        "redirect_uri": MP_REDIRECT_URI
    }

    headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}

    res = requests.post(token_url, data=payload, headers=headers)
    if res.status_code != 200:
        return JsonResponse({"error": "Error al obtener tokens", "details": res.json()}, status=res.status_code)

    data = res.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    user_id = data.get("user_id")

    # Obtener public_key
    user_info = requests.get(f"https://api.mercadopago.com/users/me", headers={"Authorization": f"Bearer {access_token}"})
    public_key = user_info.json().get("public_key") if user_info.status_code == 200 else None

    client, created = MPClient.objects.get_or_create(user_id=user_id)
    client.access_token = access_token
    client.refresh_token = refresh_token
    client.public_key = public_key
    client.save()

    return JsonResponse({
        "status": "success",
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "public_key": public_key
    })

