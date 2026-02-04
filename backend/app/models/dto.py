from typing import List

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    content: str


class AttachFileRequest(BaseModel):
    filename: str
    content: str


class RenameSessionRequest(BaseModel):
    title: str


class CreateMemoryRequest(BaseModel):
    content: str
    chat_sessionId: str


class RulesConfig(BaseModel):
    searxng: bool = True
    duckduckgo: bool = True
    tavily: bool = False
    serper: bool = False
    tavilyExtract: bool = False
    localExtract: bool = True

    advanceSearch: bool = False
    advanceExtract: bool = False

    webSearchLimit: int | None = None
    memorySearchLimit: int | None = None
    historyLimit: int | None = None
    fileUploadMaxChars: int | None = None

    customInstructions: str = ''


class ReorderSessionsRequest(BaseModel):
    sessionIds: List[str]
