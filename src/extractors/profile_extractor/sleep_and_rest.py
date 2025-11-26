# src/extractors/profile_extractor/sleep_and_rest.py

from pydantic import Field
from .base import BaseProfileModel, get_llm


class SleepAndRestProfile(BaseProfileModel):
    # Categorías fijas (siempre en inglés)
    sleep_location: list[str] | None = Field(
        None,
        description="Sleep object where the baby sleeps. Allowed values: crib, bassinet, shared_bed, floor_mattress, low_bed, regular_bed."
    )
    sleep_location_label_es: list[str] | None = None
    sleep_location_label_en: list[str] | None = None
    sleep_location_label_pt: list[str] | None = None

    sleep_room: list[str] | None = Field(
        None,
        description="Room where the baby sleeps. Allowed values: own_room, parents_room, shared_room, family_bedroom_co_sleeping."
    )
    sleep_room_label_es: list[str] | None = None
    sleep_room_label_en: list[str] | None = None
    sleep_room_label_pt: list[str] | None = None

    # NEW bedtime fields
    bedtime_start: str | None = None

    bedtime_caregiver: list[str] | None = None
    bedtime_caregiver_label_es: list[str] | None = None
    bedtime_caregiver_label_en: list[str] | None = None
    bedtime_caregiver_label_pt: list[str] | None = None

     # NEW — Sleep associations (multiple)
    sleep_association: list[str] | None = None
    sleep_association_es: list[str] | None = None
    sleep_association_en: list[str] | None = None
    sleep_association_pt: list[str] | None = None

    # NEW — Light conditions (single)
    sleep_light: str | None = None
    sleep_light_label_es: str | None = None
    sleep_light_label_en: str | None = None
    sleep_light_label_pt: str | None = None

     # Sonido (Único)
    sleep_sound: str | None = None
    sleep_sound_label_es: str | None = None
    sleep_sound_label_en: str | None = None
    sleep_sound_label_pt: str | None = None

    # Pijama / Vestimenta Base (Múltiple)
    sleep_pajama: list[str] | None = None
    sleep_pajama_es: list[str] | None = None
    sleep_pajama_en: list[str] | None = None
    sleep_pajama_pt: list[str] | None = None

    # Numero de siestas (Único)
    nap_count: str | None = None

    # Hora de dormir (Único)
    bedtime_hour: str | None = None

    # Despertares nocturnos (Único)
    night_wakings: str | None = None

    # Cómo retoma el sueño nocturno (Múltiple)
    night_soothing: list[str] | None = None
    night_soothing_es: list[str] | None = None
    night_soothing_en: list[str] | None = None
    night_soothing_pt: list[str] | None = None

    # Adulto a cargo de despertares nocturnos (Múltiple)
    night_caregiver: list[str] | None = None
    night_caregiver_es: list[str] | None = None
    night_caregiver_en: list[str] | None = None
    night_caregiver_pt: list[str] | None = None

    # Hora de despertar (Único)
    wakeup_hour: str | None = None

    # Tomas nocturnas (Único)
    night_feeding: str | None = None

    # Objetivo de la toma nocturna (Múltiple)
    night_feeding_purpose: list[str] | None = None
    night_feeding_purpose_es: list[str] | None = None
    night_feeding_purpose_en: list[str] | None = None
    night_feeding_purpose_pt: list[str] | None = None

    # Tipo de alimentación nocturna (Múltiple)
    night_feeding_type: list[str] | None = None
    night_feeding_type_es: list[str] | None = None
    night_feeding_type_en: list[str] | None = None
    night_feeding_type_pt: list[str] | None = None

    # Señales de cansancio (Múltiple)
    sleep_tired_signs: list[str] | None = None
    sleep_tired_signs_es: list[str] | None = None
    sleep_tired_signs_en: list[str] | None = None
    sleep_tired_signs_pt: list[str] | None = None



