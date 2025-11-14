# src/tests/profile_extractor_test.py
import json
from src.extractors.profile_extractor import extract_profile_info
from src.services.profile_service import BabyProfileService


def preview_storage(profile_model):
    """Muestra cómo quedarán los valores antes de persistir en Supabase."""
    preview = {}
    payload = profile_model.model_dump()

    for field, value in payload.items():
        if field == "confidence" or not value:
            continue

        if isinstance(value, list):
            entries = []
            for item in value:
                base_field = {
                    "key": item,
                    "value_es": item,
                    "value_en": item,
                    "value_pt": item,
                    "confidence": 1.0,
                }
                normalized = BabyProfileService._ensure_field_translations(field, base_field)
                entries.append({
                    "key": normalized.get("key"),
                    "value_es": normalized.get("value_es"),
                    "value_en": normalized.get("value_en"),
                    "value_pt": normalized.get("value_pt"),
                })
            preview[field] = entries
            continue

        base_field = {
            "key": value,
            "value_es": value,
            "value_en": value,
            "value_pt": value,
            "confidence": 1.0,
        }
        normalized = BabyProfileService._ensure_field_translations(field, base_field)
        preview[field] = {
            "key": normalized.get("key"),
            "value_es": normalized.get("value_es"),
            "value_en": normalized.get("value_en"),
            "value_pt": normalized.get("value_pt"),
        }

    return preview

def run_test_case(text: str):
    print("=" * 80)
    print(f"🧠 Entrada: {text}")
    try:
        result = extract_profile_info(text)
        print("✅ Resultado:")
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        storage_preview = preview_storage(result)
        if storage_preview:
            print("\n💾 Preview de guardado en baby_profile_value:")
            print(json.dumps(storage_preview, ensure_ascii=False, indent=2))
        else:
            print("\n💾 Sin campos para guardar.")
    except Exception as e:
        print("❌ Error ejecutando el extractor:", e)

def main():
    print("🚀 Iniciando pruebas del extractor de perfil multilingüe...\n")

    test_cases = [
        "Se baña una vez al día con agua tibia.",
        "Aplicamos crema hidratante cuando se reseca su piel.",
        "Para calmarse abraza su mantita y un peluche.",
        "Su abuela y su perro viven con nosotros y lo ayudan mucho.",
        "Actualmente va a la guardería medio día.",
        "Martin todavia no va al jardin.",
        "He cuddles his blankie to calm down.",
        "He plays with that toy every day.",
    ]

    for text in test_cases:
        run_test_case(text)

    print("\n🎯 Pruebas finalizadas.")

if __name__ == "__main__":
    main()
