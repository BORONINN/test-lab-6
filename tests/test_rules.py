from datetime import datetime, timedelta
from unittest import TestCase

from booking import InvalidBookingTimeError
from booking.rules import (
    intervals_overlap,
    validate_duration,
    validate_order,
    validate_working_hours,
)


def at(hour: int, minute: int = 0, day: int = 15) -> datetime:
    return datetime(2030, 1, day, hour, minute)


class BookingRuleTests(TestCase):
    def test_u1_start_must_be_earlier_than_end(self) -> None:
        cases = [(at(10), at(11), True), (at(10), at(10), False), (at(11), at(10), False)]
        for start_at, end_at, valid in cases:
            with self.subTest(start_at=start_at, end_at=end_at):
                if valid:
                    validate_order(start_at, end_at)
                else:
                    with self.assertRaises(InvalidBookingTimeError):
                        validate_order(start_at, end_at)

    def test_u2_booking_must_fit_in_one_working_day(self) -> None:
        cases = [
            (at(8), at(8, 30), True),
            (at(19, 30), at(20), True),
            (at(7, 59), at(8), False),
            (at(19, 30), at(20, 1), False),
            (at(19, 30), at(8, 30, day=16), False),
        ]
        for start_at, end_at, valid in cases:
            with self.subTest(start_at=start_at, end_at=end_at):
                if valid:
                    validate_working_hours(start_at, end_at)
                else:
                    with self.assertRaises(InvalidBookingTimeError):
                        validate_working_hours(start_at, end_at)

    def test_u3_duration_limits_are_inclusive(self) -> None:
        start_at = at(10)
        for minutes, valid in [(29, False), (30, True), (120, True), (121, False)]:
            with self.subTest(minutes=minutes):
                end_at = start_at + timedelta(minutes=minutes)
                if valid:
                    validate_duration(start_at, end_at)
                else:
                    with self.assertRaises(InvalidBookingTimeError):
                        validate_duration(start_at, end_at)

    def test_u4_touching_intervals_do_not_overlap(self) -> None:
        cases = [
            (at(10, 30), at(11, 30), True),
            (at(10), at(11), True),
            (at(9), at(12), True),
            (at(9), at(10), False),
            (at(11), at(12), False),
        ]
        for other_start, other_end, overlaps in cases:
            with self.subTest(other_start=other_start, other_end=other_end):
                self.assertEqual(
                    intervals_overlap(at(10), at(11), other_start, other_end), overlaps
                )
                self.assertEqual(
                    intervals_overlap(other_start, other_end, at(10), at(11)), overlaps
                )
