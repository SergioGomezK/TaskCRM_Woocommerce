from app.infrastructure.config import Settings
from app.infrastructure.woocommerce.checkout_link_identity import HMACCheckoutLinkIdentity


def _settings() -> Settings:
    return Settings(
        vtiger_base_url="https://crm.example.com",
        vtiger_username="api_user",
        vtiger_access_key="secret",
        checkout_link_signing_key="test-signing-key",
    )


def test_checkout_link_identity_is_deterministic() -> None:
    identity = HMACCheckoutLinkIdentity(settings=_settings())

    link_id_first = identity.create_link_id("11x1")
    link_id_second = identity.create_link_id("11x1")

    assert link_id_first == link_id_second
    assert identity.get_lead_id(link_id_first) == "11x1"


def test_checkout_link_identity_rejects_tampered_token() -> None:
    identity = HMACCheckoutLinkIdentity(settings=_settings())
    link_id = identity.create_link_id("11x1")
    tampered = link_id[:-1] + ("A" if link_id[-1] != "A" else "B")

    assert identity.get_lead_id(tampered) is None
