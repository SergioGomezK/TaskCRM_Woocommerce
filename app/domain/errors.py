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


class WooValidationError(DomainError):
    """WooCommerce rejected request data."""


class WooAuthenticationError(DomainError):
    """Authentication against WooCommerce failed."""


class WooNetworkError(DomainError):
    """Network or timeout issue while calling WooCommerce."""


class WooUnexpectedError(DomainError):
    """Unexpected WooCommerce response or unknown failure."""
