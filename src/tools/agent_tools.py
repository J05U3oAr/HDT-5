from __future__ import annotations

from agents import function_tool
from src.core.weather_service import WeatherService, ForecastRangeError, WeatherServiceError
from src.core.calendar_service import CalendarService
from src.core.faq_service import FaqService

# Instancias compartidas singleton para mantener coherencia en todas las arquitecturas
weather_service = WeatherService()
calendar_service = CalendarService()
faq_service = FaqService()


@function_tool
def consultar_clima_paracaidismo(fecha: str) -> str:
    """Consulta el pronóstico meteorológico oficial de Open-Meteo en la zona de aterrizaje de Parachute S.A.
    (coordenadas 14.013722, -90.771611) para evaluar si es seguro realizar saltos en paracaídas.

    Args:
        fecha: Fecha a consultar en formato YYYY-MM-DD, o términos como 'hoy' o 'mañana'.
               Open-Meteo provee 16 fechas contando hoy: desde hoy hasta hoy + 15 días.
    """
    try:
        reporte = weather_service.get_weather_report(fecha)
        return reporte.format_summary()
    except ForecastRangeError as e:
        return f"ALERTA DE RANGO: {str(e)}"
    except (WeatherServiceError, ValueError) as e:
        return f"ERROR AL OBTENER CLIMA: {str(e)}"
    except Exception as e:
        return f"ERROR INESPERADO: {str(e)}"


@function_tool
def agendar_cita_salto(
    nombre_cliente: str,
    fecha: str,
    hora: str = "10:00 AM",
    tipo_salto: str = "Tándem",
) -> str:
    """Agenda una cita de salto en paracaídas para un cliente, verificando automáticamente
    las condiciones meteorológicas con Open-Meteo antes de confirmar la reserva.

    Args:
        nombre_cliente: Nombre completo del cliente que saltará.
        fecha: Fecha de la cita en formato YYYY-MM-DD, o 'hoy'/'mañana'
               (ventana de 16 fechas: hoy hasta hoy + 15 días).
        hora: Hora deseada para el salto (ejemplo: '09:00 AM', '11:30 AM').
        tipo_salto: Modalidad del salto (ej. 'Tándem', 'Tándem con Video HD', 'Tándem Experimentado').
    """
    resultado = calendar_service.agendar_cita(
        nombre_cliente=nombre_cliente,
        fecha=fecha,
        hora=hora,
        tipo_salto=tipo_salto,
    )
    return resultado["mensaje"]


@function_tool
def listar_citas_registradas(filtro: str = "") -> str:
    """Consulta las citas de paracaidismo agendadas en el sistema.

    Args:
        filtro: Opcional. Nombre del cliente, fecha o código de reserva para buscar.
    """
    citas = calendar_service.listar_citas(filtro if filtro.strip() else None)
    if not citas:
        return "No hay citas registradas que coincidan con la búsqueda."

    salida = [f"Total de citas encontradas: {len(citas)}"]
    for c in citas:
        salida.append(
            f"• [{c.status}] Código: `{c.id}` | Cliente: {c.client_name} | Fecha: {c.date} | "
            f"Hora: {c.time} | Tipo: {c.jump_type} | Clima: {c.weather_status}"
        )
    return "\n".join(salida)


@function_tool
def cancelar_cita_salto(codigo_cita: str) -> str:
    """Cancela una cita de paracaidismo registrada mediante su código.

    Args:
        codigo_cita: Código de la reserva (ejemplo: 'PAR-2603-A1B2C3').
    """
    res = calendar_service.cancelar_cita(codigo_cita)
    return res["mensaje"]


@function_tool
def consultar_faqs_paracaidismo(consulta: str) -> str:
    """Consulta la base de conocimientos oficial de FAQs de Parachute S.A.
    Contiene información sobre el evento 2026, costos de saltos, requisitos físicos,
    edad mínima, peso máximo, parqueo, ubicación y transferencias.

    Args:
        consulta: Pregunta o tema a consultar en la base de conocimientos.
    """
    return faq_service.buscar_faqs(consulta)
