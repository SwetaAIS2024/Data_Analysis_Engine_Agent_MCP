from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

class DataPointer(BaseModel):
    uri: str
    format: str
    rows: Optional[list] = None  # inline demo

class AnalyzeRequest(BaseModel):
    tenant_id: str
    mode: str = Field("sync", pattern="^(sync|async)$")
    context: Dict[str, Any]
    data_pointer: DataPointer
    params: Dict[str, Any] = {}

class AnalyzeResponse(BaseModel):
    request_id: str
    status: str
    result: Dict[str, Any]
    tool_meta: Dict[str, Any]

class RunStep(BaseModel):
    name: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    steps: List[RunStep]
