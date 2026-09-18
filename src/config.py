from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled, set_default_openai_client

# Configurar salida en UTF-8 para Windows
if sys.platform.startswith("win"):
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Desactivar telemetria externa para evitar fallos de conexion con proveedores externos
set_tracing_disabled(True)

DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def resolve_api_key() -> str:
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("NVIDIA_API_KEY")
    )
    misplaced = os.getenv("OPENAI_BASE_URL", "").strip()

    # Si por error se coloco la API key de NVIDIA en OPENAI_BASE_URL
    if (not api_key or api_key == "nvapi-") and misplaced.startswith("nvapi-") and len(misplaced) >= 20:
        return misplaced

    if not api_key or api_key.startswith("tu_api_key") or (api_key.startswith("nvapi-") and len(api_key) < 20):
        raise RuntimeError(
            "Falta una API key valida. Configura NVIDIA_API_KEY, GROQ_API_KEY u OPENAI_API_KEY en tu archivo .env"
        )
    return api_key


def resolve_base_url() -> str | None:
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        if base_url.startswith("nvapi-"):
            return "https://integrate.api.nvidia.com/v1"
        if base_url.startswith(("http://", "https://")):
            return base_url
    if os.getenv("GROQ_API_KEY"):
        return "https://api.groq.com/openai/v1"
    if os.getenv("NVIDIA_API_KEY"):
        return "https://integrate.api.nvidia.com/v1"
    return None


def resolve_model_name() -> str:
    if os.getenv("MODEL"):
        return os.getenv("MODEL").strip()
    if os.getenv("NVIDIA_API_KEY"):
        return DEFAULT_NVIDIA_MODEL
    if os.getenv("GROQ_API_KEY"):
        return DEFAULT_GROQ_MODEL
    return DEFAULT_OPENAI_MODEL


def get_async_client() -> AsyncOpenAI:
    api_key = resolve_api_key()
    base_url = resolve_base_url()
    if base_url:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    return AsyncOpenAI(api_key=api_key)


def get_configured_model() -> OpenAIChatCompletionsModel:
    client = get_async_client()
    set_default_openai_client(client)
    model_name = resolve_model_name()
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
