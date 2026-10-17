from datetime import datetime, time
from typing import Tuple
from zoneinfo import ZoneInfo
from core.config import settings
from enum import Enum

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


class ScheduleStatus(str, Enum):
    HUMAN_OFFICE_HOURS = "HUMAN_OFFICE_HOURS"
    QUIET_HOURS = "QUIET_HOURS"
    BOT_ACTIVE_OFF_HOURS = "BOT_ACTIVE_OFF_HOURS"


def _parse_time(time_str: str) -> time:
    parts = [int(p) for p in time_str.split(":")]
    return time(parts[0], parts[1])


FERIADOS_AR = {
    (1, 1),
    (3, 24),
    (4, 2),
    (5, 1),
    (5, 25),
    (6, 17),
    (6, 20),
    (7, 9),
    (8, 17),
    (10, 12),
    (11, 20),
    (12, 8),
    (12, 25),
}


def evaluate_schedule(dt: datetime = None) -> ScheduleStatus:
    if dt is None:
        if settings.OVERRIDE_SCHEDULE_OFF_HOURS:
            return ScheduleStatus.BOT_ACTIVE_OFF_HOURS
        dt = datetime.now(ARGENTINA_TZ)

    current_time = dt.time()
    weekday = dt.weekday()
    es_feriado = (dt.month, dt.day) in FERIADOS_AR

    qh_start = _parse_time(settings.QUIET_HOURS_START)
    qh_end = _parse_time(settings.QUIET_HOURS_END)
    if qh_start <= current_time < qh_end:
        return ScheduleStatus.QUIET_HOURS

    if es_feriado or weekday == 6:
        return ScheduleStatus.BOT_ACTIVE_OFF_HOURS

    mf_start = _parse_time(settings.OFFICE_HOURS_MF_START)
    mf_end = _parse_time(settings.OFFICE_HOURS_MF_END)
    sat_start = _parse_time(settings.OFFICE_HOURS_SAT_START)
    sat_end = _parse_time(settings.OFFICE_HOURS_SAT_END)

    if 0 <= weekday <= 4:
        if mf_start <= current_time < mf_end:
            return ScheduleStatus.HUMAN_OFFICE_HOURS
    elif weekday == 5:
        if sat_start <= current_time < sat_end:
            return ScheduleStatus.HUMAN_OFFICE_HOURS

    return ScheduleStatus.BOT_ACTIVE_OFF_HOURS
