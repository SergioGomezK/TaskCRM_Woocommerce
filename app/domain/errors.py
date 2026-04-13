class DomainError(Exception):
    """Base class for domain/application errors."""


class CRMValidationError(DomainError):
    """The CRM rejected business data or mandatory fields."""


class CRMAuthenticationError(DomainError):
    """Authentication against CRM failed."""


class CRMNetworkError(DomainError):
    """Network or timeout issue while calling CRM."""


class CRMUnexpectedError(DomainError):
    """Unexpected CRM response or unknown failure."""


class WooUnexpectedError(DomainError):
    """Unexpected WooCommerce response or missing configuration."""


class InvalidCheckoutLinkError(DomainError):
    """Static checkout link is invalid."""