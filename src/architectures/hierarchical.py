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


def build_hierarchical_system() -> Agent:
    """Construye la arquitectura jerarquica piramidal de 3 niveles:
    Nivel 1: Director General (Executive Director)
    Nivel 2: Gerencias de Area (Operaciones Aereas y Atencion al Cliente) con .as_tool()
    Nivel 3: Agentes Especialistas Operativos (Clima, Agenda, FAQs, Normativa) con .as_tool()
    """
    model = get_configured_model()

    # =========================================================================
    # NIVEL 3: Especialistas Operativos (Nivel de Campo)
    # =========================================================================

    # 3.1 Tecnico Meteorologo
    weather_worker = Agent(
        name="TecnicoMeteorologo",
        instructions=(
            "Eres el técnico meteorólogo oficial de Parachute S.A. en la zona de aterrizaje "
            "(coordenadas 14.013722, -90.771611). Tu trabajo es consultar la API de Open-Meteo "
            "con la herramienta `consultar_clima_paracaidismo` y proporcionar el diagnóstico "
            "técnico: velocidad de viento (<20 ideal, 20-28 marginal, >28 prohibido), ráfagas (>35 prohibido), "
            "lluvia (>0 prohibido) y visibilidad/nubes (>75 prohibido)."
        ),
        model=model,
        tools=[consultar_clima_paracaidismo],
    )

    # 3.2 Despachador de Agenda
    booking_worker = Agent(
        name="DespachadorAgenda",
        instructions=(
            "Eres el despachador de vuelos y calendario de Parachute S.A. "
            "Tu tarea es ejecutar las acciones en el calendario de saltos: "
            "agendar citas (previa validación de clima), consultar citas registradas o cancelar citas. "
            "Reporta el código de confirmación o el motivo de rechazo según corresponda."
        ),
        model=model,
        tools=[agendar_cita_salto, listar_citas_registradas, cancelar_cita_salto],
    )

    # 3.3 Agente de Información General y FAQs
    faq_worker = Agent(
        name="AgenteInfoEventos",
        instructions=(
            "Eres el agente informativo sobre el evento Parachute Guatemala 2026. "
            "Tu fuente de verdad es la herramienta `consultar_faqs_paracaidismo`. "
            "Responde preguntas sobre fecha, ubicación, costo de salto básico (Q1,800) y salto con video (Q2,400), "
            "y disponibilidad de parqueo."
        ),
        model=model,
        tools=[consultar_faqs_paracaidismo],
    )

    # 3.4 Agente de Políticas y Requisitos
    policy_worker = Agent(
        name="AgenteNormativaSeguridad",
        instructions=(
            "Eres el oficial de normativas y requisitos de seguridad de Parachute S.A. "
            "Consulta la herramienta `consultar_faqs_paracaidismo` para responder con exactitud "
            "sobre edad mínima (18 años, o 16 con autorización), peso máximo (105 kg / 230 lbs), "
            "transferencias de citas (48 horas de anticipación) y suspensiones por mal tiempo."
        ),
        model=model,
        tools=[consultar_faqs_paracaidismo],
    )

    # Envolver especialistas del Nivel 3 como herramientas para los gerentes del Nivel 2
    tool_weather_worker = weather_worker.as_tool(
        tool_name="solicitar_informe_meteorologico",
        tool_description="Solicita al técnico meteorólogo el análisis detallado del clima para una fecha de salto.",
    )

    tool_booking_worker = booking_worker.as_tool(
        tool_name="solicitar_despacho_cita",
        tool_description="Solicita al despachador de agenda programar, consultar o cancelar citas de salto.",
    )

    tool_faq_worker = faq_worker.as_tool(
        tool_name="consultar_info_evento_y_precios",
        tool_description="Consulta información sobre el evento 2026, costos y ubicación.",
    )

    tool_policy_worker = policy_worker.as_tool(
        tool_name="consultar_requisitos_y_politicas",
        tool_description="Consulta requisitos físicos, límites de peso, edad y políticas de transferencia o suspensión.",
    )

    # =========================================================================
    # NIVEL 2: Gerencias de Área (Mando Medio)
    # =========================================================================

    # 2.1 Gerencia de Operaciones Aéreas (supervisa clima y agenda)
    operations_manager = Agent(
        name="GerenciaOperaciones",
        instructions=(
            "Eres el Gerente de Operaciones Aéreas de Parachute S.A. "
            "Supervisas la seguridad aeronáutica y el despacho de saltos. "
            "Tienes a tu cargo a dos especialistas operativos:\n"
            "- Para verificar el estado del tiempo: usa `solicitar_informe_meteorologico`.\n"
            "- Para agendar, consultar o cancelar citas de salto: usa `solicitar_despacho_cita`.\n"
            "Tu responsabilidad es garantizar que ningún vuelo se programe si el clima es peligroso, "
            "y coordinar eficientemente las solicitudes operativas. Devuelve una respuesta consolidada "
            "y estructurada a la Dirección General."
        ),
        model=model,
        tools=[tool_weather_worker, tool_booking_worker],
    )

    # 2.2 Gerencia de Atención al Cliente (supervisa FAQs y políticas)
    support_manager = Agent(
        name="GerenciaAtencionCliente",
        instructions=(
            "Eres el Gerente de Atención al Cliente de Parachute S.A. "
            "Supervisas la comunicación oficial y la satisfacción de los visitantes. "
            "Tienes a tu cargo a dos especialistas:\n"
            "- Para información del evento, precios y parqueo: usa `consultar_info_evento_y_precios`.\n"
            "- Para requisitos de edad, peso y políticas de seguridad: usa `consultar_requisitos_y_politicas`.\n"
            "Garantiza respuestas cordiales, verídicas y apegadas estrictamente a los lineamientos oficiales."
        ),
        model=model,
        tools=[tool_faq_worker, tool_policy_worker],
    )

    # Envolver gerentes del Nivel 2 como herramientas para el Director General del Nivel 1
    tool_operations_manager = operations_manager.as_tool(
        tool_name="delego_gerencia_operaciones",
        tool_description="Delega en la Gerencia de Operaciones todo lo relacionado con clima de vuelo, seguridad y agendamiento de citas.",
    )

    tool_support_manager = support_manager.as_tool(
        tool_name="delego_gerencia_atencion_cliente",
        tool_description="Delega en la Gerencia de Atención al Cliente todo lo relacionado con dudas generales, costos, requisitos y políticas.",
    )

    # =========================================================================
    # NIVEL 1: Dirección General (Alta Dirección / Punto de Entrada)
    # =========================================================================
    executive_director = Agent(
        name="DirectorGeneral",
        instructions=(
            "Eres el Director General de Parachute S.A. Eres la máxima autoridad y el anfitrión principal "
            "frente al usuario. Tu misión es liderar la atención al cliente canalizando las solicitudes a través de "
            "tus dos gerencias departamentales:\n"
            "1. `delego_gerencia_operaciones`: Para asuntos técnicos de vuelo, clima en la zona de salto y agendamiento de citas.\n"
            "2. `delego_gerencia_atencion_cliente`: Para consultas sobre el evento, costos de saltos, requisitos físicos y políticas.\n"
            "Tu tono debe ser ejecutivo, cálido, confiable y profesional. Revisa los resultados devueltos por tus "
            "gerentes y preséntaselos al usuario con la máxima cortesía y claridad."
        ),
        model=model,
        tools=[tool_operations_manager, tool_support_manager],
    )

    return executive_director


