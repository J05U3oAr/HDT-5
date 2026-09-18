from __future__ import annotations

import datetime
import json
import uuid
from pathlib import Path
from typing import List, Optional

from src.core.schemas import Appointment, SafetyStatus
from src.core.weather_service import ForecastRangeError, WeatherService, WeatherServiceError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CITAS_FILE = PROJECT_ROOT / "data" / "citas.json"


class CalendarService:
    def __init__(self, storage_path: Path = CITAS_FILE):
        self.storage_path = storage_path
        self.weather_service = WeatherService()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("[]", encoding="utf-8")

    def _load_appointments(self) -> List[Appointment]:
        try:
            content = self.storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            raw_list = json.loads(content)
            return [Appointment(**item) for item in raw_list]
        except Exception:
            return []

    def _save_appointments(self, appointments: List[Appointment]) -> None:
        raw_list = [a.model_dump() for a in appointments]
        self.storage_path.write_text(json.dumps(raw_list, indent=2, ensure_ascii=False), encoding="utf-8")

    def agendar_cita(
        self,
        nombre_cliente: str,
        fecha: str,
        hora: str = "10:00 AM",
        tipo_salto: str = "Tándem",
    ) -> dict:
        """Verifica el clima primero y, si es viable, agenda la cita de paracaidismo."""
        if not nombre_cliente or not nombre_cliente.strip():
            return {"exito": False, "mensaje": "Debe proporcionar el nombre del cliente para registrar la cita."}

        # 1. Validar el clima primero con Open-Meteo
        try:
            reporte = self.weather_service.get_weather_report(fecha)
        except ForecastRangeError as e:
            return {
                "exito": False,
                "mensaje": f"❌ Error de calendario: {str(e)}",
                "tipo_error": "FORECAST_RANGE_ERROR",
            }
        except (WeatherServiceError, ValueError) as e:
            return {
                "exito": False,
                "mensaje": f"❌ Error al evaluar condiciones meteorológicas: {str(e)}",
                "tipo_error": "WEATHER_ERROR",
            }

        # 2. Comprobar criterios de seguridad para saltar
        if not reporte.allowed_to_jump or reporte.overall_status == SafetyStatus.PROHIBIDO:
            return {
                "exito": False,
                "mensaje": (
                    f"⛔ NO ES POSIBLE AGENDAR PARA EL DÍA {reporte.date}.\n"
                    f"El dictamen meteorológico es NO SEGURO / PROHIBIDO.\n"
                    f"Motivo: {reporte.restrictions}\n\n"
                    f"Detalle del clima:\n"
                    f"- Viento: {reporte.wind_speed_10m:.1f} km/h (límite seguro: 28 km/h)\n"
                    f"- Ráfagas: {reporte.wind_gusts_10m:.1f} km/h (límite seguro: 35 km/h)\n"
                    f"- Precipitación: {reporte.precipitation:.1f} mm (límite: 0.0 mm)\n"
                    f"- Cobertura nubosa: {reporte.cloud_cover:.0f}% (límite: 75%)\n\n"
                    f"Por favor elija otra fecha dentro de la ventana disponible (hoy hasta hoy + 15 días)."
                ),
                "reporte": reporte.model_dump(),
            }

        # 3. Si el estado es Marginal o Ideal, agendar
        codigo_cita = f"PAR-{datetime.date.today().strftime('%y%m')}-{uuid.uuid4().hex[:6].upper()}"
        modalidad_final = tipo_salto
        if reporte.overall_status == SafetyStatus.MARGINAL:
            if "experimentado" not in modalidad_final.lower():
                modalidad_final = f"{tipo_salto} (Requisito: Tándem con Instructor Experimentado)"

        cita = Appointment(
            id=codigo_cita,
            client_name=nombre_cliente.strip(),
            date=reporte.date,
            time=hora.strip(),
            jump_type=modalidad_final,
            weather_status=reporte.overall_status.value,
            restrictions=reporte.restrictions,
            status="CONFIRMADA",
            created_at=datetime.datetime.now().isoformat(),
        )

        citas = self._load_appointments()
        citas.append(cita)
        self._save_appointments(citas)

        nota_clima = "Condiciones óptimas e ideales." if reporte.overall_status == SafetyStatus.IDEAL else "⚠️ Advertencia: Condiciones marginales, el salto se realizará estrictamente con instructor experimentado."

        return {
            "exito": True,
            "mensaje": (
                f"{cita.format_confirmation()}\n\n"
                f"Información meteorológica validada:\n"
                f"- Estado: {reporte.overall_status.value}\n"
                f"- Nota: {nota_clima}"
            ),
            "cita": cita.model_dump(),
            "reporte": reporte.model_dump(),
        }

    def listar_citas(self, filtro: Optional[str] = None) -> List[Appointment]:
        """Devuelve las citas registradas, con filtro opcional por cliente o codigo."""
        citas = self._load_appointments()
        if not filtro:
            return citas
        filtro_lower = filtro.strip().lower()
        return [
            c for c in citas
            if filtro_lower in c.client_name.lower() or filtro_lower in c.id.lower() or filtro_lower in c.date
        ]

    def cancelar_cita(self, codigo_cita: str) -> dict:
        """Cancela una cita existente por su codigo."""
        citas = self._load_appointments()
        encontrada = False
        for c in citas:
            if c.id.upper() == codigo_cita.strip().upper():
                c.status = "CANCELADA"
                encontrada = True
                break

        if encontrada:
            self._save_appointments(citas)
            return {"exito": True, "mensaje": f"La cita {codigo_cita} ha sido cancelada correctamente."}
        return {"exito": False, "mensaje": f"No se encontró ninguna cita con el código {codigo_cita}."}
