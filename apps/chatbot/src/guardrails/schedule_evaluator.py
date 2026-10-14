from datetime import datetime, time
from typing import Tuple
from zoneinfo import ZoneInfo
from core.config import settings
from enum import Enum

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


class ScheduleStatus(str, Enum):
    HUMAN_OFFICE_HOURS = "HUMAN_OFFICE_HOURS"  # Ivana atiende en persona; el bot debe hacer SILENCIO
    QUIET_HOURS = "QUIET_HOURS"                # 00:00 - 07:30: Silencio nocturno salvo emergencias
    BOT_ACTIVE_OFF_HOURS = "BOT_ACTIVE_OFF_HOURS" # Bot responde activamente con plantillas / IA


def _parse_time(time_str: str) -> time:
    parts = [int(p) for p in time_str.split(":")]
    return time(parts[0], parts[1])


def evaluate_schedule(dt: datetime = None) -> ScheduleStatus:
    """
    Evalúa si el momento actual corresponde a:
    1. Horario Humano (L-V 10-18hs, Sáb 10-13hs) -> Bot SILENCIOSO
    2. Quiet Hours (00:00 a 07:30 hs) -> Bot posterga no-urgentes
    3. Fuera de Horario -> Bot ACTIVO
    """
    if dt is None:
        if settings.OVERRIDE_SCHEDULE_OFF_HOURS:
            return ScheduleStatus.BOT_ACTIVE_OFF_HOURS
        dt = datetime.now(ARGENTINA_TZ)

    current_time = dt.time()
    weekday = dt.weekday()  # 0 = Lunes, 5 = Sábado, 6 = Domingo

    # 1. Verificar Quiet Hours (00:00 a 07:30)
    qh_start = _parse_time(settings.QUIET_HOURS_START)
    qh_end = _parse_time(settings.QUIET_HOURS_END)
    if qh_start <= current_time < qh_end:
        return ScheduleStatus.QUIET_HOURS

    # 2. Verificar Horario Humano Laboral
    mf_start = _parse_time(settings.OFFICE_HOURS_MF_START)
    mf_end = _parse_time(settings.OFFICE_HOURS_MF_END)
    sat_start = _parse_time(settings.OFFICE_HOURS_SAT_START)
    sat_end = _parse_time(settings.OFFICE_HOURS_SAT_END)

    # Lunes a Viernes (0 al 4)
    if 0 <= weekday <= 4:
        if mf_start <= current_time < mf_end:
            return ScheduleStatus.HUMAN_OFFICE_HOURS

    # Sábados (5)
    elif weekday == 5:
        if sat_start <= current_time < sat_end:
            return ScheduleStatus.HUMAN_OFFICE_HOURS

    # Domingos (6) o fuera de horario laboral de Lunes a Sábado
    return ScheduleStatus.BOT_ACTIVE_OFF_HOURS
