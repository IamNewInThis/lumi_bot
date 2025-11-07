#!/usr/bin/env python
"""Test script para detect_profile_keywords_fuzzy() con normalización unicode"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.keywords_rag import detect_profile_keywords_fuzzy, normalize_text

# Primero probar normalización
print("=" * 60)
print("TEST DE NORMALIZACIÓN DE TEXTO")
print("=" * 60)
test_texts = [
    "¡Hola! ¿Cómo está el bebé?",
    "Bebé duerme bien... 😊",
    "Ciclos cortos de sueño.",
    "El niño gatea solo y se mueve libremente"
]
for text in test_texts:
    normalized = normalize_text(text)
    print(f"Original:    '{text}'")
    print(f"Normalizado: '{normalized}'")
    print()

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
print(f"\nResultados: {len(result_es)} coincidencias encontradas")
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
print(f"\nResultados: {len(result_en)} coincidencias encontradas")
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
print(f"\nResultados: {len(result_pt)} coincidencias encontradas")
for match in result_pt[:5]:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%, categoría: {match['category']})")

# Test con caracteres especiales y acentos
print("\n" + "=" * 60)
print("TEST CON CARACTERES ESPECIALES (ES):")
print("=" * 60)
result_special = detect_profile_keywords_fuzzy(
    message="¡El bebé tiene ciclos córtos de sueño! ¿Qué hago?",
    lang='es',
    threshold=75,  # Threshold más bajo para capturar variaciones
    age_months=6,
    verbose=True
)
print(f"\nResultados: {len(result_special)} coincidencias encontradas")
for match in result_special[:5]:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%, categoría: {match['category']})")

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO EXITOSAMENTE")
print("=" * 60)
