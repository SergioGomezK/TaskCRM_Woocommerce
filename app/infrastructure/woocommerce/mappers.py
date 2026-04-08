from app.domain.entities import WooOrderInput


def map_order_input_to_woo_payload(order: WooOrderInput) -> dict[str, object]:
    payload: dict[str, object] = {
        "payment_method": order.payment_method,
        "payment_method_title": order.payment_method_title,
        "set_paid": order.set_paid,
        "billing": _clean_none(
            {
                "first_name": order.billing.first_name,
                "last_name": order.billing.last_name,
                "address_1": order.billing.address_1,
                "address_2": order.billing.address_2,
                "city": order.billing.city,
                "state": order.billing.state,
                "postcode": order.billing.postcode,
                "country": order.billing.country,
                "email": order.billing.email,
                "phone": order.billing.phone,
            }
        ),
        "shipping": _clean_none(
            {
                "first_name": order.shipping.first_name,
                "last_name": order.shipping.last_name,
                "address_1": order.shipping.address_1,
                "address_2": order.shipping.address_2,
                "city": order.shipping.city,
                "state": order.shipping.state,
                "postcode": order.shipping.postcode,
                "country": order.shipping.country,
            }
        ),
        "line_items": [
            _clean_none(
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "variation_id": line.variation_id,
                }
            )
            for line in order.line_items
        ],
    }

    if order.customer_note:
        payload["customer_note"] = order.customer_note

    return payload


def _clean_none(data: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in data.items() if value is not None}
