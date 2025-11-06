# ============================================================================
# Imports de diccionarios de keywords por categoría e idioma
# ============================================================================
from .keywords.sleep_and_rest.keyword_sleep_and_rest_ES import KEYWORDS_SLEEP_ES
from .keywords.sleep_and_rest.keyword_sleep_and_rest_EN import KEYWORDS_SLEEP_EN
from .keywords.sleep_and_rest.keyword_sleep_and_rest_PT import KEYWORDS_SLEEP_PT

# TODO: Importar cuando estén listos
from .keywords.daily_care.keywords_daily_care_ES import KEYWORDS_DAILY_CARE_ES
from .keywords.daily_care.keywords_daily_care_EN import KEYWORDS_DAILY_CARE_EN
from .keywords.daily_care.keywords_daily_care_PT import KEYWORDS_DAILY_CARE_PT

from .keywords.autonomy_and_development.keywords_autonomy_and_development_ES import KEYWORDS_DEVELOPMENT_ES
from .keywords.autonomy_and_development.keywords_autonomy_and_development_EN import KEYWORDS_DEVELOPMENT_EN
from .keywords.autonomy_and_development.keywords_autonomy_and_development_PT import KEYWORDS_DEVELOPMENT_PT

# from .keywords.emotions_bond_and_parenting.keywords_emotions_bond_and_parenting_ES import KEYWORDS_EMOTIONS_ES
# from .keywords.emotions_bond_and_parenting.keywords_emotions_bond_and_parenting_EN import KEYWORDS_EMOTIONS_EN
# from .keywords.emotions_bond_and_parenting.keywords_emotions_bond_and_parenting_PT import KEYWORDS_EMOTIONS_PT

# from .keywords.family_context_and_enviroment.keywords_family_context_and_enviroment_ES import KEYWORDS_FAMILY_ES
# from .keywords.family_context_and_enviroment.keywords_family_context_and_enviroment_EN import KEYWORDS_FAMILY_EN
# from .keywords.family_context_and_enviroment.keywords_family_context_and_enviroment_PT import KEYWORDS_FAMILY_PT

# from .keywords.travel_and_mobility.keywords_travel_and_mobility_ES import KEYWORDS_TRAVEL_ES
# from .keywords.travel_and_mobility.keywords_travel_and_mobility_EN import KEYWORDS_TRAVEL_EN
# from .keywords.travel_and_mobility.keywords_travel_and_mobility_PT import KEYWORDS_TRAVEL_PT

# Diccionario consolidado de todas las categorías por idioma
KEYWORDS_BY_CATEGORY = {
    'es': {
        'sleep and rest': KEYWORDS_SLEEP_ES,
        'daily cares': KEYWORDS_DAILY_CARE_ES,
        'autonomy and development': KEYWORDS_DEVELOPMENT_ES,
        # 'emotions bonds and parenting': KEYWORDS_EMOTIONS_ES,
        # 'family context and environment': KEYWORDS_FAMILY_ES,
        # 'travel and mobility': KEYWORDS_TRAVEL_ES,
    },
    'en': {
        'sleep and rest': KEYWORDS_SLEEP_EN,
        'daily cares': KEYWORDS_DAILY_CARE_EN,
        'autonomy and development': KEYWORDS_DEVELOPMENT_EN,
        # 'emotions bonds and parenting': KEYWORDS_EMOTIONS_EN,
        # 'family context and environment': KEYWORDS_FAMILY_EN,
        # 'travel and mobility': KEYWORDS_TRAVEL_EN,
    },
    'pt': {
        'sleep and rest': KEYWORDS_SLEEP_PT,
        'daily cares': KEYWORDS_DAILY_CARE_PT,
        'autonomy and development': KEYWORDS_DEVELOPMENT_PT,
        # 'emotions bonds and parenting': KEYWORDS_EMOTIONS_PT,
        # 'family context and environment': KEYWORDS_FAMILY_PT,
        # 'travel and mobility': KEYWORDS_TRAVEL_PT,
    }
}

