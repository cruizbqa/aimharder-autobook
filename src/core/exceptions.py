class AimHarderError(Exception):
    """Base exception for AimHarder related errors."""
    pass


class AuthError(AimHarderError):
    """Raised when authentication fails."""
    pass


class BookingError(AimHarderError):
    """Raised when booking a class fails."""
    pass


class AlreadyBookedError(BookingError):
    """Raised when there is already a booking at the same time."""
    pass
