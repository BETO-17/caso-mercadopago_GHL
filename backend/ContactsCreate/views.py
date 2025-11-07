# ContactsCreate/views.py
from django.conf import settings
from django.http import HttpResponseRedirect  # AGREGADO: Para redirect automático
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json
import os
import logging
from .models import Contact
from ghl_oauth.models import GHLClient

# Cargar .env
load_dotenv()

logger = logging.getLogger(__name__)

# Constantes GHL
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = os.getenv("GHL_API_VERSION", "2021-04-15")
ACCESS_TOKEN = os.getenv("GHL_ACCESS_TOKEN")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GHL_API_URL = f"{GHL_BASE_URL}/contacts/"
GHL_TOKEN = ACCESS_TOKEN

if not ACCESS_TOKEN:
    raise Exception("Access Token de GHL no configurado en .env (GHL_ACCESS_TOKEN)")

# Helper para token dinámico de DB
def get_ghl_token(location_id):
    """Obtiene token de GHLClient DB; fallback a .env si no existe."""
    try:
        client = GHLClient.objects.get(location_id=location_id)
        logger.info(f"Using dynamic token from DB for location {location_id}")
        return client.access_token
    except GHLClient.DoesNotExist:
        logger.warning(f"No GHLClient found for location {location_id}; fallback to .env token")
        return GHL_TOKEN

