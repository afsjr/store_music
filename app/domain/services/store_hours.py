from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domain.models import StoreStatus

TIMEZONE = ZoneInfo("America/Campo_Grande")
WEEKDAY_LABELS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)
WEEKDAY_OPEN = time(9, 0)
WEEKDAY_CLOSE = time(18, 0)
SATURDAY_CLOSE = time(13, 0)
SPECIAL_DATES_NOTE = (
    "Em datas especiais (Black Friday, Aniversário da Loja, Natal), o horário pode ser "
    "estendido. Feriados não estão no calendário; confirme nas redes sociais."
)


class StoreHoursService:
    def __init__(self, now_provider=None) -> None:
        self._now_provider = now_provider or (lambda: datetime.now(TIMEZONE))

    def _window(self, weekday: int) -> tuple[time, time] | None:
        if weekday < 5:
            return WEEKDAY_OPEN, WEEKDAY_CLOSE
        if weekday == 5:
            return WEEKDAY_OPEN, SATURDAY_CLOSE
        return None

    def _next_opening(self, moment: datetime) -> datetime | None:
        for offset in range(0, 8):
            day = moment.date() + timedelta(days=offset)
            window = self._window(day.weekday())
            if window is None:
                continue
            candidate = datetime.combine(day, window[0], tzinfo=TIMEZONE)
            if candidate > moment:
                return candidate
        return None

    def status(self, now: datetime | None = None) -> StoreStatus:
        moment = now or self._now_provider()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=TIMEZONE)
        else:
            moment = moment.astimezone(TIMEZONE)

        weekday = moment.weekday()
        window = self._window(weekday)
        is_open = False
        if window is not None:
            opens = datetime.combine(moment.date(), window[0], tzinfo=TIMEZONE)
            closes = datetime.combine(moment.date(), window[1], tzinfo=TIMEZONE)
            is_open = opens <= moment < closes
            horario_hoje = f"{window[0]:%H:%M} às {window[1]:%H:%M}"
        else:
            horario_hoje = "Fechado"

        if is_open:
            prox = None
            close_label = window[1] if window else None
            mensagem = f"A loja está aberta agora, até {close_label:%H:%M}."
        else:
            prox = self._next_opening(moment)
            if prox is None:
                mensagem = "A loja está fechada agora."
            else:
                if prox.date() == moment.date():
                    when = "hoje"
                elif prox.date() == moment.date() + timedelta(days=1):
                    when = "amanhã"
                else:
                    when = WEEKDAY_LABELS[prox.weekday()]
                mensagem = f"A loja está fechada agora. Próximo atendimento: {when}, {prox:%H:%M}."

        return StoreStatus(
            aberto=is_open,
            agora=moment,
            dia_semana=WEEKDAY_LABELS[weekday],
            horario_hoje=horario_hoje,
            proxima_abertura=prox,
            mensagem=mensagem,
            observacao_datas_especiais=SPECIAL_DATES_NOTE,
        )
