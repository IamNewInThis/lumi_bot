"""
Script de prueba para el sistema de Base de Conocimiento Estructurada
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from knowledge_base import initialize_knowledge_service, get_knowledge_service


def test_knowledge_retrieval():
    """Prueba el sistema de recuperación de conocimiento"""
    
    # Inicializar el servicio
    knowledge_base_path = Path(__file__).parent.parent / "src" / "knowledge_base"
    style_manifest_path = Path(__file__).parent.parent / "src" / "prompts" / "style_manifest.md"
    
    print(f"📁 Ruta base de conocimiento: {knowledge_base_path}")
    print(f"📄 Ruta style manifest: {style_manifest_path}")
    
    try:
        initialize_knowledge_service(str(knowledge_base_path), str(style_manifest_path))
        print("✅ Servicio de conocimiento inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando servicio: {e}")
        return
    
    # Obtener el servicio
    knowledge_service = get_knowledge_service()
    
    # Casos de prueba
    test_cases = [
        {
            "consulta": "Mi bebé de 4 meses no duerme bien, se despierta cada hora",
            "edad_esperada": 4,
            "descripcion": "Consulta sobre sueño en bebé de 4 meses"
        },
        {
            "consulta": "Mi hijo de 2 años hace berrinches terribles",
            "edad_esperada": 24,
            "descripcion": "Consulta sobre berrinches en niño de 2 años"
        },
        {
            "consulta": "Quiero hacer destete nocturno gradual",
            "edad_esperada": None,
            "descripcion": "Consulta sobre destete nocturno sin edad específica"
        }
    ]
    
    print("\n🧪 Ejecutando casos de prueba:\n")
    
    for i, caso in enumerate(test_cases, 1):
        print(f"--- Caso {i}: {caso['descripcion']} ---")
        print(f"Consulta: '{caso['consulta']}'")
        
        try:
            # Obtener conocimiento contextual
            conocimiento = knowledge_service.obtener_conocimiento_contextual(
                caso['consulta'], 
                caso['edad_esperada']
            )
            
            if conocimiento:
                print(f"✅ Conocimiento obtenido ({len(conocimiento)} caracteres)")
                print("📋 Vista previa:")
                print(conocimiento[:300] + "..." if len(conocimiento) > 300 else conocimiento)
            else:
                print("ℹ️ No se obtuvo conocimiento específico para esta consulta")
                
            # Obtener frases contextuales
            frases = knowledge_service.obtener_frases_contextuales(
                caso['consulta'],
                caso['edad_esperada']
            )
            
            if frases:
                print(f"💬 Frases contextuales ({len(frases)}):")
                for j, frase in enumerate(frases, 1):
                    print(f"  {j}. {frase}")
            else:
                print("💬 No se obtuvieron frases específicas")
                
        except Exception as e:
            print(f"❌ Error en caso {i}: {e}")
        
        print("\n" + "="*60 + "\n")
    
    # Estadísticas del sistema
    print("📊 Estadísticas del sistema:")
    print(f"📚 Temas disponibles: {knowledge_service.listar_temas_disponibles()}")
    
    for tema in knowledge_service.listar_temas_disponibles():
        fichas = knowledge_service.obtener_fichas_por_tema(tema)
        print(f"  - {tema}: {len(fichas)} fichas")


if __name__ == "__main__":
    test_knowledge_retrieval()