# ============================================================================
# Keywords para RAG (búsqueda de documentos)
# ============================================================================
keywords = {
    # 🇪🇸 ESPAÑOL ============================================================

    # 🧠 DISCIPLINA Y LÍMITES
    'disciplina': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'limites': ['limites.pdf', 'libertad.pdf'],
    'normas': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'reglas': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'obediencia': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'autoridad': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],

    # 🚫 CASTIGOS Y CONSECUENCIAS
    'castigos': ['disciplina_sin_lagrimas.pdf'],
    'consecuencias': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'regaños': ['disciplina_sin_lagrimas.pdf'],
    'correcciones': ['disciplina_sin_lagrimas.pdf'],

    # 😡 RABIETAS Y EMOCIONES INTENSAS
    'rabietas': ['disciplina_sin_lagrimas.pdf'],
    'berrinches': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'pataletas': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'frustracion': ['emociones.pdf', 'disciplina_sin_lagrimas.pdf'],

    # ⚔️ CONFLICTOS / CELOS / HERMANOS
    'conflictos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'hermanos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'celos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
    'rivalidad': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'peleas': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
    'discusiones': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'compartir': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'territorialidad': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
    'juguetes': ['el_cerebro_del_nino.pdf', 'emociones.pdf'],
    'posesion': ['el_cerebro_del_nino.pdf', 'emociones.pdf'],

    # 🧩 SOBREESTIMULACIÓN / EXCESOS
    'sobreestimulacion': ['simplicity_parenting.pdf'],
    'exceso': ['simplicity_parenting.pdf', 'limites.pdf', 'el_cerebro_del_nino.pdf'],
    'saturacion': ['simplicity_parenting.pdf'],
    'estres': ['simplicity_parenting.pdf', 'emociones.pdf'],
    'demasiado': ['simplicity_parenting.pdf'],

    # 🕒 RUTINA Y ACTIVIDADES
    'rutina': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'habitos': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'horarios': ['rutina_del_bebe.pdf'],
    'actividades': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf', 'el_cerebro_del_nino.pdf'],
    'estructura': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf'],

    # 🌙 SUEÑO / DESCANSO
    'sueño': ['sueño_infantil.pdf'],
    'dormir': ['sueño_infantil.pdf', 'bedtime.pdf', 'dormir_en_su_cuna.pdf'],
    'siestas': ['sueño_infantil.pdf', 'siestas.pdf'],
    'despertares': ['sueño_infantil.pdf', 'alteraciones_del_sueño.pdf'],
    'cuna': ['sueño_infantil.pdf', 'dormir_en_su_cuna.pdf'],
    'destete nocturno': ['sueño_infantil.pdf', 'destete_lumi.pdf'],

    # 🍎 ALIMENTACIÓN
    'alimentacion': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'alimentos': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'ingesta': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'comida': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'papillas': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'solidos': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'lactancia': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],

    # ❤️ EMOCIONES / CRIANZA RESPETUOSA
    'emociones': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'crianza respetuosa': ['emociones.pdf', 'libertad.pdf', 'simplicity_parenting.pdf'],
    'respetuosa': ['emociones.pdf', 'libertad.pdf'],
    'vinculo': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'conexion': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'empatia': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],

    # ✈️ VIAJES
    'viajes': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'vacaciones': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'traslados': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'salidas': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'paseos': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'avion': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'auto': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'bus': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],


    # 🇬🇧 ENGLISH ============================================================

    # 🧠 DISCIPLINE AND LIMITS
    'discipline': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'boundaries': ['limites.pdf', 'libertad.pdf'],
    'rules': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'authority': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'obedience': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],

    # 🚫 PUNISHMENT AND CONSEQUENCES
    'punishment': ['disciplina_sin_lagrimas.pdf'],
    'consequences': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'scolding': ['disciplina_sin_lagrimas.pdf'],
    'corrections': ['disciplina_sin_lagrimas.pdf'],

    # 😡 TANTRUMS AND EMOTIONS
    'tantrum': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'meltdown': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'frustration': ['emociones.pdf', 'disciplina_sin_lagrimas.pdf'],

    # ⚔️ CONFLICTS / SIBLINGS
    'conflicts': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'siblings': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'jealousy': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'rivalry': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'fights': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'sharing': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],

    # 🧩 OVERSTIMULATION
    'overstimulation': ['simplicity_parenting.pdf'],
    'overload': ['simplicity_parenting.pdf', 'limites.pdf', 'el_cerebro_del_nino.pdf'],
    'stress': ['simplicity_parenting.pdf', 'emociones.pdf'],
    'too much': ['simplicity_parenting.pdf'],

    # 🕒 ROUTINE
    'routine': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'habits': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'schedule': ['rutina_del_bebe.pdf'],
    'activities': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf', 'el_cerebro_del_nino.pdf'],
    'structure': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf'],

    # 🌙 SLEEP / REST
    'sleepy': ['sueño_infantil.pdf'],
    'sleep': ['sueño_infantil.pdf', 'bedtime.pdf', 'dormir_en_su_cuna.pdf'],
    'nap': ['sueño_infantil.pdf', 'siestas.pdf'],
    'awaken': ['sueño_infantil.pdf', 'alteraciones_del_sueño.pdf'],
    'cradle': ['sueño_infantil.pdf', 'dormir_en_su_cuna.pdf'],
    'night weaning': ['sueño_infantil.pdf', 'destete_lumi.pdf'],

    # 🍎 FEEDING
    'feeding': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'food': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'meals': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'weaning': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],

    # ❤️ EMOTIONS / GENTLE PARENTING
    'emotions': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'gentle parenting': ['emociones.pdf', 'libertad.pdf', 'simplicity_parenting.pdf'],
    'connection': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'bond': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'empathy': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],

    # ✈️ TRAVEL
    'travel': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'vacation': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'trip': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'car ride': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'airplane': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'bus ride': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],


    # 🇧🇷 PORTUGUÊS (BRASIL) =================================================

    # 🧠 DISCIPLINA E LIMITES
    'disciplina (pt)': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'limites (pt)': ['limites.pdf', 'libertad.pdf'],
    'regras': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'autoridade': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
    'obediência': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],

    # 🚫 CASTIGO E CONSEQUÊNCIAS
    'castigo': ['disciplina_sin_lagrimas.pdf'],
    'consequências': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
    'bronca': ['disciplina_sin_lagrimas.pdf'],
    'correções': ['disciplina_sin_lagrimas.pdf'],

    # 😡 BIRRAS E EMOÇÕES INTENSAS
    'birra': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'pirraça': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
    'frustração': ['emociones.pdf', 'disciplina_sin_lagrimas.pdf'],

    # ⚔️ CONFLITOS / CIÚMES / IRMÃOS
    'conflitos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'irmãos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'ciúmes': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'rivalidade': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'brigas': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'compartilhar': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],

    # 🧩 SOBRESTIMULAÇÃO / EXCESSOS
    'superestimulação': ['simplicity_parenting.pdf'],
    'excesso': ['simplicity_parenting.pdf', 'limites.pdf', 'el_cerebro_del_nino.pdf'],
    'estresse': ['simplicity_parenting.pdf', 'emociones.pdf'],
    'muito': ['simplicity_parenting.pdf'],

    # 🕒 ROTINA E ATIVIDADES
    'rotina': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'hábitos': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
    'horários': ['rutina_del_bebe.pdf'],
    'atividades': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf', 'el_cerebro_del_nino.pdf'],
    'estrutura': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf'],

    # 🌙 SONO / DESCANSO
    'sono': ['sueño_infantil.pdf'],
    'dormir': ['sueño_infantil.pdf', 'bedtime.pdf', 'dormir_en_su_cuna.pdf'],
    'soneca': ['sueño_infantil.pdf', 'siestas.pdf'],
    'acordar': ['sueño_infantil.pdf', 'alteraciones_del_sueño.pdf'],
    'berço': ['sueño_infantil.pdf', 'dormir_en_su_cuna.pdf'],
    'desmame noturno': ['sueño_infantil.pdf', 'destete_lumi.pdf'],

    # 🍎 ALIMENTAÇÃO / COMIDA
    'alimentação': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'comida (pt)': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'papinhas': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
    'desmame': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],

    # ❤️ EMOÇÕES / CRIAÇÃO AFETIVA
    'emoções': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'criação respeitosa': ['emociones.pdf', 'libertad.pdf', 'simplicity_parenting.pdf'],
    'vínculo': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'conexão': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
    'empatia': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],

    # ✈️ VIAGENS / DESLOCAMENTOS
    'viagem': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'férias': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'passeio': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'carro': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'avião': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    'ônibus': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
}


