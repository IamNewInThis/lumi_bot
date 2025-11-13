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
        # =============================================
        # 🇪🇸 ESPAÑOL - 10 test cases
        # =============================================
        # "Mi hija duerme en su cuna y toma pecho por la noche.", # Correcto
        # "Últimamente Pepiño duerme con nosotros, le cuesta dormir solo.", # Error: Podria inferir que es sleep_room como parents_room
        # "Duerme en la misma habitación que nosotros para sentirse seguro.", # Correcto
        # "Tiene su propia habitación desde los 6 meses.",  # Correcto
        # "Comparte habitación con su hermano mayor.", # Correcto
        # "Duerme en un moisés al lado de nuestra cama.", # Error: Podria inferir que es sleep_room como parents_room
        # "Usamos cama compartida toda la familia.", # Error: Podria inferir que es sleep_room como parents_room
        # "Tiene una cama baja estilo Montessori en su cuarto.", # Correcto
        # "Duerme en un colchón en el suelo de nuestra habitación.", # Correcto
        # "Usa crema para la dermatitis del pañal.", # Correcto
        "Se baña una vez al día con agua tibia.",
        "Aplicamos crema hidratante cuando se reseca su piel.",
        "Para calmarse abraza su mantita y un peluche.",

        # =============================================
        # 🇺🇸 INGLÉS - 10 test cases  
        # =============================================
        # "My baby sleeps in her crib and drinks formula during the day.", # Correcto 
        # "He sleeps with us most nights, and he's quite calm.", # Error: Podria inferir que es sleep_room como parents_room
        # "She has her own room since she was 3 months old.", # Correcto 
        # "The baby sleeps in our bedroom for now.", # Correcto 
        # "He shares a room with his older sister.",  # Correcto 
        # "We use a bassinet next to our bed for the newborn.", # Error: Podria inferir que es sleep_room como parents_room
        # "We co-sleep in a shared bed as a family.", # Error: Podria inferir que es sleep_room como parents_room
        # "She has a low bed in her own room.", # Correcto
        # "He sleeps on a mattress on the floor in our room.", # Correcto

        # # =============================================
        # # 🇵🇹 PORTUGUÉS - 10 test cases
        # # =============================================
        # "Meu bebê dorme no berço e mama no peito à noite.",  # Correcto
        # "Ele dorme conosco e é muito tranquilo.", # Error: Podria inferir que es sleep_room como parents_room
        # "Ela tem o próprio quarto desde os 4 meses.", # Correcto
        # "O bebê dorme no nosso quarto por enquanto.", # Correcto
        # "Ele divide o quarto com o irmão mais velho.", # Correcto
        # "Usamos um moisés ao lado da nossa cama.", # Error: Podria inferir que es sleep_room como parents_room
        # "Dormimos todos juntos na cama compartilhada.", # Error: Podria inferir que es sleep_room como parents_room
        # "Ela tem uma cama baixa no próprio quarto.", # Correcto
        # "Ele dorme num colchão no chão do nosso quarto.", # Correcto
    ]

    for text in test_cases:
        run_test_case(text)

    print("\n🎯 Pruebas finalizadas.")

if __name__ == "__main__":
    main()
