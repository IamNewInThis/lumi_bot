# src/services/profile_service.py
from typing import Dict, List, Optional, Any
import unicodedata
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
    _DEFAULT_CONFIDENCE = 0.85
    _VALUE_TRANSLATIONS: Dict[str, Dict[str, Dict[str, str]]] = {
        "sleep_location": {
            "crib": {"es": "cuna", "en": "crib", "pt": "berço"},
            "family_bed": {"es": "cama compartida con los padres", "en": "family bed", "pt": "cama compartilhada com os pais"},
            "shared_bed": {"es": "cama compartida", "en": "shared bed", "pt": "cama compartilhada"},
            "own_bed": {"es": "su propia cama", "en": "own bed", "pt": "cama própria"},
            "bassinet": {"es": "moisés", "en": "bassinet", "pt": "moisés"},
            "floor_mattress": {"es": "colchón en el piso", "en": "floor mattress", "pt": "colchão no chão"},
            "low_bed": {"es": "cama baja", "en": "low bed", "pt": "cama baixa"},
            "regular_bed": {"es": "cama regular", "en": "regular bed", "pt": "cama regular"},
            "in_motion": {"es": "en movimiento", "en": "in motion", "pt": "em movimento"},
            "variable": {"es": "variable", "en": "variable", "pt": "variável"},
        },
        "sleep_room": {
            "own_room": {"es": "habitación propia", "en": "own room", "pt": "quarto próprio"},
            "parents_room": {"es": "habitación de los padres", "en": "parents' room", "pt": "quarto dos pais"},
            "shared_room": {"es": "habitación compartida", "en": "shared room", "pt": "quarto compartilhado"},
            "living_room": {"es": "sala de estar", "en": "living room", "pt": "sala de estar"},
        },
        "bath_frequency": {
            "once_a_day": {"es": "una vez al día", "en": "once a day", "pt": "uma vez por dia"},
            "twice_a_day": {"es": "dos veces al día", "en": "twice a day", "pt": "duas vezes por dia"},
            "alternate_days": {"es": "día por medio", "en": "every other day", "pt": "dia sim, dia não"},
            "weekly": {"es": "una vez por semana", "en": "once a week", "pt": "uma vez por semana"},
            "as_needed": {"es": "según necesidad", "en": "as needed", "pt": "conforme necessário"},
        },
        "skin_care": {
            "no_products": {"es": "sin productos", "en": "no products", "pt": "sem produtos"},
            "daily_hydration": {"es": "hidratación diaria", "en": "daily hydration", "pt": "hidratação diária"},
            "hydration_as_needed": {"es": "hidratación según necesidad", "en": "hydration as needed", "pt": "hidratação conforme necessário"},
            "specialized_care": {"es": "cuidado específico indicado por profesional", "en": "specialized care prescribed by a professional", "pt": "cuidado específico indicado por profissional"},
        },
        "comfort_object": {
            "blankie": {"es": "mantita", "en": "blankie", "pt": "mantinha"},
            "cloth": {"es": "trapito", "en": "comfort cloth", "pt": "paninho"},
            "stuffed_animal": {"es": "peluche", "en": "stuffed animal", "pt": "bichinho de pelúcia"},
            "doll": {"es": "muñeca", "en": "doll", "pt": "boneca"},
            "favorite_toy": {"es": "juguete favorito", "en": "favorite toy", "pt": "brinquedo favorito"},
            "caregiver_clothing": {"es": "ropa del cuidador", "en": "caregiver clothing", "pt": "roupa do cuidador"},
            "small_pillow": {"es": "almohadita", "en": "small pillow", "pt": "travesseirinho"},
            "pacifier": {"es": "chupete", "en": "pacifier", "pt": "chupeta"},
            "transitioning": {"es": "objeto de transición", "en": "transition object", "pt": "objeto de transição"},
            "other": {"es": "otro objeto de confort", "en": "other comfort object", "pt": "outro objeto de conforto"},
        },
    }

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

    @staticmethod
    def _normalize_value_key(value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        normalized = unicodedata.normalize("NFD", value.strip().lower())
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return normalized.replace(" ", "_")

    @staticmethod
    def _ensure_field_translations(field_key: str, field_data: Dict[str, Any]) -> Dict[str, Any]:
        if not field_data:
            return field_data

        key_value = field_data.get("key") or field_data.get("value") or field_data.get("value_es") or ""
        canonical_key = BabyProfileService._normalize_value_key(key_value)
        translations_map = BabyProfileService._VALUE_TRANSLATIONS.get(field_key, {})
        translation = translations_map.get(canonical_key or key_value)

        if translation:
            field_data["key"] = canonical_key or key_value
            field_data["value_es"] = translation.get("es")
            field_data["value_en"] = translation.get("en")
            field_data["value_pt"] = translation.get("pt")
        else:
            fallback = field_data.get("value_es") or field_data.get("value_en") or field_data.get("value_pt") or key_value
            if fallback:
                field_data.setdefault("value_es", fallback)
                field_data.setdefault("value_en", fallback)
                field_data.setdefault("value_pt", fallback)
            if canonical_key:
                field_data.setdefault("key", canonical_key)

        return field_data

    @staticmethod
    def _combine_list_field(field_name: str, values: list[str]) -> Optional[Dict[str, Any]]:
        if not values:
            return None

        combined_entries = []
        seen_keys = set()

        for value in values:
            entry = BabyProfileService._build_field_data_from_text(field_name, value)
            if entry:
                entry_key = entry.get("key")
                if entry_key not in seen_keys:
                    combined_entries.append(entry)
                    if entry_key:
                        seen_keys.add(entry_key)

        if not combined_entries:
            return None

        def join(field: str) -> Optional[str]:
            texts = [entry.get(field) for entry in combined_entries if entry.get(field)]
            if not texts:
                return None
            return ", ".join(texts)

        confidence = sum(entry.get("confidence", BabyProfileService._DEFAULT_CONFIDENCE) for entry in combined_entries) / len(combined_entries)
        return {
            "key": ",".join(entry.get("key") for entry in combined_entries if entry.get("key")) or "multiple",
            "value_es": join("value_es"),
            "value_en": join("value_en"),
            "value_pt": join("value_pt"),
            "confidence": min(1.0, confidence),
        }

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
            field_data = BabyProfileService._ensure_field_translations(field_key, field_data)

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

        base_data = {
            "key": normalized_value,
            "value_es": normalized_value,
            "value_en": normalized_value,
            "value_pt": normalized_value,
            "confidence": BabyProfileService._DEFAULT_CONFIDENCE,
        }
        return BabyProfileService._ensure_field_translations(field_name, base_data)


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
            "bath_frequency": "daily care",
            "skin_care": "daily care",
            "comfort_object": "emotions bonds and respectful parenting",
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
            elif isinstance(field_value, list):
                normalized_field = BabyProfileService._combine_list_field(field_name, field_value)
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
