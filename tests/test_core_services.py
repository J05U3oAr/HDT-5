import datetime

import pytest

from src.core.faq_service import FaqService
from src.core.weather_service import ForecastRangeError, WeatherService
from src.core.schemas import SafetyStatus


def test_weather_ideal_conditions_are_allowed():
    status, allowed, _, _ = WeatherService().evaluate_safety_criteria(15, 30, 0, 20)
    assert status is SafetyStatus.IDEAL
    assert allowed is True


def test_weather_prohibited_conditions_are_rejected():
    status, allowed, _, _ = WeatherService().evaluate_safety_criteria(29, 20, 0, 20)
    assert status is SafetyStatus.PROHIBIDO
    assert allowed is False


def test_forecast_after_sixteen_days_is_rejected():
    service = WeatherService()
    future_date = datetime.date.today() + datetime.timedelta(days=17)
    with pytest.raises(ForecastRangeError):
        service.validate_date_range(future_date)


def test_faq_service_returns_price_information():
    response = FaqService().buscar_faqs("costo del salto")
    assert "Q1,800" in response
