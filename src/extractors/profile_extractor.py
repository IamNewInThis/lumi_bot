from __future__ import annotations
import os
import unicodedata
from functools import lru_cache
from typing import Iterable
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

# =========================================================
# 🧠 MODELO DE SALIDA
# =========================================================
class BabyProfile(BaseModel):
    sleep_location: str | None = Field(
        None,
        description="Lugar donde el bebé duerme (ej: cuna, cama con los padres, moisés)",
    )
    confidence: float | None = Field(
        None,
        description="Nivel de confianza general del modelo (0–1) según lo claro del texto",
    )


# =========================================================
# 📄 PROMPT DEL LLM
# =========================================================
PROFILE_EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert in child development and multilingual.
Extract the baby profile information mentioned or implied in this text.
You can understand and respond to Spanish, English, and Portuguese.

If a field is not clearly mentioned, return null.

Schema fields:
- sleep_location
Also include a 'confidence' score from 0 to 1 indicating how sure you are overall.

Text:
{message}
""")


# =========================================================
# ⚙️ CONFIGURACIÓN DEL MODELO
# =========================================================
@lru_cache(maxsize=1)
def _get_llm_chain():
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    if not api_key:
        return None

    llm = ChatOpenAI(model=model, temperature=0, openai_api_key=api_key)
    return PROFILE_EXTRACTION_PROMPT | llm.with_structured_output(schema=BabyProfile)


# =========================================================
# 🔤 UTILIDADES DE TEXTO
# =========================================================
def _normalize_text(text: str) -> str:
    """Normaliza el texto a minúsculas y elimina tildes y caracteres especiales."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def _keyword_match(text: str, keywords: Iterable[str]) -> bool:
    """Retorna True si alguna palabra clave aparece en el texto normalizado."""
    return any(keyword in text for keyword in keywords)


# =========================================================
# 🧩 EXTRACTORES HEURÍSTICOS
# =========================================================
def _infer_sleep_location(text: str):
    sleep_patterns = [
        (
            ("cuna", "crib", "berco", "berço"),
            {
                "key": "crib",
                "value_es": "cuna",
                "value_en": "crib",
                "value_pt": "berço",
                "confidence": 0.95
            },
        ),
        (
            ("con nosotros", "with us", "co-sleep", "cosleep", "cama con", "dorme conosco"),
            {
                "key": "family_bed",
                "value_es": "cama compartida con los padres",
                "value_en": "family bed",
                "value_pt": "cama compartilhada com os pais",
                "confidence": 0.9
            },
        ),
        (
            ("su cama", "his bed", "her bed", "própria cama"),
            {
                "key": "own_bed",
                "value_es": "su propia cama",
                "value_en": "own bed",
                "value_pt": "própria cama",
                "confidence": 0.9
            },
        ),
        (
            ("moises", "moisés", "bassinet"),
            {
                "key": "bassinet",
                "value_es": "moisés",
                "value_en": "bassinet",
                "value_pt": "moisés",
                "confidence": 0.85
            },
        ),
        (
            ("en movimiento", "in motion", "car seat", "auto"),
            {
                "key": "in_motion",
                "value_es": "en movimiento",
                "value_en": "in motion",
                "value_pt": "em movimento",
                "confidence": 0.8
            },
        ),
    ]

    for keywords, data in sleep_patterns:
        if _keyword_match(text, keywords):
            return data

    return None



def _fallback_profile(message: str) -> BabyProfile:
    normalized = _normalize_text(message)
    data = _infer_sleep_location(normalized)

    if not data:
        return BabyProfile(
            sleep_location=None,
            confidence=0.6,
        )

    return BabyProfile(
        sleep_location=data["key"],
        confidence=data["confidence"],
    )


# =========================================================
# 🚀 FUNCIÓN PRINCIPAL
# =========================================================
def extract_profile_info(message: str) -> BabyProfile:
    """
    Extrae información del perfil del bebé usando LLM si hay API key.
    Si no, usa heurística local.
    """
    chain = _get_llm_chain()
    if chain:
        return chain.invoke({"message": message})
    return _fallback_profile(message)
