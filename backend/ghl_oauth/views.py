# backend/ghl_oauth/views.py
from django.shortcuts import render, redirect
import requests
from django.http import JsonResponse
from django.conf import settings
from .models import GHLClient, FlowState  # Para DB temporal
import uuid
import logging

logger = logging.getLogger(__name__)

GHL_CLIENT_ID = settings.GHL_CLIENT_ID
GHL_CLIENT_SECRET = settings.GHL_CLIENT_SECRET
GHL_REDIRECT_URI = settings.GHL_REDIRECT_URI

def install_link(request):
    # AGREGADO: Genera state para CSRF (GHL lo soporta)
    state = str(uuid.uuid4())
    request.session['ghl_state'] = state  # Temporal en session para initial check (opcional)
    FlowState.objects.create(state=state, ghl_location_id=None)  # Placeholder, update en callback
    
    link = (
        f"https://marketplace.gohighlevel.com/oauth/chooselocation?"
        f"response_type=code&client_id={GHL_CLIENT_ID}"
        f"&redirect_uri={GHL_REDIRECT_URI}"
        f"&state={state}"  # AGREGADO: Para security
        f"&scope=contacts.read,contacts.write,locations.readonly,users.readonly"
    )
    logger.info(f"DEBUG GHL Install: Generated link with state={state}")
    return JsonResponse({"install_link": link})

def ghl_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")  # AGREGADO: Check state si viene
    
    if not code:
        return JsonResponse({"error": "missing_code"}, status=400)
    
    # AGREGADO: Check state vs session/DB (para security)
    session_state = request.session.get('ghl_state')
    db_state = FlowState.objects.filter(state=state).first()
    if state and (state != session_state and not db_state):
        logger.error(f"STATE MISMATCH in GHL: received={state}, session={session_state}")
        return JsonResponse({"error": "state_mismatch"}, status=400)

    token_url = "https://api.msgsndr.com/oauth/token"
    payload = {
        "client_id": GHL_CLIENT_ID,
        "client_secret": GHL_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": GHL_REDIRECT_URI,
    }

    token_res = requests.post(token_url, data=payload)
    logger.info(f"DEBUG GHL Token Exchange: Status={token_res.status_code}, Response={token_res.text[:200]}...")  # AGREGADO: Log para debug

    try:
        token_data = token_res.json()
    except Exception as e:
        logger.error(f"GHL JSON Parse Error: {e}, Raw: {token_res.text}")
        return JsonResponse({
            "error": "invalid_json_response",
            "details": token_res.text,
            "exception": str(e)
        }, status=400)

    if "access_token" not in token_data or token_res.status_code != 200:
        logger.error(f"GHL Invalid Token: {token_data}")
        return JsonResponse({"error": "invalid_token_response", "details": token_data}, status=400)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    location_id = token_data.get("locationId")
    if not location_id:
        me_url = "https://services.leadconnectorhq.com/users/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Version": "2021-07-28",
            "Accept": "application/json"
        }
        me_res = requests.get(me_url, headers=headers)
        logger.info(f"DEBUG GHL Users/Me: Status={me_res.status_code}")  # AGREGADO
        if me_res.status_code == 200:
            me_data = me_res.json()
            locations = me_data.get("company", {}).get("locations", [])
            if locations:
                location_id = locations[0].get("id")  # Asume primera; si multiple, elige via UI futura
            else:
                logger.warning("No locations in /users/me")
        else:
            logger.error(f"GHL Users/Me Failed: {me_res.text}")

    if not location_id:
        return JsonResponse({"error": "missing_location_id", "details": me_data if 'me_data' in locals() else token_data}, status=400)

    # Guarda/Actualiza client
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
    logger.info(f"DEBUG GHL: Client saved for location_id={location_id}, created={created}")

    # Actualiza FlowState con location_id
    if db_state:
        db_state.ghl_location_id = location_id
        db_state.save()
    else:
        # Crea nuevo para chain
        flow_state = str(uuid.uuid4())
        FlowState.objects.create(state=flow_state, ghl_location_id=location_id)
        logger.info(f"DEBUG GHL: Created flow_state={flow_state} for MP chain")

    # Redirige a MP con state (usa el flow_state nuevo para MP callback)
    mp_link = (
        f"https://auth.mercadopago.com/authorization?"
        f"response_type=code&client_id={settings.MP_CLIENT_ID}&"
        f"redirect_uri={settings.MP_REDIRECT_URI}&"
        f"state={flow_state}"  # Usa flow_state para recovery en MP
        f"&scope=read write"  # AGREGADO: Scopes para MP
    )
    logger.info(f"DEBUG GHL: Redirecting to MP with state={flow_state}")
    return redirect(mp_link)