# 🔹 Crear contacto en GHL y guardarlo localmente
@api_view(['GET', 'POST'])
def create_contact(request):
    if request.method == 'GET':
        # GET: Activa UI DRF (form para POST manual en navegador)
        location_id = request.GET.get('location_id', GHL_LOCATION_ID)
        return Response({
            "message": "Usa POST para crear contacto manual.",
            "example_data": {
                "first_name": "",
                "last_name": "",
                "email": "",
                "phone": "",
                "location_id": location_id
            }
        })

    # POST: Tu lógica exacta para crear
    data = request.data
    email = data.get("email")
    phone = data.get("phone")

    # Check si contacto ya existe localmente (por email o phone)
    if email or phone:
        existing_contact = None
        if email:
            existing_contact = Contact.objects.filter(email=email).first()
        if phone and not existing_contact:
            existing_contact = Contact.objects.filter(phone=phone).first()

        if existing_contact:
            # Contacto existe: Responde con opciones (editar o ir a citas)
            update_url = f"/api/contacts/update/{existing_contact.id}/"
            return Response({
                "message": "Contacto ya existe. Elige: editarlo o ir a citas.",
                "contact_exists": True,
                "contact_id": existing_contact.id,
                "ghl_id": existing_contact.ghl_id,
                "update_url": update_url,
                "redirect_to_appointment": f"/api/appointmentcreate/create/?contact_id={existing_contact.id}",
                "current_data": {
                    "first_name": existing_contact.first_name,
                    "last_name": existing_contact.last_name,
                    "email": existing_contact.email,
                    "phone": existing_contact.phone,
                    "location_id": existing_contact.location_id
                }
            }, status=status.HTTP_200_OK)

    location_id = data.get("location_id") or GHL_LOCATION_ID
    ghl_payload = {
        "firstName": data.get("first_name"),
        "lastName": data.get("last_name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "locationId": location_id,
    }

    # Usa token dinámico de DB
    token = get_ghl_token(location_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28"
    }

    logger.info(f"POST to GHL with token (first 20 chars): {token[:20]}..., location_id={location_id}")

    ghl_response = requests.post(GHL_API_URL, json=ghl_payload, headers=headers)
    logger.info(f"GHL Response Status: {ghl_response.status_code}, Body: {ghl_response.text[:200]}...")

    if ghl_response.status_code in [200, 201]:
        ghl_data = ghl_response.json()
        ghl_contact = ghl_data.get("contact", {})

        # Guardar contacto localmente
        contact = Contact.objects.create(
            ghl_id=ghl_contact.get("id"),
            first_name=ghl_contact.get("firstName"),
            last_name=ghl_contact.get("lastName"),
            email=ghl_contact.get("email"),
            phone=ghl_contact.get("phone"),
            location_id=ghl_contact.get("locationId"),
        )

        # AGREGADO: Redirect automático a cita
        redirect_url = f"/api/appointmentcreate/create/?contact_id={contact.id}"
        return HttpResponseRedirect(redirect_url)  # Automático

    elif ghl_response.status_code == 400:
        # Si duplicado, actualiza con PUT (extrae ID del error)
        try:
            ghl_data = ghl_response.json()
            if "duplicated" in ghl_data.get("message", "").lower():
                existing_id = ghl_data.get("meta", {}).get("contactId")
                if existing_id:
                    update_url = f"{GHL_API_URL}{existing_id}?locationId={location_id}"
                    update_payload = ghl_payload
                    update_res = requests.put(update_url, json=update_payload, headers=headers)
                    logger.info(f"PUT Update Status: {update_res.status_code}, Body: {update_res.text[:200]}...")
                    
                    if update_res.status_code in [200, 201]:
                        updated_data = update_res.json()
                        ghl_contact = updated_data.get("contact", updated_data.get("data", {}))

                        # Actualiza local en Contact
                        contact, created = Contact.objects.update_or_create(
                            ghl_id=ghl_contact.get("id", existing_id),
                            defaults={
                                "first_name": ghl_contact.get("firstName", data.get("first_name")),
                                "last_name": ghl_contact.get("lastName", data.get("last_name")),
                                "email": ghl_contact.get("email", data.get("email")),
                                "phone": ghl_contact.get("phone", data.get("phone")),
                                "location_id": location_id,
                            },
                        )

                        # AGREGADO: Redirect automático a cita (incluso en dup)
                        redirect_url = f"/api/appointmentcreate/create/?contact_id={contact.id}"
                        return HttpResponseRedirect(redirect_url)  # Automático

                    else:
                        logger.error(f"PUT Failed for existing_id {existing_id}: {update_res.status_code}, {update_res.text}")
                        return Response({
                            "error": "Error al actualizar duplicado en GHL",
                            "details": update_res.text,
                            "hint": "Verifica token/location_id en /admin/ghl_oauth/ghlclient/"
                        }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Exception in dup handling: {e}")
            return Response({"error": f"Error al actualizar contacto: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    elif ghl_response.status_code == 401:
        logger.error(f"GHL 401 Invalid JWT for location {location_id}")
        return Response({
            "error": "Token GHL inválido o expirado (401 Invalid JWT).",
            "details": ghl_response.text,
            "hint": "Completa auth GHL primero (/install/ghl/) para token fresco."
        }, status=status.HTTP_401_UNAUTHORIZED)

    return Response({
        "error": "No se pudo crear contacto en GHL",
        "details": ghl_response.text
    }, status=status.HTTP_400_BAD_REQUEST)


# Update contacto existente
@api_view(['GET', 'PUT'])
def update_contact(request, contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return Response({"error": "Contacto no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            "message": "Usa PUT para actualizar contacto (envía solo los campos que cambies).",
            "current_data": {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "phone": contact.phone,
                "location_id": contact.location_id
            },
            "hint": "Ejemplo: Cambia solo 'phone': {\"phone\": \"+51999456489 nuevo\"}"
        })

    # PUT: Actualiza en GHL y local
    data = request.data
    location_id = data.get("location_id", contact.location_id)

    # Payload solo con campos que envíes (partial update)
    ghl_payload = {}
    if "first_name" in data and data["first_name"]:
        ghl_payload["firstName"] = data["first_name"]
    if "last_name" in data and data["last_name"]:
        ghl_payload["lastName"] = data["last_name"]
    if "email" in data and data["email"]:
        ghl_payload["email"] = data["email"]
    if "phone" in data and data["phone"]:
        ghl_payload["phone"] = data["phone"]

    if not ghl_payload:
        return Response({"error": "Envía al menos un campo para actualizar"}, status=status.HTTP_400_BAD_REQUEST)

    token = get_ghl_token(location_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Content-Type": "application/json"
    }

    update_url = f"{GHL_API_URL}{contact.ghl_id}?locationId={location_id}"
    ghl_response = requests.put(update_url, json=ghl_payload, headers=headers)

    if ghl_response.status_code in [200, 201]:
        ghl_data = ghl_response.json()
        ghl_contact = ghl_data.get("contact", {})
        
        update_fields = {}
        if "first_name" in data:
            update_fields["first_name"] = ghl_contact.get("firstName", data["first_name"])
        if "last_name" in data:
            update_fields["last_name"] = ghl_contact.get("lastName", data["last_name"])
        if "email" in data:
            update_fields["email"] = ghl_contact.get("email", data["email"])
        if "phone" in data:
            update_fields["phone"] = ghl_contact.get("phone", data["phone"])

        Contact.objects.filter(id=contact_id).update(**update_fields)
        updated_contact = Contact.objects.get(id=contact_id)

        # AGREGADO: Redirect automático a cita
        redirect_url = f"/api/appointmentcreate/create/?contact_id={updated_contact.id}"
        return HttpResponseRedirect(redirect_url)  # Automático

    else:
        return Response({
            "error": "Error al actualizar en GHL",
            "details": ghl_response.text
        }, status=status.HTTP_400_BAD_REQUEST)


# 🔔 Webhook para sincronizar contactos creados o actualizados en GHL
@csrf_exempt
def webhook_contact_created(request):
    if request.method == "POST":
        payload = json.loads(request.body)

        contact_data = payload.get("contact", {})
        if not contact_data:
            return JsonResponse({"error": "Payload sin contacto"}, status=400)

        contact, created = Contact.objects.update_or_create(
            ghl_id=contact_data.get("id"),
            defaults={
                "first_name": contact_data.get("firstName"),
                "last_name": contact_data.get("lastName"),
                "email": contact_data.get("email"),
                "phone": contact_data.get("phone"),
                "location_id": contact_data.get("locationId"),
            },
        )

        return JsonResponse({
            "message": "Contacto sincronizado correctamente",
            "created": created,
        })
    return JsonResponse({"error": "Solo POST"}, status=405)
    