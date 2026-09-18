import datetime

import pytest

from src.core.faq_service import FaqService
from src.core.weather_service import ForecastRangeError, WeatherService, WeatherServiceError
from src.core.schemas import SafetyStatus


def test_weather_ideal_conditions_are_allowed():
    status, allowed, _, _ = WeatherService().evaluate_safety_criteria(15, 30, 0, 20)
    assert status is SafetyStatus.IDEAL
    assert allowed is True


def test_weather_prohibited_conditions_are_rejected():
    status, allowed, _, _ = WeatherService().evaluate_safety_criteria(29, 20, 0, 20)
    assert status is SafetyStatus.PROHIBIDO
    assert allowed is False


def test_last_available_forecast_day_is_allowed():
    service = WeatherService()
    last_available_date = datetime.date.today() + datetime.timedelta(days=15)
    service.validate_date_range(last_available_date)


def test_day_after_forecast_window_is_rejected():
    service = WeatherService()
    future_date = datetime.date.today() + datetime.timedelta(days=16)
    with pytest.raises(ForecastRangeError):
        service.validate_date_range(future_date)


def test_incomplete_provider_data_returns_controlled_error(monkeypatch):
    target_date = datetime.date.today()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "daily": {
                    "time": [target_date.isoformat()],
                    "temperature_2m_max": [None],
                    "wind_speed_10m_max": [None],
                    "wind_gusts_10m_max": [None],
                    "precipitation_sum": [None],
                    "cloud_cover_mean": [None],
                }
            }

    monkeypatch.setattr(
        "src.core.weather_service.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(WeatherServiceError, match="aún no publicó datos completos"):
        WeatherService().fetch_weather_for_date(target_date)


def test_faq_service_returns_price_information():
    response = FaqService().buscar_faqs("costo del salto")
    assert "Q1,800" in response


def test_faq_service_states_age_exception_unambiguously():
    response = FaqService().buscar_faqs("requisitos edad")
    assert "16 y 17 anos" in response
    assert "menores de 16 anos no pueden saltar" in response
