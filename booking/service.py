from datetime import datetime

from .models import Booking
from .repository import BookingRepository


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self._repository = repository

    def create_booking(
        self, room_id: str, user_id: str, start_at: datetime, end_at: datetime
    ) -> Booking:
        raise NotImplementedError

    def get_booking(self, booking_id: str) -> Booking:
        raise NotImplementedError

    def list_bookings(self, room_id: str) -> list[Booking]:
        raise NotImplementedError
