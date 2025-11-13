from pydantic import Field
from .base import BaseProfileModel, get_llm, normalize_text


class DailyCareProfile(BaseProfileModel):
    bath_frequency: str | None = Field(
        None, description="Frecuencia del baño del bebé (once_a_day, alternate_days, etc.)."
    )
    skin_care: str | None = Field(
        None,
        description="Rutina de cuidado de piel: no_products, daily_hydration, hydration_as_needed o specialized_care.",
    )


DAILY_CARE_PROMPT = """
You are an expert in infant daily care and multilingual (Spanish, English, Portuguese).

Extract ONLY bath / skin-care information from the text:
- bath_frequency: how often the caregiver bathes the baby (once_a_day, twice_a_day, alternate_days, weekly, as_needed, etc.)
- skin_care: whether creams/oils are applied and how often (no_products, daily_hydration, hydration_as_needed, specialized_care)

Rules:
- If the user does not mention baths/bathing, leave bath_frequency = null.
- If the user does not mention skincare (cremas, aceites, pomadas), leave skin_care = null.
- Map implicit descriptions to the closest option (e.g., “solo cuando se reseca” -> hydration_as_needed).
- Never invent data; prefer null when unsure.

Text:
{message}
"""


BATH_FREQUENCY_RULES = [
    {
        "value": "once_a_day",
        "confidence": 0.95,
        "any": [
            "una vez al dia",
            "una vez al día",
            "once a day",
            "uma vez por dia",
            "diario",
            "cada dia",
            "cada día",
            "every day",
        ],
    },
    {
        "value": "twice_a_day",
        "confidence": 0.9,
        "any": ["dos veces al dia", "dos veces al día", "twice a day", "duas vezes por dia"],
    },
    {
        "value": "alternate_days",
        "confidence": 0.9,
        "any": [
            "dia por medio",
            "día por medio",
            "every other day",
            "dias alternados",
            "días intercalados",
            "cada dos dias",
            "cada dos días",
        ],
    },
    {
        "value": "weekly",
        "confidence": 0.85,
        "any": ["una vez a la semana", "once a week", "semanal"],
    },
    {
        "value": "as_needed",
        "confidence": 0.8,
        "any": ["segun necesidad", "según necesidad", "as needed", "cuando se ensucia", "conforme necessario", "cuando lo requiere"],
    },
]

SKIN_CARE_RULES = [
    {
        "value": "no_products",
        "confidence": 0.9,
        "any": [
            "sin productos",
            "no usamos cremas",
            "no usamos aceites",
            "no aplica cremas",
            "without products",
        ],
    },
    {
        "value": "daily_hydration",
        "confidence": 0.9,
        "any": [
            "hidratacion diaria",
            "hidratación diaria",
            "hidrata a diario",
            "crema cada dia",
            "crema cada día",
            "crema todos los dias",
            "daily moisturizer",
            "daily lotion",
        ],
    },
    {
        "value": "hydration_as_needed",
        "confidence": 0.85,
        "any": [
            "segun necesidad",
            "según necesidad",
            "cuando se reseca",
            "as needed",
            "when needed",
            "solo si se reseca",
        ],
    },
    {
        "value": "specialized_care",
        "confidence": 0.9,
        "any": [
            "cuidado especifico",
            "cuidado específico",
            "dermatologo",
            "dermatólogo",
            "receta medica",
            "receta médica",
            "crema medicada",
            "indicada por profesional",
            "professional care",
            "prescribed cream",
        ],
    },
]


def _match_rule(text: str, rules: list[dict]) -> tuple[str | None, float]:
    for rule in rules:
        tokens = rule.get("any", [])
        if any(normalize_text(token) in text for token in tokens):
            return rule["value"], rule["confidence"]
    return None, 0.6


def fallback_daily_care_profile(message: str) -> DailyCareProfile:
    normalized = normalize_text(message)
    frequency, bath_conf = _match_rule(normalized, BATH_FREQUENCY_RULES)
    skin_value, skin_conf = _match_rule(normalized, SKIN_CARE_RULES)
    confidence = max(bath_conf if frequency else 0, skin_conf if skin_value else 0, 0.6)
    return DailyCareProfile(
        bath_frequency=frequency,
        skin_care=skin_value,
        confidence=confidence,
    )


def extract_daily_care(message: str) -> DailyCareProfile:
    chain = get_llm(DailyCareProfile, DAILY_CARE_PROMPT)
    profile = None
    if chain:
        try:
            profile = chain.invoke({"message": message})
        except Exception as e:
            print(f"⚠️ [DAILY_CARE_EXTRACTOR] Error con LLM ({e}). Usando heurística local.")
    if profile is None:
        profile = fallback_daily_care_profile(message)
    return _sanitize_daily_care_profile(message, profile)


BATH_FREQUENCY_HINTS = (
    "baño",
    "baña",
    "banar",
    "bañar",
    "bano",
    "banho",
    "ducha",
    "shower",
    "bath",
    "lavar",
    "wash",
)

SKIN_CARE_HINTS = (
    "crema",
    "cremitas",
    "aceite",
    "aceites",
    "hidratante",
    "hidratacion",
    "hidratación",
    "lotion",
    "moisturizer",
    "pomada",
    "unguento",
    "ungüento",
    "dermatologo",
    "dermatólogo",
    "piel",
)


def _has_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    normalized_keywords = tuple(normalize_text(keyword) for keyword in keywords)
    return any(keyword in text for keyword in normalized_keywords)


def _sanitize_daily_care_profile(message: str, profile: DailyCareProfile) -> DailyCareProfile:
    normalized = normalize_text(message)
    if profile.bath_frequency and not _has_any_keyword(normalized, BATH_FREQUENCY_HINTS):
        profile.bath_frequency = None
    if profile.skin_care and not _has_any_keyword(normalized, SKIN_CARE_HINTS):
        profile.skin_care = None
    return profile