def _log_keyword_translations(profile: SleepAndRestProfile) -> None:
    """Muestra en consola las traducciones detectadas para depuración."""
    def _print_labels(field_name: str, label: str) -> None:
        labels = {}
        es_attr = (
            getattr(profile, f"{field_name}_label_es", None)
            if hasattr(profile, f"{field_name}_label_es")
            else getattr(profile, f"{field_name}_es", None)
        )
        en_attr = (
            getattr(profile, f"{field_name}_label_en", None)
            if hasattr(profile, f"{field_name}_label_en")
            else getattr(profile, f"{field_name}_en", None)
        )
        pt_attr = (
            getattr(profile, f"{field_name}_label_pt", None)
            if hasattr(profile, f"{field_name}_label_pt")
            else getattr(profile, f"{field_name}_pt", None)
        )
        if es_attr:
            labels["ES"] = es_attr
        if en_attr:
            labels["EN"] = en_attr
        if pt_attr:
            labels["PT"] = pt_attr
        labels = {lang: value for lang, value in labels.items() if value}
        if labels:
            print(f"🔤 {label} translations:")
            for lang, value in labels.items():
                print(f"   [{lang}] {value}")

    _print_labels("sleep_location", "Sleep location")
    _print_labels("sleep_room", "Sleep room")
    _print_labels("bedtime_caregiver", "Bedtime caregiver")
    _print_labels("sleep_association", "Sleep association")
    _print_labels("sleep_light", "Sleep light")
    _print_labels("sleep_sound", "Sleep sound")
    _print_labels("sleep_pajama", "Sleep pajama")
    _print_labels("night_soothing", "Night soothing")
    _print_labels("night_caregiver", "Night caregiver")
    _print_labels("night_feeding_purpose", "Night feeding purpose")
    _print_labels("night_feeding_type", "Night feeding type")
    _print_labels("sleep_tired_signs", "Sleep tired signs")


