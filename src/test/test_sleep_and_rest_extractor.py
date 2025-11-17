from unittest.mock import patch

from src.extractors.profile_extractor.sleep_and_rest import (
    SleepAndRestProfile,
    extract_sleep_and_rest,
)


class DummyChain:
    """Simula la cadena LLM para evitar llamadas reales durante los tests."""

    def __init__(self, response):
        self.response = response
        self.invocations = []

    def invoke(self, payload):
        self.invocations.append(payload)
        return SleepAndRestProfile(**self.response)


def test_extract_sleep_and_rest_handles_multiple_locations():
    """
    Verifica que el extractor retorne los valores exactamente como los envía el LLM.
    Se simula una respuesta con múltiples ubicaciones y traducciones.
    """
    fake_response = {
        "sleep_location": ["crib", "shared_bed"],
        "sleep_room": ["parents_room"],
        "sleep_location_label_es": ["cuna", "cama compartida"],
        "sleep_location_label_en": ["crib", "shared bed"],
        "sleep_location_label_pt": ["berço", "cama compartilhada"],
        "sleep_room_label_es": ["habitación de los padres"],
        "sleep_room_label_en": ["parents' room"],
        "sleep_room_label_pt": ["quarto dos pais"],
        "confidence": 0.92,
    }

    dummy_chain = DummyChain(fake_response)

    message = "Mi bebé duerme conmigo en mi habitación, a veces en su cuna y otras en mi cama."

    with patch(
        "src.extractors.profile_extractor.sleep_and_rest.get_llm",
        return_value=dummy_chain,
    ):
        profile = extract_sleep_and_rest(message)

    # Validar que el mensaje pasó por el chain simulado
    assert dummy_chain.invocations, "El chain simulado no fue invocado."
    assert dummy_chain.invocations[0]["message"] == message

    # Validar datos devueltos
    assert profile.sleep_location == ["crib", "shared_bed"]
    assert profile.sleep_room == ["parents_room"]
    assert profile.sleep_location_label_es == ["cuna", "cama compartida"]
    assert profile.sleep_location_label_en == ["crib", "shared bed"]
    assert profile.sleep_location_label_pt == ["berço", "cama compartilhada"]
    assert profile.sleep_room_label_es == ["habitación de los padres"]
    assert profile.sleep_room_label_en == ["parents' room"]
    assert profile.sleep_room_label_pt == ["quarto dos pais"]
    assert profile.confidence == 0.92
