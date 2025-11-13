# src/extractors/profile_extractor/sleep_and_rest.py
from pydantic import Field
from .base import BaseProfileModel, get_llm, normalize_text, keyword_match


class SleepAndRestProfile(BaseProfileModel):
    sleep_location: str | None = Field(None, description="Lugar donde el bebé duerme habitualmente (ej: cuna, cama compartida, moisés)")
    sleep_room: str | None = Field(None, description="Habitación donde duerme el bebé (ej: propia habitación, habitación de los padres, habitación compartida)")


SLEEP_PROMPT = """
You are an expert in early childhood sleep patterns and multilingual (Spanish, English, Portuguese).

Analyze the text and extract information about **where** the baby sleeps (object/location) and **in which room** they sleep (environment).

Rules:
- Only fill a field if the message explicitly references that type of detail.
- If the message only mentions the room (e.g., “duerme en nuestra habitación”), set sleep_location = null.
- If it only mentions the sleep object (crib, bed, bassinet, mattress), set sleep_room = null.
- Do not invent values. When unsure, leave the field as null.

Schema fields:
- sleep_location: crib, bassinet, shared_bed, floor_mattress, low_bed, regular_bed, etc.
- sleep_room: own_room, parents_room, shared_room, family_bedroom_co_sleeping, etc.
Also include a 'confidence' score from 0 to 1.

Examples:
1. "Duerme en nuestra habitación." → sleep_room = parents_room, sleep_location = null
2. "Tiene su propia cuna." → sleep_location = crib, sleep_room = null
3. "Comparte habitación con su hermano." → sleep_room = shared_room, sleep_location = null
4. "Tiene una cama baja en su propio cuarto." → sleep_location = low_bed (o regular_bed), sleep_room = own_room

Text:
{message}
"""


SLEEP_LOCATION_RULES = [
    {
        "value": "crib",
        "confidence": 0.95,
        "any": ["cuna", "crib", "berco"],
    },
    {
        "value": "bassinet",
        "confidence": 0.9,
        "any": ["moises", "bassinet", "moisés"],
    },
    {
        "value": "shared_bed",
        "confidence": 0.9,
        "any": ["cama compartida", "shared bed", "cama con los padres", "co-sleeping"],
    },
    {
        "value": "floor_mattress",
        "confidence": 0.85,
        "any": ["colchon en el suelo", "floor mattress"],
    },
    {
        "value": "low_bed",
        "confidence": 0.88,
        "any": ["cama baja", "low bed"],
    },
    {
        "value": "regular_bed",
        "confidence": 0.8,
        "any": ["cama", "bed", "cama"],
    },
]

SLEEP_ROOM_RULES = [
    {
        "value": "own_room",
        "confidence": 0.95,
        "all": [
            ["habitacion", "cuarto", "pieza", "room"],
            ["propio", "propia", "own"],
        ],
    },
    {
        "value": "own_room",
        "confidence": 0.9,
        "any": [
            "su cuarto",
            "su habitacion",
            "su habitación",
            "seu quarto",
            "seu quarto",
            "her own room",
            "his own room",
            "their own room",
        ],
    },
    {
        "value": "parents_room",
        "confidence": 0.9,
        "all": [
            ["habitacion", "cuarto", "pieza", "room"],
            ["padres", "nosotros", "parents"],
        ],
    },
    {
        "value": "shared_room",
        "confidence": 0.85,
        "all": [
            ["habitacion", "cuarto", "pieza", "room"],
            ["hermano", "hermana", "sibling"],
        ],
    },
    {
        "value": "parents_room",
        "confidence": 0.88,
        "any": [
            "duerme con nosotros",
            "duerme con nosotras",
            "duerme con mama",
            "duerme con mamá",
            "duerme con papa",
            "duerme conmigo",
            "dormimos juntos",
            "sleep with us",
            "sleeps with us",
            "in our bed",
            "in our bedroom",
            "in our room",
            "nuestra cama",
            "nuestra habitacion",
            "nuestro cuarto",
            "nuestro dormitorio",
            "no nosso quarto",
            "nosso quarto",
            "nosso dormitorio",
            "nossa cama",
            "dorme conosco",
            "dorme com a gente",
        ],
    },
]


def _matches_rule(text: str, rule: dict) -> bool:
    def contains_any(options: list[str]) -> bool:
        return any(keyword_match(text, [option]) for option in options)

    any_clause = rule.get("any")
    all_clause = rule.get("all")

    any_ok = contains_any(any_clause) if any_clause else True
    all_ok = all(
        contains_any(options if isinstance(options, list) else [options])
        for options in (all_clause or [])
    )
    return any_ok and all_ok


def _infer_sleep_context(text: str) -> dict:
    """Devuelve coincidencias heurísticas para ubicación y habitación."""
    result: dict[str, dict] = {}

    for rule in SLEEP_LOCATION_RULES:
        if _matches_rule(text, rule):
            result["sleep_location"] = {"key": rule["value"], "confidence": rule["confidence"]}
            break

    for rule in SLEEP_ROOM_RULES:
        if _matches_rule(text, rule):
            result["sleep_room"] = {"key": rule["value"], "confidence": rule["confidence"]}
            break

    return result


def fallback_sleep_profile(message: str) -> SleepAndRestProfile:
    normalized = normalize_text(message)
    data = _infer_sleep_context(normalized)

    sleep_location = data.get("sleep_location", {}).get("key")
    sleep_room = data.get("sleep_room", {}).get("key")
    confidence = max(
        data.get("sleep_location", {}).get("confidence", 0),
        data.get("sleep_room", {}).get("confidence", 0),
        0.6,
    )

    return SleepAndRestProfile(
        sleep_location=sleep_location,
        sleep_room=sleep_room,
        confidence=confidence,
    )


def extract_sleep_and_rest(message: str) -> SleepAndRestProfile:
    chain = get_llm(SleepAndRestProfile, SLEEP_PROMPT)
    profile = None
    if chain:
        try:
            profile = chain.invoke({"message": message})
        except Exception as e:
            print(f"⚠️ [SLEEP_EXTRACTOR] Error con LLM ({e}). Usando heurística local.")
    if profile is None:
        profile = fallback_sleep_profile(message)
    return _sanitize_sleep_profile(message, profile)


LOCATION_HINTS = (
    "cuna",
    "crib",
    "berco",
    "berço",
    "moises",
    "moisés",
    "bassinet",
    "cama",
    "bed",
    "colchon",
    "colchón",
    "colchao",
    "colchão",
    "mattress",
    "colecho",
    "cosleep",
    "moises",
    "moisés",
)

ROOM_HINTS = (
    "habitacion",
    "habitación",
    "cuarto",
    "pieza",
    "dormitorio",
    "room",
    "bedroom",
    "quarto",
    "sala",
    "living",
    "comparte habitacion",
    "comparte habitación",
    "shared room",
    "shares a room",
    "con nosotros",
    "with us",
    "su cuarto",
    "su habitacion",
    "su habitación",
    "our room",
    "nuestra habitacion",
    "nuestra habitación",
    "nuestro cuarto",
    "nosso quarto",
    "nosso quarto",
    "nossa cama",
)


def _has_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _sanitize_sleep_profile(message: str, profile: SleepAndRestProfile) -> SleepAndRestProfile:
    normalized = normalize_text(message)
    if profile.sleep_location and not _has_any_keyword(normalized, LOCATION_HINTS):
        profile.sleep_location = None
    if profile.sleep_room and not _has_any_keyword(normalized, ROOM_HINTS):
        profile.sleep_room = None
    return profile
