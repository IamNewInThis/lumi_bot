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
    sleep_location: str | list[str] | None = Field(
        None,
        description="Lugar donde el bebé duerme (ej: cuna, cama con los padres, moisés)."
    )
    sleep_room: str | list[str] | None = Field(
        None,
        description="Habitación donde duerme (propia, de los padres, etc.)."
    )
    bedtime_start: str | None = Field(
        None,
        description="Hora aproximada en la que se acuesta."
    )
    bedtime_caregiver: str | list[str] | None = Field(
        None,
        description="Quién acompaña al bebé en la rutina de sueño."
    )
    sleep_association: str | list[str] | None = Field(
        None,
        description="Asociaciones de sueño (ej: pecho, brazos, chupete)."
    )
    sleep_light: str | None = Field(
        None,
        description="Condiciones de luz al dormir."
    )
    sleep_sound: str | None = Field(
        None,
        description="Condiciones de sonido al dormir."
    )
    sleep_pajama: str | list[str] | None = Field(
        None,
        description="Vestimenta o capas con las que duerme."
    )
    nap_count: str | None = Field(
        None,
        description="Cantidad de siestas diarias."
    )
    bedtime_hour: str | None = Field(
        None,
        description="Horario típico de inicio de la noche."
    )
    night_wakings: str | None = Field(
        None,
        description="Número aproximado de despertares durante la noche."
    )
    night_soothing: str | list[str] | None = Field(
        None,
        description="Cómo se reconforta al bebé durante los despertares nocturnos."
    )
    night_caregiver: str | list[str] | None = Field(
        None,
        description="Quién atiende los despertares nocturnos."
    )
    wakeup_hour: str | None = Field(
        None,
        description="Horario típico de despertar matutino."
    )
    night_feeding: str | None = Field(
        None,
        description="Frecuencia o existencia de tomas nocturnas."
    )
    night_feeding_purpose: str | list[str] | None = Field(
        None,
        description="Propósito de las tomas nocturnas."
    )
    night_feeding_type: str | list[str] | None = Field(
        None,
        description="Tipo de alimentación nocturna."
    )
    sleep_tired_signs: str | list[str] | None = Field(
        None,
        description="Señales típicas de cansancio."
    )

    # Seccion de cuidados diarios
    bath_frequency: Optional[str] = Field(None, description="Frecuencia del baño del bebé (ej: diario, cada dos días, semanal).")
    skin_care: Optional[str] = Field(
        None,
        description="Rutina de cuidado de la piel (sin productos, hidratación diaria, etc.)."
    )
    comfort_object: Optional[list[str]] = Field(
        default=None,
        description="Lista de objetos de confort preferidos (blankie, pacifier, stuffed_animal, etc.)."
    )
    family_members: Optional[list[str]] = Field(
        default=None,
        description="Miembros de la familia que conviven o cuidan (mother, father, siblings, grandparents, caregiver, pets)."
    )
    go_to_daycare: Optional[str] = Field(
        default=None,
        description="Asistencia a guardería/colegio (no, daycare, preschool, school)."
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
    """True si alguna palabra clave (normalizada) aparece en el texto normalizado."""
    return any(normalize_text(keyword) in text for keyword in keywords)
