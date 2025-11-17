# src/extractors/template_extractor/template_selector.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..profile_extractor.base import get_llm, normalize_text
from ...utils.keywords_rag import TEMPLATE_KEYWORDS, TEMPLATE_FILES

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "prompts" / "templates"


class TemplateClassifierResponse(BaseModel):
    """Salida estructurada del clasificador LLM."""

    template_key: Optional[str] = Field(
        default=None,
        description="Clave del template más útil o null si no aplica.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Breve explicación de por qué se eligió el template.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Nivel de certeza general del clasificador.",
    )


class TemplateSelection(TemplateClassifierResponse):
    """Representa la decisión final del extractor."""

    source: str = Field(
        default="heuristic",
        description="Origen de la decisión (llm o heuristic).",
    )
    trigger_language: Optional[str] = None
    trigger_keyword: Optional[str] = None
    template_filename: Optional[str] = None
    template_title: Optional[str] = None
    template_content: Optional[str] = None

    @property
    def has_template(self) -> bool:
        return bool(self.template_content)


TEMPLATE_PROMPT = """
Eres Lumi, asistente experto en crianza multilingüe.
Tu tarea es decidir si debes adjuntar un template específico antes de responder.

Templates disponibles:
- routine_template: cuando piden organizar / ajustar rutinas diarias (sueño, alimentación, juego, etc.).
- creative_food_template: cuando solicitan ideas creativas o presentaciones divertidas para comidas.
- travel_template: cuando hablan de viajes, vacaciones, traslados o qué llevar.
- weaning_template: cuando consultan sobre destete o transición de la lactancia.
- references_template: cuando preguntan por fuentes, bibliografía o fundamentación.
- food_rejection: cuando consultan sobre rechazo alimentario o dificultades para alimentar.

Responde siguiendo este esquema JSON:
{{
  "template_key": "routine_template | creative_food_template | travel_template | weaning_template | references_template | food_rejection | null",
  "reason": "explicación breve (máx 25 palabras)",
  "confidence": 0.0-1.0
}}

Usa null cuando ningún template aporte valor claro.

Mensaje del usuario:
{message}
"""


def _load_template_file(template_key: str) -> tuple[Optional[str], Optional[str]]:
    filename = TEMPLATE_FILES.get(template_key)
    if not filename:
        print(f"⚠️ [TEMPLATE_EXTRACTOR] No hay archivo asociado a {template_key}")
        return None, None

    template_path = TEMPLATES_DIR / filename
    if not template_path.exists():
        print(f"⚠️ [TEMPLATE_EXTRACTOR] Archivo no encontrado: {template_path}")
        return filename, None

    try:
        content = template_path.read_text(encoding="utf-8").strip()
        return filename, content
    except Exception as exc:
        print(f"❌ [TEMPLATE_EXTRACTOR] Error leyendo {template_path}: {exc}")
        return filename, None


def _run_llm_classifier(message: str) -> Optional[TemplateSelection]:
    chain = get_llm(TemplateClassifierResponse, TEMPLATE_PROMPT)
    if not chain:
        print("⚠️ [TEMPLATE_EXTRACTOR] Sin cadena LLM, se usará heurística.")
        return None

    try:
        print("🧠 [TEMPLATE_EXTRACTOR] Ejecutando clasificador LLM de templates…")
        response: TemplateClassifierResponse = chain.invoke({"message": message})
        print(
            f"🧠 [TEMPLATE_EXTRACTOR] LLM respondió: "
            f"template_key={response.template_key}, confidence={response.confidence}"
        )
    except Exception as exc:
        print(f"❌ [TEMPLATE_EXTRACTOR] Error LLM clasificando template: {exc}")
        return None

    if response.template_key and response.template_key not in TEMPLATE_FILES:
        print(f"⚠️ [TEMPLATE_EXTRACTOR] LLM devolvió template desconocido: {response.template_key}")
        response.template_key = None

    return TemplateSelection(**response.dict(), source="llm")


def _heuristic_detection(message: str) -> Optional[TemplateSelection]:
    normalized = normalize_text(message)

    print("🔍 [TEMPLATE_EXTRACTOR] Buscando coincidencias heurísticas…")
    for template_key, keywords_by_lang in TEMPLATE_KEYWORDS.items():
        for lang, keywords in keywords_by_lang.items():
            for keyword in keywords:
                normalized_keyword = normalize_text(keyword)
                if normalized_keyword in normalized:
                    print(
                        f"✅ [TEMPLATE_EXTRACTOR] Heurística activa template "
                        f"{template_key} por '{keyword}' ({lang})."
                    )
                    return TemplateSelection(
                        template_key=template_key,
                        confidence=0.72,
                        reason=f"Coincidencia con '{keyword}' ({lang})",
                        source="heuristic",
                        trigger_language=lang,
                        trigger_keyword=keyword,
                    )
    return None


def _humanize_template_key(template_key: str) -> str:
    return (
        template_key.replace("_template", "")
        .replace("_", " ")
        .strip()
        .title()
    )


def select_template(message: str) -> TemplateSelection:
    """
    Determina qué template aplicar combinando LLM + heurísticas.
    Siempre retorna un TemplateSelection (aunque no haya template).
    """
    print("🚦 [TEMPLATE_EXTRACTOR] Iniciando selección de template…")
    selection = _run_llm_classifier(message)

    if not selection or not selection.template_key:
        # fallback = _heuristic_detection(message)
        # 🔧 Temporalmente deshabilitado para evaluar desempeño 100% LLM.
        fallback = None
        if fallback:
            selection = fallback
        else:
            print("ℹ️ [TEMPLATE_EXTRACTOR] Ninguna heurística coincidió (fallback OFF).")
        if not selection:
            selection = TemplateSelection(
                template_key=None,
                confidence=0.0,
                reason="Sin coincidencias claras",
                source="none",
            )

    if selection.template_key:
        print(f"📄 [TEMPLATE_EXTRACTOR] Cargando archivo para {selection.template_key}…")
        filename, content = _load_template_file(selection.template_key)
        selection.template_filename = filename
        selection.template_content = content
        selection.template_title = _humanize_template_key(selection.template_key)
        if content:
            print(
                f"📄 [TEMPLATE_EXTRACTOR] Template {selection.template_key} listo "
                f"(archivo: {filename})."
            )
        else:
            print(
                f"⚠️ [TEMPLATE_EXTRACTOR] No se pudo leer contenido de {filename}."
            )
    else:
        print("🚫 [TEMPLATE_EXTRACTOR] No se seleccionó template.")

    return selection


def build_template_block(message: str) -> tuple[str, TemplateSelection]:
    """
    Retorna el bloque de markdown para el prompt y la selección detallada.
    """
    selection = select_template(message)
    if not selection.has_template:
        return "", selection

    heading = selection.template_title.upper() if selection.template_title else selection.template_key.upper()
    block = f"\n\n## TEMPLATE ESPECÍFICO - {heading}\n{selection.template_content}"
    return block, selection


__all__ = ["TemplateSelection", "select_template", "build_template_block"]
