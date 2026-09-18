# HDT-5 — Parachute S.A.

Sistema de atención para una empresa de paracaidismo que responde FAQs, consulta el clima de la zona de salto y gestiona citas. El proyecto compara tres patrones multiagente del SDK de OpenAI Agents.

## Requisitos e instalación

Se requiere Python 3.10 o superior y una API key válida de NVIDIA NIM, Groq u OpenAI.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y configura una sola combinación de proveedor, URL y modelo. Nunca se debe subir ese archivo al repositorio.

## Ejecución

Desde la raíz del proyecto, ejecuta una de las tres arquitecturas:

```powershell
python -m src.architectures.centralized
python -m src.architectures.decentralized
python -m src.architectures.hierarchical
```

Escribe `salir`, `bye` o usa `Ctrl+C` para cerrar la sesión.

## Arquitecturas evaluadas

| Patrón | Archivo | Organización |
|---|---|---|
| Centralizado | `src/architectures/centralized.py` | Un Supervisor Central coordina especialistas de clima, agenda y FAQs como `as_tool()`. |
| Descentralizado | `src/architectures/decentralized.py` | Agentes pares de información, clima y reservas transfieren conversaciones mediante `handoffs`. |
| Jerárquico | `src/architectures/hierarchical.py` | Director General → dos gerencias → cuatro especialistas operativos. |

Los diagramas de organización y flujo están en [docs/diagramas_arquitecturas.md](docs/diagramas_arquitecturas.md).

## Casos de demostración

Ejecuta cada arquitectura y prueba, como mínimo, estas preguntas:

```text
¿Cuánto cuesta el salto con video?
¿Es seguro saltar mañana?
Agenda una cita para Ana Pérez mañana a las 10:00 AM.
```

Para mostrar una transferencia descentralizada, inicia con una pregunta de clima y luego pide reservar: `¿Es seguro saltar mañana? Quiero agendar para Ana Pérez.` El agente de clima puede entregar el caso al agente de reservas mediante un handoff.

## Pruebas locales

Las pruebas unitarias no hacen llamadas a la API ni consumen créditos:

```powershell
python -m pytest -q
```

Cubren las reglas de seguridad meteorológica, el límite de 16 días y la recuperación de información de FAQs.
