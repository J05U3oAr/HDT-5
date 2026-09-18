# Diagramas de arquitecturas multiagente

## 1. Arquitectura centralizada

Un único supervisor interpreta cada solicitud y llama a los especialistas como herramientas. Los especialistas no se comunican entre sí ni con el cliente.

```mermaid
flowchart TD
    U[Cliente] --> S[Supervisor Central]
    S -->|as_tool| C[Especialista de Clima]
    S -->|as_tool| R[Especialista de Agenda]
    S -->|as_tool| F[Especialista de FAQs]
    C --> S
    R --> S
    F --> S
    S --> U
```

## 2. Arquitectura descentralizada

La recepción solo dirige el primer mensaje. Después, los agentes pares son responsables de la conversación y pueden transferirla directamente mediante `handoffs`.

```mermaid
flowchart LR
    U[Cliente] --> E[Agente de Recepción]
    E -->|handoff| I[Agente de Información]
    E -->|handoff| C[Agente de Clima]
    E -->|handoff| R[Agente de Reservas]
    I <-->|handoffs| C
    I <-->|handoffs| R
    C <-->|handoffs| R
    I --> U
    C --> U
    R --> U
```

## 3. Arquitectura jerárquica

El Director General delega en dos gerencias; cada gerencia utiliza a sus especialistas operativos como herramientas.

```mermaid
flowchart TD
    U[Cliente] --> D[Director General]
    D -->|as_tool| O[Gerencia de Operaciones]
    D -->|as_tool| A[Gerencia de Atención al Cliente]
    O -->|as_tool| C[Técnico Meteorólogo]
    O -->|as_tool| R[Despachador de Agenda]
    A -->|as_tool| I[Agente Info. Eventos]
    A -->|as_tool| P[Agente de Normativa]
    C --> O
    R --> O
    I --> A
    P --> A
    O --> D
    A --> D
    D --> U
```
