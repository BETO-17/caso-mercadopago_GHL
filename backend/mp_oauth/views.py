# backend/mp_oauth/views.py
from django.shortcuts import redirect
import requests
from django.http import JsonResponse
from django.conf import settings
from .models import MPClient
from ghl_oauth.models import GHLClient, FlowState  # AGREGADO: Para recovery de location_id via DB
from ghl_oauth.utils import refresh_ghl_token
from .utils import refresh_mp_token
import logging

logger = logging.getLogger(__name__)

MP_CLIENT_ID = settings.MP_CLIENT_ID
MP_CLIENT_SECRET = settings.MP_CLIENT_SECRET
MP_REDIRECT_URI = settings.MP_REDIRECT_URI

def install_link_mp(request):
    # AGREGADO: Incluye state si viene de session (para chain GHL, pero usa DB en callback)
    state = request.session.get('flow_state', '')  # De GHL si directo
    params = (
        f"response_type=code&client_id={MP_CLIENT_ID}&"
        f"redirect_uri={MP_REDIRECT_URI}"
    )
    if state:
        params += f"&state={state}"  # Pasa state de GHL a MP
    params += "&scope=read write"  # AGREGADO: Scopes para user_id/public_key
    link = f"https://auth.mercadopago.com/authorization?{params}"
    logger.info(f"DEBUG MP Install: Generated link with state={state if state else 'none'}")
    return JsonResponse({"install_link": link})

def mp_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")  # AGREGADO: Maneja errores de MP (e.g., access_denied)

    if error:
        logger.error(f"MP Auth Error: {error} (description: {request.GET.get('error_description')})")
        return JsonResponse({"error": f"Error en autorización MP: {error}"}, status=400)

    if not code:
        return JsonResponse({"error": "No se recibió authorization_code"}, status=400)

    logger.info(f"DEBUG MP: code={code[:20]}..., state={state}")

    # AGREGADO: Chequea state vs DB FlowState (de GHL; unificado para chain)
    try:
        flow = FlowState.objects.get(state=state)
        ghl_location_id = flow.ghl_location_id
        logger.info(f"DEBUG MP: State validated from DB, location_id={ghl_location_id}")
    except FlowState.DoesNotExist:
        logger.error(f"STATE NOT FOUND in DB: {state}")
        ghl_location_id = 'default'  # Fallback, pero loggea para debug
        # Opcional: return JsonResponse({"error": "State mismatch (flujo inválido)"}, status=400)

    # AGREGADO: Chequea state vs session (opcional para dev; descomenta en prod con HTTPS)
    # session_state = request.session.get('flow_state')
    # if state != session_state:
    #     logger.error(f"STATE MISMATCH: received={state}, session={session_state}")
    #     return JsonResponse({"error": "State mismatch (posible session perdida)"}, status=400)

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
    
    logger.info(f"DEBUG MP Token Exchange: Status={res.status_code}, Payload URI={payload['redirect_uri']}, Response={res.text[:200]}...")

    if res.status_code != 200:
        error_details = res.json() if res.text else res.text
        logger.error(f"Token Error Details: {error_details}")
        return JsonResponse({"error": "Error al obtener tokens", "details": error_details}, status=res.status_code)

    data = res.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    user_id = data.get("user_id")

    if not access_token or not user_id:
        logger.error(f"Tokens incompletos: access={bool(access_token)}, user_id={user_id}")
        return JsonResponse({"error": "Tokens incompletos en respuesta"}, status=400)

    # User info con mejor manejo
    user_info = requests.get(f"https://api.mercadopago.com/users/me", headers={"Authorization": f"Bearer {access_token}"})
    logger.info(f"DEBUG MP User Info: Status={user_info.status_code}")
    public_key = None
    if user_info.status_code == 200:
        public_key = user_info.json().get("public_key")
    else:
        logger.warning(f"User Info Failed: {user_info.text}")

    # Guarda en model
    client, created = MPClient.objects.get_or_create(user_id=user_id)
    client.access_token = access_token
    client.refresh_token = refresh_token
    client.public_key = public_key
    client.save()
    logger.info(f"DEBUG MP: Client saved for user_id={user_id}, created={created}")

    # AGREGADO: Limpia FlowState usado (buena practice)
    FlowState.objects.filter(state=state).delete()

    # AGREGADO: Opcional refresh GHL si needed (de tu utils)
    # refresh_ghl_token(ghl_location_id)  # Si tokens expiran rápido

    # Redirige directo a crear contacto con location_id de DB
    logger.info(f"DEBUG MP: Redirecting to contacts with location_id={ghl_location_id}")
    return redirect(f'/api/contacts/create/?location_id={ghl_location_id}')