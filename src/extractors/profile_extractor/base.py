# src/extractors/profile_extractor/base.py
from __future__ import annotations
import os
import unicodedata
from functools import lru_cache
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

# =========================================================
# 🧠 BASE MODELS
# =========================================================
class BaseProfileModel(BaseModel):
    """Modelo base para todas las secciones del perfil."""
    confidence: Optional[float] = Field(
        None,
        description="Nivel de confianza general del modelo (0-1)."
    )


class BabyProfile(BaseProfileModel):
    """Modelo consolidado que se expone al frontend."""
    # Campos provenientes de la sección sleep_and_rest
    sleep_location: Optional[str] = Field(
        None,
        description="Lugar donde el bebé duerme (ej: cuna, cama con los padres, moisés)."
    )
    sleep_room: Optional[str] = Field(
        None,
        description="Habitación donde duerme (propia, de los padres, etc.)."
    )

# =========================================================
# ⚙️ LLM CONFIG
# =========================================================
@lru_cache(maxsize=1)
def get_llm(model_schema: BaseModel, prompt_template: str):
    """Crea y devuelve un chain LLM con salida estructurada según el schema."""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    if not api_key:
        return None

    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = ChatOpenAI(model=model, temperature=0, openai_api_key=api_key)
    return prompt | llm.with_structured_output(schema=model_schema)

# =========================================================
# 🔤 UTILIDADES COMUNES
# =========================================================
def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, sin tildes ni caracteres especiales."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def keyword_match(text: str, keywords: list[str]) -> bool:
    """True si alguna palabra clave aparece en el texto normalizado."""
    return any(keyword in text for keyword in keywords)
