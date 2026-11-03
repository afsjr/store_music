from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain.services.store_hours import StoreHoursService

TZ = ZoneInfo("America/Campo_Grande")


def _at(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=TZ)


@pytest.mark.parametrize(
    ("moment", "open_now", "next_weekday", "next_hour"),
    [
        (_at(2026, 3, 2, 10), True, None, None),
        (_at(2026, 3, 2, 8), False, 0, 9),
        (_at(2026, 3, 2, 18), False, 1, 9),
        (_at(2026, 3, 6, 18), False, 5, 9),
        (_at(2026, 3, 7, 12), True, None, None),
        (_at(2026, 3, 7, 14), False, 0, 9),
        (_at(2026, 3, 8, 10), False, 0, 9),
    ],
)
def test_store_status_by_weekday_and_time(moment, open_now, next_weekday, next_hour):
    status = StoreHoursService().status(moment)
    assert status.aberto is open_now
    if open_now:
        assert status.proxima_abertura is None
    else:
        assert status.proxima_abertura is not None
        expected_day = moment.date().toordinal() + (
            (next_weekday - moment.weekday()) % 7 if next_weekday is not None else 0
        )
        assert status.proxima_abertura.date().toordinal() == expected_day
        assert status.proxima_abertura.hour == next_hour


def test_open_message_uses_closing_time():
    status = StoreHoursService().status(_at(2026, 3, 2, 10))
    assert "aberta agora" in status.mensagem
    assert "18:00" in status.mensagem


def test_closed_same_day_message():
    status = StoreHoursService().status(_at(2026, 3, 2, 8))
    assert "fechada agora" in status.mensagem
    assert "hoje, 09:00" in status.mensagem


def test_closed_next_day_message():
    status = StoreHoursService().status(_at(2026, 3, 2, 19))
    assert "amanhã, 09:00" in status.mensagem


def test_saturday_after_close_points_to_monday():
    status = StoreHoursService().status(_at(2026, 3, 7, 14))
    assert "segunda-feira, 09:00" in status.mensagem


def test_sunday_points_to_monday():
    status = StoreHoursService().status(_at(2026, 3, 8, 10))
    assert status.dia_semana == "domingo"
    assert status.horario_hoje == "Fechado"
    assert "amanhã, 09:00" in status.mensagem


def test_special_dates_note():
    status = StoreHoursService().status(_at(2026, 3, 2, 10))
    assert "Black Friday" in status.observacao_datas_especiais
    assert "Feriados" in status.observacao_datas_especiais


def test_status_loja_tool(tools):
    tools.hours = StoreHoursService(now_provider=lambda: _at(2026, 3, 2, 10))
    result = tools.execute("status_loja", {}, "sessao")
    assert result.ok is True
    data = result.result
    assert data["aberto"] is True
    assert data["agora"] == "02/03/2026 10:00"
    assert data["horarios"]["sabado"] == "09:00 às 13:00"
    assert data["citacoes"][0]["section"] == "2"


def test_informacoes_loja_includes_current_status(tools):
    tools.hours = StoreHoursService(now_provider=lambda: _at(2026, 3, 2, 19))
    result = tools.execute("informacoes_loja", {}, "sessao")
    assert result.ok is True
    status = result.result["status_agora"]
    assert status["aberto"] is False
    assert status["proxima_abertura"] == "03/03/2026 09:00"
