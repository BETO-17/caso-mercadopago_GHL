# payments/views.py
import os
import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreatePaymentSerializer
from .models import PaymentPreference
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from dotenv import load_dotenv, find_dotenv
from payments.reconcile import reconcile_payments
import logging

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
if not MP_ACCESS_TOKEN:
    raise EnvironmentError("❌ La variable de entorno MP_ACCESS_TOKEN no está definida.")

MP_BASE = os.getenv("MP_BASE_URL", "https://api.mercadopago.com")

# Crear preferencia de pago en MP y guardar en BD
class CreatePaymentView(APIView):
    def get(self, request):
        # GET: DRF UI con example, prellenado si ?appointment_id=
        appointment_id = request.GET.get('appointment_id')
        payment_data = {}
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                payment_data = {
                    "appointment_id": appointment.id,
                    "contact_id": appointment.contact.id,
                    "amount": 50.00,  # E.g., monto fijo o de custom field
                    "description": f"Pago por cita: {appointment.title} - {appointment.start_time}"
                }
            except Appointment.DoesNotExist:
                pass
        return Response({
            "message": "Usa POST para crear preferencia de pago (requiere appointment_id).",
            "example_data": {
                "appointment_id": appointment_id or "",
                "amount": 50.00,  # Monto en PEN
                "description": "Pago por consulta",
                "contact_id": "ghl_contact_id"
            },
            "payment_info": payment_data,  # Previsualiza
            "hint": "Monto en PEN. Post-pago, MP redirige a back_urls."
        })

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Preparar payload preferencia
        items = [{
            "title": data["description"],
            "quantity": 1,
            "unit_price": float(data["amount"]),
            "currency_id": "PEN"
        }]
        payload = {
            "items": items,
            "external_reference": f"appointment_{data['appointmentId']}",
            "metadata": {
                "appointment_id": data["appointmentId"],
                "contact_id": data["contactId"]
            },
            "back_urls": {
                "success": f"{settings.APP_PUBLIC_URL}/payments/success",
                "failure": f"{settings.APP_PUBLIC_URL}/payments/failure",
                "pending": f"{settings.APP_PUBLIC_URL}/payments/pending"
            },
            "auto_return": "approved",
            "notification_url": f"{settings.APP_PUBLIC_URL}/api/payments/webhooks/mp"
        }

        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        r = requests.post(f"{MP_BASE}/checkout/preferences", json=payload, headers=headers)
        if r.status_code == 201:
            result = r.json()
            preference_id = result["id"]
            init_point = result["init_point"]

            # Guardar en DB
            pref = PaymentPreference.objects.create(
                appointment_id=data["appointmentId"],
                contact_id=data["contactId"],
                preference_id=preference_id,
                amount=data["amount"],
                init_point=init_point
            )

            return Response({
                "message": "Preferencia creada correctamente",
                "preference_id": preference_id,
                "init_point": init_point,  # Link a MP checkout
                "next_step": "Redirige usuario a init_point para pagar."
            })
        else:
            return Response({
                "error": "Error en Mercado Pago",
                "details": r.text
            }, status=status.HTTP_400_BAD_REQUEST)

# Webhook para recibir notificaciones de MP
class MPWebhookView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            data = request.data
            payment_id = data.get("id")
            status_mp = data.get("status")
            external_ref = data.get("external_reference")

            # Mapping external_reference -> preference / appointment
            appointment_id = None
            if external_ref and external_ref.startswith("appointment_"):
                appointment_id = external_ref.replace("appointment_", "")

            # Buscar la preferencia por appointment_id
            pref = PaymentPreference.objects.filter(appointment_id=appointment_id).first()
            if not pref:
                logger.warning(f"Preferencia no encontrada para {external_ref}")
                return Response({"message": "preferencia no encontrada"}, status=404)

            # Idempotencia: si ya procesado
            if pref.payment_id == str(payment_id) or pref.status == "paid":
                return Response({"ok": True}, status=200)

            if status_mp == "approved":
                pref.payment_id = str(payment_id)
                pref.status = "paid"
                pref.save()

                # Sync con GHL
                add_tag_to_contact(pref.contact_id, "pago_confirmado")
                set_custom_field(pref.contact_id, "payment_status", "paid")
                logger.info(f"✅ Pago aprobado: {payment_id}")

            else:
                pref.status = status_mp
                pref.save()
                logger.info(f"ℹ️ Pago actualizado a {status_mp}")

            return Response({"ok": True}, status=200)
        except Exception as e:
            logger.error(f"Error en webhook MP: {e}")
            return Response({"error": str(e)}, status=500)

# Vista para reconciliar pagos
class ReconcilePaymentsView(APIView):
    def get(self, request):
        discrepancies = reconcile_payments()
        return Response({"discrepancies": discrepancies})
    