# src/services/profile_service.py
from typing import Dict, List, Optional
from ..rag.retriever import supabase
from ..utils.keywords_rag import KEYWORDS_PROFILE_ES, KEYWORDS_PROFILE_EN, KEYWORDS_PROFILE_PT

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
    def _find_keyword_in_dict(field_path: str, keywords_dict: Dict) -> Optional[str]:
        """
        Busca un keyword en un diccionario de keywords anidado siguiendo un path.
        
        Args:
            field_path: Path del campo (ej: 'sleep and rest.0_6.sleep_rhythm.short_cycles')
            keywords_dict: Diccionario de keywords (KEYWORDS_PROFILE_ES/EN/PT)
        
        Returns:
            El valor del keyword encontrado o None
        """
        parts = field_path.split('.')
        current = keywords_dict
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
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
        value_es = BabyProfileService._find_keyword_in_dict(full_path, KEYWORDS_PROFILE_ES)
        value_en = BabyProfileService._find_keyword_in_dict(full_path, KEYWORDS_PROFILE_EN)
        value_pt = BabyProfileService._find_keyword_in_dict(full_path, KEYWORDS_PROFILE_PT)
        
        return {
            'es': value_es,
            'en': value_en,
            'pt': value_pt
        }
    
    @staticmethod
    async def save_or_update_profile_keyword(
        baby_id: str, 
        category: str,
        subcategory: str,
        field_key: str,
        field_path: str = None,  # ← NUEVO: path completo (ej: 'sleepwear.base.short_sleeve_bodysuit')
        value_es: str = None,
        value_en: str = None,
        value_pt: str = None
    ) -> Optional[Dict]:
        """
        Guarda o actualiza un keyword del perfil.
        Estructura:
        1. Busca/crea registro en baby_profile con (baby_id, category_id, key=field_path)
        2. Busca/crea/actualiza registro en baby_profile_value con los valores traducidos
        
        IMPORTANTE: Ahora soporta campos anidados usando field_path.
        Para estructuras simples: key = subcategory (ej: 'sleep_rhythm')
        Para estructuras anidadas: key = field_path (ej: 'sleepwear.base.short_sleeve_bodysuit')
        
        Args:
            baby_id: ID del bebé
            category: Categoría principal (ej: 'sleep and rest')
            subcategory: Subcategoría (ej: 'sleep_rhythm', 'sleepwear')
            field_key: Clave específica (ej: 'short_cycles', 'short_sleeve_bodysuit')
            field_path: Path completo del campo (ej: 'sleepwear.base.short_sleeve_bodysuit')
                       Si no se provee, usa subcategory como fallback
            value_es: Valor en español
            value_en: Valor en inglés
            value_pt: Valor en portugués
        
        Returns:
            Dict con el registro guardado/actualizado en baby_profile_value o None si falla
        """
        try:
            # 1. Obtener el UUID de la categoría principal
            category_id = await BabyProfileService._get_category_id(category)
            
            if not category_id:
                print(f"❌ [PROFILE] No se pudo obtener category_id para '{category}'")
                return None
            
            # 2. Determinar el key a usar en baby_profile
            # Si hay field_path y contiene puntos (estructura anidada), usar el path completo
            # Si no, usar subcategory para mantener compatibilidad con estructura simple
            if field_path and '.' in field_path:
                # Estructura anidada: usar path completo
                profile_key = field_path  # ej: 'sleepwear.base.short_sleeve_bodysuit'
                print(f"📊 [PROFILE] Usando field_path anidado: {profile_key}")
            else:
                # Estructura simple: usar subcategoría
                profile_key = subcategory  # ej: 'sleep_rhythm'
                print(f"📊 [PROFILE] Usando subcategory simple: {profile_key}")
            
            # 3. Buscar o crear registro en baby_profile
            existing_profile = supabase.table("baby_profile")\
                .select("id")\
                .eq("baby_id", baby_id)\
                .eq("category_id", category_id)\
                .eq("key", profile_key)\
                .limit(1)\
                .execute()
            
            if existing_profile.data:
                profile_id = existing_profile.data[0]["id"]
                print(f"📌 [PROFILE] Usando baby_profile existente: {profile_id}")
            else:
                # Crear nuevo registro en baby_profile
                new_profile = supabase.table("baby_profile")\
                    .insert({
                        "baby_id": baby_id,
                        "category_id": category_id,
                        "key": profile_key  # Ahora puede ser 'sleep_rhythm' o 'sleepwear.base.short_sleeve_bodysuit'
                    })\
                    .execute()
                
                if not new_profile.data:
                    print(f"❌ [PROFILE] Error creando baby_profile para {category}.{profile_key}")
                    return None
                
                profile_id = new_profile.data[0]["id"]
                print(f"✅ [PROFILE] Creado baby_profile: {profile_id} ({category}.{profile_key})")
            
            # 4. Buscar o crear/actualizar registro en baby_profile_value
            existing_value = supabase.table("baby_profile_value")\
                .select("*")\
                .eq("profile_id", profile_id)\
                .limit(1)\
                .execute()
            
            # Preparar datos de valores
            value_data = {}
            if value_es is not None:
                value_data["value_es"] = value_es
            if value_en is not None:
                value_data["value_en"] = value_en
            if value_pt is not None:
                value_data["value_pt"] = value_pt
            
            if existing_value.data:
                # Actualizar valores existentes
                value_id = existing_value.data[0]["id"]
                
                result = supabase.table("baby_profile_value")\
                    .update(value_data)\
                    .eq("id", value_id)\
                    .execute()
                
                print(f"✅ [PROFILE] Actualizado baby_profile_value: {category}.{profile_key}")
                print(f"   ES: {value_es}")
                print(f"   EN: {value_en}")
                print(f"   PT: {value_pt}")
                return result.data[0] if result.data else None
            else:
                # Crear nuevo valor
                insert_data = {
                    "profile_id": profile_id,
                    **value_data
                }
                
                result = supabase.table("baby_profile_value")\
                    .insert(insert_data)\
                    .execute()
                
                print(f"✅ [PROFILE] Creado baby_profile_value: {category}.{profile_key}")
                print(f"   ES: {value_es}")
                print(f"   EN: {value_en}")
                print(f"   PT: {value_pt}")
                return result.data[0] if result.data else None
                
        except Exception as e:
            print(f"❌ [PROFILE] Error guardando/actualizando {category}.{subcategory}.{field_key}: {e}")
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
        
        Args:
            baby_id: ID del bebé
            detected_keywords: Lista de keywords detectados (de detect_profile_keywords)
                               Formato: [{'category': 'sleep and rest', 'subcategory': 'sleep_rhythm',
                                         'field_key': 'short_cycles', 'field': 'sleep and rest.0_6.sleep_rhythm.short_cycles',
                                         'keyword': 'ciclos cortos'}, ...]
            lang: Idioma del keyword detectado ('es', 'en', 'pt') - informativo
        
        Returns:
            Número de keywords guardados exitosamente
        """
        saved_count = 0
        
        for kw in detected_keywords:
            category = kw.get('category')  # ej: 'sleep and rest'
            subcategory = kw.get('subcategory')  # ej: 'sleep_rhythm' o 'sleepwear'
            field_key = kw.get('field_key')  # ej: 'short_cycles' o 'short_sleeve_bodysuit'
            field_path = kw.get('field')  # Path desde subcategoría (ej: 'sleepwear.base.short_sleeve_bodysuit')
            keyword = kw.get('keyword')  # Keyword detectado (ej: 'con body de manga corta')
            
            if not category or not subcategory or not field_key or not field_path:
                print(f"⚠️ [PROFILE] Keyword incompleto, saltando: {kw}")
                continue
            
            # 🌍 Obtener traducciones en los 3 idiomas automáticamente
            # Pasar el dict completo para que pueda construir el path completo
            translations = BabyProfileService.get_keyword_translations(keyword, kw)
            
            print(f"🌍 [PROFILE] Traducciones para {category}.{field_path}:")
            print(f"   ES: {translations.get('es', 'N/A')}")
            print(f"   EN: {translations.get('en', 'N/A')}")
            print(f"   PT: {translations.get('pt', 'N/A')}")
            
            # Guardar con los valores en los 3 idiomas
            result = await BabyProfileService.save_or_update_profile_keyword(
                baby_id=baby_id,
                category=category,  # 'sleep and rest'
                subcategory=subcategory,  # 'sleep_rhythm' o 'sleepwear'
                field_key=field_key,  # 'short_cycles' o 'short_sleeve_bodysuit'
                field_path=field_path,  # 'sleep_rhythm' o 'sleepwear.base.short_sleeve_bodysuit'
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
