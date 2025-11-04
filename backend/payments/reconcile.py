#payments/reconcile.py
# reconciliacion diaria
import os
import csv
import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from payments.models import PaymentPreference

# Cargar tokens de entorno
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

# URL base de Mercado Pago
MP_BASE_URL = "https://api.mercadopago.com/v1/payments/search"


def fetch_recent_payments(days=1):
    """Obtiene los pagos de MP en las últimas 24 horas"""
    date_from = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    params = {"date_created_from": date_from, "limit": 50}
    
    res = requests.get(MP_BASE_URL, headers=headers, params=params)
    data = res.json()
    return data.get("results", [])


def reconcile_payments():
    """Compara pagos de MP con los registrados localmente"""
    mp_payments = fetch_recent_payments()
    local_payments = PaymentPreference.objects.all()

    discrepancies = []

    for mp in mp_payments:
        mp_id = str(mp["id"])
        mp_status = mp["status"]
        mp_amount = mp["transaction_amount"]

        try:
            local = local_payments.get(payment_id=mp_id)
            if local.status != mp_status:
                discrepancies.append({
                    "payment_id": mp_id,
                    "local_status": local.status,
                    "mp_status": mp_status,
                    "amount": mp_amount
                })
        except PaymentPreference.DoesNotExist:
            discrepancies.append({
                "payment_id": mp_id,
                "local_status": "not_found",
                "mp_status": mp_status,
                "amount": mp_amount
            })

    # Exportar diferencias
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = os.path.join(settings.BASE_DIR, f"reconcile_report_{timestamp}.csv")

    with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["payment_id", "local_status", "mp_status", "amount"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(discrepancies)

    print(f"✅ Reconciliación completada. Reporte: {export_path}")
    return discrepancies
