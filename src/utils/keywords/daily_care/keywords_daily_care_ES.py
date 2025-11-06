# ============================================================================
# 🧼 CUIDADOS DIARIOS Y ALIMENTACIÓN - PERFIL DEL NIÑO (0–7 AÑOS)
# ============================================================================

KEYWORDS_DAILY_CARE_ES = {
    # ------------------------------------------------------------------------
    # 🚿 CUIDADOS DIARIOS (0–84 MESES)
    # ------------------------------------------------------------------------
    "daily cares": {
            "0_84": {
                "bath_frequency": {
                    "once_a_day": [
                        "una vez al día",
                        "baño diario",
                        "todos los días"
                    ],
                    "twice_a_day": [
                        "dos veces al día",
                        "baño dos veces al día",
                        "baña mañana y noche"
                    ],
                    "alternate_days": [
                        "días alternos",
                        "día por medio",
                        "un día sí y otro no"
                    ],
                    "as_needed": [
                        "según necesidad",
                        "cuando está sucio",
                        "cuando suda",
                        "cuando hace calor"
                    ],
                },
                "bath_products_type": {
                    "natural_organic": [
                        "naturales",
                        "orgánicos",
                        "naturales-orgánicos",
                        "productos naturales",
                        "productos orgánicos"
                    ],
                    "conventional": [
                        "convencionales",
                        "comunes",
                        "productos normales",
                        "de supermercado"
                    ],
                    "combination": [
                        "combinación",
                        "mixtos",
                        "usa de ambos tipos"
                    ],
                    "special_medicated": [
                        "especiales",
                        "medicados",
                        "para piel sensible",
                        "hipoalergénicos",
                        "dermatológicos"
                    ],
                },
                "skin_care": {
                    "no_products": [
                        "sin productos",
                        "no usa cremas",
                        "solo agua"
                        "solo con agua"
                    ],
                    "daily_hydration": [
                        "hidratación diaria",
                        "usa crema todos los días",
                        "hidrata siempre"
                    ],
                    "occasional_hydration": [
                        "hidratación según necesidad",
                        "hidrata cuando está seco",
                        "hidrata algunas veces"
                    ],
                    "specific_care": [
                        "cuidado específico",
                        "tratamiento especial",
                        "indicado por profesional",
                        "uso indicado por médico"
                    ],
                },
                "sunscreen_type": {
                    "physical_barrier": [
                        "barrera física",
                        "barrera mineral",
                        "protector mineral",
                        "protección física"
                    ],
                    "chemical": [
                        "convencional",
                        "químico",
                        "protector químico"
                    ],
                    "combination": [
                        "combinación",
                        "mixto",
                        "usa ambos tipos"
                    ],
                    "none": [
                        "no usa",
                        "sin protector solar",
                        "usa ropa o sombrero",
                        "prefiere sombra natural"
                    ],
                },
                "dental_care_type": {
                    "gauze": [
                        "limpieza con gasa",
                        "gasa húmeda",
                        "sin pasta",
                        "solo con agua"
                    ],
                    "brush_no_paste": [
                        "cepillo sin pasta",
                        "cepillado sin pasta",
                        "cepilla sin pasta"
                    ],
                    "brush_no_fluoride": [
                        "pasta sin flúor",
                        "cepilla con pasta sin flúor"
                    ],
                    "brush_with_fluoride": [
                        "pasta con flúor",
                        "cepilla con pasta con flúor"
                    ],
                },
                "dental_autonomy": {
                    "familiarizing": [
                        "se familiariza con el cepillo",
                        "muerde el cepillo",
                        "juega con el cepillo"
                    ],
                    "adult_does": [
                        "el adulto realiza el cepillado",
                        "el adulto cepilla"
                    ],
                    "with_help": [
                        "cepilla con ayuda",
                        "lo hace con ayuda del adulto"
                    ],
                    "with_supervision": [
                        "cepilla solo con supervisión",
                        "supervisado"
                    ],
                    "alone": [
                        "cepilla solo",
                        "independiente en el cepillado"
                    ],
                },
                "dental_frequency": {
                    "once": ["1 vez al día", "una vez al día"],
                    "twice": ["2 veces al día", "dos veces al día"],
                    "three_or_more": ["3 o más veces al día", "varias veces al día"],
                    "irregular": ["irregular", "no siempre", "a veces se olvida"],
                },
                "toilet_training": {
                    "not_started": ["no iniciado", "usa pañal"],
                    "initial_interest": ["interés inicial", "empieza a avisar"],
                    "started": ["iniciado", "en proceso"],
                    "consolidated": ["consolidado", "ya controla"],
                    "night_pending": ["nocturno pendiente", "control diurno logrado"],
                },
                "intimate_hygiene_autonomy": {
                    "adult_does": ["el adulto realiza la limpieza"],
                    "with_help": ["se limpia con ayuda"],
                    "with_supervision": ["se limpia solo con supervisión"],
                    "alone": ["se limpia solo", "independiente"],
                },
                "bath_autonomy": {
                    "adult_does": ["el adulto realiza el baño"],
                    "with_help": ["baño con ayuda"],
                    "with_supervision": ["baño con supervisión"],
                    "alone": ["baño independiente", "se baña solo"],
                },
                "eating_autonomy": {
                    "adult_feeds": ["el adulto da la comida", "lo alimenta un adulto"],
                    "with_help": ["come con ayuda"],
                    "with_supervision": ["come solo con supervisión"],
                    "alone": ["come solo", "independiente"],
                },
                "dressing_autonomy": {
                    "adult_dresses": ["el adulto viste al niño", "lo viste un adulto"],
                    "collaborates": ["colabora durante el vestido"],
                    "with_help": ["se viste con ayuda"],
                    "alone": ["se viste solo", "independiente para vestirse"],
                },
            },

        # ------------------------------------------------------------------------
        # 🍼 ALIMENTACIÓN (0–6 MESES)
        # ------------------------------------------------------------------------
        "0_6": {
            "principal_type_feeding": {
                "exclusive_breastfeeding": [
                    "lactancia materna exclusiva",
                    "solo pecho",
                    "solo leche materna",
                ],
                "formula": [
                    "fórmula",
                    "leche de fórmula",
                    "leche artificial",
                    "biberón",
                ],
                "mixed": [
                    "mixta",
                    "pecho y fórmula",
                    "combinada",
                    "a veces pecho y a veces fórmula",
                ],
            },
            "feeding_frequency": {
                "2_3h": ["cada 2–3 horas", "cada dos o tres horas"],
                "3_4h": ["cada 3–4 horas", "cada tres o cuatro horas"],
                "4_6h": ["cada 4–6 horas", "cada cuatro a seis horas"],
                "on_demand": ["a demanda", "cuando lo pide"],
                "irregular": ["irregular", "sin horario fijo"],
            },
            "feeding_method": {
                "breast": ["directo al pecho", "pecho"],
                "bottle": ["biberón", "mamadera"],
                "cup": ["vasito", "taza pequeña"],
                "spoon_syringe": ["cucharita", "jeringa"],
                "relactator": ["relactador", "suplementador"],
            },
        },

        # ------------------------------------------------------------------------
        # 🍎 ALIMENTACIÓN (6–12 MESES)
        # ------------------------------------------------------------------------
        "6_12": {
            "milk_type": {
                "breastfeeding": ["lactancia materna", "pecho"],
                "formula": ["fórmula", "mamadera"],
                "both": ["ambas", "pecho y fórmula"],
            },
            "solid_food_start": {
                "yes": ["sí", "ya comenzó", "ya come sólidos"],
                "no": ["aún no", "solo leche"],
            },
            "feeding_approach": {
                "traditional": ["tradicional", "purés", "triturados"],
                "blw": ["blw", "baby led weaning", "trozos"],
                "mixed": ["mixto", "combinado"],
            },
            "daily_meals": {
                "one": ["1 comida", "una comida"],
                "two": ["2 comidas", "dos comidas"],
                "three_or_more": ["3 o más comidas", "varias comidas"],
                "variable": ["varía según el día", "depende del día"],
            },
            "eating_autonomy": {
                "adult_feeds": ["el adulto da la comida", "lo alimenta un adulto"],
                "with_help": ["come con ayuda del adulto"],
                "with_supervision": ["come solo con supervisión"],
            },
        },

        # ------------------------------------------------------------------------
        # 🍽️ ALIMENTACIÓN (12-84 MESES)
        # ------------------------------------------------------------------------
        "12_84": {
            "meal_structure": {
                "4_plus_1": ["4 comidas principales + 1 colación"],
                "4_plus_2": ["4 comidas principales + 2 colaciones"],
                "3_plus_2": ["3 comidas principales + 2 colaciones"],
                "no_snacks": ["sin colaciones", "solo comidas principales"],
                "variable": ["varía según el día", "depende del día"],
            },
            "dairy_factor": {
                "none": ["no toma leche", "sin lácteos"],
                "once": ["1 vez al día", "una vez al día"],
                "twice": ["2 veces al día", "dos veces al día"],
                "three_or_more": ["3 o más veces al día", "varias veces al día"],
            },
            "eating_autonomy": {
                "adult_feeds": ["el adulto da la comida", "lo alimenta el adulto"],
                "with_help": ["come con ayuda"],
                "with_supervision": ["come solo con supervisión"],
                "alone": ["come solo", "independiente"],
            },
            "meal_participation": {
                "none": ["no participa"],
                "occasional": ["participa ocasionalmente", "ayuda a veces"],
                "habitual": ["participa de forma habitual", "siempre ayuda"],
            },
            "sensory_reactions": {
                "texture": [
                    "prefiere alimentos suaves",
                    "evita alimentos con grumos",
                    "evita crujientes",
                    "evita fibrosos",
                    "prefiere papillas",
                    "mastica poco",
                    "prefiere secos o crocantes",
                    "evita duros",
                    "prefiere textura uniforme",
                ],
                "temperature": [
                    "evita alimentos fríos",
                    "evita calientes",
                    "prefiere tibios",
                    "solo temperatura ambiente",
                ],
                "flavor": [
                    "evita sabores amargos",
                    "evita ácidos",
                    "evita dulces",
                    "evita salados",
                    "prefiere sabores neutros",
                    "busca sabores fuertes",
                ],
                "smell": [
                    "sensible a olores intensos",
                    "rechaza alimentos por olor",
                ],
                "appearance": [
                    "rechaza alimentos por color",
                    "rechaza alimentos mezclados",
                    "prefiere separados",
                    "huele la comida antes de probarla",
                ],
            },
            "mild_reactions": {
                "milk_protein": ["proteína de la leche de vaca"],
                "gluten": ["gluten"],
                "additives": ["colorantes", "aditivos artificiales"],
                "sugar": ["azúcar refinada", "jarabe de maíz"],
                "acidic_fruits": ["fresas", "tomates", "kiwi", "piña"],
                "soy": ["soja"],
                "eggs": ["huevos"],
                "nuts": ["frutos secos"],
                "legumes": ["legumbres"],
                "seafood": ["mariscos"],
                "fish": ["pescados"],
                "corn": ["maíz"],
                "rice": ["arroz"],
                "citrus": ["cítricos"],
                "chocolate": ["chocolate", "cacao"],
                "dried_fruits": ["frutas secas", "deshidratadas"],
                "cruciferous": ["brócoli", "coliflor", "repollo"],
                "oils": ["aceite de oliva", "aceite de coco", "palta"],
                "spicy_foods": ["picantes", "condimentadas"],
                "difficult_combinations": ["fruta después del almuerzo"],
            },
        },
    }

}  # Fin cuidados_diarios_y_alimentacion
