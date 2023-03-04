"""Custom errors for atuyka."""

__all__ = [
    "AtuykaError",
    "AuthenticationError",
    "InvalidIDError",
    "InvalidResourceError",
    "InvalidServiceError",
    "InvalidTokenError",
    "MissingTokenError",
    "MissingUserIDError",
    "PrivateResourceError",
    "RateLimitedError",
    "ServiceError",
    "SuspendedResourceError",
]


class AtuykaError(Exception):
    """Base error for atuyka."""

    message: str = "An error occurred"

    service: str

    def __init__(self, service: str, message: str | None = None) -> None:
        self.service = service
        self.message = message or self.message
        super().__init__(self.message)


class RateLimitedError(AtuykaError):
    """Rate limit error."""

    message = "Rate limit exceeded"

    service: str
    reset: int | None

    def __init__(self, service: str, reset: int | None = None) -> None:
        self.reset = reset
        super().__init__(service, f"Rate limit exceeded for service {service!r}")


class ServiceError(AtuykaError):
    """Service error."""

    message = "Service error"

    service: str


class InvalidServiceError(ServiceError):
    """Invalid service error."""

    message = "Invalid service"

    available_services: list[str]

    def __init__(self, service: str, services: list[str]) -> None:
        self.available_services = services
        super().__init__(service, f"Service {service!r} not found, must be one of: {', '.join(services)!r}")


class MissingEndpointError(ServiceError):
    """Missing endpoint error."""

    message = "Missing endpoint"

    endpoint: str

    def __init__(self, service: str, endpoint: str) -> None:
        self.endpoint = endpoint
        super().__init__(service, f"Endpoint {endpoint!r} not found for service {service!r}")


class InvalidResourceError(ServiceError):
    """Invalid resource error."""

    message = "Invalid resource"

    resource: str

    def __init__(self, service: str, resource: str, message: str | None = None) -> None:
        self.resource = resource
        super().__init__(service, message or f"Resource {resource!r} not found for service {service!r}")


class SuspendedResourceError(InvalidResourceError):
    """Suspended resource error."""

    message = "Suspended resource"

    resource: str

    def __init__(self, service: str, resource: str) -> None:
        self.resource = resource
        super().__init__(service, resource, f"Resource {resource!r} is suspended for service {service!r}")


class MissingUserIDError(InvalidResourceError):
    """Missing ID error."""

    message = "Missing user ID"

    suggestion: str | None

    def __init__(self, service: str, suggestion: str | None = None) -> None:
        self.suggestion = suggestion
        super().__init__(service, "", f"ID is missing for service {service!r}")


class InvalidIDError(InvalidResourceError):
    """Invalid ID error."""

    message = "Invalid ID"

    id: str
    id_type: str

    def __init__(self, service: str, id: str, id_type: str) -> None:
        self.id = id
        super().__init__(service, "", f"{id_type.capitalize()} ID {id!r} is invalid for service {service!r}")


class AuthenticationError(AtuykaError):
    """Service authentication error."""

    message = "Authentication error"


class MissingTokenError(AuthenticationError):
    """Missing token error."""

    message = "Missing token"


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""

    message = "Invalid token"

    service: str
    token: str

    def __init__(self, service: str, token: str) -> None:
        self.token = token
        super().__init__(service, f"Invalid token {token!r} for service {service!r}")


class PrivateResourceError(AuthenticationError):
    """Private resource error."""

    message = "Resource is private"

    resource: str

    def __init__(self, service: str, resource: str) -> None:
        self.resource = resource
        super().__init__(service, f"Resource {resource!r} is private for service {service!r}")
