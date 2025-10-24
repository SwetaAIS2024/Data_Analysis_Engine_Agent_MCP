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

        # Try to infer columns/features from inline data
        columns = set()
        if req.data_pointer.format == "inline" and req.data_pointer.rows:
            first_row = req.data_pointer.rows[0] if len(req.data_pointer.rows) > 0 else {}
            columns = set(first_row.keys())

        tool = None
        # Rule-based logic
        if "latitude" in columns and "longitude" in columns:
            tool = "geospatial_mapper"
        elif task == "anomaly_detection" and data_type in ("tabular","timeseries"):
            tool = "anomaly_zscore"
        elif task == "clustering" and data_type == "tabular":
            tool = "clustering"
        elif task == "feature_engineering" and data_type == "tabular":
            tool = "feature_engineering"
        elif task == "classification" and data_type == "tabular":
            tool = "classifier_regressor"
        elif task == "forecasting" and data_type == "timeseries":
            tool = "timeseries_forecaster"
        elif task == "stats_comparison" and data_type == "tabular":
            tool = "stats_comparator"
        elif task == "incident_detection" and data_type == "tabular":
            tool = "incident_detector"

        endpoint, version, protocol = None, "1.0.0", "REST"
        if tool:
            t = self.registry.get_tool(tool)
            if t:
                protocol = "REST"
                endpoint = t["endpoints"].get(protocol)
                version = t["version"]

        return RouteDecision(request_id=rid, trace_id=tid, tool=tool, version=version, protocol=protocol, endpoint=endpoint)
