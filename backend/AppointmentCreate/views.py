# AppointmentCreate/views.py
import os
import json
import uuid
from django.http import JsonResponse
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from .models import Appointment
from .serializers import AppointmentSerializer
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from ContactsCreate.models import Contact
from ghl_oauth.models import GHLClient
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Constantes GHL
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = os.getenv("GHL_API_VERSION", "2021-07-28")
ACCESS_TOKEN = os.getenv("GHL_ACCESS_TOKEN")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GHL_APPOINTMENTS_URL = f"{GHL_BASE_URL}/calendars/events/appointments/"

if not ACCESS_TOKEN:
    raise Exception("Access Token de GHL no configurado en .env (GHL_ACCESS_TOKEN)")

# Helper para token dinámico
def get_ghl_token(location_id):
    try:
        client = GHLClient.objects.get(location_id=location_id)
        logger.info(f"Using dynamic token from DB for appointment location {location_id}")
        return client.access_token
    except GHLClient.DoesNotExist:
        logger.warning(f"No GHLClient for location {location_id}; fallback to .env")
        return ACCESS_TOKEN

# Función para convertir ISO8601 a datetime aware
def _to_datetime(iso_str):
    if not iso_str:
        return None
    dt = parse_datetime(iso_str)
    if dt is None:
        return None
    if settings.USE_TZ and timezone.is_naive(dt):
        tz = timezone.get_current_timezone()
        dt = timezone.make_aware(dt, tz)
    return dt

