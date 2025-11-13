# Extractors

Esta carpeta contiene los extractores de información del sistema Lumi. Los extractores son componentes especializados que analizan texto y activan funcionalidades específicas.

## Propósito

Los extractores procesan mensajes de los usuarios para identificar y extraer información relevante que puede ser utilizada para:
- Mantener perfiles de bebes actualizados

## Extractores Disponibles

### profile_extractor.py

Extrae información del perfil del bebé a partir de mensajes de los usuarios. Identifica automáticamente:

- **Lugar de sueño**: Donde duerme el bebé (cuna, cama con los padres, moisés, etc.)
- **Método de alimentación**: Tipo de alimentación (lactancia materna, fórmula, mixta)
- **Temperamento**: Características del comportamiento del bebé (tranquilo, activo, sensible)

#### Características:
- **Multiidioma**: Soporta español, inglés y portugués
- **Modo dual**: 
  - Utiliza LLM (GPT-4o-mini) cuando hay API key disponible para mayor precisión
  - Modo de respaldo con heurísticas basadas en palabras clave cuando no hay API key
- **Normalización de texto**: Maneja tildes y variaciones en mayúsculas/minúsculas
- **Confianza**: Proporciona un nivel de confianza en la extracción (cuando usa LLM)

#### Uso:
```python
from extractors.profile_extractor import extract_profile_info

profile = extract_profile_info("Mi bebé duerme en su cuna y toma pecho")
# Retorna: BabyProfile(sleep_location="cuna/crib", feeding_method="lactancia materna", ...)
```

### knowledge_extractor.py

🚧 **En desarrollo**: Este extractor tendrá funcionalidad en el futuro para extraer y procesar conocimiento específico del dominio.

## Estructura de Datos

Los extractores utilizan modelos Pydantic para garantizar la consistencia y validación de los datos extraídos. Esto permite:
- Validación automática de tipos
- Serialización/deserialización consistente
- Documentación clara de los campos esperados

## Configuración

Los extractores pueden configurarse a través de variables de entorno:
- `OPENAI_API_KEY`: Para habilitar el modo LLM en profile_extractor
- `OPENAI_MODEL`: Modelo a utilizar (por defecto: gpt-4o-mini)