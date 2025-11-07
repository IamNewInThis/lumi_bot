#!/usr/bin/env python
"""Test específico para detección de keywords de cuidado dental"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.keywords_rag import detect_profile_keywords_fuzzy, normalize_text

# Test de normalización primero
print("=" * 60)
print("NORMALIZACIÓN DEL MENSAJE:")
print("=" * 60)
mensaje_original = "A Matías le lavamos los dientes con una gasa humedaa"
mensaje_normalizado = normalize_text(mensaje_original)
print(f"Original:    '{mensaje_original}'")
print(f"Normalizado: '{mensaje_normalizado}'")

# Normalizar keywords esperados
keywords_esperados = [
    "limpieza con gasa",
    "gasa húmeda",
    "lavar dientes",
    "lavamos los dientes"
]
print("\nKeywords esperados (normalizados):")
for kw in keywords_esperados:
    print(f"  '{kw}' → '{normalize_text(kw)}'")

# Test con diferentes thresholds
print("\n" + "=" * 60)
print("TEST CON THRESHOLD 80 (ESTRICTO):")
print("=" * 60)
result_80 = detect_profile_keywords_fuzzy(
    message=mensaje_original,
    lang='es',
    threshold=80,
    age_months=12,  # Edad donde se lavan dientes
    verbose=True
)
print(f"\n✅ Resultados (threshold 80): {len(result_80)} coincidencias")
for match in result_80:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%)")

print("\n" + "=" * 60)
print("TEST CON THRESHOLD 70 (TOLERANTE):")
print("=" * 60)
result_70 = detect_profile_keywords_fuzzy(
    message=mensaje_original,
    lang='es',
    threshold=70,
    age_months=12,
    verbose=True
)
print(f"\n✅ Resultados (threshold 70): {len(result_70)} coincidencias")
for match in result_70:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%)")

print("\n" + "=" * 60)
print("TEST CON THRESHOLD 60 (MUY TOLERANTE):")
print("=" * 60)
result_60 = detect_profile_keywords_fuzzy(
    message=mensaje_original,
    lang='es',
    threshold=60,
    age_months=12,
    verbose=True
)
print(f"\n✅ Resultados (threshold 60): {len(result_60)} coincidencias")
for match in result_60:
    print(f"  - {match['keyword']} (similitud: {match['similarity']}%)")

# Test manual de fuzzy matching
print("\n" + "=" * 60)
print("TEST MANUAL DE FUZZY MATCHING:")
print("=" * 60)
try:
    from rapidfuzz import fuzz
    
    test_keywords = [
        "gasa húmeda",
        "gasa humeda",
        "limpieza con gasa",
        "lavar dientes",
        "lavamos los dientes",
        "cepillado dental"
    ]
    
    print(f"Mensaje normalizado: '{mensaje_normalizado}'")
    print("\nSimilitudes:")
    for kw in test_keywords:
        kw_norm = normalize_text(kw)
        similarity = fuzz.partial_ratio(kw_norm, mensaje_normalizado)
        print(f"  '{kw}' → '{kw_norm}' = {similarity}%")
        
except ImportError:
    print("❌ rapidfuzz no instalado")

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO")
print("=" * 60)
