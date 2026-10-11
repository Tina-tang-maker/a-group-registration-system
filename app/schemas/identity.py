from pydantic import BaseModel, ConfigDict
from typing import Optional


class Persona(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    stable_number: Optional[str] = None


class SelectPersona(BaseModel):
    persona_id: str
    activity_id: Optional[str] = None
    role: Optional[str] = None


class CurrentActor(BaseModel):
    user_id: str
    name: str
    activity_id: Optional[str] = None
    role: Optional[str] = None
    is_operator: bool = False
    token: Optional[str] = None


class ContextQuery(BaseModel):
    activity_id: Optional[str] = None
    role: Optional[str] = None
