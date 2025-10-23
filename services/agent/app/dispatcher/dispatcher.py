import requests, hashlib, hmac, os, json
from typing import Dict, Any
from ..schemas.api import AnalyzeRequest
from ..router.rule_router import RouteDecision
from ..utils.normalize import normalize_to_dataframe

SECRET = b"demo-secret"

class Dispatcher:
    def __init__(self, registry):
        self.registry = registry

    def invoke(self, decision: RouteDecision, req: AnalyzeRequest) -> Dict[str, Any]:
        payload = {
            "input": self._make_input(req),
            "params": req.params,
            "context": {"tenant_id": req.tenant_id, "task": req.context.get("task"), "trace_id": decision.trace_id}
        }
        # sign HMAC for internal calls
        body = json.dumps(payload).encode("utf-8")
        sig = hmac.new(SECRET, body, hashlib.sha256).hexdigest()

        if decision.protocol == "REST":
            r = requests.post(decision.endpoint, json=payload, headers={"X-Signature": sig}, timeout=30)
            r.raise_for_status()
            return r.json()
        else:
            raise NotImplementedError("Only REST is wired in the skeleton.")

    def _make_input(self, req: AnalyzeRequest) -> Dict[str, Any]:
        if req.data_pointer.format == "inline" and req.data_pointer.rows:
            # inline path for demo
            return {
                "frame_uri": "inline://rows",
                "rows": req.data_pointer.rows,
                "schema": {
                    "timestamp": req.params.get("timestamp_field","timestamp"),
                    "entity_keys": req.params.get("key_fields",["segment_id"]),
                    "metric": req.params.get("metric","speed_kmh")
                }
            }
        # otherwise pass through the pointer (parquet/csv/etc.)
        return {
            "frame_uri": req.data_pointer.uri,
            "schema": {
                "timestamp": req.params.get("timestamp_field","timestamp"),
                "entity_keys": req.params.get("key_fields",["segment_id"]),
                "metric": req.params.get("metric","speed_kmh")
            }
        }