# Crear cita (DRF UI para manual)
@api_view(['GET', 'POST'])
def create_appointment(request):
    if request.method == 'GET':
        # GET: DRF UI con example y prellenado si ?contact_id=
        contact_id = request.GET.get('contact_id')
        location_id = request.GET.get('location_id', GHL_LOCATION_ID)
        contact_data = {}
        if contact_id:
            try:
                contact = Contact.objects.get(id=contact_id)
                contact_data = {
                    "contact_id": contact.id,
                    "contact_name": f"{contact.first_name} {contact.last_name}",
                    "ghl_contact_id": contact.ghl_id  # Para payload GHL
                }
            except Contact.DoesNotExist:
                pass
        return Response({
            "message": "Usa POST para crear cita manual (requiere contact_id o or ghl_contact_id).",
            "example_data": {
                "title": "Consulta inicial",
                "calendar_id": "tu_calendar_id",  # De GHL calendars
                "start_time": "2025-11-08T10:00:00Z",  # ISO para GHL
                "end_time": "2025-11-08T11:00:00Z",
                "location_id": location_id,
                "contact_id": contact_id or "",  # Prellenado
                "notes": "Notas opcionales"
            },
            "contact_info": contact_data,  # Previsualiza si existe
            "hint": "Obtén calendar_id de GHL dashboard. Post-cita, ve a pagos."
        })

    # POST: Crea cita en GHL y local
    data = request.data
    location_id = data.get("location_id") or GHL_LOCATION_ID
    contact_id = data.get("contact_id") or request.GET.get("contact_id")

    # Valida contacto existe (FK)
    if not contact_id:
        return Response({"error": "Requiere contact_id"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return Response({"error": "Contacto no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Payload para GHL
    ghl_payload = {
        "calendarId": data.get("calendar_id"),
        "locationId": location_id,
        "contactId": contact.ghl_id,  # Usa ghl_id para GHL API
        "startTime": data.get("start_time"),
        "endTime": data.get("end_time"),
        "title": data.get("title", "Cita"),
        "notes": data.get("notes", ""),
    }

    # Valida campos requeridos (GHL rechaza sin ellos)
    required = ["calendarId", "startTime", "endTime"]
    for field in required:
        if not ghl_payload.get(field):
            return Response({
                "error": f"Campo requerido faltante: {field}",
                "hint": "Verifica 'calendar_id', 'start_time', 'end_time' en JSON."
            }, status=status.HTTP_400_BAD_REQUEST)

    token = get_ghl_token(location_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": GHL_API_VERSION,
        "Content-Type": "application/json"
    }

    logger.info(f"Payload to GHL: {json.dumps(ghl_payload, indent=2)}")
    logger.info(f"Headers to GHL: {headers}")

    ghl_response = requests.post(GHL_APPOINTMENTS_URL, json=ghl_payload, headers=headers)

    logger.info(f"GHL Status Code: {ghl_response.status_code}")
    logger.info(f"GHL Response Headers: {ghl_response.headers}")
    logger.info(f"GHL Response Text: '{ghl_response.text}'")

    if ghl_response.status_code in [200, 201]:
        ghl_data = ghl_response.json()
        # FIX: GHL response es flat (no "appointment" o "data" wrapper)
        ghl_appointment = ghl_data  # FIX: Usa directo ghl_data

        # Guarda local (FK a contact)
        appointment = Appointment.objects.create(
            ghl_id=ghl_appointment.get("id"),
            location_id=location_id,
            calendar_id=ghl_appointment.get("calendarId"),
            contact=contact,  # FK
            title=ghl_appointment.get("title"),
            appointment_status=ghl_appointment.get("appointmentStatus", "confirmed"),
            assigned_user_id=ghl_appointment.get("assignedUserId"),
            notes=ghl_appointment.get("notes"),
            start_time=_to_datetime(ghl_appointment.get("startTime")),
            end_time=_to_datetime(ghl_appointment.get("endTime")),
            source=ghl_appointment.get("source"),
        )

        return Response({
            "message": "Cita creada correctamente",
            "appointment_id": appointment.id,
            "ghl_id": appointment.ghl_id,
            "next_step": f"Ve a /api/payments/create/?appointment_id={appointment.id} para pagos"
        })

    elif ghl_response.status_code == 400:
        # Manejo dup (e.g., slot ocupado)
        try:
            ghl_data = ghl_response.json()
            if "duplicated" in ghl_data.get("message", "").lower():
                existing_id = ghl_data.get("meta", {}).get("appointmentId") or ghl_data.get("data", {}).get("id")
                if existing_id:
                    update_url = f"{GHL_APPOINTMENTS_URL}{existing_id}?locationId={location_id}"
                    update_res = requests.put(update_url, json=ghl_payload, headers=headers)
                    if update_res.status_code in [200, 201]:
                        # Update local
                        Appointment.objects.update_or_create(
                            ghl_id=existing_id,
                            defaults={
                                "calendar_id": ghl_payload["calendarId"],
                                "contact": contact,
                                "title": ghl_payload["title"],
                                "appointment_status": "confirmed",
                                "start_time": _to_datetime(ghl_payload["startTime"]),
                                "end_time": _to_datetime(ghl_payload["endTime"]),
                                "location_id": location_id,
                            }
                        )
                        return Response({"message": "Cita actualizada correctamente (duplicada)"})

        except Exception as e:
            pass

        return Response({
            "error": "No se pudo crear cita (posible duplicado o slot ocupado)",
            "details": ghl_response.text
        }, status=status.HTTP_400_BAD_REQUEST)

    elif ghl_response.status_code == 401:
        return Response({
            "error": "Token GHL inválido (401)",
            "hint": "Completa auth GHL para token fresco"
        }, status=status.HTTP_401_UNAUTHORIZED)

    return Response({
        "error": "Error en creación de cita",
        "details": ghl_response.text or "No response body – chequea logs para status/headers",
        "status_code": ghl_response.status_code,
        "hint": "Verifica payload (calendar_id requerido) y logs en terminal."
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR if ghl_response.status_code == 0 else status.HTTP_400_BAD_REQUEST)

# Webhook para recibir notificaciones de citas desde GHL
@csrf_exempt
def appointment_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extraer datos principales del webhook
            appointment_data = data.get("appointment", {})
            appointment_id = data.get("ghl_id") or data.get("id") or appointment_data.get("id")
            
            if not appointment_id:
                appointment_id = f"test-{uuid.uuid4()}"

            # Normalizamos campos
            calendar_id = data.get("calendarId") or appointment_data.get("calendarId")
            contact_ghl_id = data.get("contactId") or appointment_data.get("contactId")
            location_id = data.get("locationId") or appointment_data.get("locationId")
            title = data.get("title") or appointment_data.get("title") or "Cita"
            appointment_status = (
                data.get("appointmentStatus") or
                appointment_data.get("appointmentStatus") or
                "confirmed"
            )
            assigned_user_id = (
                data.get("assignedUserId") or appointment_data.get("assignedUserId")
            )
            notes = data.get("notes") or appointment_data.get("notes")
            source = data.get("source") or appointment_data.get("source")

            start_time = _to_datetime(data.get("startTime") or appointment_data.get("startTime"))
            end_time = _to_datetime(data.get("endTime") or appointment_data.get("endTime"))

            # Valida FK contact por ghl_id
            try:
                contact = Contact.objects.get(ghl_id=contact_ghl_id)
            except Contact.DoesNotExist:
                logger.warning(f"No Contact found for ghl_id {contact_ghl_id} in webhook")
                return JsonResponse({"error": "Contacto no encontrado para sync"}, status=400)

            # Guardar o actualizar en DB
            obj, created = Appointment.objects.update_or_create(
                ghl_id=appointment_id,
                defaults={
                    "calendar_id": calendar_id,
                    "contact": contact,  # FK
                    "location_id": location_id,
                    "title": title,
                    "appointment_status": appointment_status,
                    "assigned_user_id": assigned_user_id,
                    "notes": notes,
                    "start_time": start_time,
                    "end_time": end_time,
                    "source": source,
                }
            )

            return JsonResponse({
                "ok": True,
                "ghl_id": appointment_id,
                "created": created
            }, status=200)
        except Exception as e:
            logger.error(f"Webhook Error: {e}")
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)