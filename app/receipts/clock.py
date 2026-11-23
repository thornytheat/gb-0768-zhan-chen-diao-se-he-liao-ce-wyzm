from datetime import UTC, datetime, timedelta, timezone

STUDIO = timezone(timedelta(hours=8))


def timepoint(raw):
    try:
        value = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if value.tzinfo is None or not 2000 <= value.year <= 2099:
            raise ValueError
        return value.astimezone(UTC)
    except (AttributeError, ValueError, OverflowError):
        raise ValueError('BAD_TIME') from None


def studio_label(iso):
    return timepoint(iso).astimezone(STUDIO).strftime('%m/%d %H:%M')
