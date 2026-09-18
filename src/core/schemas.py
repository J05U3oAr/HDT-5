from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SafetyStatus(str, Enum):
    IDEAL = "IDEAL"
    MARGINAL = "MARGINAL"
    PROHIBIDO = "PROHIBIDO"


class WeatherMetricEvaluation(BaseModel):
    name: str
    value: float
    unit: str
    status: SafetyStatus
    description: str


class WeatherReport(BaseModel):
    latitude: float = 14.013722
    longitude: float = -90.771611
    date: str
    temperature_2m: float = Field(..., description="Temperatura en grados Celsius a 2m")
    wind_speed_10m: float = Field(..., description="Velocidad del viento en km/h a 10m")
    wind_gusts_10m: float = Field(..., description="Rafagas de viento en km/h a 10m")
    precipitation: float = Field(..., description="Precipitacion en mm")
    cloud_cover: float = Field(..., description="Cobertura nubosa / Visibilidad en porcentaje %")
    overall_status: SafetyStatus = Field(..., description="Dictamen global de seguridad")
    allowed_to_jump: bool = Field(..., description="Si esta permitido realizar saltos")
    restrictions: str = Field(..., description="Restricciones o condiciones especiales")
    details: List[str] = Field(default_factory=list, description="Desglose de cada metrica")

    def format_summary(self) -> str:
        simbolo = "✅" if self.overall_status == SafetyStatus.IDEAL else ("⚠️" if self.overall_status == SafetyStatus.MARGINAL else "❌")
        lineas = [
            f"{simbolo} **Dictamen Meteorológico ({self.date})**: {self.overall_status.value}",
            f"- Ubicación: {self.latitude}, {self.longitude} (Zona de salto Escuintla / Pacífico)",
            f"- Temperatura: {self.temperature_2m:.1f} °C",
            f"- Velocidad de viento superficie: {self.wind_speed_10m:.1f} km/h",
            f"- Ráfagas de viento: {self.wind_gusts_10m:.1f} km/h",
            f"- Precipitación: {self.precipitation:.1f} mm",
            f"- Cobertura de nubes / Visibilidad: {self.cloud_cover:.0f}%",
            f"- Estado de operación: {'PERMITIDO' if self.allowed_to_jump else 'NO PERMITIDO / CANCELADO'}",
            f"- Restricciones: {self.restrictions}",
        ]
        if self.details:
            lineas.append("\nEvaluación de criterios:")
            for d in self.details:
                lineas.append(f"  • {d}")
        return "\n".join(lineas)


class Appointment(BaseModel):
    id: str
    client_name: str
    date: str
    time: str
    jump_type: str = "Tándem Estándar"
    weather_status: str
    restrictions: str
    status: str = "CONFIRMADA"
    created_at: str

    def format_confirmation(self) -> str:
        return (
            f"🎉 **Cita Agendada Exitosamente**\n"
            f"- Código de Reserva: `{self.id}`\n"
            f"- Cliente: {self.client_name}\n"
            f"- Fecha: {self.date}\n"
            f"- Hora: {self.time}\n"
            f"- Modalidad: {self.jump_type}\n"
            f"- Condición Meteorológica: {self.weather_status}\n"
            f"- Observaciones: {self.restrictions}\n"
            f"- Estado: {self.status}"
        )
