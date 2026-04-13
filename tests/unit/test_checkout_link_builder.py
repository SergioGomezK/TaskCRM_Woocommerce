from app.domain.entities import WooBilling, WooShipping
from app.infrastructure.config import Settings
from app.infrastructure.woocommerce.checkout_link_builder import WooCheckoutLinkBuilder


def _settings() -> Settings:
    return Settings(
        vtiger_base_url="https://crm.example.com",
        vtiger_username="api_user",
        vtiger_access_key="secret",
        woo_base_url="https://shop.example.com",
        woo_checkout_path="/checkout/",
    )


def test_checkout_link_builder_builds_expected_url() -> None:
    builder = WooCheckoutLinkBuilder(settings=_settings())

    url = builder.build_checkout_url(
        product_id=55,
        billing=WooBilling(
            first_name="Ana Maria",
            last_name="Perez",
            email="ana@example.com",
            phone="3001234567",
            address_1="Calle 1",
            city="Bogota",
            country="CO",
        ),
        shipping=WooShipping(
            first_name="Ana Maria",
            last_name="Perez",
            address_1="Calle 1",
            city="Bogota",
            country="CO",
        ),
        student_id_type="dni",
        student_id_number="12345678X",
        student_academic_program="ia_generativa",
    )

    assert url.startswith("https://shop.example.com/checkout/?")
    assert "add-to-cart=55" in url
    assert "student_first_name=Ana+Maria" in url
    assert "student_last_name=Perez" in url
    assert "student_id_type=dni" in url
    assert "student_id_number=12345678X" in url
    assert "student_phone=3001234567" in url
    assert "student_email=ana%40example.com" in url
    assert "student_academic_program=ia_generativa" in url
