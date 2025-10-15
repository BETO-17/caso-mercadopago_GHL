# payments/urls.py
from django.urls import path
from .views import CreatePaymentView, MPWebhookView  # ver webhook abajo
urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="payments-create"),
    path("webhooks/mp", MPWebhookView.as_view(), name="mp-webhook"),  # ver webhook abajo
]
