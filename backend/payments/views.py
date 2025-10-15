# payments/views.py
import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreatePaymentSerializer
from .models import PaymentPreference
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser


MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
MP_BASE = os.getenv("MP_BASE_URL", "https://api.mercadopago.com")


# crear preferencia de pago en MP y guardar en BD
class CreatePaymentView(APIView):
    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # preparar payload preferencia
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
            "notification_url": f"{os.getenv('APP_PUBLIC_URL')}/webhooks/mp"
        }
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}", 
            "Content-Type": "application/json"
        }

        r = requests.post(f"{MP_BASE}/checkout/preferences", json=payload, headers=headers)
        if r.status_code not in (200, 201):
            return Response({"error": "MP error", "details": r.text}, status=500)
        
        resp = r.json()
        pref_id = resp.get("id")
        init_point = resp.get("init_point")
        sandbox_init_point = resp.get("sandbox_init_point")

        # guardar en BD
        p = PaymentPreference.objects.create(
            appointment_id=data["appointmentId"],
            contact_id=data["contactId"],
            preference_id=pref_id,
            init_point=init_point or sandbox_init_point,
            amount=data["amount"],
            status="pending"
        )

        # ✅ Devuelve ambos (para pruebas y producción)
        return Response({
            "sandbox_init_point": sandbox_init_point,
            "init_point": init_point, 
            "preference_id": pref_id
            })


# webhook para notificaciones de Mercado Pago
@method_decorator(csrf_exempt, name='dispatch')
class MPWebhookView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        payload = request.data
        # Mercado Pago puede enviar distintos shapes; lo común: data.id (payment id) o type=payment + data.id
        # Normalmente webhook trae: {"id": 123, "type": "payment"}, luego consultamos detalle
        try:
            # extraer payment id robustamente
            payment_id = None
            if "data" in payload and isinstance(payload["data"], dict) and payload["data"].get("id"):
                payment_id = payload["data"]["id"]
            elif payload.get("id"):
                payment_id = payload.get("id")

            if not payment_id:
                return Response({"ok": True}, status=200)

            # consultar MP para detalle payment
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            r = requests.get(f"{MP_BASE}/v1/payments/{payment_id}", headers=headers)

            # ⚠️ Evita 500 en simulaciones o pagos no encontrados
            if r.status_code != 200:
                print(f"⚠️ Mercado Pago devolvió {r.status_code} para payment_id={payment_id}")
                print("Respuesta:", r.text)
                # responder 200 para no repetir el intento del webhook
                return Response({"ok": True, "note": "payment not found or simulated"}, status=200)
            
            payment = r.json()
            status_mp = payment.get("status")
            external_ref = payment.get("external_reference") or payment.get("metadata", {}).get("external_reference")

            # mapping external_reference -> preference / appointment
            # external_ref puede ser "appointment_12345"
            appointment_id = None
            if external_ref and external_ref.startswith("appointment_"):
                appointment_id = external_ref.replace("appointment_", "")

            # Buscar la preferencia por external reference o por payment.preference_id si lo guardaste
            # Mejor: busca por appointment_id
            pref = None
            if appointment_id:
                pref = PaymentPreference.objects.filter(appointment_id=appointment_id).first()
            # fallback: buscar por payment.preference_id en payment['preference_id']
            if not pref and payment.get("preference_id"):
                pref = PaymentPreference.objects.filter(preference_id=payment.get("preference_id")).first()

            if not pref:
                # guarda log o crea registro mínimo
                print("⚠️ Preferencia no encontrada para:", external_ref)
                return Response({"message": "preference not found"}, status=404)

            # Idempotencia: si payment_id ya fue procesado
            if pref.payment_id == str(payment_id) or pref.status == "paid":
                return Response({"ok": True}, status=200)

            if status_mp == "approved":
                pref.mark_paid(payment_id=str(payment_id))
                print(f"✅ Pago aprobado: {payment_id}")

                # llamar a GHL para actualizar contacto (ver gh_client)
                from ..ghlmp_updates.ghl_client import add_tag_to_contact
                add_tag_to_contact(pref.contact_id, "pago_confirmado")
            else:
                # actualizar estado local si quieres
                pref.status = status_mp
                pref.save()
                print(f"ℹ️ Pago actualizado a estado {status_mp}")

            return Response({"ok": True}, status=200)

        except Exception as e:
            print("❌ Error en webhook:", str(e))
            return Response({"error": str(e)}, status=500)
