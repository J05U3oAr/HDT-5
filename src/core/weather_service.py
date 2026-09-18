from __future__ import annotations

import datetime
from typing import Tuple
import requests

from src.core.schemas import SafetyStatus, WeatherReport

# Constantes fijadas por los requerimientos del proyecto
LATITUDE = 14.013722
LONGITUDE = -90.771611
# Open-Meteo devuelve una ventana de 16 fechas que incluye el día actual.
# Por ello, el último desplazamiento válido es hoy + 15 días.
MAX_FORECAST_DAYS = 16
MAX_FORECAST_OFFSET_DAYS = MAX_FORECAST_DAYS - 1


class WeatherServiceError(Exception):
    """Excepcion base para errores del servicio meteorologico."""
    pass


class ForecastRangeError(WeatherServiceError):
    """Excepcion cuando la fecha queda fuera de la ventana de prediccion."""
    pass


class WeatherService:
    def __init__(self, lat: float = LATITUDE, lon: float = LONGITUDE):
        self.latitude = lat
        self.longitude = lon

    def parse_target_date(self, date_str: str) -> datetime.date:
        """Parsea una fecha en texto a un objeto date. Soporta 'hoy', 'mañana' o 'YYYY-MM-DD'."""
        cleaned = date_str.strip().lower()
        today = datetime.date.today()

        if cleaned in ("hoy", "today", "current", "actual"):
            return today
        if cleaned in ("mañana", "manana", "tomorrow"):
            return today + datetime.timedelta(days=1)
        if cleaned in ("pasado mañana", "pasado manana"):
            return today + datetime.timedelta(days=2)

        # Intentar formato ISO YYYY-MM-DD
        try:
            return datetime.date.fromisoformat(cleaned)
        except ValueError:
            pass

        # Intentar formato DD/MM/YYYY o DD-MM-YYYY
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        raise ValueError(
            f"Formato de fecha inválido: '{date_str}'. Utilice el formato YYYY-MM-DD (ejemplo: {today.isoformat()}) "
            f"o términos como 'hoy' o 'mañana'."
        )

    def validate_date_range(self, target_date: datetime.date) -> None:
        """Verifica la ventana de 16 fechas: desde hoy hasta hoy + 15 dias."""
        today = datetime.date.today()
        max_allowed_date = today + datetime.timedelta(days=MAX_FORECAST_OFFSET_DAYS)

        if target_date < today:
            raise ForecastRangeError(
                f"La fecha solicitada ({target_date.isoformat()}) es anterior a hoy ({today.isoformat()}). "
                f"No es posible consultar el clima ni agendar citas para fechas pasadas."
            )

        if target_date > max_allowed_date:
            raise ForecastRangeError(
                f"Open-Meteo provee una ventana de {MAX_FORECAST_DAYS} fechas contando el día de hoy. "
                f"La fecha solicitada ({target_date.isoformat()}) excede este límite (la fecha máxima permitida es {max_allowed_date.isoformat()}). "
                f"Por favor elija una fecha entre hoy y los próximos {MAX_FORECAST_OFFSET_DAYS} días."
            )

    @staticmethod
    def _require_numeric_metric(value: object, metric: str, date_str: str) -> float:
        """Convierte una métrica sin ocultar datos ausentes del proveedor."""
        if value is None:
            raise WeatherServiceError(
                f"Open-Meteo aún no publicó datos completos para {date_str}; "
                f"falta la métrica '{metric}'. Intente nuevamente más tarde o elija una fecha más cercana."
            )
        try:
            return float(value)
        except (TypeError, ValueError) as err:
            raise WeatherServiceError(
                f"Open-Meteo devolvió un valor inválido para '{metric}' en la fecha {date_str}."
            ) from err

    def fetch_weather_for_date(self, target_date: datetime.date) -> dict:
        """Consulta la API de Open-Meteo para las coordenadas y fecha indicadas."""
        today = datetime.date.today()
        self.validate_date_range(target_date)

        # Si es el dia de hoy, podemos usar current y daily
        endpoint = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": "auto",
            "forecast_days": MAX_FORECAST_DAYS,
            "daily": "temperature_2m_max,wind_speed_10m_max,wind_gusts_10m_max,precipitation_sum,cloud_cover_mean",
        }

        if target_date == today:
            params["current"] = "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation,cloud_cover"

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as err:
            raise WeatherServiceError(f"Error al conectar con la API de Open-Meteo: {err}") from err

        date_str = target_date.isoformat()

        # Si es hoy y tenemos current, podemos combinar la informacion
        if target_date == today and "current" in data:
            curr = data["current"]
            return {
                "date": date_str,
                "temperature_2m": self._require_numeric_metric(curr.get("temperature_2m"), "temperature_2m", date_str),
                "wind_speed_10m": self._require_numeric_metric(curr.get("wind_speed_10m"), "wind_speed_10m", date_str),
                "wind_gusts_10m": self._require_numeric_metric(curr.get("wind_gusts_10m"), "wind_gusts_10m", date_str),
                "precipitation": self._require_numeric_metric(curr.get("precipitation"), "precipitation", date_str),
                "cloud_cover": self._require_numeric_metric(curr.get("cloud_cover"), "cloud_cover", date_str),
            }

        # Extraer del bloque daily
        daily = data.get("daily", {})
        time_list = daily.get("time", [])
        if date_str not in time_list:
            raise WeatherServiceError(f"No se encontraron datos de pronóstico para la fecha {date_str} en Open-Meteo.")

        idx = time_list.index(date_str)

        def daily_value(metric: str) -> float:
            values = daily.get(metric)
            value = values[idx] if isinstance(values, list) and idx < len(values) else None
            return self._require_numeric_metric(value, metric, date_str)

        return {
            "date": date_str,
            "temperature_2m": daily_value("temperature_2m_max"),
            "wind_speed_10m": daily_value("wind_speed_10m_max"),
            "wind_gusts_10m": daily_value("wind_gusts_10m_max"),
            "precipitation": daily_value("precipitation_sum"),
            "cloud_cover": daily_value("cloud_cover_mean"),
        }

    def evaluate_safety_criteria(
        self,
        wind_speed_10m: float,
        wind_gusts_10m: float,
        precipitation: float,
        cloud_cover: float,
    ) -> Tuple[SafetyStatus, bool, str, list[str]]:
        """Aplica la matriz de decision estricta exigida por Parachute S.A."""
        details = []
        is_prohibited = False
        is_marginal = False

        # 1. Velocidad de viento en superficie (wind_speed_10m)
        # Ideal: < 20 km/h
        # Marginal (Solo tandem experimentado): 20–28 km/h
        # NO SEGURO / PROHIBIDO: > 28 km/h
        if wind_speed_10m > 28.0:
            is_prohibited = True
            details.append(f"Viento en superficie ({wind_speed_10m:.1f} km/h): NO SEGURO / PROHIBIDO (> 28 km/h, muy difícil de controlar el salto).")
        elif 20.0 <= wind_speed_10m <= 28.0:
            is_marginal = True
            details.append(f"Viento en superficie ({wind_speed_10m:.1f} km/h): MARGINAL (20-28 km/h, solo tándem experimentado).")
        else:
            details.append(f"Viento en superficie ({wind_speed_10m:.1f} km/h): IDEAL (< 20 km/h).")

        # 2. Rafagas de viento (wind_gusts_10m)
        # NO SEGURO / PROHIBIDO: > 35 km/h
        if wind_gusts_10m > 35.0:
            is_prohibited = True
            details.append(f"Ráfagas de viento ({wind_gusts_10m:.1f} km/h): NO SEGURO / PROHIBIDO (> 35 km/h).")
        else:
            details.append(f"Ráfagas de viento ({wind_gusts_10m:.1f} km/h): SEGURO (≤ 35 km/h).")

        # 3. Precipitacion (precipitation)
        # NO SEGURO / PROHIBIDO: > 0.0 mm
        if precipitation > 0.0:
            is_prohibited = True
            details.append(f"Precipitación ({precipitation:.1f} mm): NO SEGURO / PROHIBIDO (> 0.0 mm, saltar con lluvia daña el equipo y lastima la piel).")
        else:
            details.append(f"Precipitación ({precipitation:.1f} mm): SEGURO (0.0 mm, sin lluvia).")

        # 4. Cobertura de nubes / Visibilidad (cloud_cover)
        # Ideal: < 30% (Visibilidad clara)
        # Marginal: 30 - 75% (Nubes dispersas)
        # NO SEGURO / PROHIBIDO: > 75%
        if cloud_cover > 75.0:
            is_prohibited = True
            details.append(f"Cobertura nubosa ({cloud_cover:.0f}%): NO SEGURO / PROHIBIDO (> 75%, techo de nubes bajo impide reglas visuales VFR).")
        elif 30.0 <= cloud_cover <= 75.0:
            is_marginal = True
            details.append(f"Cobertura nubosa ({cloud_cover:.0f}%): MARGINAL (30-75%, nubes dispersas).")
        else:
            details.append(f"Cobertura nubosa ({cloud_cover:.0f}%): IDEAL (< 30%, visibilidad clara).")

        # Dictamen consolidado
        if is_prohibited:
            status = SafetyStatus.PROHIBIDO
            allowed = False
            restrictions = "SALTO PROHIBIDO: Condiciones meteorológicas adversas. No se permite realizar saltos."
        elif is_marginal:
            status = SafetyStatus.MARGINAL
            allowed = True
            restrictions = "CONDICIÓN MARGINAL: Solo permitido para saltos en tándem con instructor experimentado."
        else:
            status = SafetyStatus.IDEAL
            allowed = True
            restrictions = "CONDICIÓN IDEAL: Viento calmo y visibilidad despejada. Apto para todo público."

        return status, allowed, restrictions, details

    def get_weather_report(self, date_input: str) -> WeatherReport:
        """Obtiene y evalua el reporte meteorologico para una fecha dada."""
        target_date = self.parse_target_date(date_input)
        raw = self.fetch_weather_for_date(target_date)

        status, allowed, restrictions, details = self.evaluate_safety_criteria(
            wind_speed_10m=raw["wind_speed_10m"],
            wind_gusts_10m=raw["wind_gusts_10m"],
            precipitation=raw["precipitation"],
            cloud_cover=raw["cloud_cover"],
        )

        return WeatherReport(
            latitude=self.latitude,
            longitude=self.longitude,
            date=raw["date"],
            temperature_2m=raw["temperature_2m"],
            wind_speed_10m=raw["wind_speed_10m"],
            wind_gusts_10m=raw["wind_gusts_10m"],
            precipitation=raw["precipitation"],
            cloud_cover=raw["cloud_cover"],
            overall_status=status,
            allowed_to_jump=allowed,
            restrictions=restrictions,
            details=details,
        )
