import base64
import hashlib
import hmac

from app.domain.errors import WooUnexpectedError
from app.domain.ports import CheckoutLinkIdentityPort
from app.infrastructure.config import Settings


class HMACCheckoutLinkIdentity(CheckoutLinkIdentityPort):
    def __init__(self, settings: Settings) -> None:
        if settings.checkout_link_signing_key is None:
            raise WooUnexpectedError("Missing CHECKOUT_LINK_SIGNING_KEY configuration.")
        self._secret = settings.checkout_link_signing_key.get_secret_value().encode("utf-8")

    def create_link_id(self, lead_id: str) -> str:
        normalized = lead_id.strip()
        signature = self._sign(normalized)
        return f"{normalized}.{signature}"

    def get_lead_id(self, link_id: str) -> str | None:
        lead_id, sep, signature = link_id.rpartition(".")
        if not sep:
            return None
        if not lead_id or not signature:
            return None
        expected = self._sign(lead_id)
        if not hmac.compare_digest(signature, expected):
            return None
        return lead_id

    def _sign(self, value: str) -> str:
        digest = hmac.new(self._secret, value.encode("utf-8"), hashlib.sha256).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return encoded[:24]
