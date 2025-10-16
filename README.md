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
  ```

---

## ⚙️ FLUJO DE CASO DE USO

1️⃣ Usuario reserva cita  →  Se crea Appointment (local + GHL)  
2️⃣ Se genera link de pago (Mercado Pago sandbox)  
   → Se guarda en PaymentPreference:
   - appointment_id = appointment.ghl_id
   - contact_id = contact.ghl_id
   - init_point = link de pago
   - status = "pending"

3️⃣ Usuario paga → Mercado Pago envía webhook → Django lo recibe  
   → Django marca el pago como "paid":  
   ```python
   payment.mark_paid(payment_id)
   ```

4️⃣ Django actualiza en GHL:
   ```python
   add_tag_to_contact(contact_id, "pago_confirmado")
   set_custom_field(contact_id, "payment_status", "paid")
   ```

---

## 🧩 Requisitos

| Elemento | Descripción |
|-----------|-------------|
| **Cuenta Mercado Pago** | Modo sandbox habilitado |
| **Credenciales** | MP_ACCESS_TOKEN, MP_PUBLIC_KEY |
| **Cuenta GoHighLevel** | Subcuenta ReflexoPerú |
| **Token GHL** | GHL_TOKEN (Private API Key) |
| **Backend** | Django o FastAPI + SQLite |
| **Webhook** | Ngrok / Cloudflare Tunnel |
| **Pruebas** | Postman / CURL |

---

## 🌐 Endpoints del Proyecto

| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `POST` | `/payments/create` | Crear link de pago |
| `POST` | `/payments/webhooks/mp` | Recibir evento Mercado Pago |
| `PUT` | `/ghl/update-contact` | Actualizar contacto en GHL |

---

## 🧱 Estructura del Módulo `payments`

**Modelo local:**

| Campo | Descripción |
|--------|-------------|
| appointment_id | ID cita (GHL) |
| contact_id | ID contacto (GHL) |
| preference_id | ID preferencia MP |
| payment_id | ID pago MP |
| amount | Monto |
| status | pending / paid |

**Endpoint `/payments/create`**  
- Recibe JSON `{appointmentId, contactId, amount, description}`  
- Crea preferencia en Mercado Pago  
- Guarda en BD → status="pending"  
- Devuelve `init_point` (URL de pago)

---

## 📩 Webhook Mercado Pago

**Endpoint:** `/payments/webhooks/mp`  
- Recibe POST desde MP  
- Extrae `payment_id` y `status`  
- Valida idempotencia  
- Si `status="approved"`:
  - Actualiza BD → `status="paid"`  
  - Llama helper GHL (`add_tag_to_contact`, `set_custom_field`)  
- Retorna `200 OK`

---

## 🔗 GoHighLevel (GHL)

- Actualiza contacto usando `contactId`  
- Opciones:  
  A) Agregar tag `"pago_confirmado"`  
  B) Actualizar campo personalizado `payment_status=paid`  

**Endpoints API GHL:**  
```
POST /contacts/{id}/tags
PUT /contacts/{id}
```

---

## 🔄 Flujo Completo

```text
1️⃣ Cliente crea cita en GHL
2️⃣ Backend genera link de pago (MP)
3️⃣ Usuario paga con tarjeta sandbox
4️⃣ MP envía webhook → /webhooks/mp
5️⃣ Backend marca pago como “paid”
6️⃣ Actualiza contacto en GHL (tag/campo)
7️⃣ Se ve “pago_confirmado” en el Dashboard
```

---

## 🧪 Pruebas QA

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1️⃣ | POST /payments/create | Retorna init_point |
| 2️⃣ | Abrir link de pago | Página sandbox Mercado Pago |
| 3️⃣ | Completar pago | Webhook recibido en Django |
| 4️⃣ | Revisar contacto en GHL | Tag o campo “paid” actualizado |
| 5️⃣ | Verificar BD | `status = "paid"` |

---

## 📁 Variables `.env`

```
MP_ACCESS_TOKEN=TEST-xxx
MP_PUBLIC_KEY=TEST-xxx
GHL_API_KEY=xxxx
BASE_URL=https://tu-tunnel.trycloudflare.com
```

---

## 📸 Evidencias Recomendadas

- Captura: Link de pago generado  
- Captura: Webhook recibido  
- Captura: Contacto en GHL actualizado  
- Captura: BD con estado "paid"

---

🧠 **Autor:** ReflexoPerú Dev Team  
📅 **Versión:** 1.0 - Octubre 2025