# ============================================================================
# 📋 TEMPLATE DETECTION KEYWORDS (Separado de RAG keywords)
# ============================================================================
TEMPLATE_KEYWORDS = {
    # 📅 RUTINAS / ROUTINE / ROTINA
    'routine_template': {
        'es': ['rutina', 'organizar', 'horarios', 'estructura', 'día completo'],
        'en': ['routine', 'organize', 'schedule', 'structure', 'full day'],
        'pt': ['rotina', 'estrutura']
    },
    
    # 🍎 IDEAS CREATIVAS DE ALIMENTOS / CREATIVE FOOD IDEAS
    'creative_food_template': {
        'es': ['ideas creativas', 'presentar', 'verduras', 'alimentos', 'menú', 'comida'],
        'en': ['creative ideas', 'present', 'vegetables', 'food', 'menu', 'meals'],
        'pt': ['ideias criativas', 'apresentar', 'vegetais', 'cardápio', 'comida']
    },
    
    # ✈️ VIAJES CON NIÑOS / TRAVEL WITH CHILDREN
    'travel_template': {
        'es': ['viajar', 'viajes', 'viaje', 'destino', 'destinos', 'vacaciones', 'mochila', 'maleta'],
        'en': ['travel', 'travels', 'trip', 'destination', 'destinations', 'vacation', 'backpack', 'suitcase'],
        'pt': ['viagens', 'viagem', 'férias', 'mala']
    },
    
    # 🤱 DESTETE Y LACTANCIA / WEANING AND BREASTFEEDING
    'weaning_template': {
        'es': ['destete', 'reducir tomas', 'dejar pecho', 'tomas nocturnas', 'descansar mejor', 
               'transición lactancia', 'lactancia', 'pecho', 'mamar', 'teta'],
        'en': ['weaning', 'reduce feedings', 'stop breastfeeding', 'night feedings', 'sleep better',
               'breastfeeding transition', 'breastfeeding', 'breast', 'nursing', 'nurse'],
        'pt': ['desmame', 'reduzir mamadas', 'parar amamentação', 'mamadas noturnas', 'dormir melhor',
               'transição amamentação', 'amamentação', 'peito', 'mamar', 'mama']
    },
    
    # 📚 REFERENCIAS / REFERENCES / REFERÊNCIAS
    'references_template': {
        'es': ['fuentes', 'referencias', 'bibliografía', 'origen de la información', 
               'de dónde sacaste', 'dónde obtuviste', 'qué fuentes', 'basado en qué'],
        'en': ['sources', 'references', 'bibliography', 'origin of information',
               'where did you get', 'where did you obtain', 'what sources', 'based on what'],
        'pt': ['fontes', 'origem da informação',
               'de onde você tirou', 'onde você obteve', 'quais fontes', 'baseado em quê']
    }
    
}

