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

def ingest_pdf(path, source_name):
    raw = pdf_to_text(path)
    chunks = chunk(raw)
    cleaned_chunks = [clean_text(c) for c in chunks]

    source_name = source_name.lower().strip()
    metas = [{"source": source_name, "type": "pdf", "chunk": i} for i, _ in enumerate(chunks)]
    vectorstore.add_texts(texts=chunks, metadatas=metas)
    print(f"✅ Ingestado {len(chunks)} chunks de {source_name}")

if __name__ == "__main__":
    # Ingesta documentos 1
    # ingest_pdf("docs/1/Acompanar_despertares.pdf", "Acompanar_despertares.pdf")
    # ingest_pdf("docs/1/Destete_nocturno.pdf", "Destete_nocturno.pdf")
    # ingest_pdf("docs/1/Dormir_en_su_cuna.pdf", "Dormir_en_su_cuna.pdf")
    # ingest_pdf("docs/1/Rutina_del_bebe.pdf", "Rutina_del_bebe.pdf")
    # ingest_pdf("docs/1/Sueño_infantil_gonzalo_pin.pdf", "Sueño_infantil_gonzalo_pin.pdf")

    # Ingesta documentos 2
    # ingest_pdf("docs/2/AE.pdf", "AE.pdf")
    # ingest_pdf("docs/2/Child_of_mine_Feeding.pdf", "Child_of_mine_Feeding.pdf")
    # ingest_pdf("docs/2/Cuidado_dental.pdf", "Cuidado_dental.pdf")
    # ingest_pdf("docs/2/Cuidados_corporales.pdf", "Cuidados_corporales.pdf")
    # ingest_pdf("docs/2/Cuidados_desagradables.pdf", "Cuidados_desagradables.pdf")
    # ingest_pdf("docs/2/Lavado_nasal.pdf", "Lavado_nasal.pdf")
    # ingest_pdf("docs/2/Mi_nino_no_me_come.pdf", "Mi_nino_no_me_come.pdf")
    # ingest_pdf("docs/2/Nebulizador.pdf", "Nebulizador.pdf")
    # ingest_pdf("docs/2/Toxic_twenty.pdf", "Toxic_twenty.pdf")

    # Ingesta documentos 3
    ingest_pdf("docs/3/libertad.pdf", "libertad.pdf")

    # Ingesta documentos 4
    # ingest_pdf("docs/disciplina_sin_lagrimas.pdf", "disciplina_sin_lagrimas.pdf")
    # ingest_pdf("docs/el_cerebro_del_niño.pdf", "el_cerebro_del_niño.pdf")
    # ingest_pdf("docs/el_poder_de_la_presencia.pdf", "el_poder_de_la_presencia.pdf")
    # ingest_pdf("docs/emociones.pdf", "emociones.pdf")
    # ingest_pdf("docs/simplicity_parenting.pdf", "simplicity_parenting.pdf")
    ingest_pdf("docs/4/LIMITES.pdf", "LIMITES.pdf")

