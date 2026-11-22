from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from .errors import BookingCancellationError, BookingNotFoundError
from .models import Booking, BookingStatus
from .notifications import NotificationService
from .repository import BookingRepository
from .rules import validate_duration, validate_order, validate_working_hours


class BookingService:
    def __init__(
        self,
        repository: BookingRepository,
        *,
        clock: Callable[[], datetime] = datetime.now,
        notification_service: NotificationService,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._notification_service = notification_service

    def cancel_booking(self, booking_id: str, user_id: str) -> Booking:
        booking = self.get_booking(booking_id)
        if booking.user_id != user_id:
            raise BookingCancellationError("Only the owner can cancel the booking.")
        if booking.status is not BookingStatus.ACTIVE:
            raise BookingCancellationError("Only active bookings can be cancelled.")
        if self._clock() >= booking.start_at:
            raise BookingCancellationError("Cancel before the booking starts.")
        return self._repository.update_status(
            booking_id, BookingStatus.ACTIVE, BookingStatus.CANCELLED
        )

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
