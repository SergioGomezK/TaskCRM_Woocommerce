from fastapi import Depends

from app.application.use_cases.generate_checkout_links_from_vtiger_leads import (
    GenerateCheckoutLinksFromVtigerLeadsUseCase,
)
from app.application.use_cases.resolve_checkout_link import ResolveCheckoutLinkUseCase
from app.domain.ports import CRMClientPort, CheckoutLinkIdentityPort, CheckoutLinkPort
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.woocommerce.checkout_link_builder import WooCheckoutLinkBuilder
from app.infrastructure.woocommerce.checkout_link_identity import HMACCheckoutLinkIdentity
from app.infrastructure.vtiger.client import VtigerClient


def get_crm_client(settings: Settings = Depends(get_settings)) -> CRMClientPort:
    return VtigerClient(settings=settings)


def get_checkout_link_builder(
    settings: Settings = Depends(get_settings),
) -> CheckoutLinkPort:
    return WooCheckoutLinkBuilder(settings=settings)


def get_checkout_link_identity(
    settings: Settings = Depends(get_settings),
) -> CheckoutLinkIdentityPort:
    return HMACCheckoutLinkIdentity(settings=settings)


def get_generate_checkout_links_from_vtiger_leads_use_case(
    crm_client: CRMClientPort = Depends(get_crm_client),
    link_identity: CheckoutLinkIdentityPort = Depends(get_checkout_link_identity),
    settings: Settings = Depends(get_settings),
) -> GenerateCheckoutLinksFromVtigerLeadsUseCase:
    return GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        link_identity=link_identity,
        pending_status=settings.vtiger_sync_pending_value,
        batch_limit_default=settings.vtiger_sync_batch_limit_default,
    )


def get_resolve_checkout_link_use_case(
    settings: Settings = Depends(get_settings),
    crm_client: CRMClientPort = Depends(get_crm_client),
    checkout_link_builder: CheckoutLinkPort = Depends(get_checkout_link_builder),
    link_identity: CheckoutLinkIdentityPort = Depends(get_checkout_link_identity),
) -> ResolveCheckoutLinkUseCase:
    return ResolveCheckoutLinkUseCase(
        crm_client=crm_client,
        checkout_link_builder=checkout_link_builder,
        link_identity=link_identity,
        default_country=settings.woo_default_country,
    )