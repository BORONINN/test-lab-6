from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Booking:
    id: str
    room_id: str
    user_id: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus
