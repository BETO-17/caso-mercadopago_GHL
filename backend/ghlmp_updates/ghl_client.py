# ghl_client.py
import os
import requests
from dotenv import load_dotenv


# Cargar variables de entorno (.env)
load_dotenv()

# 🔹 Configuración base de la API de GoHighLevel
GHL_TOKEN = os.getenv("GHL_TOKEN")
GHL_BASE = os.getenv("GHL_BASE_URL", "https://api.gohighlevel.com/v1")
HEADERS = {
    "Authorization": f"Bearer {GHL_TOKEN}",
    "Content-Type": "application/json"
}

# --------------------------------------------------------------------------
# 🔹 CONTACTOS
# --------------------------------------------------------------------------

def create_contact(contact):
    """
    Crea un contacto en GoHighLevel a partir del modelo Contact local.
    Retorna el ID del contacto creado o None si hay error.
    """
    payload = {
        "firstName": contact.first_name,
        "lastName": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "locationId": contact.location_id,
    }

    r = requests.post(f"{GHL_BASE}/contacts/", json=payload, headers=HEADERS)
    if r.status_code in (200, 201):
        data = r.json()
        contact.ghl_id = data.get("contact", {}).get("id") or data.get("id")
        contact.save()
        return contact.ghl_id
    else:
        print(f"[GHL ERROR create_contact] {r.text}")
        return None


def update_contact(contact):
    """
    Actualiza los datos de un contacto existente en GHL.
    """
    if not contact.ghl_id:
        print("[GHL WARNING] No se puede actualizar, contacto sin ghl_id.")
        return False

    payload = {
        "firstName": contact.first_name,
        "lastName": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
    }

    r = requests.patch(f"{GHL_BASE}/contacts/{contact.ghl_id}", json=payload, headers=HEADERS)
    if r.status_code in (200, 201):
        return True
    else:
        print(f"[GHL ERROR update_contact] {r.text}")
        return False


def add_tag_to_contact(contact_id, tag_name):
    """
    Agrega un tag (etiqueta) a un contacto en GHL.
    """
    r = requests.post(
        f"{GHL_BASE}/contacts/{contact_id}/tags",
        json={"tagName": tag_name},
        headers=HEADERS,
    )
    if r.status_code in (200, 201):
        return True
    else:
        print(f"[GHL ERROR add_tag_to_contact] {r.text}")
        return False


def set_custom_field(contact_id, field_key, value):
    """
    Actualiza un campo personalizado del contacto.
    """
    payload = {"customFields": {field_key: value}}
    r = requests.patch(f"{GHL_BASE}/contacts/{contact_id}", json=payload, headers=HEADERS)
    if r.status_code in (200, 201):
        return True
    else:
        print(f"[GHL ERROR set_custom_field] {r.text}")
        return False


# --------------------------------------------------------------------------
# 🔹 CITAS (Appointments)
# --------------------------------------------------------------------------

def create_appointment(appointment):
    """
    Crea una cita en GoHighLevel a partir del modelo Appointment local.
    Retorna el ID de la cita creada o None si hay error.
    """
    payload = {
        "calendarId": appointment.calendar_id,
        "contactId": appointment.contact.ghl_id,
        "title": appointment.title,
        "appointmentStatus": appointment.appointment_status,
        "assignedUserId": appointment.assigned_user_id,
        "notes": appointment.notes,
        "startTime": appointment.start_time.isoformat(),
        "endTime": appointment.end_time.isoformat(),
        "locationId": appointment.location_id,
    }

    r = requests.post(f"{GHL_BASE}/calendars/events/appointments/", json=payload, headers=HEADERS)
    if r.status_code in (200, 201):
        data = r.json()
        appointment.ghl_id = data.get("appointment", {}).get("id") or data.get("id")
        appointment.save()
        return appointment.ghl_id
    else:
        print(f"[GHL ERROR create_appointment] {r.text}")
        return None


def update_appointment_status(appointment, new_status):
    """
    Actualiza el estado de una cita en GHL.
    """
    if not appointment.ghl_id:
        print("[GHL WARNING] No se puede actualizar, cita sin ghl_id.")
        return False

    payload = {"appointmentStatus": new_status}
    r = requests.patch(
        f"{GHL_BASE}/calendars/events/appointments/{appointment.ghl_id}",
        json=payload,
        headers=HEADERS,
    )
    if r.status_code in (200, 201):
        appointment.appointment_status = new_status
        appointment.save()
        return True
    else:
        print(f"[GHL ERROR update_appointment_status] {r.text}")
        return False
