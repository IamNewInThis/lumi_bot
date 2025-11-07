#!/usr/bin/env python
"""Test script para detect_profile_keywords_fuzzy()"""

from keywords_rag import detect_profile_keywords_fuzzy

# Test en español
print("=" * 60)
print("TEST EN ESPAÑOL:")
print("=" * 60)
result_es = detect_profile_keywords_fuzzy(
    message="el bebé gatea solo y se mueve libremente por la casa",
    lang='es',
    threshold=80,
    age_months=9,
    verbose=True
)
print(f"Resultados: {len(result_es)} coincidencias encontradas")
for match in result_es[:5]:  # Show first 5 matches
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%, categoría: {match['category']})")

# Test en inglés
print("\n" + "=" * 60)
print("TEST EN INGLÉS:")
print("=" * 60)
result_en = detect_profile_keywords_fuzzy(
    message="baby crawls independently and moves around the house",
    lang='en',
    threshold=80,
    age_months=9,
    verbose=True
)
print(f"Resultados: {len(result_en)} coincidencias encontradas")
for match in result_en[:5]:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%, categoría: {match['category']})")

# Test en portugués
print("\n" + "=" * 60)
print("TEST EN PORTUGUÉS:")
print("=" * 60)
result_pt = detect_profile_keywords_fuzzy(
    message="o bebê engatinha sozinho e se move livremente pela casa",
    lang='pt',
    threshold=80,
    age_months=9,
    verbose=True
)
print(f"Resultados: {len(result_pt)} coincidencias encontradas")
for match in result_pt[:5]:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%, categoría: {match['category']})")

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO EXITOSAMENTE")
print("=" * 60)
