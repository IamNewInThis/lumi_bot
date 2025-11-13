# src/tests/profile_extractor_test.py
import json
from src.extractors.profile_extractor import extract_profile_info

def run_test_case(text: str):
    print("=" * 80)
    print(f"🧠 Entrada: {text}")
    try:
        result = extract_profile_info(text)
        print("✅ Resultado:")
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    except Exception as e:
        print("❌ Error ejecutando el extractor:", e)

def main():
    print("🚀 Iniciando pruebas del extractor de perfil multilingüe...\n")

    test_cases = [
        # Español
        "Mi hija duerme en su cuna y toma pecho por la noche. Es muy tranquila y sonriente.",
        "Últimamente Pepiño duerme con nosotros, le cuesta dormir solo.",

        # Inglés
        "My baby sleeps in her crib and drinks formula during the day. She is very active and curious.",
        "He sleeps with us most nights, and he’s quite calm.",

        # Portugués
        "Meu bebê dorme no berço e mama no peito à noite.",
        "Ele dorme conosco e é muito tranquilo.",
    ]

    for text in test_cases:
        run_test_case(text)

    print("\n🎯 Pruebas finalizadas.")

if __name__ == "__main__":
    main()
