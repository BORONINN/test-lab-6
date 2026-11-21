from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
from unittest import TestCase

from booking import (
    Booking,
    BookingConflictError,
    BookingNotFoundError,
    BookingService,
    BookingStatus,
    InMemoryBookingRepository,
    InvalidBookingTimeError,
    RoomNotFoundError,
)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2030, 1, 15, hour, minute)


class BookingServiceTests(TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryBookingRepository(["room1", "room2"])
        self.service = BookingService(self.repository)

    def test_a2_get_and_list_bookings_include_cancelled(self) -> None:
        active = self.service.create_booking("room1", "user1", at(11), at(12))
        cancelled = Booking(
            "old-id", "room1", "user1", at(10), at(11), BookingStatus.CANCELLED
        )
        self.repository.add(cancelled)
        self.service.create_booking("room2", "user1", at(10), at(11))

        self.assertEqual(active.status, BookingStatus.ACTIVE)
        self.assertEqual(self.service.get_booking(active.id), active)
        self.assertEqual(self.service.get_booking(cancelled.id), cancelled)
        self.assertEqual(self.service.list_bookings("room1"), [cancelled, active])

    def test_a2_list_is_empty_for_free_room(self) -> None:
        self.service.create_booking("room2", "user1", at(10), at(11))

        self.assertEqual(self.service.list_bookings("room1"), [])

    def test_a2_unknown_booking_id_raises(self) -> None:
        with self.assertRaises(BookingNotFoundError):
            self.service.get_booking("unknown")

    def test_a3_active_overlap_is_rejected_without_saving(self) -> None:
        active = self.service.create_booking("room1", "user1", at(10), at(11))

        with self.assertRaises(BookingConflictError):
            self.service.create_booking("room1", "user2", at(10, 30), at(11, 30))

        self.assertEqual(self.service.list_bookings("room1"), [active])

    def test_a3_other_rooms_and_adjacent_intervals_are_available(self) -> None:
        active = self.service.create_booking("room1", "user1", at(10), at(11))
        next_booking = self.service.create_booking("room1", "user2", at(11), at(12))
        other_room = self.service.create_booking("room2", "user2", at(10), at(11))

        self.assertEqual(self.service.list_bookings("room1"), [active, next_booking])
        self.assertEqual(self.service.list_bookings("room2"), [other_room])
        self.assertEqual(len({active.id, next_booking.id, other_room.id}), 3)

    def test_a3_cancelled_record_does_not_block_creation(self) -> None:
        cancelled = Booking(
            "old-id", "room1", "user1", at(10), at(11), BookingStatus.CANCELLED
        )
        self.repository.add(cancelled)

        active = self.service.create_booking("room1", "user2", at(10), at(11))

        self.assertNotEqual(active.id, cancelled.id)
        self.assertEqual(self.service.get_booking(cancelled.id), cancelled)
        self.assertCountEqual(self.service.list_bookings("room1"), [cancelled, active])

    def test_a3_concurrent_requests_cannot_both_book_the_same_interval(self) -> None:
        start_together = Barrier(2, timeout=5)

        def try_booking(user_id: str) -> Booking | None:
            service = BookingService(self.repository)
            start_together.wait()
            try:
                return service.create_booking("room1", user_id, at(10), at(11))
            except BookingConflictError:
                return None

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(try_booking, ["user1", "user2"]))

        saved = self.service.list_bookings("room1")
        self.assertEqual(len(saved), 1)
        self.assertCountEqual(results, [saved[0], None])

    def test_create_rejects_invalid_time_without_saving(self) -> None:
        with self.assertRaises(InvalidBookingTimeError):
            self.service.create_booking("room1", "user1", at(7, 30), at(8, 30))

        self.assertEqual(self.service.list_bookings("room1"), [])

    def test_create_requires_a_registered_room(self) -> None:
        with self.assertRaises(RoomNotFoundError):
            self.service.create_booking("unknown", "user1", at(10), at(11))
