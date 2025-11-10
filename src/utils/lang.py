import re
from langdetect import detect, detect_langs, DetectorFactory, LangDetectException

# Para hacer el resultado reproducible
DetectorFactory.seed = 0

SUPPORTED = {"es", "en", "pt"}  # español, inglés, portugués (Brasil)
# Palabras clave exclusivas de cada idioma para mejorar la detección
PORTUGUESE_MARKERS = {
    'quero', 'você', 'voce', 'não', 'nao', 'está', 'esta', 'estão', 'estao',
    'também', 'tambem', 'comigo', 'fazer', 'muito', 'obrigado', 'obrigada',
    'tchau', 'oi', 'sim', 'nós', 'nos', 'vocês', 'voces', 'são', 'sao',
    'têm', 'tem', 'mais', 'por favor', 'bom dia', 'boa tarde', 'boa noite',
    'tudo bem', 'com', 'para', 'onde', 'quando', 'porque', 'porquê'
}

SPANISH_MARKERS = {
    'quiero', 'tú', 'tu', 'usted', 'ustedes', 'también', 'tambien', 'conmigo',
    'hacer', 'mucho', 'gracias', 'adiós', 'adios', 'hola', 'sí', 'si',
    'nosotros', 'vosotros', 'tienen', 'buenos días', 'buenos dias',
    'buenas tardes', 'buenas noches', 'qué tal', 'que tal', 'con',
    'para', 'dónde', 'donde', 'cuándo', 'cuando', 'porque', 'porqué'
}

ENGLISH_MARKERS = {
    'want', 'you', 'with', 'for', 'where', 'when', 'because', 'hello',
    'hi', 'thank you', 'thanks', 'goodbye', 'bye', 'yes', 'no',
    'please', 'good morning', 'good afternoon', 'good evening', 'how are you'
}

SPANISH_UNIQUE_CHARS = {'ñ', '¡', '¿'}
PORTUGUESE_UNIQUE_CHARS = {'ã', 'õ', 'â', 'ê', 'ô', 'ç'}


def count_marker_hits(text: str, markers: set) -> int:
    """
    Cuenta coincidencias de markers usando límites de palabra para evitar falsos positivos.
    """
    hits = 0
    for marker in markers:
        marker = marker.strip().lower()
        if not marker:
            continue
        if " " in marker:
            pattern = rf"\b{re.escape(marker)}\b"
        else:
            pattern = rf"(?<!\w){re.escape(marker)}(?!\w)"
        if re.search(pattern, text, flags=re.UNICODE):
            hits += 1
    return hits


