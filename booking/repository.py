from collections.abc import Iterable
from dataclasses import replace
from threading import Lock
from typing import Protocol

from .errors import (
    BookingCancellationError,
    BookingConflictError,
    BookingNotFoundError,
    RoomNotFoundError,
)
from .models import Booking, BookingStatus
from .rules import intervals_overlap


class BookingRepository(Protocol):
    def update_status(
        self, booking_id: str, expected_status: BookingStatus, new_status: BookingStatus
    ) -> Booking:
        """Change status only if it still matches expected_status, atomically."""
        ...

    def add(self, booking: Booking) -> None:
        """Insert a booking, checking room existence and conflicts atomically."""
        ...

    def get(self, booking_id: str) -> Booking | None:
        ...

    def list_for_room(self, room_id: str) -> list[Booking]:
        """Return bookings of any status for the room."""
        ...


class InMemoryBookingRepository:
    def update_status(
        self, booking_id: str, expected_status: BookingStatus, new_status: BookingStatus
    ) -> Booking:
        with self._lock:
            booking = self._bookings.get(booking_id)
            if booking is None:
                raise BookingNotFoundError(f"Unknown booking: {booking_id}")
            if booking.status is not expected_status:
                raise BookingCancellationError("The booking status has changed.")
            updated = replace(booking, status=new_status)
            if new_status is BookingStatus.ACTIVE:
                raise ValueError("Status updates cannot reactivate a booking.")
            self._bookings[booking_id] = updated
            return updated

    def __init__(self, room_ids: Iterable[str]) -> None:
        self._room_ids = set(room_ids)
        self._bookings: dict[str, Booking] = {}
        self._lock = Lock()

    def add(self, booking: Booking) -> None:
        if booking.room_id not in self._room_ids:
            raise RoomNotFoundError(f"Unknown room: {booking.room_id}")

        with self._lock:
            if booking.id in self._bookings:
                raise ValueError(f"Booking ID already exists: {booking.id}")
            if booking.status is BookingStatus.ACTIVE and self._has_conflict(booking):
                raise BookingConflictError(f"The room is already booked: {booking.room_id}")
            self._bookings[booking.id] = booking

    def get(self, booking_id: str) -> Booking | None:
        with self._lock:
            return self._bookings.get(booking_id)

    def list_for_room(self, room_id: str) -> list[Booking]:
        with self._lock:
            return [
                booking
                for booking in self._bookings.values()
                if booking.room_id == room_id
            ]

    def _has_conflict(self, candidate: Booking) -> bool:
        return any(
            intervals_overlap(
                candidate.start_at, candidate.end_at, booking.start_at, booking.end_at
            )
            for booking in self._bookings.values()
            if booking.room_id == candidate.room_id and booking.status is BookingStatus.ACTIVE
        )
