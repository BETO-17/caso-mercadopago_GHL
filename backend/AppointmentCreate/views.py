#AppointmentCreate/views.py
import os
import json
import uuid
from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from .models import Appointment
from .serializers import AppointmentSerializer
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from rest_framework.generics import ListAPIView
from ContactsCreate.models import Contact  # ✅ Importamos el modelo Contact

# Cargar .env
load_dotenv()

# Constantes GHL
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = os.getenv("GHL_API_VERSION", "2021-04-15")
ACCESS_TOKEN = os.getenv("GHL_ACCESS_TOKEN")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")  # fallback si viene vacío en el webhook
if not ACCESS_TOKEN:
    raise Exception("Access Token de GHL no configurado en .env (GHL_ACCESS_TOKEN)")


# Función para convertir ISO8601 a datetime aware
def _to_datetime(iso_str):
    """Convierte ISO8601 string a datetime aware o devuelve None."""
    if not iso_str:
        return None
    dt = parse_datetime(iso_str)
    if dt is None:
        return None
    if settings.USE_TZ and timezone.is_naive(dt):
        tz = timezone.get_current_timezone()
        dt = timezone.make_aware(dt, tz)
    return dt


# Crear cita en GHL y guardarla en MySQL
class AppointmentCreateView(APIView):
    """Crear una cita en GHL y guardarla en MySQL (sin romper la FK con Contact)."""

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        required_fields = ["calendarId", "contactId", "startTime", "endTime"]
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Falta el campo: {field}"}, status=status.HTTP_400_BAD_REQUEST)

        location_id = data.get("locationId") or GHL_LOCATION_ID
        if not location_id:
            return Response({"error": "No se encontró locationId (poner GHL_LOCATION_ID en .env o enviarlo en el payload)"},
                            status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Version": GHL_API_VERSION,
            "Content-Type": "application/json",
            "LocationId": location_id
        }

        api_payload = {
            "calendarId": data["calendarId"],
            "locationId": location_id,
            "contactId": data["contactId"],
            "startTime": data["startTime"],
            "endTime": data["endTime"],
            "title": data.get("title", "Cita creada desde API"),
            "appointmentStatus": data.get("appointmentStatus", "confirmed"),
            "assignedUserId": data.get("assignedUserId"),
            "ignoreFreeSlotValidation": True,
            "toNotify": True
        }

        try:
            # 🔹 Crear cita en GoHighLevel
            resp = requests.post(f"{GHL_BASE_URL}/calendars/events/appointments", json=api_payload, headers=headers, timeout=15)
            resp.raise_for_status()
            ghl_data = resp.json()

            # 🔹 Convertimos fechas
            start_dt = _to_datetime(ghl_data.get("startTime") or api_payload["startTime"])
            end_dt = _to_datetime(ghl_data.get("endTime") or api_payload["endTime"])

            # ✅ Buscar el contacto localmente usando su `ghl_id`
            contact_obj = Contact.objects.filter(ghl_id=ghl_data.get("contactId")).first()
            if not contact_obj:
                # Si no existe, lo creamos automáticamente
                contact_obj = Contact.objects.create(ghl_id=ghl_data.get("contactId"))

            # ✅ Guardar o actualizar cita, relacionándola con el contacto encontrado
            appointment, created = Appointment.objects.update_or_create(
                ghl_id=ghl_data.get("id"),
                defaults={
                    "location_id": ghl_data.get("locationId") or location_id,
                    "calendar_id": ghl_data.get("calendarId") or api_payload["calendarId"],
                    "contact": contact_obj,  # 🔹 Aquí se usa el objeto, no el ID string
                    "title": ghl_data.get("title") or api_payload.get("title", "Cita"),
                    "appointment_status": ghl_data.get("appointmentStatus") or api_payload.get("appointmentStatus", "confirmed"),
                    "assigned_user_id": ghl_data.get("assignedUserId") or api_payload.get("assignedUserId"),
                    "notes": ghl_data.get("notes") or None,
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "source": ghl_data.get("source")
                }
            )

            serializer = AppointmentSerializer(appointment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except requests.exceptions.HTTPError as http_err:
            resp = http_err.response
            details = resp.text if resp is not None else str(http_err)
            code = resp.status_code if resp is not None else 500
            return Response({"error": "Error HTTP al crear cita en GHL", "details": details}, status=code)
        except requests.exceptions.RequestException as e:
            return Response({"error": "Error conexión GHL", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"error": "Error interno", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                appointment_id = f"test-{uuid.uuid4()}"  # ID temporal para pruebas

            # Normalizamos campos
            calendar_id = data.get("calendarId") or appointment_data.get("calendarId")
            contact_id = data.get("contactId") or appointment_data.get("contactId")
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

            # Guardar o actualizar en DB
            obj, created = Appointment.objects.update_or_create(
                ghl_id=appointment_id,
                defaults={
                    "calendar_id": calendar_id,
                    "contact_id": contact_id,
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

            return JsonResponse(
                {"ok": True, "ghl_id": appointment_id, "created": created}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)