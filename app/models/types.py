from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on any backend.

    SQLite has no timezone support: DateTime(timezone=True) silently drops
    the offset on write and returns naive values on read, which then reach
    JSON without "Z" and are shown in the browser's local time.
    Values are stored as naive UTC and returned as aware UTC.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)  # CURRENT_TIMESTAMP is UTC
        return value.astimezone(timezone.utc)
