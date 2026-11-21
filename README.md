# Сервис бронирования переговорных комнат

Практическая работа № 6, вариант 1.

## Запуск тестов

Нужен Python 3.10 или новее. Тесты используют стандартную библиотеку. Запустите их из корня проекта.

```bash
python -m unittest discover -v
```

## Программный API

```python
from datetime import datetime

from booking import BookingService, InMemoryBookingRepository

repository = InMemoryBookingRepository(["room1", "room2"])
service = BookingService(repository)

booking = service.create_booking(
    room_id="room1",
    user_id="user1",
    start_at=datetime(2030, 1, 15, 10, 0),
    end_at=datetime(2030, 1, 15, 11, 0),
)
print(service.get_booking(booking.id))
print(service.list_bookings("room1"))
```

- `create_booking(room_id, user_id, start_at, end_at) -> Booking` сохраняет бронь со статусом `ACTIVE`. Идентификаторы передаются строками, время — как локальный `datetime` офиса без часового пояса. Некорректное время вызывает `InvalidBookingTimeError`, неизвестная комната — `RoomNotFoundError`, пересечение активных броней — `BookingConflictError`.
- `get_booking(booking_id) -> Booking` возвращает запись любого статуса. Для неизвестного ID возникает `BookingNotFoundError`.
- `list_bookings(room_id) -> list[Booking]` возвращает записи комнаты обоих статусов в порядке начала и ID. Если у комнаты нет записей, возвращается `[]`.
- Сигнатура для PR 2 — `cancel_booking(booking_id: str, user_id: str) -> Booking`.

`BookingService` принимает реализацию `BookingRepository`. Метод `add(booking)` проверяет комнату и атомарно отклоняет пересечение активных записей при вставке. `get(booking_id)` возвращает запись или `None`, а `list_for_room(room_id)` возвращает записи комнаты обоих статусов. В хранилище в памяти список доступных комнат задаётся при создании объекта.

## Тесты PR 1

[PR 1 — создание и чтение бронирований](https://github.com/BORONINN/test-lab-6/pull/1)

| Сценарии | Что проверяется |
| --- | --- |
| U1–U4 | Порядок границ, рабочий день 08:00–20:00, длительность 30–120 минут, пересечение и соприкосновение интервалов. Проверки вызываются напрямую. |
| A2–A3 | Чтение обоих статусов, выборка по комнате, отказ при пересечении и сохранение только одной брони при одновременных запросах. Используется сервис с хранилищем в памяти. |

- [Red — тесты и заготовки API](https://github.com/BORONINN/test-lab-6/commit/80d4bbd4bda99733e07eb5cdeab5c99a3702ed3b).
- [Green — рабочая реализация](https://github.com/BORONINN/test-lab-6/commit/85a1e9ddf9192c66e3fd75c58b7e7f0ec483d0e2).