SLEEP_PROMPT = """
You are an expert in infant sleep patterns and a multilingual assistant (Spanish, English, Portuguese).

Your task is to extract structured sleep information.  
Some fields may return ONE value or MULTIPLE values.  
When a field contains multiple values, you MUST return a list for that field AND lists of the same length for all translations.

────────────────────────────────────
MANDATORY CATEGORY RULES (ALL FIELDS)
────────────────────────────────────

For every field below, the model MUST use ONLY values inside the allowed list.
The model MUST NOT create new values, synonyms, paraphrases, or inferred options.
If the user text contains wording not in the list, choose the closest match
OR return null if none applies.

────────────────────────────────────
SLEEP LOCATION  (list[str])
────────────────────────────────────
Allowed:
["crib", "bassinet", "shared_bed", "floor_mattress", "low_bed", "regular_bed"]

────────────────────────────────────
SLEEP ROOM  (list[str])
────────────────────────────────────
Allowed:
["own_room", "parents_room", "shared_room", "family_bedroom_co_sleeping"]

────────────────────────────────────
BEDTIME START (str)
────────────────────────────────────
Allowed approximate values:
["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "later_than_22"]

────────────────────────────────────
BEDTIME CAREGIVER (list[str])
────────────────────────────────────
Allowed:
["mother", "father", "both_parents", "grandparent", "other_caregiver"]

────────────────────────────────────
SLEEP ASSOCIATION (list[str])
────────────────────────────────────
Allowed:
[
 "in_arms", "rocking", "breastfeeding", "bottle", "pacifier", "hand_on_child",
 "soft_sounds", "white_noise", "contact_nap", "movement", "soothing_object",
 "gentle_touch", "singing", "shushing"
]

────────────────────────────────────
SLEEP LIGHT (str)
────────────────────────────────────
Allowed:
["red_light", "dim_light", "complete_darkness", "night_light", "no_light", "environment_dependent"]

────────────────────────────────────
SLEEP SOUND (str)
────────────────────────────────────
Allowed:
["white_noise_continuous", "white_noise_initial", "none", "environment_dependent"]

────────────────────────────────────
SLEEP PAJAMA / BASE LAYER (list[str])
────────────────────────────────────
Allowed:
[
 "diaper_only", "underwear", "sleeveless_body", "short_sleeve_body",
 "long_sleeve_body", "shirt", "long_socks", "socks", "full_pajama",
 "thermal_pajama", "two_piece_pajama", "light_sleep_sack",
 "medium_sleep_sack", "thick_sleep_sack",
 "thin_blanket", "thick_blanket"
]

────────────────────────────────────
NAP COUNT (str)
────────────────────────────────────
Allowed:
["0", "1", "2", "3", "4", "5", "6", "variable"]

────────────────────────────────────
BEDTIME HOUR (str)
────────────────────────────────────
Allowed:
["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "later_than_22"]

────────────────────────────────────
NIGHT WAKINGS (str)
────────────────────────────────────
Allowed:
["none", "1", "1–2", "2", "2–3", "3", "3–4", "4–5", "5_or_more", "no_pattern"]

────────────────────────────────────
NIGHT SOOTHING (list[str])
────────────────────────────────────
Allowed:
[
 "pick_up", "hold_on_chest", "lie_next_to_child", "sit_nearby",
 "rocking", "feeding_breast", "feeding_bottle", "pacifier",
 "comfort_object", "hand_on_body", "caressing", "rhythmic_patting",
 "shushing", "soft_voice", "singing_softly", "offer_water",
 "turn_on_light"
]

────────────────────────────────────
NIGHT CAREGIVER (list[str])
────────────────────────────────────
Allowed:
["mother", "father", "both_parents", "other_caregiver"]

────────────────────────────────────
WAKEUP HOUR (str)
────────────────────────────────────
Allowed:
[
 "before_4_30",
 "04:30–05:00", "05:00–05:30", "05:30–06:00",
 "06:00–06:30", "06:30–07:00",
 "07:00–07:30", "07:30–08:00",
 "08:00–08:30", "08:30–09:00",
 "after_09"
]

────────────────────────────────────
NIGHT FEEDING COUNT (str)
────────────────────────────────────
Allowed:
["0", "1", "2", "3", "4", "between_1_and_2", "between_2_and_3", "between_3_and_4"]

────────────────────────────────────
NIGHT FEEDING PURPOSE (list[str])
────────────────────────────────────
Allowed:
["nutrition", "medical_indication", "help_return_to_sleep"]

────────────────────────────────────
NIGHT FEEDING TYPE (list[str])
────────────────────────────────────
Allowed:
["breast", "bottle"]

────────────────────────────────────
TIREDNESS SIGNS (list[str])
────────────────────────────────────
Allowed:
[
 "yawn", "rub_eyes", "rub_face", "frown", "lost_stare", "reduced_attention",
 "loss_of_interest", "stillness", "contact_seeking", "ask_to_be_held",
 "rest_head_on_adult", "clingy", "irritability", "cry_easily",
 "frustration_with_objects", "sensitivity_to_noise", "sensitivity_to_light",
 "arm_movements_fast", "leg_movements_fast", "head_side_to_side",
 "chewing_hands", "chewing_fingers", "chewing_clothes", "touch_ears",
 "rub_nose", "rub_head", "complain_softly"
]


────────────────────────────────────
TRANSLATION RULES (VERY IMPORTANT)
────────────────────────────────────

If a field contains N items (e.g., sleep_association = 3 items):

- Translation fields MUST contain lists with the same number of items.
- Translations MUST be literal and accurate.
- Languages required:
  • Spanish (ES)
  • English (EN)
  • Portuguese (PT)

NO translation field may be omitted or set to null if the original field exists.

Example:
sleep_association: ["in arms", "pacifier"]
sleep_association_es: ["en brazos", "chupete"]
sleep_association_en: ["in arms", "pacifier"]
sleep_association_pt: ["nos braços", "chupeta"]

────────────────────────────────────
FIELDS TO EXTRACT
────────────────────────────────────

1) sleep_location (list[str] | None)
2) sleep_location_label_es (list[str] | None)
3) sleep_location_label_en (list[str] | None)
4) sleep_location_label_pt (list[str] | None)

5) sleep_room (list[str] | None)
6) sleep_room_label_es (list[str] | None)
7) sleep_room_label_en (list[str] | None)
8) sleep_room_label_pt (list[str] | None)

9) bedtime_start (single string or null)

10) bedtime_caregiver (list[str] | None)
11) bedtime_caregiver_label_es (list[str] | None)
12) bedtime_caregiver_label_en (list[str] | None)
13) bedtime_caregiver_label_pt (list[str] | None)

14) sleep_association (list[str] | None)
15) sleep_association_es (list[str] | None)
16) sleep_association_en (list[str] | None)
17) sleep_association_pt (list[str] | None)

18) sleep_light (single string | None)
19) sleep_light_label_es (string | None)
20) sleep_light_label_en (string | None)
21) sleep_light_label_pt (string | None)

────────────────────────────────────
NEW FIELDS (Based on extended sleep profile)
────────────────────────────────────

# Sonido (Único)
22) sleep_sound (string | None)
23) sleep_sound_label_es (string | None)
24) sleep_sound_label_en (string | None)
25) sleep_sound_label_pt (string | None)

# Pijama / Base Layer (Múltiple)
26) sleep_pajama (list[str] | None)
27) sleep_pajama_es (list[str] | None)
28) sleep_pajama_en (list[str] | None)
29) sleep_pajama_pt (list[str] | None)

# Número de siestas (Único)
30) nap_count (string | None)

# Hora de dormir (Único)
31) bedtime_hour (string | None)

# Despertares nocturnos (Único)
32) night_wakings (string | None)

# Cómo retoma el sueño (Múltiple)
33) night_soothing (list[str] | None)
34) night_soothing_es (list[str] | None)
35) night_soothing_en (list[str] | None)
36) night_soothing_pt (list[str] | None)

# Adulto a cargo de despertares (Múltiple)
37) night_caregiver (list[str] | None)
38) night_caregiver_es (list[str] | None)
39) night_caregiver_en (list[str] | None)
40) night_caregiver_pt (list[str] | None)

# Hora de despertar (Único)
41) wakeup_hour (string | None)

# Tomas nocturnas (Único)
42) night_feeding (string | None)

# Objetivo de la toma nocturna (Múltiple)
43) night_feeding_purpose (list[str] | None)
44) night_feeding_purpose_es (list[str] | None)
45) night_feeding_purpose_en (list[str] | None)
46) night_feeding_purpose_pt (list[str] | None)

# Tipo de alimentación nocturna (Múltiple)
47) night_feeding_type (list[str] | None)
48) night_feeding_type_es (list[str] | None)
49) night_feeding_type_en (list[str] | None)
50) night_feeding_type_pt (list[str] | None)

# Señales de cansancio (Múltiple)
51) sleep_tired_signs (list[str] | None)
52) sleep_tired_signs_es (list[str] | None)
53) sleep_tired_signs_en (list[str] | None)
54) sleep_tired_signs_pt (list[str] | None)

────────────────────────────────────

55) confidence (0–1)

────────────────────────────────────
ADDITIONAL RULES
────────────────────────────────────

- If no information is present for a field, return null.
- DO NOT invent content.
- DO NOT mix languages.
- For list fields, align each translation with the same list index.
- Output MUST strictly match the Pydantic schema.

────────────────────────────────────

Message to analyze:
{message}
"""

def extract_sleep_and_rest(message: str) -> SleepAndRestProfile:
    """Extracts sleep context using ONLY the LLM, no heuristics."""
    chain = get_llm(SleepAndRestProfile, SLEEP_PROMPT)

    try:
        profile = chain.invoke({"message": message})
        _log_keyword_translations(profile)
    except Exception as e:
        print(f"⚠️ [SLEEP_EXTRACTOR] LLM error: {e}")
        return SleepAndRestProfile(confidence=0.0)

    return profile
