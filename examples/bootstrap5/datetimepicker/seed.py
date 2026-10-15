import datetime

from django.utils import timezone

from datetimepicker.models import Event, PickerVariant

#: (title, days from the first of this month, doors open, start, duration in hours or None)
EVENTS = [
    ("Kick-off", 2, "17:30", "18:00", 2),
    ("Django meetup", 9, "18:30", "19:00", 3),
    ("Code review clinic", 16, "16:45", "17:00", 1),
    ("Release party", 23, "19:00", "20:00", None),
    ("Sprint planning", 33, "08:45", "09:00", 2),
    ("Accessibility workshop", 40, "09:30", "10:00", 6),
    ("Django meetup", 47, "18:30", "19:00", 3),
    ("Hack night", 54, "19:30", "20:00", 4),
    ("Quarterly review", 64, "13:45", "14:00", 2),
    ("Django meetup", 75, "18:30", "19:00", 3),
    ("Year-end retro", 86, "15:30", "16:00", 2),
    ("Holiday dinner", 92, "18:00", "19:00", None),
]


def _time(text: str) -> datetime.time:
    return datetime.time.fromisoformat(text)


def seed():
    seed_events()
    seed_variants()


def seed_events():
    # days are relative to the current month: seed once, or a later run (task run seeds on every start) would add a
    # second set of events in the new month
    if Event.objects.exists():
        return
    tz = timezone.get_current_timezone()
    first = timezone.localdate().replace(day=1)
    for title, offset, doors, start, hours in EVENTS:
        day = first + datetime.timedelta(days=offset)
        starts_at = datetime.datetime.combine(day, _time(start), tzinfo=tz)
        Event.objects.get_or_create(
            title=title,
            day=day,
            defaults={
                "doors_open": _time(doors),
                "starts_at": starts_at,
                "ends_at": starts_at + datetime.timedelta(hours=hours) if hours else None,
            },
        )


def seed_variants():
    PickerVariant.objects.get_or_create(name="Example", defaults={"quarter_hour": datetime.time(9, 15)})