# Mapeo de template_key a archivo de template
TEMPLATE_FILES = {
    'routine_template': 'template_rutinas.md',
    'creative_food_template': 'template_ideas_creativas_alimentos.md',
    'travel_template': 'travel_with_children.md',
    'weaning_template': 'template_destete_lactancia.md',
    'references_template': 'template_referencias.md'
}

# ============================================================================
# 🔍 FUNCIONES DE DETECCIÓN DE KEYWORDS DEL PERFIL
# ============================================================================

def get_age_range_key(age_months: int) -> str:
    """
    Retorna la clave del rango de edad según los meses del bebé.
    
    Args:
        age_months: Edad del bebé en meses
    
    Returns:
        String con el rango de edad ('0_6', '6_12', '12_24', '24_48', '48_84')
    """
    if age_months <= 6:
        return '0_6', '0_84'
    elif age_months <= 12:
        return '6_12', '0_84'
    elif age_months <= 24:
        return '12_24', '0_84'
    elif age_months <= 48:
        return '24_48', '0_84'
    else:
        return '48_84', '0_84'


def get_age_appropriate_categories(age_months: int) -> set:
    """
    Retorna las categorías principales permitidas según la edad del bebé.
    Con la nueva estructura jerárquica, todas las categorías están disponibles,
    pero filtradas por rango de edad dentro de cada categoría.
    
    Args:
        age_months: Edad del bebé en meses
    
    Returns:
        Set con las categorías principales disponibles (siempre todas para la nueva estructura)
    """
    # ⚠️ Si age_months es None o inválido, NO permitir nada por seguridad
    if age_months is None or age_months < 0:
        print(f"[AGE FILTER] Edad inválida ({age_months}), retornando set vacío")
        return set()
    
    age_ranges = get_age_range_key(age_months)  # Retorna tupla: ('6_12', '0_84')
    print(f"[AGE FILTER] {age_months} meses -> Rangos: {age_ranges}")
    
    # Con la nueva estructura, retornamos todas las categorías principales
    # El filtro de edad se aplica automáticamente porque cada categoría tiene sus propios rangos
    # IMPORTANTE: Usar las claves en inglés (sin guiones bajos) que están en los diccionarios
    return {
        'sleep and rest',
        'daily cares',
        'autonomy and development',
        'emotions bonds and parenting',
        'family context and environment',
        'travel and mobility'
    }


