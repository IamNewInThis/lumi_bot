import re
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# =========================================================
# HEURÍSTICA BÁSICA PARA TEMPLATES
# =========================================================

TEMPLATE_TRIGGERS = [
    "plantilla", "template", "formato", "estructura", "modelo",
    "checklist", "lista de tareas", "lista estructurada",
    "pauta", "ejemplo estructurado", "guía", "guide",
    "estructura propuesta", "armar plantilla", "hacer plantilla",
    "formulario", "esquema", "blueprint"
]

def should_trigger_template_heuristic(text: str) -> bool:
    normalized = text.lower()
    normalized = re.sub(r"[^a-zA-Záéíóúüñçãõâêô ]", " ", normalized)

    if any(keyword in normalized for keyword in TEMPLATE_TRIGGERS):
        print("🧩 [TEMPLATE_TRIGGER] Activado por HEURÍSTICA.")
        return True
    return False


# =========================================================
# CLASIFICADOR LLM (nivel 2)
# =========================================================

DEFAULT_TEMPLATE_MODEL = "gpt-4o-mini"

TEMPLATE_CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Eres un clasificador experto.

Tu tarea:
Determinar SI el usuario está pidiendo explícitamente
una plantilla, estructura, formato, pauta o documento estructurado.

Responde SOLO con "sí" o "no".

Mensaje:
{message}
""")

def should_trigger_template_llm(message: str) -> bool:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ [TEMPLATE_TRIGGER] Sin API key.")
        return False
    
    try:
        llm = ChatOpenAI(
            model=DEFAULT_TEMPLATE_MODEL,
            temperature=0,
            openai_api_key=api_key
        )
        response = llm.invoke(TEMPLATE_CLASSIFIER_PROMPT.format(message=message))
        content = response.content.strip().lower()

        if "sí" in content or "yes" in content:
            print("✅ [TEMPLATE_TRIGGER_LLM] Clasificador detectó TEMPLATE.")
            return True
        else:
            print("💬 [TEMPLATE_TRIGGER_LLM] Clasificador NO detectó template.")
            return False

    except Exception as e:
        print(f"❌ [TEMPLATE_TRIGGER_LLM] Error: {e}")
        return False


# =========================================================
# FUNCIÓN FINAL — UNIFICADA
# =========================================================

def should_trigger_template(message: str) -> bool:
    """
    1) Heurística rápida (gratis)
    2) Si pasa → verificación con LLM mini
    3) Si ambos dicen que sí → Ejecutar extractor/generador de plantillas
    """
    if not should_trigger_template_heuristic(message):
        return False

    return should_trigger_template_llm(message)
