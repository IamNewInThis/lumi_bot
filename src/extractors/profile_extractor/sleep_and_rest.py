# src/extractors/profile_extractor/sleep_and_rest.py
from pydantic import Field
from .base import BaseProfileModel, get_llm, normalize_text, keyword_match

# =========================================================
# 🧠 MODELO DE SALIDA
# =========================================================
class SleepAndRestProfile(BaseProfileModel):
    sleep_location: str | None = Field(None,description="Lugar donde el bebé o niño duerme habitualmente durante la noche. (ej: cuna, cama con los padres, moisés)")
    sleep_room: str | None = Field(None,description="Habitación donde duerme el bebé o niño (ej: propia habitación, habitación de los padres)")

# =========================================================
# 📄 PROMPT DEL LLM
# =========================================================
SLEEP_PROMPT = """
You are an expert in child development and multilingual.
Extract the baby sleep-related profile information mentioned or implied in this text.
You can understand and respond to Spanish, English, and Portuguese.

If a field is not clearly mentioned, return null.

Schema fields:
- sleep_location
- sleep_room
Also include a 'confidence' score from 0 to 1 indicating how sure you are overall.

Text:
{message}
"""

# =========================================================
# 🧩 EXTRACTORES HEURÍSTICOS
# =========================================================
def infer_sleep_location(text: str):
    sleep_patterns = [
        (("cuna", "crib", "berco", "berço"), {
            "key": "crib", "confidence": 0.95
        }),
        (("con nosotros", "with us", "co-sleep", "cosleep", "cama con", "dorme conosco"), {
            "key": "family_bed", "confidence": 0.9
        }),
        (("su cama", "his bed", "her bed", "própria cama"), {
            "key": "own_bed", "confidence": 0.9
        }),
        (("moises", "moisés", "bassinet"), {
            "key": "bassinet", "confidence": 0.85
        }),
        (("en movimiento", "in motion", "car seat", "auto"), {
            "key": "in_motion", "confidence": 0.8
        }),
    ]
    
    sleep_room_patterns = [
        (("habitación propia", "own room", "quarto próprio"), {
            "key": "own_room", "confidence": 0.95
        }),
        (("habitación de los padres", "parents' room", "quarto dos pais"), {
            "key": "parents_room", "confidence": 0.9
        }),
        (("salón", "living room", "sala de estar"), {
            "key": "living_room", "confidence": 0.8
        }),
    ]

    # Primero buscar ubicación de sueño
    for keywords, data in sleep_patterns:
        if keyword_match(text, keywords):
            return {"field": "sleep_location", **data}

    # Luego buscar habitación
    for keywords, data in sleep_room_patterns:
        if keyword_match(text, keywords):
            return {"field": "sleep_room", **data}

    return None

def fallback_sleep_profile(message: str) -> SleepAndRestProfile:
    normalized = normalize_text(message)
    data = infer_sleep_location(normalized)

    if not data:
        return SleepAndRestProfile(sleep_location=None, sleep_room=None, confidence=0.6)

    if data["field"] == "sleep_location":
        return SleepAndRestProfile(
            sleep_location=data["key"],
            confidence=data["confidence"]
        )
    elif data["field"] == "sleep_room":
        return SleepAndRestProfile(
            sleep_room=data["key"],
            confidence=data["confidence"]
        )

    return SleepAndRestProfile(confidence=0.6)

# =========================================================
# 🚀 FUNCIÓN PRINCIPAL
# =========================================================
def extract_sleep_and_rest(message: str) -> SleepAndRestProfile:
    chain = get_llm(SleepAndRestProfile, SLEEP_PROMPT)
    if chain:
        return chain.invoke({"message": message})
    return fallback_sleep_profile(message)
