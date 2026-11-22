from datetime import datetime
from unittest import TestCase
from unittest.mock import create_autospec

from booking import (
    Booking,
    BookingService,
    BookingStatus,
    InMemoryBookingRepository,
    NotificationService,
)


def at(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2030, 1, 15, hour, minute, second)


class BookingContractTests(TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryBookingRepository(["room1", "room2"])
        self.notifications = create_autospec(NotificationService, instance=True)
        self.service = BookingService(
            self.repository, notification_service=self.notifications
        )

    def assert_booking_format(self, booking: Booking) -> None:
        self.assertIsInstance(booking, Booking)
        self.assertIsInstance(booking.id, str)
        self.assertIsInstance(booking.room_id, str)
        self.assertIsInstance(booking.user_id, str)
        self.assertIsInstance(booking.start_at, datetime)
        self.assertIsInstance(booking.end_at, datetime)
        self.assertIsInstance(booking.status, BookingStatus)

    def test_c1_create_returns_booking_format(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10), at(11))

        self.assert_booking_format(booking)

    def test_c1_get_returns_booking_format(self) -> None:
        self.repository.add(
            Booking("saved-id", "room1", "user1", at(10), at(11), BookingStatus.ACTIVE)
        )

        booking = self.service.get_booking("saved-id")

        self.assert_booking_format(booking)

    def test_c2_populated_list_contains_bookings(self) -> None:
        self.repository.add(
            Booking("saved-id", "room1", "user1", at(10), at(11), BookingStatus.ACTIVE)
        )

        bookings = self.service.list_bookings("room1")

        self.assertIsInstance(bookings, list)
        self.assertEqual(len(bookings), 1)
        self.assert_booking_format(bookings[0])

    def test_c2_empty_room_returns_empty_list(self) -> None:
        self.assertEqual(self.service.list_bookings("room2"), [])

    def test_c3_notification_receives_booking_values(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10), at(11))

        self.notifications.notify_booking_created.assert_called_once_with(
            user_id=booking.user_id,
            booking_id=booking.id,
            room_id=booking.room_id,
            start_at=booking.start_at,
            end_at=booking.end_at,
        )

    def test_c4_notification_preserves_start_seconds(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10, 15, 30), at(11, 45, 45))

        self.notifications.notify_booking_created.assert_called_once()
        self.assertEqual(
            self.notifications.notify_booking_created.call_args.kwargs["start_at"],
            booking.start_at,
        )

    def test_c4_notification_preserves_end_seconds(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10, 15, 30), at(11, 45, 45))

        self.notifications.notify_booking_created.assert_called_once()
        self.assertEqual(
            self.notifications.notify_booking_created.call_args.kwargs["end_at"],
            booking.end_at,
        )
