# src/services/profile_service.py
from typing import Dict, List, Optional
from ..rag.retriever import supabase
from ..utils.keywords_rag import KEYWORDS_BY_CATEGORY

class BabyProfileService:
    """
    Servicio para gestionar el perfil del bebé
    Estructura de tablas:
    - profile_category: Categorías principales (ej: "Sleep and rest")
    - baby_profile: Keys/subcategorías por bebé (vinculado a category_id)
    - baby_profile_value: Valores traducidos (vinculado a profile_id de baby_profile)
    """
    
    # Cache para categorías (evitar múltiples queries)
    _category_cache: Dict[str, str] = {}
    
    @staticmethod
    async def _get_category_id(category_name: str) -> Optional[str]:
        """
        Obtiene el UUID de una categoría desde profile_category.
        Usa cache para evitar múltiples queries.
        
        Args:
            category_name: Nombre de la categoría (ej: 'sleep and rest')
        
        Returns:
            UUID de la categoría o None si no existe
        """
        # Verificar cache primero
        if category_name in BabyProfileService._category_cache:
            return BabyProfileService._category_cache[category_name]
        
        try:
            # Intentar diferentes formatos de capitalización
            # Opciones: 'Sleep and rest', 'Sleep And Rest', 'sleep and rest'
            
            # Primero intentar con capitalize (Sleep and rest)
            db_category_name = category_name.capitalize()
            
            result = supabase.table("profile_category")\
                .select("id, category")\
                .ilike("category", db_category_name)\
                .limit(1)\
                .execute()
            
            # Si no encuentra, intentar con title (Sleep And Rest)
            if not result.data:
                db_category_name = category_name.title()
                result = supabase.table("profile_category")\
                    .select("id, category")\
                    .ilike("category", db_category_name)\
                    .limit(1)\
                    .execute()
            
            # Si aún no encuentra, intentar exacto lowercase
            if not result.data:
                db_category_name = category_name.lower()
                result = supabase.table("profile_category")\
                    .select("id, category")\
                    .ilike("category", db_category_name)\
                    .limit(1)\
                    .execute()
            
            if result.data and len(result.data) > 0:
                category_id = result.data[0]['id']
                actual_name = result.data[0]['category']
                # Guardar en cache
                BabyProfileService._category_cache[category_name] = category_id
                print(f"✅ [PROFILE] Categoría encontrada: '{actual_name}' (ID: {category_id})")
                return category_id
            else:
                print(f"⚠️ [PROFILE] Categoría '{category_name}' no encontrada en profile_category")
                print(f"   Se intentó buscar: '{category_name.capitalize()}', '{category_name.title()}', '{category_name.lower()}'")
                return None
                
        except Exception as e:
            print(f"❌ [PROFILE] Error obteniendo category_id para '{category_name}': {e}")
            return None
    
    @staticmethod
    def _find_keyword_in_dict(field_path: str, category_name: str, lang: str) -> Optional[str]:
        """
        Busca un keyword en el diccionario de una categoría específica siguiendo un path.
        
        Args:
            field_path: Path del campo completo (ej: 'autonomy and development.6_12.coordinacion_y_precision_manual.no_iniciado')
            category_name: Nombre de la categoría (ej: 'autonomy and development')
            lang: Idioma ('es', 'en', 'pt')
        
        Returns:
            El valor del keyword encontrado o None
        """
        # Obtener el diccionario de la categoría para ese idioma
        if lang not in KEYWORDS_BY_CATEGORY:
            print(f"⚠️ [TRANSLATION] Idioma '{lang}' no encontrado en KEYWORDS_BY_CATEGORY")
            return None
        
        if category_name not in KEYWORDS_BY_CATEGORY[lang]:
            print(f"⚠️ [TRANSLATION] Categoría '{category_name}' no encontrada en idioma '{lang}'")
            print(f"   Categorías disponibles: {list(KEYWORDS_BY_CATEGORY[lang].keys())}")
            return None
        
        keywords_dict = KEYWORDS_BY_CATEGORY[lang][category_name]
        
        # El diccionario tiene estructura: {category: {age_range: {field: ...}}}
        # Ejemplo: KEYWORDS_DEVELOPMENT_ES = {"autonomy and development": {"6_12": {...}}}
        # Necesitamos navegar desde la categoría interna
        
        # Navegar el path completo
        parts = field_path.split('.')
        current = keywords_dict
        
        print(f"🔍 [TRANSLATION DEBUG] Lang: {lang}, Path: {field_path}")
        print(f"   Navegando parts: {parts}")
        
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
                print(f"   ✅ Part {i} '{part}' encontrado")
            else:
                print(f"   ❌ Part {i} '{part}' NO encontrado")
                if isinstance(current, dict):
                    print(f"      Keys disponibles: {list(current.keys())[:5]}")
                return None
        
        # Si es una lista, tomar el primer elemento
        if isinstance(current, list) and len(current) > 0:
            result = current[0]
            print(f"   ✅ Resultado (lista): '{result}'")
            return result
        
        result = current if isinstance(current, str) else None
        print(f"   {'✅' if result else '❌'} Resultado (string): '{result}'")
        return result
    
    @staticmethod
    def get_keyword_translations(keyword: str, detected_kw: Dict) -> Dict[str, Optional[str]]:
        """
        Obtiene las traducciones de un keyword detectado buscando en los 3 diccionarios de idiomas.
        
        Args:
            keyword: El keyword detectado en cualquier idioma (ej: 'ciclos cortos', 'short cycles')
            detected_kw: Dict completo del keyword detectado con category, age_range y field
        
        Returns:
            Dict con {'es': valor_es, 'en': valor_en, 'pt': valor_pt}
        """
        # Construir path completo: category.age_range.field
        # ej: 'sleep and rest.0_6.sleepwear.base.short_sleeve_bodysuit'
        category = detected_kw.get('category', '')
        age_range = detected_kw.get('age_range', '')
        field = detected_kw.get('field', '')
        
        full_path = f"{category}.{age_range}.{field}"
        
        # Buscar el valor directamente navegando el path en cada diccionario
        value_es = BabyProfileService._find_keyword_in_dict(full_path, category, 'es')
        value_en = BabyProfileService._find_keyword_in_dict(full_path, category, 'en')
        value_pt = BabyProfileService._find_keyword_in_dict(full_path, category, 'pt')
        
        return {
            'es': value_es,
            'en': value_en,
            'pt': value_pt
        }
    
    @staticmethod
    async def get_or_create_baby_profile(
        baby_id: str,
        category: str,
        profile_key: str
    ) -> Optional[str]:
        """
        Obtiene o crea un registro en baby_profile.
        
        Args:
            baby_id: ID del bebé
            category: Categoría principal (ej: 'sleep and rest')
            profile_key: Key del perfil - puede ser:
                        - Simple: 'sleep_rhythm', 'sleep_location'
                        - Compuesto: 'sleep_location.own_bed', 'sleepwear.base.short_sleeve_bodysuit'
        
        Returns:
            UUID del registro baby_profile o None si falla
        """
        try:
            # 1. Obtener el UUID de la categoría principal
            category_id = await BabyProfileService._get_category_id(category)
            
            if not category_id:
                print(f"❌ [PROFILE] No se pudo obtener category_id para '{category}'")
                return None
            
            # 2. Buscar registro existente en baby_profile
            existing_profile = supabase.table("baby_profile")\
                .select("id")\
                .eq("baby_id", baby_id)\
                .eq("category_id", category_id)\
                .eq("key", profile_key)\
                .limit(1)\
                .execute()
            
            if existing_profile.data:
                profile_id = existing_profile.data[0]["id"]
                print(f"📌 [PROFILE] Usando baby_profile existente: {profile_id} ({category}.{profile_key})")
                return profile_id
            
            # 3. Crear nuevo registro en baby_profile
            new_profile = supabase.table("baby_profile")\
                .insert({
                    "baby_id": baby_id,
                    "category_id": category_id,
                    "key": profile_key
                })\
                .execute()
            
            if not new_profile.data:
                print(f"❌ [PROFILE] Error creando baby_profile para {category}.{profile_key}")
                return None
            
            profile_id = new_profile.data[0]["id"]
            print(f"✅ [PROFILE] Creado baby_profile: {profile_id} ({category}.{profile_key})")
            return profile_id
            
        except Exception as e:
            print(f"❌ [PROFILE] Error en get_or_create_baby_profile: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    async def save_or_update_profile_value(
        baby_profile_id: str,
        value_es: str = None,
        value_en: str = None,
        value_pt: str = None
    ) -> Optional[Dict]:
        """
        Guarda o actualiza valores en baby_profile_value.
        Verifica si el valor ya existe antes de crear uno nuevo.
        
        Args:
            baby_profile_id: UUID del registro en baby_profile
            value_es: Valor en español
            value_en: Valor en inglés
            value_pt: Valor en portugués
        
        Returns:
            Dict con el registro guardado/actualizado o None si falla
        """
        try:
            # 1. Buscar si YA existe este valor específico (por value_es, value_en o value_pt)
            # para evitar duplicados del mismo keyword
            existing_value = None
            
            if value_es:
                check = supabase.table("baby_profile_value")\
                    .select("*")\
                    .eq("baby_profile_id", baby_profile_id)\
                    .eq("value_es", value_es)\
                    .limit(1)\
                    .execute()
                if check.data:
                    existing_value = check.data[0]
            
            if not existing_value and value_en:
                check = supabase.table("baby_profile_value")\
                    .select("*")\
                    .eq("baby_profile_id", baby_profile_id)\
                    .eq("value_en", value_en)\
                    .limit(1)\
                    .execute()
                if check.data:
                    existing_value = check.data[0]
            
            if not existing_value and value_pt:
                check = supabase.table("baby_profile_value")\
                    .select("*")\
                    .eq("baby_profile_id", baby_profile_id)\
                    .eq("value_pt", value_pt)\
                    .limit(1)\
                    .execute()
                if check.data:
                    existing_value = check.data[0]
            
            # 2. Preparar datos de valores (solo incluir los que no son None)
            value_data = {}
            if value_es is not None:
                value_data["value_es"] = value_es
            if value_en is not None:
                value_data["value_en"] = value_en
            if value_pt is not None:
                value_data["value_pt"] = value_pt
            
            if existing_value:
                # 3a. Actualizar valores existentes
                value_id = existing_value["id"]
                
                result = supabase.table("baby_profile_value")\
                    .update(value_data)\
                    .eq("id", value_id)\
                    .execute()
                
                print(f"✅ [PROFILE] Actualizado baby_profile_value")
                print(f"   ES: {value_es}")
                print(f"   EN: {value_en}")
                print(f"   PT: {value_pt}")
                return result.data[0] if result.data else None
            else:
                # 3b. Crear nuevo valor (permite múltiples valores para el mismo baby_profile_id)
                insert_data = {
                    "baby_profile_id": baby_profile_id,
                    **value_data
                }
                
                result = supabase.table("baby_profile_value")\
                    .insert(insert_data)\
                    .execute()
                
                print(f"✅ [PROFILE] Creado baby_profile_value")
                print(f"   ES: {value_es}")
                print(f"   EN: {value_en}")
                print(f"   PT: {value_pt}")
                return result.data[0] if result.data else None
                
        except Exception as e:
            print(f"❌ [PROFILE] Error en save_or_update_profile_value: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    async def save_detected_keywords(
        baby_id: str,
        detected_keywords: List[Dict],
        lang: str = 'es'
    ) -> int:
        """
        Guarda múltiples keywords detectados del perfil.
        Automáticamente busca y guarda las traducciones en los 3 idiomas.
        
        Estructura de guardado:
        - baby_profile.key: Guarda solo la subcategoría base (ej: 'sleep_rhythm', 'sensory_profile')
        - baby_profile_value: Permite múltiples valores para el mismo baby_profile_id
        
        Args:
            baby_id: ID del bebé
            detected_keywords: Lista de keywords detectados (de detect_profile_keywords)
                               Formato: [{'category': 'sleep and rest', 'subcategory': 'sleep_rhythm',
                                         'field_key': 'short_cycles', 'field': 'sleep_rhythm.short_cycles',
                                         'keyword': 'ciclos cortos'}, ...]
            lang: Idioma del keyword detectado ('es', 'en', 'pt') - informativo
        
        Returns:
            Número de keywords guardados exitosamente
        """
        saved_count = 0
        
        for kw in detected_keywords:
            category = kw.get('category')  # ej: 'sleep and rest'
            subcategory = kw.get('subcategory')  # ej: 'sleep_rhythm', 'sleepwear'
            field_key = kw.get('field_key')  # ej: 'short_cycles', 'short_sleeve_bodysuit'
            field_path = kw.get('field')  # Path completo (ej: 'sleep_rhythm.short_cycles', 'sleepwear.base.short_sleeve_bodysuit')
            keyword = kw.get('keyword')  # Keyword detectado (ej: 'ciclos cortos')
            
            if not category or not subcategory or not field_key or not field_path:
                print(f"⚠️ [PROFILE] Keyword incompleto, saltando: {kw}")
                continue
            
            # 🌍 Obtener traducciones en los 3 idiomas automáticamente
            translations = BabyProfileService.get_keyword_translations(keyword, kw)
            
            print(f"🌍 [PROFILE] Traducciones para {category}.{field_path}:")
            print(f"   ES: {translations.get('es', 'N/A')}")
            print(f"   EN: {translations.get('en', 'N/A')}")
            print(f"   PT: {translations.get('pt', 'N/A')}")
            
            # 1️⃣ Obtener o crear baby_profile con solo la subcategoría base
            # Esto permite agrupar múltiples keywords bajo la misma categoría
            baby_profile_id = await BabyProfileService.get_or_create_baby_profile(
                baby_id=baby_id,
                category=category,
                profile_key=subcategory  # Solo subcategoría (ej: 'sleep_rhythm', 'sensory_profile')
            )
            
            if not baby_profile_id:
                print(f"❌ [PROFILE] No se pudo crear/obtener baby_profile para {category}.{subcategory}")
                continue
            
            # 2️⃣ Guardar el valor en baby_profile_value
            # La lógica actualizada permite múltiples valores para el mismo baby_profile_id
            result = await BabyProfileService.save_or_update_profile_value(
                baby_profile_id=baby_profile_id,
                value_es=translations.get('es'),
                value_en=translations.get('en'),
                value_pt=translations.get('pt')
            )
            
            if result:
                saved_count += 1
        
        if saved_count > 0:
            print(f"✅ [PROFILE] Total guardados/actualizados: {saved_count} keywords en 3 idiomas")
        
        return saved_count
    
    @staticmethod
    async def get_baby_profile(baby_id: str) -> List[Dict]:
        """
        Obtiene todo el perfil de un bebé.
        
        Args:
            baby_id: ID del bebé
        
        Returns:
            Lista de registros del perfil
        """
        try:
            result = supabase.table("baby_profile")\
                .select("*")\
                .eq("baby_id", baby_id)\
                .execute()
            
            return result.data or []
        except Exception as e:
            print(f"❌ [PROFILE] Error obteniendo perfil: {e}")
            return []
    
    @staticmethod
    async def get_profile_by_category(baby_id: str, category: str) -> List[Dict]:
        """
        Obtiene registros de una categoría específica del perfil.
        
        Args:
            baby_id: ID del bebé
            category: Categoría a filtrar (ej: 'sleep_rhythm')
        
        Returns:
            Lista de registros de esa categoría
        """
        try:
            result = supabase.table("baby_profile")\
                .select("*")\
                .eq("baby_id", baby_id)\
                .eq("category_id", category)\
                .execute()
            
            return result.data or []
        except Exception as e:
            print(f"❌ [PROFILE] Error obteniendo categoría {category}: {e}")
            return []
    
    @staticmethod
    def format_profile_for_context(profile_data: List[Dict]) -> str:
        """
        Formatea los datos del perfil para incluir en el contexto del sistema.
        
        Args:
            profile_data: Lista de registros del perfil
        
        Returns:
            String formateado para el contexto
        """
        if not profile_data:
            return ""
        
        # Agrupar por categoría
        by_category = {}
        for item in profile_data:
            category = item.get('category_id', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(item)
        
        context_parts = ["\n📋 PERFIL DEL BEBÉ:"]
        
        for category, items in by_category.items():
            context_parts.append(f"\n🔹 {category.upper()}:")
            for item in items:
                key = item.get('key')
                # Mostrar valor en español primero, luego inglés, luego portugués
                value = item.get('value_es') or item.get('value_en') or item.get('value_pt') or 'N/A'
                context_parts.append(f"   • {key}: {value}")
        
        return "\n".join(context_parts)
