# Formulario CRM (FastAPI + Vtiger + WooCommerce)

Servicio API para cron jobs que:
- lee leads pendientes desde Vtiger,
- genera links estaticos de pago,
- redirige cada link al checkout final de WooCommerce con datos prellenados.

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
3. Configura campos de Leads en Vtiger:
   - `VTIGER_LEAD_FIELD_PRODUCT_ID`
   - `VTIGER_LEAD_FIELD_WOO_ORDER_ID`
   - `VTIGER_LEAD_FIELD_SYNC_STATUS`
   - `VTIGER_LEAD_FIELD_STUDENT_ID_TYPE`
   - `VTIGER_LEAD_FIELD_STUDENT_ID_NUMBER`
   - `VTIGER_LEAD_FIELD_STUDENT_ACADEMIC_PROGRAM`
   - `VTIGER_SYNC_PENDING_VALUE`
   - `VTIGER_SYNC_BATCH_LIMIT_DEFAULT`
4. Configura WooCommerce checkout:
   - `WOO_BASE_URL`
   - `WOO_CHECKOUT_PATH` (ej: `/finalizar-compra/`)
   - `WOO_DEFAULT_COUNTRY`
5. Configura seguridad de integracion:
   - `INTEGRATION_API_KEY`
   - `CHECKOUT_LINK_SIGNING_KEY`
6. Opcional para links publicos absolutos:
   - `APP_PUBLIC_BASE_URL`

## Ejecucion

```bash
uvicorn app.main:app --reload
```

## Endpoints activos

- `GET /health`
- `POST /integrations/vtiger/leads-to-checkout-links/sync?limit=50` (JSON + `X-Integration-Key`)
- `GET /checkout-links/{link_id}` (redirect 307 a checkout final de Woo)

## Ejemplo cron externo

```bash
curl -X POST "http://localhost:8000/integrations/vtiger/leads-to-checkout-links/sync?limit=50" \
  -H "X-Integration-Key: $INTEGRATION_API_KEY"
```

Respuesta esperada:
- `processed`, `generated`, `failed`, `skipped`
- `items[]` con `lead_id`, `status`, `link_id`, `static_link` o `error`

El `static_link` es deterministico por `lead_id`, por lo que el mismo lead mantiene un unico link estable.

La URL final de checkout se construye con esta forma:

`https://tu-tienda/finalizar-compra/?add-to-cart={product_id}&student_first_name=...&student_last_name=...&student_id_type=...&student_id_number=...&student_country=...&student_state=...&student_address=...&student_postcode=...&student_phone=...&student_email=...&student_academic_program=...`

`student_academic_program` se normaliza a:
- `tech_mba`
- `ia_generativa`
- `data_science`

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

3. Verificar:

- `http://localhost:8000/health`

4. Logs:

```bash
docker compose logs -f web
```