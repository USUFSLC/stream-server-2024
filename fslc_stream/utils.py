from datetime import UTC, datetime


def parse_datetime_permissive(dt: int | float | str) -> datetime:
    if isinstance(dt, int) or isinstance(dt, float):
        return datetime.fromtimestamp(dt, UTC)
    if isinstance(dt, str):
        return datetime.fromisoformat(dt)
