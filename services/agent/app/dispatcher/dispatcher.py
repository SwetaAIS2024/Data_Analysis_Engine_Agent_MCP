import requests, hashlib, hmac, os, json
import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..schemas.api import AnalyzeRequest
from ..router.rule_router import RouteDecision
from ..utils.normalize import normalize_to_dataframe

SECRET = b"demo-secret"

class Dispatcher:
    """
    Enhanced Dispatcher with Parallel/Sequential Tool Invocation
    Supports execution strategies from the Planner:
    - Unified (sequential): Execute tasks one by one
    - Parallel: Execute independent tasks concurrently
    - Conditional: Execute based on previous results
    """
    
    def __init__(self, registry):
        self.registry = registry
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def invoke(self, decision: RouteDecision, req: AnalyzeRequest) -> Dict[str, Any]:
        """Single tool invocation (legacy method for backward compatibility)"""
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
    
    def execute_plan(
        self,
        plan: Dict[str, Any],
        req: AnalyzeRequest
    ) -> Dict[str, Any]:
        """
        Execute a complete plan from the Planner
        
        Args:
            plan: Execution plan with tasks, strategy, and dependencies
            req: Original request
        
        Returns:
            Combined results from all tasks
        """
        strategy = plan.get("strategy", "unified")
        tasks = plan.get("tasks", [])
        
        if strategy == "parallel":
            return self._execute_parallel(tasks, req, plan)
        elif strategy == "conditional":
            return self._execute_conditional(tasks, req, plan)
        else:  # unified (sequential)
            return self._execute_sequential(tasks, req, plan)
    
    def _execute_sequential(
        self,
        tasks: List[Dict[str, Any]],
        req: AnalyzeRequest,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially (one after another)"""
        results = []
        previous_result = None
        
        for task in sorted(tasks, key=lambda t: t.get("order", 0)):
            tool_name = task["tool"]
            tool_params = task["params"]
            
            # Get tool endpoint from registry
            tool_info = self.registry.get(tool_name)
            if not tool_info:
                results.append({
                    "task": task,
                    "status": "error",
                    "error": f"Tool {tool_name} not found in registry"
                })
                continue
            
            # Build payload
            payload = {
                "input": self._make_input(req, previous_result),
                "params": {**req.params, **tool_params},
                "context": {
                    "tenant_id": req.tenant_id,
                    "task": tool_name,
                    "trace_id": plan.get("trace_id", "unknown")
                }
            }
            
            # Invoke tool
            try:
                result = self._invoke_tool(tool_info["endpoint"], payload, tool_info.get("protocol", "REST"))
                results.append({
                    "task": task,
                    "tool": tool_name,
                    "status": "success",
                    "output": result
                })
                previous_result = result  # For next task in pipeline
            except Exception as e:
                results.append({
                    "task": task,
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "strategy": "sequential",
            "plan": plan,
            "results": results,
            "status": "completed"
        }
    
    def _execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        req: AnalyzeRequest,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute independent tasks in parallel"""
        futures = []
        
        for task in tasks:
            tool_name = task["tool"]
            tool_params = task["params"]
            
            # Get tool endpoint from registry
            tool_info = self.registry.get(tool_name)
            if not tool_info:
                continue
            
            # Build payload
            payload = {
                "input": self._make_input(req),
                "params": {**req.params, **tool_params},
                "context": {
                    "tenant_id": req.tenant_id,
                    "task": tool_name,
                    "trace_id": plan.get("trace_id", "unknown")
                }
            }
            
            # Submit to thread pool
            future = self.executor.submit(
                self._invoke_tool,
                tool_info["endpoint"],
                payload,
                tool_info.get("protocol", "REST")
            )
            futures.append((future, task, tool_name))
        
        # Collect results
        results = []
        for future, task, tool_name in futures:
            try:
                result = future.result(timeout=60)
                results.append({
                    "task": task,
                    "tool": tool_name,
                    "status": "success",
                    "output": result
                })
            except Exception as e:
                results.append({
                    "task": task,
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "strategy": "parallel",
            "plan": plan,
            "results": results,
            "status": "completed"
        }
    
    def _execute_conditional(
        self,
        tasks: List[Dict[str, Any]],
        req: AnalyzeRequest,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks with conditional logic based on previous results"""
        # TODO: Implement conditional execution
        # For now, fall back to sequential
        return self._execute_sequential(tasks, req, plan)
    
    def _invoke_tool(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        protocol: str = "REST"
    ) -> Dict[str, Any]:
        """Invoke a single tool with HMAC signature"""
        body = json.dumps(payload).encode("utf-8")
        sig = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
        
        if protocol == "REST":
            r = requests.post(endpoint, json=payload, headers={"X-Signature": sig}, timeout=30)
            r.raise_for_status()
            return r.json()
        else:
            raise NotImplementedError(f"Protocol {protocol} not implemented")

    def _make_input(self, req: AnalyzeRequest, previous_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build input for tool invocation
        
        Args:
            req: Original request
            previous_result: Result from previous task (for pipelines)
        """
        # If previous result exists, use its output as input
        if previous_result and "output" in previous_result:
            # Extract processed data from previous step
            prev_output = previous_result.get("output", {})
            if "processed_data" in prev_output:
                return {
                    "frame_uri": "inline://from_previous",
                    "rows": prev_output["processed_data"],
                    "schema": {
                        "timestamp": req.params.get("timestamp_field","timestamp"),
                        "entity_keys": req.params.get("key_fields",["segment_id"]),
                        "metric": req.params.get("metric","speed_kmh")
                    }
                }
        
        # Default: use original request data
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
