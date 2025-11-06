"""
Test para verificar detección de keywords de Daily Care con rangos duales (específico + 0_84)
"""
import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.keywords_rag import detect_profile_keywords, get_age_range_key

print("=" * 80)
print("🧪 TEST DE RANGOS DE EDAD DUALES")
print("=" * 80)

# Verificar que get_age_range_key retorna tupla con 2 valores
print("\n📊 Verificando get_age_range_key():")
test_ages = [3, 8, 15, 30, 60]
for age in test_ages:
    ranges = get_age_range_key(age)
    print(f"   {age} meses → {ranges} (tipo: {type(ranges)})")

print("\n" + "=" * 80)
print("🔍 TESTS DE DETECCIÓN")
print("=" * 80)

test_cases = [
    {
        "message": "mi bebé se baña una vez al día",
        "age_months": 12,
        "expected": "bath_frequency (debe detectarse en 0_84 o 6_12)"
    },
    {
        "message": "le doy lactancia materna exclusiva",
        "age_months": 3,
        "expected": "principal_type_feeding (debe detectarse en 0_6)"
    },
    {
        "message": "come solo con supervisión",
        "age_months": 24,
        "expected": "eating_autonomy (debe detectarse en 0_84 o 12_24)"
    },
    {
        "message": "usa productos naturales para el baño",
        "age_months": 18,
        "expected": "bath_products_type (debe detectarse en 0_84 o 12_24)"
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
        verbose=False,  # Silenciar verbose para ver solo resultados
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