def run_interactive_session() -> None:
    """Ejecuta una sesion interactiva en consola de la arquitectura jerarquica."""
    console = Console()
    director = build_hierarchical_system()

    console.print(
        Panel.fit(
            "[bold cyan]PARACHUTE S.A. - SISTEMA MULTIAGENTE JERÁRQUICO[/bold cyan]\n"
            "[yellow]Patrón:[/yellow] Jerarquía Piramidal de 3 Niveles (Director -> Gerencias -> Especialistas Operativos vía `as_tool()`)\n"
            "[green]Estructura:[/green] Nivel 1 (Director General) ➔ Nivel 2 (Gerencia Operaciones / Gerencia Atención) ➔ Nivel 3 (Técnicos y Despachadores)\n"
            "[dim]Escribe tu consulta. Para finalizar escribe 'bye', 'salir' o presiona Ctrl-C.[/dim]",
            border_style="magenta",
            title="👑 Arquitectura 2: Jerárquica",
        )
    )

    history = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]Cliente[/bold cyan]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("bye", "salir", "exit", "adios"):
                console.print("[bold green]Director General:[/bold green] Ha sido un honor atenderle en Parachute S.A. ¡Esperamos verle pronto en los cielos! 🪂")
                break

            console.print("[dim]Canalizando a través de la jerarquía ejecutiva y departamental...[/dim]")

            if not history:
                result = Runner.run_sync(director, user_input)
            else:
                history.append({"role": "user", "content": user_input})
                result = Runner.run_sync(director, history)

            history = result.to_input_list()
            console.print(f"\n[bold green]Director General (Parachute S.A.):[/bold green]\n{result.final_output}")

        except KeyboardInterrupt:
            console.print("\n[bold green]Director General:[/bold green] Sesión finalizada. ¡Hasta luego!")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error en la sesión jerárquica:[/bold red] {e}")


if __name__ == "__main__":
    run_interactive_session()
