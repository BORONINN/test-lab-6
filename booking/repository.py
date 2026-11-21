from collections.abc import Iterable
from threading import Lock
from typing import Protocol

from .errors import BookingConflictError, RoomNotFoundError
from .models import Booking, BookingStatus
from .rules import intervals_overlap


class BookingRepository(Protocol):
    def add(self, booking: Booking) -> None:
        """Insert a booking, checking room existence and conflicts atomically."""
        ...

    def get(self, booking_id: str) -> Booking | None:
        ...

    def list_for_room(self, room_id: str) -> list[Booking]:
        """Return bookings of any status for the room."""
        ...


class InMemoryBookingRepository:
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
