from datetime import datetime, time, timedelta

from .errors import InvalidBookingTimeError

OPENING_TIME = time(8)
CLOSING_TIME = time(20)
MIN_DURATION = timedelta(minutes=30)
MAX_DURATION = timedelta(hours=2)


def validate_order(start_at: datetime, end_at: datetime) -> None:
    if start_at.utcoffset() is not None or end_at.utcoffset() is not None:
        raise InvalidBookingTimeError("Use local office time without a time zone.")
    if start_at >= end_at:
        raise InvalidBookingTimeError("The booking must start before it ends.")


def validate_working_hours(start_at: datetime, end_at: datetime) -> None:
    if (
        start_at.date() != end_at.date()
        or start_at.time() < OPENING_TIME
        or end_at.time() > CLOSING_TIME
    ):
        raise InvalidBookingTimeError("Book within one day between 08:00 and 20:00.")


def validate_duration(start_at: datetime, end_at: datetime) -> None:
    if not MIN_DURATION <= end_at - start_at <= MAX_DURATION:
        raise InvalidBookingTimeError("Book for at least 30 minutes and at most 2 hours.")


def intervals_overlap(
    start_at: datetime,
    end_at: datetime,
    other_start_at: datetime,
    other_end_at: datetime,
) -> bool:
    return start_at < other_end_at and other_start_at < end_at
