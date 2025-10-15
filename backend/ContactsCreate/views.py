# ContactsCreate/views.py
from django.conf import settings
from django.shortcuts import render
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json
import os
from .models import Contact

# Cargar .env
load_dotenv()

# Constantes GHL
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = os.getenv("GHL_API_VERSION", "2021-04-15")
ACCESS_TOKEN = os.getenv("GHL_ACCESS_TOKEN")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GHL_API_URL = f"{GHL_BASE_URL}/contacts/"
GHL_TOKEN = ACCESS_TOKEN

if not ACCESS_TOKEN:
    raise Exception("Access Token de GHL no configurado en .env (GHL_ACCESS_TOKEN)")


# 🔹 Crear contacto en GHL y guardarlo localmente
@api_view(['POST'])
def create_contact(request):
    data = request.data

    ghl_payload = {
        "firstName": data.get("first_name"),
        "lastName": data.get("last_name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "locationId": data.get("location_id") or GHL_LOCATION_ID,
    }

    headers = {
        "Authorization": f"Bearer {GHL_TOKEN}",
        "Version": "2021-07-28"  # 👈 encabezado requerido por la API GHL v2
    }


    ghl_response = requests.post(GHL_API_URL, json=ghl_payload, headers=headers)
    if ghl_response.status_code not in [200, 201]:
        return JsonResponse({
            "error": "No se pudo crear contacto en GHL",
            "details": ghl_response.text
        }, status=400)

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

    return JsonResponse({
        "message": "Contacto creado correctamente",
        "contact_id": contact.id
    })


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
