from datetime import datetime


def validate_order(start_at: datetime, end_at: datetime) -> None:
    raise NotImplementedError


def validate_working_hours(start_at: datetime, end_at: datetime) -> None:
    raise NotImplementedError


def validate_duration(start_at: datetime, end_at: datetime) -> None:
    raise NotImplementedError


def intervals_overlap(
    start_at: datetime,
    end_at: datetime,
    other_start_at: datetime,
    other_end_at: datetime,
) -> bool:
    raise NotImplementedError
