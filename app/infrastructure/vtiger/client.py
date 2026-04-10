import hashlib
import json
import logging
from typing import Any

import requests

from app.domain.entities import CRMCreateResult, CRMLeadForSync, CRMLeadSummary, ClientLead
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    CRMValidationError,
)
from app.domain.ports import CRMClientPort
from app.infrastructure.config import Settings
from app.infrastructure.vtiger.mappers import map_client_to_vtiger_contact

AUTH_ERROR_CODES = {
    "ACCESS_DENIED",
    "AUTHENTICATION_REQUIRED",
    "INVALID_AUTH_TOKEN",
    "INVALID_USER_CREDENTIALS",
}

VALIDATION_ERROR_CODES = {
    "INVALID_DATA",
    "INVALID_MODULE",
    "MANDATORY_FIELDS_MISSING",
    "RECORD_NOT_FOUND",
}


class VtigerClient(CRMClientPort):
    def __init__(
        self,
        settings: Settings,
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._logger = logger or logging.getLogger(__name__)
        self._endpoint = f"{self._settings.vtiger_base_url}/webservice.php"

    def create_contact(
        self, contact: ClientLead, request_id: str | None = None
    ) -> CRMCreateResult:
        token = self._get_challenge()
        session_name, user_id = self._login(token)
        assigned_user_id = self._settings.vtiger_assigned_user_id or user_id
        payload = map_client_to_vtiger_contact(contact, assigned_user_id)
        result = self._create_contact(session_name, payload)

        crm_record_id = result.get("id")
        if not crm_record_id:
            raise CRMUnexpectedError("Vtiger did not return a contact id.")

        self._logger.info(
            "vtiger_contact_created request_id=%s crm_record_id=%s",
            request_id,
            crm_record_id,
        )
        return CRMCreateResult(crm_record_id=str(crm_record_id))

    def list_leads(
        self, limit: int = 20, request_id: str | None = None
    ) -> list[CRMLeadSummary]:
        safe_limit = max(1, min(limit, 200))
        token = self._get_challenge()
        session_name, _user_id = self._login(token)
        leads = self._list_leads(session_name=session_name, limit=safe_limit)
        self._logger.info(
            "vtiger_leads_listed request_id=%s count=%s limit=%s",
            request_id,
            len(leads),
            safe_limit,
        )
        return leads

    def list_leads_for_sync(
        self,
        *,
        limit: int,
        sync_status_value: str,
        request_id: str | None = None,
    ) -> list[CRMLeadForSync]:
        safe_limit = max(1, min(limit, 500))
        token = self._get_challenge()
        session_name, _user_id = self._login(token)
        leads = self._query_leads_for_sync(
            session_name=session_name,
            limit=safe_limit,
            sync_status_value=sync_status_value,
        )
        self._logger.info(
            "vtiger_sync_candidates_listed request_id=%s count=%s limit=%s",
            request_id,
            len(leads),
            safe_limit,
        )
        return leads

    def update_lead_sync_result(
        self,
        *,
        lead_id: str,
        sync_status: str,
        woo_order_id: str | None = None,
        sync_error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        token = self._get_challenge()
        session_name, _user_id = self._login(token)

        element: dict[str, str] = {
            "id": lead_id,
            self._settings.vtiger_lead_field_sync_status: sync_status,
        }
        if woo_order_id is not None:
            element[self._settings.vtiger_lead_field_woo_order_id] = woo_order_id
        if sync_error is not None:
            element[self._settings.vtiger_lead_field_sync_error] = _truncate(sync_error, 240)
        else:
            element[self._settings.vtiger_lead_field_sync_error] = ""

        result = self._call_operation(
            method="POST",
            data={
                "operation": "revise",
                "sessionName": session_name,
                "element": json.dumps(element),
            },
        )
        if not isinstance(result, dict):
            raise CRMUnexpectedError("Vtiger revise result has invalid shape.")
        self._logger.info(
            "vtiger_sync_result_updated request_id=%s lead_id=%s sync_status=%s",
            request_id,
            lead_id,
            sync_status,
        )

    def _get_challenge(self) -> str:
        result = self._call_operation(
            method="GET",
            params={
                "operation": "getchallenge",
                "username": self._settings.vtiger_username,
            },
        )
        token = result.get("token")
        if not token:
            raise CRMAuthenticationError("Vtiger challenge token not found.")
        return str(token)

    def _login(self, token: str) -> tuple[str, str]:
        access_key_hash = hashlib.md5(
            f"{token}{self._settings.vtiger_access_key.get_secret_value()}".encode(
                "utf-8"
            )
        ).hexdigest()

        result = self._call_operation(
            method="POST",
            data={
                "operation": "login",
                "username": self._settings.vtiger_username,
                "accessKey": access_key_hash,
            },
        )

        session_name = result.get("sessionName")
        user_id = result.get("userId")
        if not session_name:
            raise CRMAuthenticationError("Vtiger sessionName not found in login.")
        if not user_id:
            raise CRMUnexpectedError("Vtiger userId not found in login.")
        return str(session_name), str(user_id)

    def _create_contact(self, session_name: str, payload: dict[str, str]) -> dict[str, Any]:
        result = self._call_operation(
            method="POST",
            data={
                "operation": "create",
                "sessionName": session_name,
                "elementType": "Leads",
                "element": json.dumps(payload),
            },
        )
        if not isinstance(result, dict):
            raise CRMUnexpectedError("Vtiger create result has invalid shape.")
        return result

    def _list_leads(self, session_name: str, limit: int) -> list[CRMLeadSummary]:
        query = (
            "SELECT * "
            f"FROM Leads LIMIT {limit};"
        )
        result = self._call_operation(
            method="GET",
            params={
                "operation": "query",
                "sessionName": session_name,
                "query": query,
            },
        )
        if not isinstance(result, list):
            raise CRMUnexpectedError("Vtiger leads query did not return a list.")

        leads: list[CRMLeadSummary] = []
        for item in result:
            if not isinstance(item, dict):
                continue
            lead_id = item.get("id")
            if not lead_id:
                continue
            leads.append(
                CRMLeadSummary(
                    crm_record_id=str(lead_id),
                    first_name=_clean_nullable(item.get("firstname")),
                    last_name=_clean_nullable(item.get("lastname")),
                    email=_clean_nullable(item.get("email")),
                    phone=_clean_nullable(item.get("phone")),
                    company=_clean_nullable(item.get("company")),
                    lead_source=_clean_nullable(item.get("leadsource")),
                )
            )
        return leads

    def _query_leads_for_sync(
        self, *, session_name: str, limit: int, sync_status_value: str
    ) -> list[CRMLeadForSync]:
        product_field = self._settings.vtiger_lead_field_product_id
        woo_order_field = self._settings.vtiger_lead_field_woo_order_id
        sync_status_field = self._settings.vtiger_lead_field_sync_status
        escaped_status = sync_status_value.replace("'", "\\'")
        query = (
            "SELECT id, firstname, lastname, email, phone, lane, city, state, code, country, "
            f"{product_field}, {woo_order_field}, {sync_status_field} "
            "FROM Leads "
            f"WHERE {sync_status_field} = '{escaped_status}' "
            f"LIMIT {limit};"
        )
        result = self._call_operation(
            method="GET",
            params={
                "operation": "query",
                "sessionName": session_name,
                "query": query,
            },
        )
        if not isinstance(result, list):
            raise CRMUnexpectedError("Vtiger sync leads query did not return a list.")

        leads: list[CRMLeadForSync] = []
        for item in result:
            if not isinstance(item, dict):
                continue
            lead_id = _clean_nullable(item.get("id"))
            if not lead_id:
                continue
            leads.append(
                CRMLeadForSync(
                    lead_id=lead_id,
                    first_name=_clean_nullable(item.get("firstname")),
                    last_name=_clean_nullable(item.get("lastname")),
                    email=_clean_nullable(item.get("email")),
                    phone=_clean_nullable(item.get("phone")),
                    address_1=_clean_nullable(item.get("lane")),
                    city=_clean_nullable(item.get("city")),
                    country=_clean_nullable(item.get("country")),
                    state=_clean_nullable(item.get("state")),
                    postcode=_clean_nullable(item.get("code")),
                    product_id=_to_int(item.get(product_field)),
                    woo_order_id=_clean_nullable(item.get(woo_order_field)),
                    sync_status=_clean_nullable(item.get(sync_status_field)),
                )
            )
        return leads

    def _call_operation(
        self,
        *,
        method: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Any:
        try:
            response = self._session.request(
                method=method,
                url=self._endpoint,
                params=params,
                data=data,
                timeout=self._settings.vtiger_timeout_seconds,
            )
        except requests.Timeout as exc:
            raise CRMNetworkError("Timeout while connecting to Vtiger.") from exc
        except requests.RequestException as exc:
            raise CRMNetworkError("Network error while connecting to Vtiger.") from exc

        if response.status_code in (401, 403):
            raise CRMAuthenticationError("HTTP authentication error from Vtiger.")
        if response.status_code >= 500:
            raise CRMNetworkError("Vtiger service unavailable.")
        if response.status_code >= 400:
            raise CRMUnexpectedError(
                f"Unexpected HTTP status from Vtiger: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise CRMUnexpectedError("Vtiger response is not valid JSON.") from exc

        if not payload.get("success"):
            self._raise_vtiger_error(payload.get("error"))

        if "result" not in payload:
            raise CRMUnexpectedError("Vtiger response missing result object.")
        return payload["result"]

    def _raise_vtiger_error(self, error_payload: Any) -> None:
        if not isinstance(error_payload, dict):
            raise CRMUnexpectedError("Unknown Vtiger error response.")

        code = str(error_payload.get("code", "")).upper()
        message = str(error_payload.get("message", "Unknown Vtiger error."))

        if code in AUTH_ERROR_CODES or "AUTH" in code:
            raise CRMAuthenticationError(message)
        if code in VALIDATION_ERROR_CODES or "MANDATORY" in code or "INVALID" in code:
            raise CRMValidationError(message)

        raise CRMUnexpectedError(message)


def _clean_nullable(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _to_int(value: Any) -> int | None:
    normalized = _clean_nullable(value)
    if normalized is None:
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
