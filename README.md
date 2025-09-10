# Chatbot con LangChain y OpenAI

Este proyecto es un chatbot basado en [LangChain](https://python.langchain.com/) y [OpenAI](https://platform.openai.com/), diseñado para generar posts para redes sociales.

## Requisitos previos
- Python 3.12 o superior
- Una clave de API de OpenAI

## Configuración del entorno virtual

1. **Crear el entorno virtual:**

```bash
python3 -m venv lumi_env
```

2. **Activar el entorno virtual:**

- En Linux/Mac:
  ```bash
  source lumi_env/bin/activate
  ```
- En Windows:
  ```cmd
  .\lumi_env\Scripts\activate
  ```

3. **Instalar las dependencias:**

```bash
pip install -r requirements.txt
```

## Configuración de variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
OPENAI_API_KEY=tu_clave_de_openai
OPENAI_MODEL=modelo_de_openia
SUPABASE_URL=supabase
SUPABASE_SERVICE_ROLE_KEY=supabase
PORT=puerto
```

Reemplaza `tu_clave_de_openai` por tu clave real de OpenAI.

## Uso

Puedes ejecutar el chatbot o probar la plantilla de prompt:

```bash
python chatbot.py
```

# 4. correr el servidor
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 3000

# 5. Cargar documentos
python -m src.rag.ingest

# 6. Testing
python -m src.test.test_retriever

## Notas - Congelar librerias 
pip freeze > requirements.txt

