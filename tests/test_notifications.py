from datetime import datetime
from unittest import TestCase
from unittest.mock import create_autospec

from booking import (
    BookingConflictError,
    BookingService,
    BookingStatus,
    InMemoryBookingRepository,
    InvalidBookingTimeError,
    NotificationService,
    RoomNotFoundError,
)


def at(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2030, 1, 15, hour, minute, second)


class BookingNotificationTests(TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryBookingRepository(["room1"])
        self.notifications = create_autospec(NotificationService, instance=True)
        self.service = BookingService(
            self.repository,
            clock=lambda: at(9),
            notification_service=self.notifications,
        )

    def test_a1_creation_returns_active_booking(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10), at(11))

        self.assertEqual(booking.status, BookingStatus.ACTIVE)

    def test_a1_creation_saves_returned_booking(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10), at(11))

        self.assertEqual(self.repository.get(booking.id), booking)

    def test_a1_creation_notifies_once(self) -> None:
        self.service.create_booking("room1", "user1", at(10), at(11))

        self.notifications.notify_booking_created.assert_called_once()

    def test_a1_booking_is_saved_before_notification(self) -> None:
        saved_at_notification = []

        def record_saved_booking(**values) -> None:
            saved_at_notification.append(self.repository.get(values["booking_id"]))

        self.notifications.notify_booking_created.side_effect = record_saved_booking

        booking = self.service.create_booking("room1", "user1", at(10), at(11))

        self.assertEqual(saved_at_notification, [booking])

    def test_conflict_does_not_notify(self) -> None:
        self.service.create_booking("room1", "user1", at(10), at(11))
        self.notifications.reset_mock()

        with self.assertRaises(BookingConflictError):
            self.service.create_booking("room1", "user2", at(10, 30), at(11, 30))

        self.notifications.notify_booking_created.assert_not_called()

    def test_invalid_time_does_not_notify(self) -> None:
        with self.assertRaises(InvalidBookingTimeError):
            self.service.create_booking("room1", "user1", at(7), at(8))

        self.notifications.notify_booking_created.assert_not_called()

    def test_unknown_room_does_not_notify(self) -> None:
        with self.assertRaises(RoomNotFoundError):
            self.service.create_booking("unknown", "user1", at(10), at(11))

        self.notifications.notify_booking_created.assert_not_called()

    def test_cancellation_does_not_send_creation_notification(self) -> None:
        booking = self.service.create_booking("room1", "user1", at(10), at(11))
        self.notifications.reset_mock()

        self.service.cancel_booking(booking.id, "user1")

        self.notifications.notify_booking_created.assert_not_called()
