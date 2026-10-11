from pydantic import BaseModel, Field
from typing import Optional


class AiSessionInput(BaseModel):
    topic_key: str = Field(min_length=1)


class MessageInput(BaseModel):
    content: str = Field(min_length=1)
    client_message_id: str = Field(min_length=1)


class MessageAccepted(BaseModel):
    message_id: str
    job_id: Optional[str] = None
    status: str


class DossierJobInput(BaseModel):
    session_id: str


class JobView(BaseModel):
    id: str
    job_type: str
    status: str
    input_version: Optional[int] = None
    result_data: Optional[dict] = None
    error_code: Optional[str] = None
    attempts: int


class AiSessionView(BaseModel):
    id: str
    activity_member_id: str
    topic_key: str
    status: str


class AiMessageView(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: str
