from pydantic import Field
from .base import BaseProfileModel, get_llm, normalize_text


class EmotionsBondAndParentingProfile(BaseProfileModel):
    comfort_object: list[str] | None = Field(
        default=None,
        description="Lista de objetos de confort (blankie, cloth, stuffed_animal, doll, favorite_toy, caregiver_clothing, small_pillow, pacifier, transitioning, other)."
    )


EMOTIONS_PROMPT = """
You are a multilingual expert in respectful parenting.

Extract the baby's comfort objects explicitly mentioned in the text. A comfort object is anything the child uses for emotional regulation (blankie, stuffed animal, doll, caregiver clothing, pacifier, etc.).

Rules:
- Return an array `comfort_object` containing any matching categories:
  blankie, cloth, stuffed_animal, doll, favorite_toy, caregiver_clothing, small_pillow, pacifier, transitioning, other
- If multiple objects are mentioned, include all of them.
- If nothing related to comfort objects appears, return an empty list or null.
- Never invent items; rely only on the message.

Text:
{message}
"""

COMFORT_OBJECT_KEYWORDS = {
    "blankie": [
        "manta",
        "mantita",
        "blanket",
        "blankie",
        "security blanket",
    ],
    "cloth": [
        "pañuelo",
        "panuelito",
        "trapito",
        "cloth",
        "muselina",
        "muslin",
        "gasa",
    ],
    "stuffed_animal": [
        "peluche",
        "oso de peluche",
        "stuffed animal",
        "soft toy",
    ],
    "doll": [
        "muñeca",
        "muñeco",
        "doll",
    ],
    "favorite_toy": [
        "juguete favorito",
        "toy he loves",
        "favorite toy",
        "su juguete especial",
        "juguete preferido",
        "toy every day",
        "plays with that toy",
        "juega con ese juguete",
    ],
    "caregiver_clothing": [
        "camiseta de mama",
        "camiseta de mamá",
        "ropa de papa",
        "ropa de papá",
        "camisa del cuidador",
        "caregiver clothing",
        "shirt that smells like mom",
    ],
    "small_pillow": [
        "almohadita",
        "almohada pequeña",
        "small pillow",
    ],
    "pacifier": [
        "chupete",
        "pacifier",
        "binky",
        "tetina",
    ],
    "transitioning": [
        "dejando el chupete",
        "transicionando del pacifier",
        "weaning from pacifier",
        "quitando el chupete",
        "transition object",
    ],
    "other": [
        "otro objeto",
        "cualquier objeto",
        "objecto especial",
        "special object",
    ],
}

COMFORT_OBJECT_HINTS = tuple(
    keyword for keywords in COMFORT_OBJECT_KEYWORDS.values() for keyword in keywords
)


def _match_comfort_objects(text: str) -> list[str]:
    matches = []
    normalized_text = normalize_text(text)
    for label, keywords in COMFORT_OBJECT_KEYWORDS.items():
        if any(normalize_text(keyword) in normalized_text for keyword in keywords):
            matches.append(label)
    return list(dict.fromkeys(matches))


def fallback_emotions_profile(message: str) -> EmotionsBondAndParentingProfile:
    matches = _match_comfort_objects(message)
    confidence = 0.85 if matches else 0.6
    return EmotionsBondAndParentingProfile(
        comfort_object=matches or None,
        confidence=confidence,
    )


def extract_emotions_bond_and_parenting(message: str) -> EmotionsBondAndParentingProfile:
    chain = get_llm(EmotionsBondAndParentingProfile, EMOTIONS_PROMPT)
    profile = None
    if chain:
        try:
            profile = chain.invoke({"message": message})
        except Exception as e:
            print(f"⚠️ [EMOTIONS_EXTRACTOR] Error con LLM ({e}). Usando heurística local.")
    if profile is None:
        profile = fallback_emotions_profile(message)
    else:
        profile.comfort_object = _ensure_list(profile.comfort_object)
    return _sanitize_emotions_profile(message, profile)


def _ensure_list(value) -> list[str] | None:
    if not value:
        return None
    if isinstance(value, str):
        value = [value]
    cleaned = [normalize_text(item).replace(" ", "_") if isinstance(item, str) else item for item in value if item]
    cleaned = [item for item in cleaned if item]
    return cleaned or None


def _has_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    normalized = normalize_text(text)
    normalized_keywords = tuple(normalize_text(keyword) for keyword in keywords)
    return any(keyword in normalized for keyword in normalized_keywords)


def _sanitize_emotions_profile(message: str, profile: EmotionsBondAndParentingProfile) -> EmotionsBondAndParentingProfile:
    if profile.comfort_object:
        normalized = normalize_text(message)
        if not _has_any_keyword(normalized, COMFORT_OBJECT_HINTS):
            profile.comfort_object = None
    return profile
