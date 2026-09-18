from __future__ import annotations

from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FAQ_PATH = PROJECT_ROOT / "faqs" / "FAQs.txt"


class FaqService:
    def __init__(self, faq_file: Path = DEFAULT_FAQ_PATH):
        self.faq_file = faq_file
        self.faq_text = self._load_faq_text()
        self.faqs = self._parse_faqs()

    def _load_faq_text(self) -> str:
        if not self.faq_file.exists():
            return "No se encontró el archivo de FAQs."
        return self.faq_file.read_text(encoding="utf-8").strip()

    def _parse_faqs(self) -> List[Dict[str, str]]:
        items = []
        blocks = self.faq_text.split("Pregunta:")
        for b in blocks:
            if "Respuesta:" in b:
                parts = b.split("Respuesta:")
                q = parts[0].strip()
                a = parts[1].strip()
                items.append({"pregunta": q, "respuesta": a})
        return items

    def get_full_faq_context(self) -> str:
        return self.faq_text

    def buscar_faqs(self, consulta: str) -> str:
        """Busca preguntas y respuestas que coincidan con la consulta del usuario."""
        if not consulta or not consulta.strip():
            return self.faq_text

        consulta_tokens = set(consulta.lower().split())
        coincidencias = []

        for item in self.faqs:
            texto = f"{item['pregunta']} {item['respuesta']}".lower()
            puntos = sum(1 for token in consulta_tokens if token in texto and len(token) > 3)
            if puntos > 0:
                coincidencias.append((puntos, item))

        if not coincidencias:
            return (
                "Información oficial disponible en FAQs:\n\n"
                + self.faq_text
                + "\n\n(Nota: Si la consulta específica no está descrita en este texto, debe indicarse al cliente que contacte a soporte@parachutesa.gt)."
            )

        coincidencias.sort(key=lambda x: x[0], reverse=True)
        resultado = ["Resultados relevantes de FAQs Parachute S.A.:"]
        for _, item in coincidencias[:3]:
            resultado.append(f"• Pregunta: {item['pregunta']}\n  Respuesta: {item['respuesta']}\n")

        return "\n".join(resultado)
