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
from unittest.mock import create_autospec

from booking import BookingService, InMemoryBookingRepository, NotificationService

repository = InMemoryBookingRepository(["room1", "room2"])
notifications = create_autospec(NotificationService, instance=True)
service = BookingService(
    repository,
    clock=lambda: datetime(2030, 1, 15, 9, 0),
    notification_service=notifications,
)

booking = service.create_booking(
    room_id="room1",
    user_id="user1",
    start_at=datetime(2030, 1, 15, 10, 0),
    end_at=datetime(2030, 1, 15, 11, 0),
)
print(service.get_booking(booking.id))
print(service.list_bookings("room1"))
print(service.cancel_booking(booking.id, "user1"))
notifications.notify_booking_created.assert_called_once()
```

- `create_booking(room_id, user_id, start_at, end_at) -> Booking` сохраняет бронь со статусом `ACTIVE`. Идентификаторы передаются строками, время - как локальный `datetime` офиса без часового пояса. Некорректное время вызывает `InvalidBookingTimeError`, неизвестная комната - `RoomNotFoundError`, пересечение активных броней - `BookingConflictError`.
- `get_booking(booking_id) -> Booking` возвращает запись любого статуса. Для неизвестного ID возникает `BookingNotFoundError`.
- `list_bookings(room_id) -> list[Booking]` возвращает записи комнаты обоих статусов в порядке начала и ID. Если у комнаты нет записей, возвращается `[]`.
- `cancel_booking(booking_id, user_id) -> Booking` отменяет только свою активную бронь до начала. Возвращает и сохраняет `CANCELLED`; ID, комната, владелец и время не изменяются. Чужая, повторная или поздняя отмена вызывает `BookingCancellationError`, неизвестный ID - `BookingNotFoundError`. В момент начала отмена уже запрещена.

`BookingService` принимает реализацию `BookingRepository`. Метод `add(booking)` проверяет комнату и атомарно отклоняет пересечение активных записей при вставке. `get(booking_id)` возвращает запись или `None`, а `list_for_room(room_id)` возвращает записи комнаты обоих статусов. В хранилище в памяти список доступных комнат задаётся при создании объекта.

## Тесты PR 1

[PR 1 - создание и чтение бронирований](https://github.com/BORONINN/test-lab-6/pull/1)

| Сценарии | Что проверяется |
| --- | --- |
| U1–U4 | Порядок границ, рабочий день 08:00–20:00, длительность 30–120 минут, пересечение и соприкосновение интервалов. Проверки вызываются напрямую. |
| A2–A3 | Чтение обоих статусов, выборка по комнате, отказ при пересечении и сохранение только одной брони при одновременных запросах. Используется сервис с хранилищем в памяти. |

- [Red - тесты и заготовки API](https://github.com/BORONINN/test-lab-6/commit/80d4bbd4bda99733e07eb5cdeab5c99a3702ed3b).
- [Green - рабочая реализация](https://github.com/BORONINN/test-lab-6/commit/85a1e9ddf9192c66e3fd75c58b7e7f0ec483d0e2).


## Отмена и часы

`clock` - функция без аргументов, возвращающая локальный `datetime` без часового пояса. По умолчанию используется `datetime.now`. В тестах часы задаются явно: проверки не зависят от даты запуска и не используют ожидания.

Хранилище предоставляет `update_status(booking_id, expected_status, new_status) -> Booking`. Проверка ожидаемого статуса и обновление выполняются под одной блокировкой. Если статус уже изменился, возникает `BookingCancellationError`. Это не позволяет двум запросам успешно отменить одну бронь. Обновление не удаляет запись; реактивация через этот метод запрещена. SQLite-реализация должна сохранить ту же семантику.

## Уведомления

Компонент `notification_service` обязательно передаётся в `BookingService` по интерфейсу `NotificationService`:

```python
notify_booking_created(
    user_id: str,
    booking_id: str,
    room_id: str,
    start_at: datetime,
    end_at: datetime,
) -> None
```

После успешного сохранения сервис вызывает этот метод один раз с именованными аргументами. Значения берутся из сохранённой брони; секунды времени не округляются. Если валидация или сохранение завершается ошибкой, вызова нет. Отмена не вызывает уведомление о создании.

Реализация внешнего сервиса в проект не входит. Пример и тесты используют `create_autospec(NotificationService, instance=True)`: mock проверяет сигнатуру и фиксирует вызовы, не отправляя сообщений. Если внешний компонент выбрасывает исключение, оно передаётся вызывающему коду; уже сохранённая бронь остаётся в хранилище. Повторные отправки не реализованы.

## Тесты PR 2

| Сценарий | Проверки |
| --- | --- |
| A1 | Статус ACTIVE, сохранение возвращаемой записи, один вызов уведомления, сохранение до вызова. |
| A4 | Отмена владельцем, сохранение CANCELLED, неизменность остальных полей, доступность записи после отмены. |
| C1 | Формат Booking отдельно для создания и чтения. |
| C2 | Формат заполненного списка и пустой список отдельными тестами. |
| C3 | Сигнатура вызова Notification Service и пять значений из созданной брони. |
| C4 | Сохранение секунд начала и окончания отдельными тестами. |

Дополнительно проверяются запреты чужой, повторной и поздней отмены, неизвестный ID, освобождение интервала и отсутствие уведомления при отказе в создании. В API-тестах работают настоящая бизнес-логика и хранилище в памяти. Часы фиксированы, внешний компонент заменён mock. Контрактные тесты проверяют структуры Python и вызовы интерфейса. SQLite и системные сценарии S1–S4 относятся к PR 3.

Каждый новый тест проверяет одно поведение и имеет независимую подготовку. Несколько утверждений используются для проверки одного результата, например отказа без изменения записи. Составные проверки чтения и соседних интервалов из PR 1 разделены на отдельные тесты.

Запуск отдельных групп:

```bash
# Unit
python -m unittest tests.test_rules -v

# API и обновление статуса хранилища
python -m unittest tests.test_service tests.test_cancellation tests.test_notifications -v

# Contract
python -m unittest tests.test_contracts -v

# Все имеющиеся тесты
python -m unittest discover -v
```


### История изменений PR 2

[Изменения ветки polyanskiy-part2](https://github.com/BORONINN/test-lab-6/compare/main...polyanskiy-part2)

- [test: define booking cancellation rules (Red)](https://github.com/BORONINN/test-lab-6/commit/ddc2d64a754aff07e9eb807b2923e2d6db61d499).
- [feat: implement booking cancellation (Green)](https://github.com/BORONINN/test-lab-6/commit/148c0fc24bc50f37880365b4606d1d5e927d1739).
- [test: define booking notification contracts (Red)](https://github.com/BORONINN/test-lab-6/commit/4de19529903e32b0eedf25f06bc93587a9d573d9).
- [feat: notify after saving a booking (Green)](https://github.com/BORONINN/test-lab-6/commit/0b177bb5ffca5f177a139edef1135520be69be80).
- [test: separate booking API scenarios](https://github.com/BORONINN/test-lab-6/commit/1fe075cec2044cbcfddf7479375d8b980e7b4a9a).

Проверенный коммит реализации: `1fe075cec2044cbcfddf7479375d8b980e7b4a9a`.
