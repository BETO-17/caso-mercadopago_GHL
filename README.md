# 💳 Integración Mercado Pago + GoHighLevel (ReflexoPerú)

## 🎯 Objetivo
Cuando se cree una cita en GHL, generar un link de pago de **Mercado Pago (sandbox)**.  
Cuando el pago se **apruebe**, el sistema actualizará al **contacto en GHL** (por ejemplo, agregando el tag `pago_confirmado` o el campo personalizado `payment_status=paid`).

---

## ✅ Criterios de aceptación (QA)

- Endpoint **POST /payments/create** que devuelve `init_point` (URL de pago).
- Webhook **POST /webhooks/mp** que recibe el evento de pago y procesa al menos `status=approved`.
- Cuando el pago es aprobado, el **contacto en GHL** se actualiza automáticamente.
- **README** con pasos, variables `.env`, capturas (link de pago, webhook recibido, contacto actualizado).

---

## 🗓️ Plan de trabajo (3 días)

### **Día 1 — Crear link de pago**

#### Backend
- Endpoint: `POST /payments/create`
- Recibe:
  ```json
  {
    "appointmentId": "A123",
    "contactId": "RzNZvdktZo8DHYMH6xyj",
    "amount": 50.0,
    "description": "Cita ReflexoPerú"
  }


### FLUJO DE CASO DE USO 
1️⃣ Usuario reserva cita  →  Se crea Appointment (local + GHL)

2️⃣ Se genera link de pago (Mercado Pago sandbox)
    → Se guarda en PaymentPreference:
       - appointment_id = appointment.ghl_id
       - contact_id = contact.ghl_id
       - init_point = link de pago
       - status = "pending"

3️⃣ Usuario paga → Mercado Pago envía webhook → Django lo recibe
    → Django marca el pago como "paid":
         payment.mark_paid(payment_id)

4️⃣ Django actualiza en GHL:
    → add_tag_to_contact(contact_id, "pago_confirmado")
    → set_custom_field(contact_id, "payment_status", "paid")


┌──────────────────────────────────────────────┐
│ 1. Requisitos                                │
├──────────────────────────────────────────────┤
│ - Cuenta Mercado Pago (sandbox)              │
│ - Credenciales: MP_ACCESS_TOKEN, MP_PUBLIC_KEY │
│ - Cuenta GoHighLevel (subcuenta ReflexoPerú) │
│ - GHL_TOKEN (Private API Key)                │
│ - Django o FastAPI + SQLite                  │
│ - Ngrok / Hookdeck para recibir Webhooks     │
│ - Postman para pruebas                       │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 2. Endpoints del Proyecto                    │
├──────────────────────────────────────────────┤
│ POST /payments/create   → Crear link de pago │
│ POST /webhooks/mp       → Recibir evento MP  │
│ PUT  /ghl/update-contact → Actualizar contacto│
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 3. Django / FastAPI – Módulo Payments        │
├──────────────────────────────────────────────┤
│ Modelo local:                                │
│ • appointmentId                              │
│ • contactId                                  │
│ • preference_id                              │
│ • payment_id                                 │
│ • amount                                     │
│ • status (pending/paid)                      │
│                                              │
│ Endpoint /payments/create                    │
│ • Recibe JSON {appointmentId, contactId, ...}│
│ • Crea preferencia en Mercado Pago           │
│ • Guarda en BD → status="pending"            │
│ • Devuelve init_point (URL de pago)          │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 4. Webhook Mercado Pago                      │
├──────────────────────────────────────────────┤
│ Endpoint: /webhooks/mp                       │
│ • Recibe POST desde MP                       │
│ • Extrae payment_id y status                 │
│ • Valida idempotencia                        │
│ • Si status="approved":                      │
│    - Actualiza BD → status="paid"            │
│    - Llama helper GHL para marcar pago       │
│ • Retorna 200 OK                             │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 5. GoHighLevel (GHL)                         │
├──────────────────────────────────────────────┤
│ • Actualiza contacto usando contactId        │
│ Opciones:                                    │
│   A) Agregar tag "pago_confirmado"           │
│   B) Actualizar custom field payment_status=paid │
│ • Endpoint API GHL: /contacts/{id}/tags o PUT /contacts/{id} │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 6. Flujo Completo                            │
├──────────────────────────────────────────────┤
│ 1️⃣ Cliente crea cita en GHL                 │
│ 2️⃣ Backend genera link de pago (MP)         │
│ 3️⃣ Usuario paga con tarjeta de prueba       │
│ 4️⃣ MP envía webhook → /webhooks/mp          │
│ 5️⃣ Backend marca pago como “paid”           │
│ 6️⃣ Actualiza contacto en GHL (tag/campo)    │
│ 7️⃣ Se ve “pago_confirmado” en el Dashboard  │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 7. Pruebas QA                                │
├──────────────────────────────────────────────┤
│ 1. POST /payments/create en Postman          │
│ 2. Abrir init_point (pago sandbox)           │
│ 3. Confirmar recepción del webhook           │
│ 4. Revisar contacto en GHL                   │
│ 5. Validar registro en BD status="paid"      │
└──────────────────────────────────────────────┘

