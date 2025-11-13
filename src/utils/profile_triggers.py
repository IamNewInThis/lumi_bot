# src/utils/profile_triggers.py
import re
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# =========================================================
# Propósito
# profile_triggers sirve para determinar si el mensaje del usuario
# contiene informacion para activar el profile_extractor.
# 1. Primer capa con heurística básica (keywords)
# 2. Segunda capa con LLM pequeño (clasificador)
# =========================================================

# =========================================================
# 🧠 HEURÍSTICA BÁSICA
# =========================================================

PROFILE_TRIGGERS = {
    "sleep": [
        "duerme", "dormir", "despierta", "cuna", "moisés", "berço", "crib", "colecho",
        "siesta", "sueño", "bed", "sleep", "siesta", "noche"
    ],
    "daily_care": [
        "baño", "bano", "banho", "toallitas", "pañal", "pañales", "fralda", "diaper", "bath", "wipes"
    ],
    "emotions_bond_and_parenting": [
        "abraza", "abrazo", "mima", "mimar", "caricia", "cariño", "love", "hug", "cuddle", "se calma",
        "tranquiliza", "soothing", "comfort"
    ], 
}


def should_trigger_profile_extraction(text: str) -> bool:
    """
    Heurística para determinar si un mensaje probablemente contiene
    información del perfil del bebé (sueño).
    """
    normalized = text.lower()

    # Limpieza básica
    normalized = re.sub(r"[^a-zA-Záéíóúüñçãõâêô ]", "", normalized)

    for category, keywords in PROFILE_TRIGGERS.items():
        if any(keyword in normalized for keyword in keywords):
            print(f"🧩 [PROFILE_TRIGGER] Activado por categoría: {category}")
            return True

    return False

# =========================================================
# 🧠 CLASIFICADOR LLM (SEGUNDA CAPA)
# =========================================================
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Eres un asistente experto en desarrollo infantil.
Tu tarea es decidir si este mensaje del usuario contiene información relevante
para el perfil del bebé (temas: sueño, descanso, cuidado diario).

Responde solo con "sí" o "no".

Mensaje:
{message}
""")


def should_trigger_profile_extraction_llm(message: str) -> bool:
    """
    Usa un modelo LLM pequeño (GPT-4o-mini) para determinar si
    el mensaje contiene información del perfil del bebé.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ [PROFILE_TRIGGER] No hay API key, no se ejecuta clasificador LLM.")
        return False

    try:
        llm = ChatOpenAI(model=DEFAULT_OPENAI_MODEL, temperature=0, openai_api_key=api_key)
        response = llm.invoke(CLASSIFIER_PROMPT.format(message=message))
        content = response.content.strip().lower()

        if "sí" in content or "yes" in content:
            print("✅ [PROFILE_TRIGGER_LLM] Clasificador detectó información relevante.")
            return True
        else:
            print("💬 [PROFILE_TRIGGER_LLM] Clasificador no detectó información relevante.")
            return False

    except Exception as e:
        print(f"❌ [PROFILE_TRIGGER_LLM] Error ejecutando clasificador: {e}")
        return False
