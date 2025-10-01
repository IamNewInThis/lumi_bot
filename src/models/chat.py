# src/models.py
from pydantic import BaseModel
from typing import Optional, List, Dict

class ChatRequest(BaseModel):
    message: str
    profile: Optional[dict] = None

class KnowledgeConfirmRequest(BaseModel):
    detected_knowledge: List[Dict]
    confirm: bool  # True para guardar, False para ignorar

class RoutineConfirmRequest(BaseModel):
    detected_routine: Dict
    confirm: bool  # True para guardar, False para ignorar
