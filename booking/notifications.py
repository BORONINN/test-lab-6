from datetime import datetime
from typing import Protocol


class NotificationService(Protocol):
    def notify_booking_created(
        self,
        user_id: str,
        booking_id: str,
        room_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        ...