def detect_profile_keywords(message: str, lang: str = 'es', verbose: bool = True, age_months: int = None) -> list:
    """
    Detecta keywords del perfil del bebé en el mensaje del usuario.
    Ahora con estructura jerárquica: categoria_principal > rango_edad > subcategoría > keywords
    
    IMPORTANTE: Busca en los 3 idiomas (ES, EN, PT) simultáneamente para evitar problemas
    de detección de idioma incorrecta.
    
    Args:
        message: El mensaje del usuario
        lang: Idioma detectado ('es', 'en', 'pt') - usado solo para informar, busca en todos
        verbose: Si es True, imprime en consola cada keyword detectado
        age_months: Edad del bebé en meses (REQUERIDO). Si no se provee, no detecta nada.
    
    Returns:
        Lista de diccionarios con información de keywords encontradas
        Formato: [{'category': str, 'age_range': str, 'field': str, 'field_key': str, 'keyword': str}, ...]
    """
    if verbose:
        print(f"🔍 [PROFILE DETECT] Iniciando detección...")
        print(f"   Mensaje: '{message[:100]}'")
        print(f"   Edad: {age_months} meses")
        print(f"   Categorías disponibles: {list(KEYWORDS_BY_CATEGORY.get('es', {}).keys())}")
    
    detected_keywords = []
    detected_categories = set()
    message_lower = message.lower()
    
    # ⚠️ Si no hay edad, retornar lista vacía (no detectar nada por seguridad)
    if age_months is None:
        if verbose:
            print(f"❌ [AGE FILTER] No hay edad del bebé disponible, NO se detectarán keywords del perfil")
            print(f"   SOLUCIÓN: Asegúrate de que el bebé tiene una fecha de nacimiento registrada")
        return []
    
    # Obtener rangos de edad (específico + común 0_84) y categorías permitidas
    age_ranges = get_age_range_key(age_months)  # Retorna tupla: ('6_12', '0_84')
    allowed_categories = get_age_appropriate_categories(age_months)
    
    if verbose:
        print(f"✅ [AGE FILTER] Edad: {age_months} meses -> Rangos: {age_ranges}")
        print(f"   Categorías permitidas: {allowed_categories}")
    
    # 🌍 Buscar en los 3 idiomas para evitar problemas de detección de idioma
    # Ahora usando KEYWORDS_BY_CATEGORY que tiene keywords específicos por categoría
    
    def search_in_dict(data, category_path="", main_category=None, current_age_range=None, subcategory=None):
        """
        Función recursiva para buscar en diccionarios anidados con estructura jerárquica.
        
        Estructura esperada:
        {
            'sleep and rest': {
                '0_6': {
                    'sleep_rhythm': {
                        'short_cycles': 'ciclos cortos',
                        ...
                    },
                    'sleepwear': {
                        'base': {
                            'short_sleeve_bodysuit': 'con body de manga corta',
                            ...
                        },
                        'mid_layer': {...},
                        ...
                    },
                    ...
                },
                ...
            },
            ...
        }
        
        Soporta niveles anidados ilimitados y los concatena con punto:
        - sleepwear.base.short_sleeve_bodysuit
        - sleepwear.mid_layer.one_piece_sleeper
        """
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{category_path}.{key}" if category_path else key
                
                # Nivel 1: Categoría principal (ej: 'sleep and rest')
                if not main_category:
                    # Es una categoría principal
                    if key in allowed_categories and isinstance(value, dict):
                        # Buscar dentro de esta categoría
                        search_in_dict(value, current_path, main_category=key)
                
                # Nivel 2: Rango de edad (ej: '0_6', '6_12', '0_84')
                elif not current_age_range:
                    # Verificar si es uno de los rangos de edad permitidos (específico o común)
                    if key in age_ranges and isinstance(value, dict):
                        # Este es un rango válido (específico o 0_84), buscar dentro
                        search_in_dict(value, current_path, main_category=main_category, current_age_range=key)
                    elif isinstance(value, dict):
                        # Seguir buscando otros niveles
                        search_in_dict(value, current_path, main_category=main_category, current_age_range=current_age_range)
                
                # Nivel 3+: Subcategorías y keywords (con soporte para anidación profunda)
                else:
                    if isinstance(value, str):
                        # Es un keyword final
                        if value.lower() in message_lower:
                            path_parts = current_path.split('.')
                            # Remover categoría principal y rango de edad del path
                            # path_parts = ['sleep and rest', '0_6', 'sleepwear', 'base', 'short_sleeve_bodysuit']
                            # Queremos: subcategory='sleepwear', field='sleepwear.base.short_sleeve_bodysuit'
                            
                            if len(path_parts) >= 3:
                                # Subcategoría principal (nivel 3)
                                main_subcategory = path_parts[2]
                                
                                # Field completo: concatenar desde subcategoría hasta el final
                                field_path = '.'.join(path_parts[2:])
                                
                                # field_key es la última parte
                                field_key = path_parts[-1]
                                
                                keyword_info = {
                                    'category': main_category,
                                    'age_range': current_age_range,
                                    'subcategory': main_subcategory,
                                    'field': field_path,  # ej: 'sleepwear.base.short_sleeve_bodysuit'
                                    'field_key': field_key,  # ej: 'short_sleeve_bodysuit'
                                    'keyword': value
                                }
                                detected_keywords.append(keyword_info)
                                
                                # Imprimir categoría detectada
                                if verbose:
                                    category_key = f"{main_category}.{main_subcategory}"
                                    if category_key not in detected_categories:
                                        print(f">> {main_category} > {current_age_range} > {main_subcategory}")
                                        detected_categories.add(category_key)
                    
                    elif isinstance(value, dict):
                        # Seguir navegando en niveles más profundos
                        search_in_dict(value, current_path, main_category=main_category, current_age_range=current_age_range, subcategory=subcategory)
                    
                    elif isinstance(value, list):
                        # Lista de keywords
                        for item in value:
                            if isinstance(item, str) and item.lower() in message_lower:
                                path_parts = current_path.split('.')
                                
                                if len(path_parts) >= 3:
                                    main_subcategory = path_parts[2]
                                    field_path = '.'.join(path_parts[2:])
                                    field_key = path_parts[-1]
                                    
                                    keyword_info = {
                                        'category': main_category,
                                        'age_range': current_age_range,
                                        'subcategory': main_subcategory,
                                        'field': field_path,
                                        'field_key': field_key,
                                        'keyword': item
                                    }
                                    detected_keywords.append(keyword_info)
                                    
                                    if verbose:
                                        category_key = f"{main_category}.{main_subcategory}"
                                        if category_key not in detected_categories:
                                            print(f">> {main_category} > {current_age_range} > {main_subcategory}")
                                            detected_categories.add(category_key)
    
    # 🌍 Buscar en todos los idiomas (ES, EN, PT) y todas las categorías
    # Iterar sobre cada idioma y cada categoría dentro de KEYWORDS_BY_CATEGORY
    for lang_code in ['es', 'en', 'pt']:
        if lang_code in KEYWORDS_BY_CATEGORY:
            for category_name, category_keywords in KEYWORDS_BY_CATEGORY[lang_code].items():
                # category_keywords es el diccionario completo de esa categoría
                # Ej: KEYWORDS_SLEEP_ES que contiene {"sleep and rest": {...}}
                search_in_dict(category_keywords)
    
    # Eliminar duplicados (puede que un keyword esté en múltiples idiomas)
    # Usar el campo 'field' como clave única
    unique_keywords = {}
    for kw in detected_keywords:
        field = kw['field']
        if field not in unique_keywords:
            unique_keywords[field] = kw
    
    detected_keywords = list(unique_keywords.values())
    
    return detected_keywords


def print_detected_keywords_summary(detected_keywords: list):
    """
    Imprime un resumen organizado de los keywords detectados.
    
    Args:
        detected_keywords: Lista de keywords detectados (output de detect_profile_keywords)
    """
    if not detected_keywords:
        print("ℹ️  No se detectaron keywords del perfil")
        return
    
    # Agrupar por categoría
    by_category = {}
    for kw in detected_keywords:
        category = kw['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(kw)
    
    print(f"\n{'='*70}")
    print(f"🎯 KEYWORDS DEL PERFIL DETECTADOS: {len(detected_keywords)} matches")
    print(f"{'='*70}")
    
    for category, keywords in by_category.items():
        print(f"\n📁 Categoría: {category.upper()}")
        print(f"   Total en esta categoría: {len(keywords)}")
        
        # Mostrar keywords únicos
        unique_kws = {}
        for kw in keywords:
            if kw['keyword'] not in unique_kws:
                unique_kws[kw['keyword']] = kw['field']
        
        for keyword, field in unique_kws.items():
            print(f"   • {field} → '{keyword}'")
    
    print(f"\n{'='*70}\n")