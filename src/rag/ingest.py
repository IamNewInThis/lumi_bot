import os, math
from supabase import create_client
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pathlib import Path
from dotenv import load_dotenv

def get_supabase_config():
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env')
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en .env")
    
    return supabase_url, supabase_key

# Initialize variables that will be used by the functions
SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY = get_supabase_config()  
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
emb = OpenAIEmbeddings(model="text-embedding-3-small")
DEFAULT_METADATA_VERSION = os.getenv("KNOWLEDGE_VERSION", "1.0")

vectorstore = SupabaseVectorStore(
    client=supabase,
    table_name="documents",
    query_name="match_documents",
    embedding=emb,
)

def pdf_to_text(path):
    reader = PdfReader(path)
    pages = [p.extract_text() or "" for p in reader.pages]
    return "\n\n".join(pages)

def clean_text(text: str) -> str:
    """Limpia saltos de línea múltiples y espacios extra"""
    return " ".join(text.split())

def chunk(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150, separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)

def ingest_pdf(path, source_name, category, version=None):
    raw = pdf_to_text(path)
    chunks = chunk(raw)
    cleaned_chunks = [clean_text(c) for c in chunks]

    source_name = source_name.lower().strip()
    if not category:
        raise ValueError(f"Debe indicar la categoría para '{source_name}'.")
    version = version or DEFAULT_METADATA_VERSION
    
    metas = [
        {
            "source": source_name,
            "type": "pdf",
            "chunk": i,
            "category": category,
            "version": version
        }
        for i, _ in enumerate(cleaned_chunks)
    ]
    vectorstore.add_texts(texts=cleaned_chunks, metadatas=metas)
    print(f"✅ Ingestado {len(chunks)} chunks de {source_name} - Categoría: {category} | Versión: {version}")

if __name__ == "__main__":
    """
    Define aquí los documentos que querés ingerir.
    Para cada uno puedes especificar una versión distinta (por ejemplo, "v1", "v2", "2024.10").
    Si no indicás versión se usará la definida en `DEFAULT_METADATA_VERSION`.
    """
    DOCUMENTS_TO_INGEST = [
        {"path": "docs/2/AE.pdf", "name": "AE.pdf", "category": "Cuidados diarios", "version": "2"},
        {"path": "docs/2/Respeto_y_cuidados_RP.pdf", "name": "Respeto_y_cuidados_RP.pdf", "category": "Cuidados diarios", "version": "1"},
        {"path": "docs/3/Juego_y_autonomia_RP.pdf", "name": "Juego_y_autonomia_RP.pdf", "category": "Autonomía y desarrollo integral", "version": "1"},
        {"path": "docs/3/Movimiento_libre_RP.pdf", "name": "Movimiento_libre_RP.pdf", "category": "Autonomía y desarrollo integral", "version": "1"},
        {"path": "docs/4/disciplina_sin_lagrimas.pdf", "name": "disciplina_sin_lagrimas.pdf", "category": "Autonomía y desarrollo integral", "version": "2"},
        {"path": "docs/4/el_cerebro_del_niño.pdf", "name": "el_cerebro_del_niño.pdf", "category": "Autonomía y desarrollo integral", "version": "2"},
        {"path": "docs/4/el_poder_de_la_presencia.pdf", "name": "el_poder_de_la_presencia.pdf", "category": "Autonomía y desarrollo integral", "version": "2"},
        {"path": "docs/4/Emociones_y_limites_RP.pdf", "name": "Emociones_y_limites_RP.pdf", "category": "Autonomía y desarrollo integral", "version": "1"},
        {"path": "docs/4/simplicity_parenting.pdf", "name": "simplicity_parenting.pdf", "category": "Autonomía y desarrollo integral", "version": "2"},
        {"path": "docs/5/Tips_viajes_R.pdf", "name": "Tips_viajes_R.pdf", "category": "Viajes con niños", "version": "1"},
        {"path": "docs/5/Viajes_con_niños_MC.pdf", "name": "Viajes_con_niños_MC.pdf", "category": "Viajes con niños", "version": "1"},
    ]

    for doc in DOCUMENTS_TO_INGEST:
        ingest_pdf(
            doc["path"],
            doc["name"],
            category=doc["category"],
            version=doc.get("version"),
        )
