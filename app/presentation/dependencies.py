from fastapi import Depends

from app.application.use_cases.create_woo_order import CreateWooOrderUseCase
from app.application.use_cases.generate_checkout_links_from_vtiger_leads import (
    GenerateCheckoutLinksFromVtigerLeadsUseCase,
)
from app.application.use_cases.list_leads import ListLeadsUseCase
from app.application.use_cases.submit_client_form import SubmitClientFormUseCase
from app.application.use_cases.sync_vtiger_leads_to_woo_orders import (
    SyncVtigerLeadsToWooOrdersUseCase,
)
from app.domain.ports import CRMClientPort, CheckoutLinkPort, WooCommercePort
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.woocommerce.checkout_link_builder import WooCheckoutLinkBuilder
from app.infrastructure.woocommerce.client import WooCommerceClient
from app.infrastructure.vtiger.client import VtigerClient


def get_crm_client(settings: Settings = Depends(get_settings)) -> CRMClientPort:
    return VtigerClient(settings=settings)


def get_woocommerce_client(
    settings: Settings = Depends(get_settings),
) -> WooCommercePort:
    return WooCommerceClient(settings=settings)


def get_checkout_link_builder(
    settings: Settings = Depends(get_settings),
) -> CheckoutLinkPort:
    return WooCheckoutLinkBuilder(settings=settings)


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


def get_sync_vtiger_leads_to_woo_orders_use_case(
    settings: Settings = Depends(get_settings),
    crm_client: CRMClientPort = Depends(get_crm_client),
    woo_client: WooCommercePort = Depends(get_woocommerce_client),
) -> SyncVtigerLeadsToWooOrdersUseCase:
    return SyncVtigerLeadsToWooOrdersUseCase(
        crm_client=crm_client,
        woo_client=woo_client,
        pending_status=settings.vtiger_sync_pending_value,
        processed_status=settings.vtiger_sync_processed_value,
        failed_status=settings.vtiger_sync_failed_value,
        default_country=settings.woo_default_country,
        default_payment_method=settings.woo_default_payment_method,
        default_payment_method_title=settings.woo_default_payment_method_title,
        default_set_paid=settings.woo_default_set_paid,
        batch_limit_default=settings.vtiger_sync_batch_limit_default,
    )


def get_generate_checkout_links_from_vtiger_leads_use_case(
    settings: Settings = Depends(get_settings),
    crm_client: CRMClientPort = Depends(get_crm_client),
    checkout_link_builder: CheckoutLinkPort = Depends(get_checkout_link_builder),
) -> GenerateCheckoutLinksFromVtigerLeadsUseCase:
    return GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        checkout_link_builder=checkout_link_builder,
        pending_status=settings.vtiger_sync_pending_value,
        default_country=settings.woo_default_country,
        batch_limit_default=settings.vtiger_sync_batch_limit_default,
    )
