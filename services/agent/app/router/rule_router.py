import uuid, time
from pydantic import BaseModel
from typing import Optional
from ..schemas.api import AnalyzeRequest
from ..registry.registry import ToolRegistry

class RouteDecision(BaseModel):
    request_id: str
    trace_id: str
    tool: Optional[str] = None
    version: str = "1.0.0"
    protocol: str = "REST"
    endpoint: Optional[str] = None

class RuleRouter:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def route(self, req: AnalyzeRequest) -> RouteDecision:
        rid = str(uuid.uuid4())[:8]
        tid = str(uuid.uuid4())[:8]
        task = (req.context or {}).get("task","").lower()
        data_type = (req.context or {}).get("data_type","").lower()

        # Minimal rules
        if task == "anomaly_detection" and data_type in ("tabular","timeseries"):
            tool = "anomaly_zscore"
        else:
            tool = None

        endpoint, version, protocol = None, "1.1.0", "REST"
        if tool:
            t = self.registry.get_tool(tool)
            if t:
                endpoint, version, protocol = t["endpoint"], t["version"], t["protocol"]

        return RouteDecision(request_id=rid, trace_id=tid, tool=tool, version=version, protocol=protocol, endpoint=endpoint)
