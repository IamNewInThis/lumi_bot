from pydantic import Field
from .base import BaseProfileModel, get_llm, normalize_text


class FamilyContextProfile(BaseProfileModel):
    family_members: list[str] | None = Field(
        default=None,
        description="Miembros clave que conviven o apoyan al bebé (mother, father, siblings, grandparents, caregiver, pets).",
    )
    go_to_daycare: str | None = Field(
        default=None,
        description="Asistencia a guardería/colegio (no, daycare, preschool, school).",
    )


FAMILY_CONTEXT_PROMPT = """
You are an expert in respectful parenting and multilingual (Spanish, English, Portuguese).

Extract the following information:
- family_members: array containing any of (mother, father, siblings, grandparents, caregiver, pets)
- go_to_daycare: does the child attend daycare/preschool/school? options = no, daycare, preschool, school

Rules:
- Include every family member mentioned; remove duplicates.
- For nannies/aunts/uncles or other regular caregivers, map to caregiver.
- For pets (dog, cat, etc.), map to pets.
- go_to_daycare: map informal nursery mentions to daycare; “jardín infantil/preescolar” to preschool; “colegio/escuela” to school; “no va a guardería” -> no.
- If no data is present for a field, leave it null/empty.
- Never invent details.

Text:
{message}
"""


FAMILY_MEMBER_KEYWORDS = {
    "mother": ["mamá", "mama", "madre", "mom", "mother"],
    "father": ["papá", "papa", "padre", "dad", "father"],
    "siblings": ["hermano", "hermana", "siblings", "brother", "sister"],
    "grandparents": ["abuela", "abuelo", "abuelos", "grandma", "grandpa", "grandparents"],
    "caregiver": [
        "cuidador",
        "cuidadora",
        "nanny",
        "niñera",
        "niñero",
        "tía",
        "tio",
        "tío",
        "tutor",
        "caregiver",
    ],
    "pets": [
        "mascota",
        "perro",
        "gata",
        "gato",
        "perrita",
        "perrito",
        "cat",
        "dog",
        "pet",
    ],
}

DAYCARE_RULES = [
    {
        "value": "no",
        "confidence": 0.85,
        "any": [
            "no va a guarderia",
            "no va a guardería",
            "no va a jardin",
            "no va a jardín",
            "todavia no va al jardin",
            "todavía no va al jardín",
            "no asiste a jardin",
            "no asiste al jardin",
            "no asiste al jardín",
            "no va a colegio",
            "no va al daycare",
            "no asistimos a guardería",
            "todavia no va a la guarderia",
            "todavía no va a la guardería",
            "todavia no asiste a guarderia",
            "todavía no asiste a guarderia",
        ],
    },
    {
        "value": "daycare",
        "confidence": 0.9,
        "any": [
            "guarderia",
            "guardería",
            "daycare",
            "nursery",
            "ludoteca",
        ],
    },
    {
        "value": "preschool",
        "confidence": 0.9,
        "any": [
            "jardin infantil",
            "jardín infantil",
            "preescolar",
            "preschool",
            "kindergarten",
        ],
    },
    {
        "value": "school",
        "confidence": 0.9,
        "any": [
            "colegio",
            "escuela",
            "school",
        ],
    },
]

FAMILY_MEMBER_HINTS = tuple(
    keyword for keywords in FAMILY_MEMBER_KEYWORDS.values() for keyword in keywords
)


def _match_family_members(text: str) -> list[str]:
    normalized = normalize_text(text)
    matches = []
    for label, keywords in FAMILY_MEMBER_KEYWORDS.items():
        if any(normalize_text(keyword) in normalized for keyword in keywords):
            matches.append(label)
    return list(dict.fromkeys(matches))


def _match_daycare(text: str) -> tuple[str | None, float]:
    normalized = normalize_text(text)
    for rule in DAYCARE_RULES:
        if any(normalize_text(keyword) in normalized for keyword in rule["any"]):
            return rule["value"], rule["confidence"]
    return None, 0.6


def fallback_family_context(message: str) -> FamilyContextProfile:
    members = _match_family_members(message)
    daycare_value, daycare_conf = _match_daycare(message)
    confidence = max(
        0.85 if members else 0,
        daycare_conf if daycare_value else 0,
        0.6,
    )
    return FamilyContextProfile(
        family_members=members or None,
        go_to_daycare=daycare_value,
        confidence=confidence,
    )


def extract_family_context(message: str) -> FamilyContextProfile:
    chain = get_llm(FamilyContextProfile, FAMILY_CONTEXT_PROMPT)
    profile = None
    if chain:
        try:
            profile = chain.invoke({"message": message})
        except Exception as e:
            print(f"⚠️ [FAMILY_CONTEXT] Error con LLM ({e}). Usando heurística local.")
    if profile is None:
        profile = fallback_family_context(message)
    else:
        profile.family_members = _ensure_list(profile.family_members)
    return _sanitize_family_profile(message, profile)


def _ensure_list(value) -> list[str] | None:
    if not value:
        return None
    if isinstance(value, str):
        value = [value]
    cleaned = [normalize_text(item).replace(" ", "_") if isinstance(item, str) else item for item in value if item]
    cleaned = [item for item in cleaned if item]
    return cleaned or None


def _sanitize_family_profile(message: str, profile: FamilyContextProfile) -> FamilyContextProfile:
    if profile.family_members:
        normalized = normalize_text(message)
        normalized_hints = tuple(normalize_text(hint) for hint in FAMILY_MEMBER_HINTS)
        if not any(hint in normalized for hint in normalized_hints):
            profile.family_members = None
    if profile.go_to_daycare:
        normalized = normalize_text(message)
        normalized_keywords = [
            normalize_text(keyword)
            for rule in DAYCARE_RULES
            for keyword in rule["any"]
        ]
        if not any(keyword in normalized for keyword in normalized_keywords):
            profile.go_to_daycare = None
    return profile
