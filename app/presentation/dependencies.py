from fastapi import Depends

from app.application.use_cases.create_woo_order import CreateWooOrderUseCase
from app.application.use_cases.list_leads import ListLeadsUseCase
from app.application.use_cases.submit_client_form import SubmitClientFormUseCase
from app.domain.ports import CRMClientPort, WooCommercePort
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.woocommerce.client import WooCommerceClient
from app.infrastructure.vtiger.client import VtigerClient


def get_crm_client(settings: Settings = Depends(get_settings)) -> CRMClientPort:
    return VtigerClient(settings=settings)


def get_woocommerce_client(
    settings: Settings = Depends(get_settings),
) -> WooCommercePort:
    return WooCommerceClient(settings=settings)


def get_submit_client_form_use_case(
    crm_client: CRMClientPort = Depends(get_crm_client),
) -> SubmitClientFormUseCase:
    return SubmitClientFormUseCase(crm_client=crm_client)


def get_list_leads_use_case(
    crm_client: CRMClientPort = Depends(get_crm_client),
) -> ListLeadsUseCase:
    return ListLeadsUseCase(crm_client=crm_client)


def get_create_woo_order_use_case(
    woo_client: WooCommercePort = Depends(get_woocommerce_client),
) -> CreateWooOrderUseCase:
    return CreateWooOrderUseCase(woo_client=woo_client)
