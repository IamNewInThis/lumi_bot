import re
from langdetect import detect, detect_langs, DetectorFactory, LangDetectException

# Para hacer el resultado reproducible
DetectorFactory.seed = 0

SUPPORTED = {"es", "en", "pt"}  # español, inglés, portugués (Brasil)
# Palabras clave exclusivas de cada idioma para mejorar la detección
PORTUGUESE_MARKERS = {
    'saudade', 'filho', 'filha', 'mãe', 'mae', 'pai', 'bebê', 'bebe',
    'fralda', 'cólica', 'colica', 'leitinho', 'amamentação', 'amamentacao',
    'berço', 'berco', 'soninho', 'soneca', 'chorando', 'acolher',
    'maternidade', 'cafuné', 'cafune', 'dengo', 'brincadeira', 'acolhimento',
    'carinho', 'desmame', 'canguru', 'banho morno', 'rede', 'mordedor',
    'marcos do desenvolvimento', 'desenvolvimento', 'sono tranquilo',
    'fôlego',
}

SPANISH_MARKERS = {
    'hola', 'quiero', 'quieres', 'dónde', 'cuando', 'porque','mamá',
    'mama', 'papá', 'papa', 'niño', 'niña', 'nino', 'nina',
    'colecho', 'pañal', 'panal', 'llanto', 'abrazos', 'cariño', 'carino',
    'crianza', 'destete', 'porteo', 'puerperio', 'cansancio', 'berrinche',
    'rabieta', 'maternidad', 'biberón', 'biberon', 'chupete', 'pickler',
    'respira conmigo', 'acompañar', 'acompanar', 'regazo' , 'calorcito',
    'últimamente', 'durmiendo', 'duerme','corrido', 'muchas', 'veces'
}

ENGLISH_MARKERS = {
    'want','sleep','sleeps' , 'you', 'with', 'for', 'where', 'when', 'because', 'hello',
    'thank you', 'thanks', 'goodbye', 'food', 'milk', 'diaper', 'nap',
    'cycles', 'crying', 'cuddle', 'parenting', 'bottle', 'pacifier',
    'colics', 'crib', 'bedtime', 'tired', 'maternity', 'playtime',
    'attachment', 'nursing', 'swaddling', 'teething', 'milestone',
    'development', 'babywearing', 'gentle parenting', 'positive discipline',
    'please', 'good night', 'good morning', 'doesn´t', 'doesnt', 'isn´t', 'isnt',
    'sleeping', 'baby', 'tired', 'play', 'time', 'night', 'day', 'feed', 'hungry',
    'irritability', 'breastfeed', 'breastfeeding','lullaby', 'short sleeve', 'long sleeve',
    
    
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


def detect_lang(text: str, default: str = "es", return_matches: bool = False):
    """
    Detecta idioma del texto. Devuelve 'es', 'en' o 'pt'.
    
    Estrategia:
    1. Primero intenta detectar por palabras clave exclusivas (más preciso para frases cortas)
    2. Si no hay coincidencias claras, usa langdetect
    3. Si falla o viene vacío, retorna default
    """
    empty_matches = {'pt': [], 'es': [], 'en': []}
    
    if not text or not text.strip():
        return (default, empty_matches) if return_matches else default

    text_lower = text.lower()
    has_spanish_chars = any(ch in text_lower for ch in SPANISH_UNIQUE_CHARS)
    has_portuguese_chars = any(ch in text_lower for ch in PORTUGUESE_UNIQUE_CHARS)
    
    # 1️⃣ Contar coincidencias con palabras clave de cada idioma
    pt_matches = [marker for marker in PORTUGUESE_MARKERS if marker in text_lower]
    es_matches = [marker for marker in SPANISH_MARKERS if marker in text_lower]
    en_matches = [marker for marker in ENGLISH_MARKERS if marker in text_lower]
    
    pt_count = len(pt_matches)
    es_count = len(es_matches)
    en_count = len(en_matches)
    
    if pt_matches:
        print(f"🇧🇷 [LANG] Markers PT detectados: {pt_matches}")
    if es_matches:
        print(f"🇪🇸 [LANG] Markers ES detectados: {es_matches}")
    if en_matches:
        print(f"🇬🇧 [LANG] Markers EN detectados: {en_matches}")
    
    # 2️⃣ Si hay coincidencias claras, retornar el idioma con más coincidencias
    max_count = max(pt_count, es_count, en_count)
    
    def finalize(result_lang: str):
        if return_matches:
            return result_lang, {
                'pt': pt_matches,
                'es': es_matches,
                'en': en_matches
            }
        return result_lang
    
    if max_count > 0:
        if pt_count == max_count and pt_count > es_count:
            print(f"🇧🇷 [LANG] Portugués detectado por keywords (score: {pt_count})")
            return finalize("pt")
        elif es_count == max_count and es_count > pt_count:
            print(f"🇪🇸 [LANG] Español detectado por keywords (score: {es_count})")
            return finalize("es")
        elif en_count == max_count and en_count > max(pt_count, es_count):
            print(f"🇬🇧 [LANG] Inglés detectado por keywords (score: {en_count})")
            return finalize("en")

    # 3️⃣ Si no hay coincidencias claras o hay empate, usar langdetect
    try:
        lang = detect(text)
        print(f"🔍 [LANG] Idioma detectado por librería: {lang}")
        
        # langdetect devuelve 'pt' para portugués de Brasil
        if lang in SUPPORTED:
            return finalize(lang)
        
        # Si detecta algo distinto (ej. 'fr'), usa default
        print(f"⚠️ [LANG] Idioma '{lang}' no soportado, usando default: {default}")
        return finalize(default)
        
    except LangDetectException:
        print(f"⚠️ [LANG] Error en detección, usando default: {default}")
        return finalize(default)
