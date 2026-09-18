from __future__ import annotations

"""Arquitectura descentralizada basada en handoffs del SDK de Agents.

No existe un supervisor que sintetice las respuestas: el agente que recibe el
handoff se vuelve responsable de atender al cliente y puede transferir la
conversación directamente a otro especialista cuando el tema cambie.
"""

from agents import Agent, Runner, handoff
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


def build_decentralized_system() -> Agent:
    """Crea una red de agentes pares que se transfieren trabajo con handoffs."""
    model = get_configured_model()

    faq_agent = Agent(
        name="AgenteInformacion",
        handoff_description="Atiende preguntas de precios, evento, ubicacion, requisitos y politicas.",
        instructions=(
            "Eres el agente independiente de informacion de Parachute S.A. "
            "Responde en espanol las preguntas de evento, precios, ubicacion, parqueo, "
            "requisitos y politicas usando exclusivamente `consultar_faqs_paracaidismo`. "
            "Si el cliente cambia a clima o reservas, transfiere el caso al especialista adecuado."
        ),
        model=model,
        tools=[consultar_faqs_paracaidismo],
    )

    weather_agent = Agent(
        name="AgenteClima",
        handoff_description="Evalua el clima y la seguridad de salto para una fecha.",
        instructions=(
            "Eres el agente independiente de meteorologia y seguridad de Parachute S.A. "
            "Consulta `consultar_clima_paracaidismo` para toda pregunta de clima o viabilidad de salto. "
            "Explica viento, rafagas, lluvia, nubes y el dictamen IDEAL, MARGINAL o PROHIBIDO. "
            "Si el cliente desea reservar, transfiere la conversacion al agente de reservas; "
            "si pide datos generales, transfiere al agente de informacion."
        ),
        model=model,
        tools=[consultar_clima_paracaidismo],
    )

    booking_agent = Agent(
        name="AgenteReservas",
        handoff_description="Agenda, consulta o cancela citas de salto.",
        instructions=(
            "Eres el agente independiente de reservas de Parachute S.A. "
            "Gestiona citas con `agendar_cita_salto`, `listar_citas_registradas` y `cancelar_cita_salto`. "
            "Para agendar solicita nombre y fecha si faltan; la herramienta valida el clima antes de confirmar. "
            "Si el cliente solo requiere analizar el clima, transfiere al agente de clima. "
            "Si necesita precios, requisitos o politicas, transfiere al agente de informacion."
        ),
        model=model,
        tools=[agendar_cita_salto, listar_citas_registradas, cancelar_cita_salto],
    )

    # Cada especialista puede delegar directamente en los demas: no hay manager.
    faq_agent.handoffs = [
        handoff(weather_agent, tool_name_override="transferir_a_agente_clima"),
        handoff(booking_agent, tool_name_override="transferir_a_agente_reservas"),
    ]
    weather_agent.handoffs = [
        handoff(faq_agent, tool_name_override="transferir_a_agente_informacion"),
        handoff(booking_agent, tool_name_override="transferir_a_agente_reservas"),
    ]
    booking_agent.handoffs = [
        handoff(faq_agent, tool_name_override="transferir_a_agente_informacion"),
        handoff(weather_agent, tool_name_override="transferir_a_agente_clima"),
    ]

    # Punto de entrada sin herramientas ni autoridad de supervisor: solo enruta el
    # primer mensaje al agente par que debe resolverlo.
    reception_agent = Agent(
        name="AgenteRecepcion",
        instructions=(
            "Eres la recepcion de Parachute S.A. No resuelvas solicitudes: transfiere de inmediato "
            "al AgenteInformacion para dudas generales, al AgenteClima para clima y seguridad, o al "
            "AgenteReservas para agendar, listar o cancelar citas."
        ),
        model=model,
        handoffs=[
            handoff(faq_agent, tool_name_override="transferir_a_agente_informacion"),
            handoff(weather_agent, tool_name_override="transferir_a_agente_clima"),
            handoff(booking_agent, tool_name_override="transferir_a_agente_reservas"),
        ],
    )
    return reception_agent


def run_interactive_session() -> None:
    """Ejecuta una sesion interactiva de la red descentralizada."""
    console = Console()
    reception = build_decentralized_system()
    console.print(
        Panel.fit(
            "[bold cyan]PARACHUTE S.A. - SISTEMA MULTIAGENTE DESCENTRALIZADO[/bold cyan]\n"
            "[yellow]Patron:[/yellow] Agentes pares que se delegan casos mediante handoffs\n"
            "[green]Agentes:[/green] Informacion, Clima y Reservas\n"
            "[dim]Escribe tu consulta. Para finalizar escribe 'bye', 'salir' o presiona Ctrl-C.[/dim]",
            border_style="yellow",
            title="Arquitectura 2: Descentralizada",
        )
    )

    history = []
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]Cliente[/bold cyan]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("bye", "salir", "exit", "adios"):
                console.print("[bold green]Parachute S.A.:[/bold green] Gracias por comunicarse. ¡Hasta pronto!")
                break

            console.print("[dim]Delegando el caso entre agentes pares...[/dim]")
            if not history:
                result = Runner.run_sync(reception, user_input)
            else:
                history.append({"role": "user", "content": user_input})
                result = Runner.run_sync(reception, history)
            history = result.to_input_list()
            active_agent = getattr(getattr(result, "last_agent", None), "name", "Agente")
            console.print(f"\n[bold green]{active_agent}:[/bold green]\n{result.final_output}")
        except KeyboardInterrupt:
            console.print("\n[bold green]Parachute S.A.:[/bold green] Sesion terminada. ¡Hasta luego!")
            break
        except Exception as error:
            console.print(f"\n[bold red]Error en la sesion:[/bold red] {error}")


if __name__ == "__main__":
    run_interactive_session()
