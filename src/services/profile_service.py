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
        "bedtime_caregiver": {
            "mother": {"es": "madre", "en": "mother", "pt": "mãe"},
            "father": {"es": "padre", "en": "father", "pt": "pai"},
            "both_parents": {"es": "ambos los padres", "en": "both parents", "pt": "ambos os pais"},
            "grandparent": {"es": "abuelo o abuela", "en": "grandparent", "pt": "avô ou avó"},
            "other_caregiver": {"es": "otro cuidador", "en": "other caregiver", "pt": "outro cuidador"},
        },
        "sleep_association": {
            "in_arms": {"es": "en brazos", "en": "in arms", "pt": "no colo"},
            "rocking": {"es": "meciéndose", "en": "rocking", "pt": "embalando"},
            "breastfeeding": {"es": "lactancia materna", "en": "breastfeeding", "pt": "amamentação"},
            "bottle": {"es": "mamadera", "en": "bottle", "pt": "mamadeira"},
            "pacifier": {"es": "chupete", "en": "pacifier", "pt": "chupeta"},
            "hand_on_child": {"es": "mano sobre el bebé", "en": "hand on child", "pt": "mão sobre o bebê"},
            "soft_sounds": {"es": "sonidos suaves", "en": "soft sounds", "pt": "sons suaves"},
            "white_noise": {"es": "ruido blanco", "en": "white noise", "pt": "ruído branco"},
            "contact_nap": {"es": "siesta en contacto", "en": "contact nap", "pt": "soneca em contato"},
            "movement": {"es": "con movimiento", "en": "movement", "pt": "com movimento"},
            "soothing_object": {"es": "objeto de apego", "en": "soothing object", "pt": "objeto de apego"},
            "gentle_touch": {"es": "caricias suaves", "en": "gentle touch", "pt": "toque suave"},
            "singing": {"es": "canto suave", "en": "singing", "pt": "cantando"},
            "shushing": {"es": "sonidos shhh", "en": "shushing", "pt": "sons de shhh"},
        },
        "sleep_light": {
            "red_light": {"es": "luz roja", "en": "red light", "pt": "luz vermelha"},
            "dim_light": {"es": "luz tenue", "en": "dim light", "pt": "luz suave"},
            "complete_darkness": {"es": "oscuridad total", "en": "complete darkness", "pt": "escuridão total"},
            "night_light": {"es": "luz nocturna", "en": "night light", "pt": "luz noturna"},
            "no_light": {"es": "sin luz", "en": "no light", "pt": "sem luz"},
            "environment_dependent": {"es": "según el entorno", "en": "environment dependent", "pt": "dependendo do ambiente"},
        },
        "sleep_sound": {
            "white_noise_continuous": {"es": "ruido blanco continuo", "en": "continuous white noise", "pt": "ruído branco contínuo"},
            "white_noise_initial": {"es": "ruido blanco al inicio", "en": "white noise at bedtime", "pt": "ruído branco no início"},
            "none": {"es": "sin sonido especial", "en": "none", "pt": "nenhum"},
            "environment_dependent": {"es": "según el entorno", "en": "environment dependent", "pt": "dependendo do ambiente"},
        },
        "sleep_pajama": {
            "diaper_only": {"es": "solo pañal", "en": "diaper only", "pt": "apenas fralda"},
            "underwear": {"es": "ropa interior", "en": "underwear", "pt": "roupa íntima"},
            "sleeveless_body": {"es": "body sin mangas", "en": "sleeveless bodysuit", "pt": "body sem mangas"},
            "short_sleeve_body": {"es": "body manga corta", "en": "short-sleeve bodysuit", "pt": "body de manga curta"},
            "long_sleeve_body": {"es": "body manga larga", "en": "long-sleeve bodysuit", "pt": "body de manga longa"},
            "shirt": {"es": "polera o camiseta", "en": "shirt", "pt": "camiseta"},
            "long_socks": {"es": "medias largas", "en": "long socks", "pt": "meias longas"},
            "socks": {"es": "calcetines", "en": "socks", "pt": "meias"},
            "full_pajama": {"es": "pijama completo", "en": "full pajama", "pt": "pijama completo"},
            "thermal_pajama": {"es": "pijama térmico", "en": "thermal pajama", "pt": "pijama térmico"},
            "two_piece_pajama": {"es": "pijama de dos piezas", "en": "two-piece pajama", "pt": "pijama de duas peças"},
            "light_sleep_sack": {"es": "saco de dormir liviano", "en": "light sleep sack", "pt": "saco de dormir leve"},
            "medium_sleep_sack": {"es": "saco de dormir medio", "en": "medium sleep sack", "pt": "saco de dormir médio"},
            "thick_sleep_sack": {"es": "saco de dormir grueso", "en": "thick sleep sack", "pt": "saco de dormir grosso"},
            "thin_blanket": {"es": "manta delgada", "en": "thin blanket", "pt": "cobertor fino"},
            "thick_blanket": {"es": "manta gruesa", "en": "thick blanket", "pt": "cobertor grosso"},
        },
        "nap_count": {
            "0": {"es": "0 siestas", "en": "0 naps", "pt": "0 sonecas"},
            "1": {"es": "1 siesta", "en": "1 nap", "pt": "1 soneca"},
            "2": {"es": "2 siestas", "en": "2 naps", "pt": "2 sonecas"},
            "3": {"es": "3 siestas", "en": "3 naps", "pt": "3 sonecas"},
            "4": {"es": "4 siestas", "en": "4 naps", "pt": "4 sonecas"},
            "5": {"es": "5 siestas", "en": "5 naps", "pt": "5 sonecas"},
            "6": {"es": "6 siestas", "en": "6 naps", "pt": "6 sonecas"},
            "variable": {"es": "siestas variables", "en": "variable naps", "pt": "sonecas variáveis"},
        },
        "bedtime_start": {
            "18:00": {"es": "18:00", "en": "18:00", "pt": "18:00"},
            "18:30": {"es": "18:30", "en": "18:30", "pt": "18:30"},
            "19:00": {"es": "19:00", "en": "19:00", "pt": "19:00"},
            "19:30": {"es": "19:30", "en": "19:30", "pt": "19:30"},
            "20:00": {"es": "20:00", "en": "20:00", "pt": "20:00"},
            "20:30": {"es": "20:30", "en": "20:30", "pt": "20:30"},
            "21:00": {"es": "21:00", "en": "21:00", "pt": "21:00"},
            "21:30": {"es": "21:30", "en": "21:30", "pt": "21:30"},
            "22:00": {"es": "22:00", "en": "22:00", "pt": "22:00"},
            "later_than_22": {"es": "después de las 22:00", "en": "later than 22:00", "pt": "depois das 22:00"},
        },
        "bedtime_hour": {
            "18:00": {"es": "18:00", "en": "18:00", "pt": "18:00"},
            "18:30": {"es": "18:30", "en": "18:30", "pt": "18:30"},
            "19:00": {"es": "19:00", "en": "19:00", "pt": "19:00"},
            "19:30": {"es": "19:30", "en": "19:30", "pt": "19:30"},
            "20:00": {"es": "20:00", "en": "20:00", "pt": "20:00"},
            "20:30": {"es": "20:30", "en": "20:30", "pt": "20:30"},
            "21:00": {"es": "21:00", "en": "21:00", "pt": "21:00"},
            "21:30": {"es": "21:30", "en": "21:30", "pt": "21:30"},
            "22:00": {"es": "22:00", "en": "22:00", "pt": "22:00"},
            "later_than_22": {"es": "después de las 22:00", "en": "later than 22:00", "pt": "depois das 22:00"},
        },
        "night_wakings": {
            "none": {"es": "sin despertares", "en": "none", "pt": "sem despertares"},
            "1": {"es": "1 despertar", "en": "1 waking", "pt": "1 despertar"},
            "1–2": {"es": "1–2 despertares", "en": "1–2 wakings", "pt": "1–2 despertares"},
            "2": {"es": "2 despertares", "en": "2 wakings", "pt": "2 despertares"},
            "2–3": {"es": "2–3 despertares", "en": "2–3 wakings", "pt": "2–3 despertares"},
            "3": {"es": "3 despertares", "en": "3 wakings", "pt": "3 despertares"},
            "3–4": {"es": "3–4 despertares", "en": "3–4 wakings", "pt": "3–4 despertares"},
            "4–5": {"es": "4–5 despertares", "en": "4–5 wakings", "pt": "4–5 despertares"},
            "5_or_more": {"es": "5 o más despertares", "en": "5 or more wakings", "pt": "5 ou mais despertares"},
            "no_pattern": {"es": "sin patrón claro", "en": "no pattern", "pt": "sem padrão"},
        },
        "night_soothing": {
            "pick_up": {"es": "tomarlo en brazos", "en": "pick up", "pt": "pegar no colo"},
            "hold_on_chest": {"es": "sobre el pecho", "en": "hold on chest", "pt": "sobre o peito"},
            "lie_next_to_child": {"es": "acostarse al lado", "en": "lie next to child", "pt": "deitar ao lado"},
            "sit_nearby": {"es": "sentarse cerca", "en": "sit nearby", "pt": "sentar por perto"},
            "rocking": {"es": "mecer", "en": "rocking", "pt": "embalar"},
            "feeding_breast": {"es": "dar pecho", "en": "breastfeeding", "pt": "amamentar"},
            "feeding_bottle": {"es": "dar mamadera", "en": "bottle feeding", "pt": "dar mamadeira"},
            "pacifier": {"es": "dar chupete", "en": "pacifier", "pt": "dar chupeta"},
            "comfort_object": {"es": "objeto de consuelo", "en": "comfort object", "pt": "objeto de conforto"},
            "hand_on_body": {"es": "mano sobre el cuerpo", "en": "hand on body", "pt": "mão sobre o corpo"},
            "caressing": {"es": "acariciar", "en": "caressing", "pt": "acariciar"},
            "rhythmic_patting": {"es": "palmaditas rítmicas", "en": "rhythmic patting", "pt": "tapinhas rítmicas"},
            "shushing": {"es": "hacer shhh", "en": "shushing", "pt": "sons de shhh"},
            "soft_voice": {"es": "voz suave", "en": "soft voice", "pt": "voz suave"},
            "singing_softly": {"es": "cantar suave", "en": "singing softly", "pt": "cantar suave"},
            "offer_water": {"es": "ofrecer agua", "en": "offer water", "pt": "oferecer água"},
            "turn_on_light": {"es": "encender una luz", "en": "turn on light", "pt": "acender a luz"},
        },
        "night_caregiver": {
            "mother": {"es": "madre", "en": "mother", "pt": "mãe"},
            "father": {"es": "padre", "en": "father", "pt": "pai"},
            "both_parents": {"es": "ambos los padres", "en": "both parents", "pt": "ambos os pais"},
            "other_caregiver": {"es": "otro cuidador", "en": "other caregiver", "pt": "outro cuidador"},
        },
        "wakeup_hour": {
            "5:00": {"es": "05:00", "en": "05:00", "pt": "05:00"},
            "5:30": {"es": "05:30", "en": "05:30", "pt": "05:30"},
            "6:00": {"es": "06:00", "en": "06:00", "pt": "06:00"},
            "6:30": {"es": "06:30", "en": "06:30", "pt": "06:30"},
            "7:00": {"es": "07:00", "en": "07:00", "pt": "07:00"},
            "7:30": {"es": "07:30", "en": "07:30", "pt": "07:30"},
            "8:00": {"es": "08:00", "en": "08:00", "pt": "08:00"},
            "later_than_8": {"es": "después de las 8:00", "en": "later than 8:00", "pt": "depois das 8:00"},
        },
        "night_feeding": {
            "none": {"es": "sin tomas nocturnas", "en": "no night feedings", "pt": "sem mamadas noturnas"},
            "1": {"es": "1 toma nocturna", "en": "1 night feeding", "pt": "1 mamada noturna"},
            "2": {"es": "2 tomas nocturnas", "en": "2 night feedings", "pt": "2 mamadas noturnas"},
            "3_or_more": {"es": "3 o más tomas", "en": "3 or more feedings", "pt": "3 ou mais mamadas"},
            "on_demand": {"es": "a demanda", "en": "on demand", "pt": "sob demanda"},
        },
        "night_feeding_purpose": {
            "hunger": {"es": "hambre", "en": "hunger", "pt": "fome"},
            "comfort": {"es": "consuelo", "en": "comfort", "pt": "conforto"},
            "hydration": {"es": "hidratación", "en": "hydration", "pt": "hidratação"},
            "habit": {"es": "hábito", "en": "habit", "pt": "hábito"},
        },
        "night_feeding_type": {
            "breast": {"es": "pecho", "en": "breast", "pt": "peito"},
            "bottle": {"es": "mamadera", "en": "bottle", "pt": "mamadeira"},
            "water": {"es": "agua", "en": "water", "pt": "água"},
            "other": {"es": "otro tipo", "en": "other type", "pt": "outro tipo"},
        },
        "sleep_tired_signs": {
            "rubs_eyes": {"es": "se frota los ojos", "en": "rubs eyes", "pt": "coça os olhos"},
            "yawns": {"es": "bosteza", "en": "yawns", "pt": "boceja"},
            "stares_blankly": {"es": "mirada perdida", "en": "blank stare", "pt": "olhar fixo"},
            "seeks_contact": {"es": "busca contacto", "en": "seeks contact", "pt": "busca contato"},
            "gets_irritable": {"es": "se irrita", "en": "gets irritable", "pt": "fica irritado"},
            "calms_down": {"es": "se queda quieto", "en": "becomes still", "pt": "fica quieto"},
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
        "family_members": {
            "mother": {"es": "madre", "en": "mother", "pt": "mãe"},
            "father": {"es": "padre", "en": "father", "pt": "pai"},
            "siblings": {"es": "hermanos/as", "en": "siblings", "pt": "irmãos/irmãs"},
            "grandparents": {"es": "abuelos/as", "en": "grandparents", "pt": "avós"},
            "caregiver": {"es": "cuidador/a", "en": "caregiver", "pt": "cuidador/a"},
            "pets": {"es": "mascotas", "en": "pets", "pt": "animais de estimação"},
        },
        "go_to_daycare": {
            "no": {"es": "no asiste a guardería", "en": "does not attend daycare", "pt": "não frequenta creche"},
            "daycare": {"es": "guardería", "en": "daycare", "pt": "creche"},
            "preschool": {"es": "jardín infantil / preescolar", "en": "preschool", "pt": "pré-escola"},
            "school": {"es": "colegio / escuela", "en": "school", "pt": "escola"},
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
            "bedtime_start": "sleep and rest",
            "bedtime_caregiver": "sleep and rest",
            "sleep_association": "sleep and rest",
            "sleep_light": "sleep and rest",
            "sleep_sound": "sleep and rest",
            "sleep_pajama": "sleep and rest",
            "nap_count": "sleep and rest",
            "bedtime_hour": "sleep and rest",
            "night_wakings": "sleep and rest",
            "night_soothing": "sleep and rest",
            "night_caregiver": "sleep and rest",
            "wakeup_hour": "sleep and rest",
            "night_feeding": "sleep and rest",
            "night_feeding_purpose": "sleep and rest",
            "night_feeding_type": "sleep and rest",
            "sleep_tired_signs": "sleep and rest",
            "feeding_method": "feeding",
            "temperament": "behavior",
            "bath_frequency": "daily care",
            "skin_care": "daily care",
            "comfort_object": "emotions bonds and respectful parenting",
            "family_members": "family context and environment",
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
