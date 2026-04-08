# Formulario CRM (FastAPI + Vtiger + WooCommerce)

Aplicacion con formulario HTML para crear pre-contactos en `Leads`, API JSON para listar leads en Vtiger y API JSON para crear ordenes en WooCommerce.

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

## Ejecucion

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /clientes/form`
- `POST /clientes/form`
- `GET /leads?limit=20` (JSON)
- `POST /woocommerce/orders` (JSON)

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
