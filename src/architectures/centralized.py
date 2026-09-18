from __future__ import annotations

import sys
from agents import Agent, Runner
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.config import get_configured_model
from src.tools.agent_tools import (
    agendar_cita_salto,
    cancelar_cita_salto,
    consultar_clima_paracaidismo,
    consultar_faqs_paracaidismo,
    listar_citas_registradas,
)


def build_centralized_system() -> Agent:
    """Construye la arquitectura multiagente centralizada con un supervisor
    y especialistas encapsulados mediante .as_tool().
    """
    model = get_configured_model()

    # 1. Especialista Meteorológico
    weather_specialist = Agent(
        name="EspecialistaClima",
        instructions=(
            "Eres el especialista meteorológico y de seguridad aeronáutica de Parachute S.A. "
            "Tu única tarea es consultar y analizar el clima en la zona de aterrizaje "
            "(coordenadas 14.013722, -90.771611) utilizando tu herramienta `consultar_clima_paracaidismo`. "
            "Explica con claridad las métricas obtenidas (viento, ráfagas, lluvia, cobertura de nubes) "
            "y dictamina si el salto es IDEAL, MARGINAL (solo tándem experimentado) o PROHIBIDO."
        ),
        model=model,
        tools=[consultar_clima_paracaidismo],
    )

    # 2. Especialista en Agenda y Reservaciones
    booking_specialist = Agent(
        name="EspecialistaAgenda",
        instructions=(
            "Eres el especialista en reservaciones y gestión de citas de Parachute S.A. "
            "Tu tarea es gestionar el calendario: agendar nuevas citas (siempre validando el clima antes), "
            "consultar citas registradas o cancelar citas solicitadas. "
            "Usa tus herramientas para realizar las acciones en el calendario y reporta el resultado."
        ),
        model=model,
        tools=[agendar_cita_salto, listar_citas_registradas, cancelar_cita_salto],
    )

    # 3. Especialista en Atención al Cliente y FAQs
    faq_specialist = Agent(
        name="EspecialistaFAQs",
        instructions=(
            "Eres el especialista en atención al cliente y preguntas frecuentes de Parachute S.A. "
            "Tu tarea es responder preguntas sobre el evento Guatemala 2026, precios, ubicación, "
            "parqueo, restricciones de edad/peso y políticas corporativas. "
            "Utiliza tu herramienta `consultar_faqs_paracaidismo` como única fuente de verdad. "
            "Si la información no existe en las FAQs, indica amablemente que escriban a soporte@parachutesa.gt."
        ),
        model=model,
        tools=[consultar_faqs_paracaidismo],
    )

    # Convertir a los 3 especialistas en herramientas para el Supervisor Central
    weather_tool = weather_specialist.as_tool(
        tool_name="consultar_especialista_clima",
        tool_description="Consulta al especialista meteorológico para verificar el pronóstico y la viabilidad de salto en una fecha.",
    )

    booking_tool = booking_specialist.as_tool(
        tool_name="consultar_especialista_agenda",
        tool_description="Consulta al especialista de agenda para programar citas de salto, revisar citas agendadas o cancelarlas.",
    )

    faq_tool = faq_specialist.as_tool(
        tool_name="consultar_especialista_faqs",
        tool_description="Consulta al especialista en preguntas frecuentes sobre precios, ubicación, requisitos físicos y evento.",
    )

    # Supervisor Orquestador Central
    supervisor = Agent(
        name="SupervisorCentral",
        instructions=(
            "Eres el Supervisor y Orquestador Central de Parachute S.A. "
            "Eres el único agente que interactúa directamente con el cliente. "
            "Tu función es interpretar las solicitudes del usuario y coordinar las respuestas "
            "delegando a los agentes especialistas según corresponda:\n"
            "1. Para preguntas generales, costos, requisitos o políticas del evento: delega en `consultar_especialista_faqs`.\n"
            "2. Para dudas sobre el estado del tiempo o seguridad de salto: delega en `consultar_especialista_clima`.\n"
            "3. Para agendar una cita, listar o cancelar citas: delega en `consultar_especialista_agenda`.\n"
            "IMPORTANTE: Si el cliente pide agendar pero no proporciona nombre o fecha, solicítaselos amablemente. "
            "Recuerda que las predicciones meteorológicas solo cubren hasta 16 días a partir de hoy. "
            "Sintetiza la respuesta devuelta por el especialista y entrégala con calidez, profesionalismo y formato claro en español."
        ),
        model=model,
        tools=[weather_tool, booking_tool, faq_tool],
    )

    return supervisor


def run_interactive_session() -> None:
    """Ejecuta una sesion interactiva en consola de la arquitectura centralizada."""
    console = Console()
    supervisor = build_centralized_system()

    console.print(
        Panel.fit(
            "[bold cyan]PARACHUTE S.A. - SISTEMA MULTIAGENTE CENTRALIZADO[/bold cyan]\n"
            "[yellow]Patrón:[/yellow] Supervisor Central / Manager Orquestador con especialistas como herramientas (`as_tool()`)\n"
            "[green]Capacidades:[/green] FAQs, Consulta de Clima en Zona de Salto (Open-Meteo) y Agendamiento de Citas\n"
            "[dim]Escribe tu consulta. Para finalizar escribe 'bye', 'salir' o presiona Ctrl-C.[/dim]",
            border_style="cyan",
            title="🪂 Arquitectura 1: Centralizada",
        )
    )

    history = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]Cliente[/bold cyan]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("bye", "salir", "exit", "adios"):
                console.print("[bold green]Supervisor:[/bold green] ¡Gracias por comunicarte con Parachute S.A.! Cielos despejados y hasta pronto. 🪂")
                break

            console.print("[dim]Delegando tarea a especialistas...[/dim]")

            if not history:
                result = Runner.run_sync(supervisor, user_input)
            else:
                history.append({"role": "user", "content": user_input})
                result = Runner.run_sync(supervisor, history)

            history = result.to_input_list()
            console.print(f"\n[bold green]Supervisor Central:[/bold green]\n{result.final_output}")

        except KeyboardInterrupt:
            console.print("\n[bold green]Supervisor:[/bold green] Sesión terminada. ¡Hasta luego!")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error en la sesión:[/bold red] {e}")


if __name__ == "__main__":
    run_interactive_session()
