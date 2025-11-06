"""
Test para verificar detección de keywords de Autonomy and Development
"""
import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.keywords_rag import detect_profile_keywords

print("=" * 80)
print("🧪 TEST DE DETECCIÓN - AUTONOMY AND DEVELOPMENT")
print("=" * 80)

test_cases = [
    {
        "message": "mi bebé ya camina con confianza",
        "age_months": 15,
        "expected": "marcha_y_equilibrio"
    },
    {
        "message": "mi hijo salta, corre y trepa con confianza",
        "age_months": 30,
        "expected": "coordinacion_y_control_corporal"
    },
    {
        "message": "crea escenas cotidianas y de ficción",
        "age_months": 36,
        "expected": "juego_simbolico_y_representacion"
    },
    {
        "message": "usa frases complejas y participa en conversaciones",
        "age_months": 40,
        "expected": "lenguaje_expresivo_y_comprension"
    },
    {
        "message": "ensambla, corta o dibuja con intención y cuidado",
        "age_months": 60,
        "expected": "motricidad_fina_y_precision"
    },
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'─' * 80}")
    print(f"Test #{i}: {test['message']}")
    print(f"Edad: {test['age_months']} meses")
    print(f"Esperado: {test['expected']}")
    
    detected = detect_profile_keywords(
        test['message'],
        lang='es',
        verbose=False,
        age_months=test['age_months']
    )
    
    if detected:
        print(f"\n✅ DETECTADOS {len(detected)} keyword(s):")
        for kw in detected:
            print(f"   📌 {kw['category']}.{kw.get('age_range', '?')}.{kw.get('field', '?')}")
            print(f"      Keyword: '{kw['keyword']}'")
    else:
        print(f"\n❌ NO SE DETECTÓ NADA")

print("\n" + "=" * 80)
print("✅ Tests completados")
print("=" * 80)
