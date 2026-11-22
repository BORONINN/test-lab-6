class InvalidBookingTimeError(ValueError):
    pass


class BookingConflictError(ValueError):
    pass


class BookingNotFoundError(LookupError):
    pass


class RoomNotFoundError(LookupError):
    pass


class BookingCancellationError(ValueError):
    pass
