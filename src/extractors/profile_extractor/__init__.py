# src/extractors/profile_extractor/__init__.py
from .base import BabyProfile
from .sleep_and_rest import extract_sleep_and_rest, SleepAndRestProfile
from .daily_care import extract_daily_care, DailyCareProfile
from .emotions_bond_and_parenting import extract_emotions_bond_and_parenting, EmotionsBondAndParentingProfile

def extract_profile_info(message: str) -> BabyProfile:
    """
    Orquestador principal. Ejecuta los extractores por área y consolida la información.
    """
    sleep_profile = extract_sleep_and_rest(message)
    daily_care_profile = extract_daily_care(message)
    emotions_profile = extract_emotions_bond_and_parenting(message)

    combined_confidence = max(
        sleep_profile.confidence or 0,
        daily_care_profile.confidence or 0,
        emotions_profile.confidence or 0,
    ) or None

    return BabyProfile(
        sleep_location=sleep_profile.sleep_location,
        sleep_room=sleep_profile.sleep_room,
        bath_frequency=daily_care_profile.bath_frequency,
        skin_care=daily_care_profile.skin_care,
        comfort_object=emotions_profile.comfort_object,
        confidence=combined_confidence,
    )


__all__ = [
    "BabyProfile",
    "extract_profile_info",
    "SleepAndRestProfile",
    "DailyCareProfile",
    "EmotionsBondAndParentingProfile",
]
