from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.interviews.models import (
    Interview,
    InterviewAvailabilityBlock,
    InterviewAvailabilityProfile,
    InterviewPanelist,
)

WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


@dataclass
class Interval:
    start: datetime
    end: datetime


def _parse_hhmm(value: str, fallback: str) -> time:
    candidate = (value or fallback or '').strip()
    try:
        hh, mm = candidate.split(':', 1)
        return time(hour=int(hh), minute=int(mm))
    except Exception:
        hh, mm = fallback.split(':', 1)
        return time(hour=int(hh), minute=int(mm))


def _ensure_tz(dt: datetime, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, tz)
    return dt.astimezone(tz)


def _profile_for(tenant_id, interviewer_id):
    profile, _ = InterviewAvailabilityProfile.objects.get_or_create(
        tenant_id=tenant_id,
        interviewer_id=interviewer_id,
        defaults={
            'mode': 'system',
            'timezone': 'UTC',
        },
    )
    return profile


def _work_window(profile: InterviewAvailabilityProfile, day: date, target_tz: str) -> Interval | None:
    day_key = WEEKDAY_KEYS[day.weekday()]
    cfg = (profile.working_hours or {}).get(day_key) or {}
    if not cfg.get('enabled', False):
        return None

    start_t = _parse_hhmm(str(cfg.get('start', '09:00')), '09:00')
    end_t = _parse_hhmm(str(cfg.get('end', '18:00')), '18:00')
    if (end_t.hour, end_t.minute) <= (start_t.hour, start_t.minute):
        return None

    interviewer_tz = profile.timezone or 'UTC'
    start_dt = _ensure_tz(datetime.combine(day, start_t), interviewer_tz)
    end_dt = _ensure_tz(datetime.combine(day, end_t), interviewer_tz)
    return Interval(start=start_dt.astimezone(ZoneInfo(target_tz)), end=end_dt.astimezone(ZoneInfo(target_tz)))


def _busy_intervals(tenant_id, interviewer_ids, window_start: datetime, window_end: datetime):
    busy = {str(i): [] for i in interviewer_ids}

    for row in InterviewAvailabilityBlock.objects.filter(
        tenant_id=tenant_id,
        interviewer_id__in=interviewer_ids,
        starts_at__lt=window_end,
        ends_at__gt=window_start,
    ):
        key = str(row.interviewer_id)
        if key in busy:
            busy[key].append(Interval(start=row.starts_at, end=row.ends_at))

    interview_ids = list(
        InterviewPanelist.objects.filter(interviewer_id__in=interviewer_ids).values_list('interview_id', flat=True)
    )
    interviews = Interview.objects.filter(
        tenant_id=tenant_id,
        id__in=interview_ids,
        is_deleted=False,
        scheduled_at__isnull=False,
        scheduled_at__lt=window_end,
    )
    interview_map = {str(iv.id): iv for iv in interviews}

    for panel in InterviewPanelist.objects.filter(interviewer_id__in=interviewer_ids, interview_id__in=interview_map.keys()):
        interview = interview_map.get(str(panel.interview_id))
        if not interview or not interview.scheduled_at:
            continue
        duration = interview.duration_minutes or 60
        start = interview.scheduled_at
        end = start + timedelta(minutes=duration)
        if end <= window_start or start >= window_end:
            continue
        key = str(panel.interviewer_id)
        if key in busy:
            busy[key].append(Interval(start=start, end=end))

    return busy


def _has_overlap(interval: Interval, existing: list[Interval]) -> bool:
    for row in existing:
        if interval.start < row.end and interval.end > row.start:
            return True
    return False


def compute_common_slots(*, tenant_id, interviewer_ids, timezone_name: str,
                         from_date: date, to_date: date,
                         duration_minutes: int = 60,
                         step_minutes: int = 30,
                         limit: int = 20):
    if not interviewer_ids:
        return []

    tz = timezone_name or 'UTC'
    results = []

    start_dt = _ensure_tz(datetime.combine(from_date, time.min), tz)
    end_dt = _ensure_tz(datetime.combine(to_date + timedelta(days=1), time.min), tz)
    busy = _busy_intervals(tenant_id, interviewer_ids, start_dt, end_dt)

    day = from_date
    while day <= to_date and len(results) < limit:
        windows = []
        for interviewer_id in interviewer_ids:
            profile = _profile_for(tenant_id, interviewer_id)
            window = _work_window(profile, day, tz)
            if not window:
                windows = []
                break
            windows.append(window)
        if windows:
            open_start = max(w.start for w in windows)
            open_end = min(w.end for w in windows)
            cursor = open_start
            while cursor + timedelta(minutes=duration_minutes) <= open_end and len(results) < limit:
                candidate = Interval(start=cursor, end=cursor + timedelta(minutes=duration_minutes))
                if all(not _has_overlap(candidate, busy[str(i)]) for i in interviewer_ids):
                    results.append({
                        'starts_at': candidate.start.isoformat(),
                        'ends_at': candidate.end.isoformat(),
                        'timezone': tz,
                    })
                cursor += timedelta(minutes=step_minutes)
        day += timedelta(days=1)

    return results
