class BioTrackError(Exception):
    """Base application exception."""


class BadRequestError(BioTrackError):
    """Raised when an incoming request is malformed."""


class MethodNotAllowedError(BioTrackError):
    """Raised when the route exists but the method is unsupported."""


class NotFoundError(BioTrackError):
    """Raised when a resource or route is not found."""


class ConflictError(BioTrackError):
    """Raised when a create/update violates uniqueness or integrity."""


class ServiceValidationError(BioTrackError):
    """Raised when business validation rejects an operation."""


class ApiError(Exception):
    """Represents an HTTP error raised by the client layer."""

    def __init__(self, status: int, detail: str | None = None, payload=None):
        super().__init__(detail or f"HTTP {status}")
        self.status = status
        self.detail = detail
        self.payload = payload
