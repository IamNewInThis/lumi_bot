import re
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..keywords_rag import TEMPLATE_KEYWORDS

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


def _normalize(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^a-zA-Záéíóúüñçãõâêô ]", " ", normalized)
    return " ".join(normalized.split())

def should_trigger_template_heuristic(text: str) -> tuple[bool, str | None]:
    normalized = _normalize(text)

    if any(keyword in normalized for keyword in TEMPLATE_TRIGGERS):
        print("🧩 [TEMPLATE_TRIGGER] Activado por HEURÍSTICA.")
        return True, "generic"

    for template_key, keywords_by_lang in (TEMPLATE_KEYWORDS or {}).items():
        for lang, keywords in keywords_by_lang.items():
            for keyword in keywords:
                normalized_keyword = _normalize(keyword)
                if normalized_keyword and normalized_keyword in normalized:
                    print(
                        "🧩 [TEMPLATE_TRIGGER] Activado por keyword "
                        f"'{keyword}' ({lang}) → template {template_key}."
                    )
                    return True, f"keyword:{template_key}"
    return False, None


# =========================================================
# CLASIFICADOR LLM (nivel 2)
# =========================================================

DEFAULT_TEMPLATE_MODEL = "gpt-4o-mini"

TEMPLATE_CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
Eres un clasificador experto.

Tu tarea:
    Determinar SI el usuario está pidiendo algo relacionado con: viajes, alimentos, referencias, rutinas, creatividad sobre alimentos, rechazo de alimentos o destete y lactancia
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
    3) Se acepta el template si:
       - LLM confirma, o
       - La heurística fuerte por keyword específica lo activó.
    """
    triggered, reason = should_trigger_template_heuristic(message)
    if not triggered:
        return False

    llm_result = should_trigger_template_llm(message)
    if llm_result:
        return True

    if reason and reason.startswith("keyword:"):
        print("🧷 [TEMPLATE_TRIGGER] Manteniendo activación por keyword específica.")
        return True

    return False
