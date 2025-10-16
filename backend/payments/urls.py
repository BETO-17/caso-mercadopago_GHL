# payments/urls.py
from django.urls import path
from .views import CreatePaymentView, MPWebhookView  # ver webhook abajo
from django.http import JsonResponse


# === Vistas simples para back_urls ===
def payment_success(request):
    return JsonResponse({"message": "✅ Pago aprobado correctamente."})

def payment_failure(request):
    return JsonResponse({"message": "❌ El pago fue rechazado o falló."})

def payment_pending(request):
    return JsonResponse({"message": "⏳ El pago está pendiente de aprobación."})

# === Rutas principales ===
urlpatterns = [
    # Crear preferencia de pago
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    # Webhook (recibe notificaciones de Mercado Pago)
    path("webhooks/mp", MPWebhookView.as_view(), name="mp-webhook"),  # ver webhook abajo
    # Rutas de retorno (back_urls)
    path('success', payment_success, name='payment_success'),
    path('failure', payment_failure, name='payment_failure'),
    path('pending', payment_pending, name='payment_pending'),
]

