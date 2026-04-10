# Formulario CRM (FastAPI + Vtiger + WooCommerce)

Aplicacion con formulario HTML para crear pre-contactos en `Leads`, API JSON para listar leads en Vtiger y API JSON para generar checkout links de WooCommerce a partir de datos de Vtiger.

## Requisitos

- Python 3.11+
- Dependencias de `requirements.txt`

## Configuracion

1. Copia `.env.example` a `.env`.
2. Completa credenciales de Vtiger:
   - `VTIGER_BASE_URL`
   - `VTIGER_USERNAME`
   - `VTIGER_ACCESS_KEY`
   - `VTIGER_TIMEOUT_SECONDS`
   - `VTIGER_ASSIGNED_USER_ID` (opcional)
3. Completa credenciales de WooCommerce:
   - `WOO_BASE_URL`
   - `WOO_CONSUMER_KEY`
   - `WOO_CONSUMER_SECRET`
   - `WOO_API_VERSION` (default `wc/v3`)
   - `WOO_TIMEOUT_SECONDS`
   - `WOO_QUERY_STRING_AUTH` (`true` o `false`)
   - `WOO_CHECKOUT_PATH` (default `/checkout/`)
4. Configura integracion Vtiger -> WooCommerce:
   - `VTIGER_LEAD_FIELD_PRODUCT_ID`
   - `VTIGER_LEAD_FIELD_WOO_ORDER_ID`
   - `VTIGER_LEAD_FIELD_SYNC_STATUS`
   - `VTIGER_LEAD_FIELD_SYNC_ERROR`
   - `VTIGER_SYNC_PENDING_VALUE`
   - `VTIGER_SYNC_PROCESSED_VALUE`
   - `VTIGER_SYNC_FAILED_VALUE`
   - `VTIGER_SYNC_BATCH_LIMIT_DEFAULT`
   - `WOO_DEFAULT_COUNTRY`
   - `WOO_DEFAULT_PAYMENT_METHOD`
   - `WOO_DEFAULT_PAYMENT_METHOD_TITLE`
   - `WOO_DEFAULT_SET_PAID`
   - `INTEGRATION_API_KEY`

## Ejecucion

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /clientes/form`
- `POST /clientes/form`
- `GET /leads?limit=20` (JSON)
- `POST /woocommerce/orders` (JSON, **deprecated**)
- `POST /integrations/vtiger/leads-to-orders/sync?limit=50` (JSON + `X-Integration-Key`)
- `POST /integrations/vtiger/leads-to-checkout-links/sync?limit=50` (JSON + `X-Integration-Key`)

### Ejemplo rapido para crear orden

```bash
curl -X POST http://localhost:8000/woocommerce/orders \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "bacs",
    "payment_method_title": "Transferencia bancaria",
    "set_paid": false,
    "billing": {
      "first_name": "Ana",
      "last_name": "Perez",
      "address_1": "Calle 1",
      "city": "Bogota",
      "country": "CO",
      "email": "ana@example.com",
      "phone": "3001234567"
    },
    "shipping": {
      "first_name": "Ana",
      "last_name": "Perez",
      "address_1": "Calle 1",
      "city": "Bogota",
      "country": "CO"
    },
    "line_items": [
      {"product_id": 55, "quantity": 1}
    ]
  }'
```

### Ejemplo cron externo

```bash
curl -X POST "http://localhost:8000/integrations/vtiger/leads-to-checkout-links/sync?limit=50" \
  -H "X-Integration-Key: $INTEGRATION_API_KEY"
```

## Pruebas

```bash
pytest
```

## Docker

1. Copia `.env.example` a `.env` y completa credenciales.
2. Construye y levanta:

```bash
docker compose up --build -d
```

3. Accede a:

- `http://localhost:8000/health`
- `http://localhost:8000/clientes/form`

4. Ver logs:

```bash
docker compose logs -f web
```
