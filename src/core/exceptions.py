class AimHarderError(Exception):
    """Base exception for AimHarder related errors."""
    pass


class AuthError(AimHarderError):
    """Raised when authentication fails."""
    pass


class BookingError(AimHarderError):
    """Raised when booking a class fails."""
    pass