def detect_lang(text: str, default: str = "es") -> str:
    """
    Detecta idioma del texto. Devuelve 'es', 'en' o 'pt'.
    
    Estrategia:
    1. Primero intenta detectar por palabras clave exclusivas (más preciso para frases cortas)
    2. Si no hay coincidencias claras, usa langdetect
    3. Si falla o viene vacío, retorna default
    """
    if not text or not text.strip():
        return default

    text_lower = text.lower()
    has_spanish_chars = any(ch in text_lower for ch in SPANISH_UNIQUE_CHARS)
    has_portuguese_chars = any(ch in text_lower for ch in PORTUGUESE_UNIQUE_CHARS)
    
    # 1️⃣ Contar coincidencias con palabras clave de cada idioma
    pt_hits = count_marker_hits(text_lower, PORTUGUESE_MARKERS)
    es_hits = count_marker_hits(text_lower, SPANISH_MARKERS)
    en_hits = count_marker_hits(text_lower, ENGLISH_MARKERS)

    # Bonificar la detección si aparecen caracteres exclusivos de un idioma
    pt_score = pt_hits + (1 if has_portuguese_chars else 0)
    es_score = es_hits + (1 if has_spanish_chars else 0)
    en_score = en_hits
    scores = {'pt': pt_score, 'es': es_score, 'en': en_score}

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    max_score = sorted_scores[0][1]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
    top_langs = [lang for lang, score in scores.items() if score == max_score and score > 0]

    langdetect_cache = {}

    def get_langdetect():
        if langdetect_cache:
            return langdetect_cache['lang'], langdetect_cache['prob']
        try:
            lang_probs = detect_langs(text)
            primary = lang_probs[0] if lang_probs else None
            lang = primary.lang if primary else detect(text)
            prob = getattr(primary, "prob", None) if primary else None
            prob_suffix = f" (prob: {prob:.2f})" if prob is not None else ""
            print(f"🔍 [LANG] Idioma detectado por librería: {lang}{prob_suffix}")
        except LangDetectException:
            print(f"⚠️ [LANG] Error en detección con librería, usando default provisional: {default}")
            lang = default
            prob = None
        langdetect_cache['lang'] = lang
        langdetect_cache['prob'] = prob
        return lang, prob

    pt_override_logged = False

    def resolve_langdetect_choice(choice: str) -> str:
        nonlocal pt_override_logged
        if choice == "pt" and es_score > pt_score and es_score > 0:
            if not pt_override_logged:
                print("⚠️ [LANG] La librería sugirió 'pt' pero las señales contextuales coinciden más con español. Forzando 'es'.")
                pt_override_logged = True
            return "es"
        return choice

    if top_langs:
        if len(top_langs) == 1:
            candidate = top_langs[0]
            unique_bonus = (candidate == "es" and has_spanish_chars) or (candidate == "pt" and has_portuguese_chars)
            strong_unique = max_score >= 2 or (max_score == 1 and second_score == 0 and unique_bonus)
            if strong_unique:
                flag = "🇧🇷" if candidate == "pt" else "🇪🇸" if candidate == "es" else "🇬🇧"
                print(f"{flag} [LANG] {candidate.upper()} detectado por keywords (score: {max_score})")
                return candidate

            langdetect_lang, langdetect_prob = get_langdetect()
            if langdetect_lang in SUPPORTED:
                resolved = resolve_langdetect_choice(langdetect_lang)
                if langdetect_lang == candidate:
                    print(f"🤝 [LANG] Coincidencia entre keywords y librería: {resolved} (score: {max_score})")
                    return resolved
                if langdetect_prob and langdetect_prob >= 0.6:
                    print(f"⚠️ [LANG] Conflicto keywords '{candidate}' vs librería '{langdetect_lang}'. Priorizando librería (prob: {langdetect_prob:.2f})")
                    return resolved
                print(f"⚠️ [LANG] Evidencia débil para '{candidate}' por keywords, usando librería: {resolved}")
                return resolved

            print(f"⚠️ [LANG] Evidencia débil para '{candidate}' y sin librería disponible, usando default: {default}")
            return default

        langdetect_lang, langdetect_prob = get_langdetect()
        if langdetect_lang in top_langs and langdetect_lang in SUPPORTED:
            resolved = resolve_langdetect_choice(langdetect_lang)
            prob_msg = f" (prob: {langdetect_prob:.2f})" if langdetect_prob is not None else ""
            print(f"⚖️ [LANG] Empate en keywords {top_langs}, librería eligió '{resolved}'{prob_msg}")
            return resolved

        preferred_order = [default, "es", "pt", "en"]
        for candidate in preferred_order:
            if candidate in top_langs:
                print(f"⚖️ [LANG] Empate en detección por keywords {top_langs}, priorizando '{candidate}' (score: {scores[candidate]})")
                return candidate

        if langdetect_lang in SUPPORTED:
            resolved = resolve_langdetect_choice(langdetect_lang)
            print(f"⚠️ [LANG] Empate sin resolución clara, usando librería: {resolved}")
            return resolved

        return default

    langdetect_lang, _ = get_langdetect()
    if langdetect_lang in SUPPORTED:
        return resolve_langdetect_choice(langdetect_lang)

    print(f"⚠️ [LANG] Idioma '{langdetect_lang}' no soportado, usando default: {default}")
    return default
