from dataclasses import replace
from datetime import datetime
from unittest import TestCase

from booking import (
    BookingCancellationError,
    BookingNotFoundError,
    BookingService,
    BookingStatus,
    InMemoryBookingRepository,
)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2030, 1, 15, hour, minute)


class BookingCancellationTests(TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryBookingRepository(["room1"])
        self.now = at(9, 59)
        self.service = BookingService(self.repository, clock=lambda: self.now)
        self.booking = self.service.create_booking("room1", "user1", at(10), at(11))

    def test_a4_owner_can_cancel_before_start(self) -> None:
        cancelled = self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(cancelled.status, BookingStatus.CANCELLED)

    def test_a4_cancelled_status_is_saved(self) -> None:
        self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(
            self.repository.get(self.booking.id).status, BookingStatus.CANCELLED
        )

    def test_a4_cancellation_preserves_other_fields(self) -> None:
        cancelled = self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(cancelled, replace(self.booking, status=BookingStatus.CANCELLED))

    def test_a4_cancelled_booking_remains_readable(self) -> None:
        cancelled = self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(self.service.get_booking(self.booking.id), cancelled)

    def test_a4_cancelled_booking_remains_in_room_list(self) -> None:
        cancelled = self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(self.service.list_bookings("room1"), [cancelled])

    def test_other_user_cannot_cancel(self) -> None:
        with self.assertRaises(BookingCancellationError):
            self.service.cancel_booking(self.booking.id, "user2")

        self.assertEqual(self.repository.get(self.booking.id), self.booking)

    def test_cancelled_booking_cannot_be_cancelled_again(self) -> None:
        cancelled = self.service.cancel_booking(self.booking.id, "user1")

        with self.assertRaises(BookingCancellationError):
            self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(self.repository.get(self.booking.id), cancelled)

    def test_cancellation_at_start_is_rejected(self) -> None:
        self.now = at(10)

        with self.assertRaises(BookingCancellationError):
            self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(self.repository.get(self.booking.id), self.booking)

    def test_cancellation_after_start_is_rejected(self) -> None:
        self.now = at(10, 1)

        with self.assertRaises(BookingCancellationError):
            self.service.cancel_booking(self.booking.id, "user1")

        self.assertEqual(self.repository.get(self.booking.id), self.booking)

    def test_unknown_booking_cannot_be_cancelled(self) -> None:
        with self.assertRaises(BookingNotFoundError):
            self.service.cancel_booking("unknown", "user1")

    def test_cancellation_releases_interval(self) -> None:
        self.service.cancel_booking(self.booking.id, "user1")

        new_booking = self.service.create_booking("room1", "user2", at(10), at(11))

        self.assertEqual(new_booking.status, BookingStatus.ACTIVE)


class BookingStatusUpdateTests(TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryBookingRepository(["room1"])
        self.service = BookingService(self.repository)
        self.booking = self.service.create_booking("room1", "user1", at(10), at(11))

    def test_status_update_preserves_booking_data(self) -> None:
        updated = self.repository.update_status(
            self.booking.id, BookingStatus.ACTIVE, BookingStatus.CANCELLED
        )

        self.assertEqual(updated, replace(self.booking, status=BookingStatus.CANCELLED))

    def test_status_update_rejects_stale_expected_status(self) -> None:
        cancelled = self.repository.update_status(
            self.booking.id, BookingStatus.ACTIVE, BookingStatus.CANCELLED
        )

        with self.assertRaises(BookingCancellationError):
            self.repository.update_status(
                self.booking.id, BookingStatus.ACTIVE, BookingStatus.CANCELLED
            )

        self.assertEqual(self.repository.get(self.booking.id), cancelled)

    def test_status_update_rejects_unknown_id(self) -> None:
        with self.assertRaises(BookingNotFoundError):
            self.repository.update_status(
                "unknown", BookingStatus.ACTIVE, BookingStatus.CANCELLED
            )
