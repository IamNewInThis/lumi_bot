# src/extractors/profile_extractor/__init__.py
from .base import BabyProfile
from .sleep_and_rest import extract_sleep_and_rest, SleepAndRestProfile


def extract_profile_info(message: str) -> BabyProfile:
    """
    Orquestador principal. Ejecuta los extractores por área y consolida la información.
    Por ahora solo incluye la sección de sueño y descanso.
    """
    sleep_profile = extract_sleep_and_rest(message)

    return BabyProfile(
        sleep_location=sleep_profile.sleep_location,
        sleep_room=sleep_profile.sleep_room,
        confidence=sleep_profile.confidence,
    )


__all__ = ["BabyProfile", "extract_profile_info", "SleepAndRestProfile"]
