import hashlib
import logging
from typing import Any

import requests

from app.domain.entities import CRMLeadForSync
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    CRMValidationError,
)
from app.domain.ports import CRMClientPort
from app.infrastructure.config import Settings

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

    def get_lead_for_checkout(
        self, *, lead_id: str, request_id: str | None = None
    ) -> CRMLeadForSync | None:
        token = self._get_challenge()
        session_name, _user_id = self._login(token)
        lead = self._get_single_lead_by_id(session_name=session_name, lead_id=lead_id)
        self._logger.info(
            "vtiger_lead_for_checkout request_id=%s lead_id=%s found=%s",
            request_id,
            lead_id,
            bool(lead),
        )
        return lead

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

    def _query_leads_for_sync(
        self, *, session_name: str, limit: int, sync_status_value: str
    ) -> list[CRMLeadForSync]:
        product_field = self._settings.vtiger_lead_field_product_id
        woo_order_field = self._settings.vtiger_lead_field_woo_order_id
        sync_status_field = self._settings.vtiger_lead_field_sync_status
        student_id_type_field = self._settings.vtiger_lead_field_student_id_type
        student_id_number_field = self._settings.vtiger_lead_field_student_id_number
        student_program_field = self._settings.vtiger_lead_field_student_academic_program
        escaped_status = sync_status_value.replace("'", "\\'")
        query = (
            "SELECT id, firstname, lastname, email, phone, lane, city, state, code, country, "
            f"{product_field}, {woo_order_field}, {sync_status_field}, "
            f"{student_id_type_field}, {student_id_number_field}, {student_program_field} "
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
                    student_id_type=_clean_nullable(item.get(student_id_type_field)),
                    student_id_number=_clean_nullable(item.get(student_id_number_field)),
                    student_academic_program=_clean_nullable(
                        item.get(student_program_field)
                    ),
                )
            )
        return leads

    def _get_single_lead_by_id(
        self, *, session_name: str, lead_id: str
    ) -> CRMLeadForSync | None:
        product_field = self._settings.vtiger_lead_field_product_id
        woo_order_field = self._settings.vtiger_lead_field_woo_order_id
        sync_status_field = self._settings.vtiger_lead_field_sync_status
        student_id_type_field = self._settings.vtiger_lead_field_student_id_type
        student_id_number_field = self._settings.vtiger_lead_field_student_id_number
        student_program_field = self._settings.vtiger_lead_field_student_academic_program
        escaped_id = lead_id.replace("'", "\\'")
        query = (
            "SELECT id, firstname, lastname, email, phone, lane, city, state, code, country, "
            f"{product_field}, {woo_order_field}, {sync_status_field}, "
            f"{student_id_type_field}, {student_id_number_field}, {student_program_field} "
            "FROM Leads "
            f"WHERE id = '{escaped_id}' "
            "LIMIT 1;"
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
            raise CRMUnexpectedError("Vtiger single lead query did not return a list.")
        if not result:
            return None

        item = result[0]
        if not isinstance(item, dict):
            return None

        lead_id_value = _clean_nullable(item.get("id"))
        if not lead_id_value:
            return None
        return CRMLeadForSync(
            lead_id=lead_id_value,
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
            student_id_type=_clean_nullable(item.get(student_id_type_field)),
            student_id_number=_clean_nullable(item.get(student_id_number_field)),
            student_academic_program=_clean_nullable(item.get(student_program_field)),
        )

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