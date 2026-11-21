from datetime import datetime
from uuid import uuid4

from .errors import BookingNotFoundError
from .models import Booking, BookingStatus
from .repository import BookingRepository
from .rules import validate_duration, validate_order, validate_working_hours


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self._repository = repository

    def create_booking(
        self, room_id: str, user_id: str, start_at: datetime, end_at: datetime
    ) -> Booking:
        validate_order(start_at, end_at)
        validate_working_hours(start_at, end_at)
        validate_duration(start_at, end_at)

        booking = Booking(
            id=str(uuid4()),
            room_id=room_id,
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
            status=BookingStatus.ACTIVE,
        )
        self._repository.add(booking)
        return booking

    def get_booking(self, booking_id: str) -> Booking:
        booking = self._repository.get(booking_id)
        if booking is None:
            raise BookingNotFoundError(f"Unknown booking: {booking_id}")
        return booking

    def list_bookings(self, room_id: str) -> list[Booking]:
        bookings = self._repository.list_for_room(room_id)
        return sorted(bookings, key=lambda booking: (booking.start_at, booking.id))
