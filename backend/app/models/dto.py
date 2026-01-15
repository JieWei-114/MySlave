from pydantic import BaseModel

class CreateSessionRequest(BaseModel):
    title: str

class SendMessageRequest(BaseModel):
    content: str

class RenameSessionRequest(BaseModel):
    title: str
