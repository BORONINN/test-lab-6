from collections.abc import Iterable
from typing import Protocol

from .models import Booking


class BookingRepository(Protocol):
    def add(self, booking: Booking) -> None:
        """Insert a booking, checking room existence and conflicts atomically."""
        ...

    def get(self, booking_id: str) -> Booking | None:
        ...

    def list_for_room(self, room_id: str) -> list[Booking]:
        ...


class InMemoryBookingRepository:
    def __init__(self, room_ids: Iterable[str]) -> None:
        pass

    def add(self, booking: Booking) -> None:
        raise NotImplementedError

    def get(self, booking_id: str) -> Booking | None:
        raise NotImplementedError

    def list_for_room(self, room_id: str) -> list[Booking]:
        raise NotImplementedError
