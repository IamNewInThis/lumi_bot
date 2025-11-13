# src/services/profile_service.py
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..rag.retriever import supabase
from ..extractors.profile_extractor import BabyProfile


class BabyProfileService:
    """
    Servicio centralizado para manejar la persistencia del perfil del bebé:
    - Obtiene o crea registros en baby_profile (por key y categoría)
    - Inserta valores multilingües en baby_profile_value
    - Usa directamente los valores y traducciones del profile_extractor
    """

    _category_cache: Dict[str, str] = {}

    # =========================================================
    # 🔍 UTILIDAD: Obtener categoría
    # =========================================================
    @staticmethod
    async def _get_category_id(category_name: str) -> Optional[str]:
        """Obtiene el ID de la categoría desde profile_category (cacheada)."""
        if category_name in BabyProfileService._category_cache:
            return BabyProfileService._category_cache[category_name]

        try:
            result = (
                supabase.table("profile_category")
                .select("id, category")
                .ilike("category", category_name)
                .limit(1)
                .execute()
            )

            if not result.data:
                print(f"⚠️ [PROFILE] Categoría '{category_name}' no encontrada")
                return None

            category_id = result.data[0]["id"]
            BabyProfileService._category_cache[category_name] = category_id
            return category_id

        except Exception as e:
            print(f"❌ [PROFILE] Error obteniendo category_id: {e}")
            return None

    # =========================================================
    # 🧩 Guardar cualquier campo del perfil
    # =========================================================
    @staticmethod
    async def save_profile_field(
        baby_id: str,
        category_name: str,
        field_key: str,
        field_data: Dict[str, Any],
        min_confidence: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Guarda o actualiza el campo del perfil del bebé.
        Si ya existe un valor previo para ese campo, lo actualiza en lugar de crear uno nuevo.
        """
        try:
            if not field_data or not field_data.get("key"):
                print(f"⚠️ [PROFILE] Campo '{field_key}' sin datos válidos, se omite.")
                return None

            confidence = field_data.get("confidence", 1.0)
            if confidence < min_confidence:
                print(f"⚠️ [PROFILE] Confianza baja ({confidence}) para '{field_key}', no se guarda.")
                return None

            # 1️⃣ Obtener categoría
            category_id = await BabyProfileService._get_category_id(category_name)
            if not category_id:
                print(f"❌ [PROFILE] No se encontró categoría '{category_name}'")
                return None

            # 2️⃣ Buscar o crear baby_profile
            existing_profile = (
                supabase.table("baby_profile")
                .select("id")
                .eq("baby_id", baby_id)
                .eq("category_id", category_id)
                .eq("key", field_key)
                .limit(1)
                .execute()
            )

            if existing_profile.data:
                baby_profile_id = existing_profile.data[0]["id"]
            else:
                result = (
                    supabase.table("baby_profile")
                    .insert(
                        {
                            "baby_id": baby_id,
                            "category_id": category_id,
                            "key": field_key,
                            "created_at": datetime.utcnow().isoformat() + "+00",
                            "updated_at": datetime.utcnow().isoformat() + "+00",
                        }
                    )
                    .execute()
                )
                baby_profile_id = result.data[0]["id"]

            # 3️⃣ Preparar datos de traducción
            translations = {
                "value_es": field_data.get("value_es"),
                "value_en": field_data.get("value_en"),
                "value_pt": field_data.get("value_pt"),
                "updated_at": datetime.utcnow().isoformat() + "+00",
            }

            # 4️⃣ Buscar si ya existe un valor previo
            existing_value = (
                supabase.table("baby_profile_value")
                .select("id")
                .eq("baby_profile_id", baby_profile_id)
                .limit(1)
                .execute()
            )

            if existing_value.data:
                # 🔄 Actualizar valor existente
                value_id = existing_value.data[0]["id"]
                updated = (
                    supabase.table("baby_profile_value")
                    .update(translations)
                    .eq("id", value_id)
                    .execute()
                )
                print(f"🔄 [PROFILE] Actualizado '{field_key}' = {translations['value_es']}")
                return updated.data[0] if updated.data else None
            else:
                # 🆕 Insertar nuevo valor
                inserted = (
                    supabase.table("baby_profile_value")
                    .insert({"baby_profile_id": baby_profile_id, **translations})
                    .execute()
                )
                print(f"✅ [PROFILE] Guardado '{field_key}' = {translations['value_es']}")
                return inserted.data[0] if inserted.data else None

        except Exception as e:
            print(f"❌ [PROFILE] Error guardando '{field_key}': {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _build_field_data_from_text(field_name: str, value: str) -> Optional[Dict[str, Any]]:
        """Convierte un string simple en el formato esperado por save_profile_field."""
        if not value:
            return None

        normalized_value = value.strip()
        if not normalized_value:
            return None

        return {
            "key": field_name,
            "value_es": normalized_value,
            "value_en": normalized_value,
            "value_pt": normalized_value,
        }


    # =========================================================
    # 🚀 Guardar todo el perfil del extractor
    # =========================================================
    @staticmethod
    async def process_profile_extraction(baby_id: str, profile: BabyProfile):
        """
        Procesa un objeto completo de BabyProfile y guarda cada campo detectado.
        Usa las traducciones y confianza devueltas por el extractor.
        """
        print("🚀 [PROFILE] Procesando extracción del perfil...")

        # Mapear los campos a categorías
        FIELD_CATEGORY_MAP = {
            "sleep_location": "sleep and rest",
            "sleep_room": "sleep and rest",
            "feeding_method": "feeding",
            "temperament": "behavior",
        }

        saved = 0

        # Iterar sobre cada atributo del modelo (pueden ser más en el futuro)
        for field_name, field_value in profile.model_dump().items():
            if field_name == "confidence":
                continue

            if not field_value:
                continue

            category = FIELD_CATEGORY_MAP.get(field_name)
            if not category:
                print(f"⚠️ [PROFILE] No hay categoría definida para '{field_name}'")
                continue

            if isinstance(field_value, dict):
                normalized_field = field_value
            elif isinstance(field_value, str):
                normalized_field = BabyProfileService._build_field_data_from_text(field_name, field_value)
            else:
                normalized_field = None

            if not normalized_field:
                print(f"⚠️ [PROFILE] Campo '{field_name}' no tiene datos detallados utilizables.")
                continue

            result = await BabyProfileService.save_profile_field(
                baby_id=baby_id,
                category_name=category,
                field_key=field_name,
                field_data=normalized_field,
                min_confidence=0.7,
            )
            if result:
                saved += 1

        print(f"✅ [PROFILE] Campos guardados: {saved}")
        return saved
