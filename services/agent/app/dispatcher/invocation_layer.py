"""
MCP Tools Invocation Layer
Handles tool execution based on structured plan from Chaining Manager:
- Invoke tools or combinations of tools
- Handle tool unavailability and get user feedback
- Create new tools with user feedback if needed
"""
import requests
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..schemas.api import AnalyzeRequest

logger = logging.getLogger(__name__)

SECRET = b"demo-secret"


class ToolInvocationResult:
    """Result from tool invocation"""
    def __init__(self, tool_id: str, status: str, output: Any = None, error: str = None):
        self.tool_id = tool_id
        self.status = status  # "success", "error", "unavailable"
        self.output = output
        self.error = error


class MCPToolsInvocationLayer:
    """
    MCP Tools Invocation Layer
    
    Input: Structured JSON execution plan from Chaining Manager
    Output: Tool results or user feedback request
    
    Responsibilities:
    1. Invoke single tools or combinations
    2. Handle tool unavailability
    3. Request user feedback when needed
    4. Suggest/create new tools based on feedback
    """
    
    def __init__(self, tool_registry, max_workers: int = 5):
        self.tool_registry = tool_registry
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"MCPToolsInvocationLayer initialized with {max_workers} workers")
    
    def execute(
        self,
        execution_plan: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the complete execution plan
        
        Args:
            execution_plan: Structured plan from Chaining Manager
            request_data: Original request data
        
        Returns:
            Results dictionary with:
            - status: "success", "partial_success", "failed", "needs_feedback"
            - results: List of tool results
            - errors: List of errors encountered
            - user_feedback_required: Dict with feedback request
        """
        logger.info(f"Executing plan with strategy: {execution_plan['execution_plan']['strategy']}")
        
        plan = execution_plan["execution_plan"]
        strategy = plan.get("strategy", "single")
        tools = plan.get("tools", [])
        
        # Check if user feedback is required before execution
        if execution_plan.get("requires_user_feedback", False):
            return self._request_user_feedback(execution_plan, request_data)
        
        # Execute based on strategy
        if strategy == "single":
            results = self._execute_single(tools, request_data)
        elif strategy == "sequential":
            results = self._execute_sequential(tools, request_data)
        elif strategy == "parallel":
            results = self._execute_parallel(tools, request_data)
        else:
            results = []
            logger.error(f"Unknown strategy: {strategy}")
        
        # Analyze results
        return self._analyze_results(results, execution_plan)
    
    def _execute_single(
        self,
        tools: List[Dict[str, Any]],
        request_data: Dict[str, Any]
    ) -> List[ToolInvocationResult]:
        """Execute a single tool"""
        if not tools:
            return []
        
        tool_spec = tools[0]
        result = self._invoke_tool(tool_spec, request_data)
        return [result]
    
    def _execute_sequential(
        self,
        tools: List[Dict[str, Any]],
        request_data: Dict[str, Any]
    ) -> List[ToolInvocationResult]:
        """Execute tools sequentially (output of one feeds into next)"""
        results = []
        previous_output = None
        
        for tool_spec in sorted(tools, key=lambda t: t.get("order", 0)):
            logger.info(f"Executing tool {tool_spec['tool_id']} (order: {tool_spec.get('order')})")
            
            # Use previous output if available
            data = self._merge_with_previous_output(request_data, previous_output)
            
            result = self._invoke_tool(tool_spec, data)
            results.append(result)
            
            # Check if execution should continue
            if result.status == "error":
                logger.warning(f"Tool {tool_spec['tool_id']} failed, stopping sequential execution")
                break
            
            previous_output = result.output
        
        return results
    
    def _execute_parallel(
        self,
        tools: List[Dict[str, Any]],
        request_data: Dict[str, Any]
    ) -> List[ToolInvocationResult]:
        """Execute tools in parallel"""
        futures = []
        
        for tool_spec in tools:
            future = self.executor.submit(
                self._invoke_tool,
                tool_spec,
                request_data
            )
            futures.append((future, tool_spec["tool_id"]))
        
        results = []
        for future, tool_id in futures:
            try:
                result = future.result(timeout=60)
                results.append(result)
                logger.info(f"Tool {tool_id} completed: {result.status}")
            except Exception as e:
                logger.error(f"Tool {tool_id} execution failed: {str(e)}")
                results.append(ToolInvocationResult(
                    tool_id=tool_id,
                    status="error",
                    error=str(e)
                ))
        
        return results
    
    def _invoke_tool(
        self,
        tool_spec: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> ToolInvocationResult:
        """
        Invoke a single tool
        
        Args:
            tool_spec: Tool specification with endpoint, params, etc.
            request_data: Request data to send to tool
        
        Returns:
            ToolInvocationResult
        """
        tool_id = tool_spec["tool_id"]
        endpoint = tool_spec.get("tool_endpoint")
        params = tool_spec.get("params", {})
        timeout = tool_spec.get("timeout", 30)
        
        logger.info(f"🔧 Invoking tool: {tool_id}")
        logger.info(f"   └─ Endpoint: {endpoint}")
        logger.info(f"   └─ Parameters: {list(params.keys()) if params else 'None'}")
        logger.info(f"   └─ Timeout: {timeout}s")
        
        # Check if tool is available
        if not endpoint:
            logger.error(f"❌ Tool {tool_id} has no endpoint configured")
            return ToolInvocationResult(
                tool_id=tool_id,
                status="unavailable",
                error=f"Tool {tool_id} endpoint not found in registry"
            )
        
        # Build payload
        payload = {
            "input": request_data.get("input", {}),
            "params": {**request_data.get("params", {}), **params},
            "context": request_data.get("context", {})
        }
        
        # Log payload summary
        input_rows = len(payload["input"].get("rows", []))
        logger.info(f"   └─ Input: {input_rows} rows")
        
        # Sign with HMAC
        body = json.dumps(payload).encode("utf-8")
        sig = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
        
        # Invoke tool with retry
        retry_count = tool_spec.get("retry_count", 2)
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"   └─ Retry attempt {attempt}/{retry_count}")
                
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"X-Signature": sig},
                    timeout=timeout
                )
                response.raise_for_status()
                
                result_data = response.json()
                
                # Log success with details
                logger.info(f"✅ Tool {tool_id} completed successfully")
                
                # Extract and log summary
                if isinstance(result_data, dict) and "output" in result_data:
                    output_summary = self._log_output_summary(tool_id, result_data["output"])
                    logger.info(f"   └─ {output_summary}")
                
                return ToolInvocationResult(
                    tool_id=tool_id,
                    status="success",
                    output=result_data
                )
            
            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {timeout}s"
                logger.warning(f"⚠️ Tool {tool_id}: {last_error}")
            
            except requests.exceptions.ConnectionError:
                last_error = f"Connection failed - tool service may be down"
                logger.warning(f"⚠️ Tool {tool_id}: {last_error}")
            
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                logger.error(f"❌ Tool {tool_id}: {last_error}")
                break  # Don't retry HTTP errors
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"❌ Tool {tool_id}: {last_error}")
                break
        
        # All retries failed
        logger.error(f"❌ Tool {tool_id} failed after {retry_count + 1} attempts")
        return ToolInvocationResult(
            tool_id=tool_id,
            status="error",
            error=last_error
        )
    
    def _log_output_summary(self, tool_id: str, output: Dict[str, Any]) -> str:
        """Generate a one-line summary of tool output for logging"""
        if not isinstance(output, dict):
            return f"Output: {str(output)[:100]}"
        
        # Tool-specific summaries
        if "anomalies_detected" in output:
            count = output["anomalies_detected"]
            return f"Found {count} anomalies"
        
        elif "forecast" in output:
            periods = len(output["forecast"])
            return f"Generated {periods} period forecast"
        
        elif "predictions" in output:
            count = len(output["predictions"])
            acc = output.get("accuracy", "N/A")
            return f"Generated {count} predictions (accuracy: {acc})"
        
        elif "clusters" in output:
            num = output["clusters"]
            return f"Created {num} clusters"
        
        elif "rows_processed" in output:
            rows = output["rows_processed"]
            return f"Processed {rows} rows"
        
        else:
            return f"Execution completed"
    
    def _merge_with_previous_output(
        self,
        request_data: Dict[str, Any],
        previous_output: Optional[Any]
    ) -> Dict[str, Any]:
        """Merge request data with previous tool output for sequential execution"""
        if not previous_output:
            return request_data
        
        merged = request_data.copy()
        
        # If previous output has processed data, use it
        if isinstance(previous_output, dict):
            if "output" in previous_output:
                prev_out = previous_output["output"]
                if "processed_data" in prev_out:
                    merged["input"]["rows"] = prev_out["processed_data"]
                elif "enriched_data" in prev_out:
                    merged["input"]["rows"] = prev_out["enriched_data"]
        
        return merged
    
    def _analyze_results(
        self,
        results: List[ToolInvocationResult],
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze execution results and determine overall status"""
        
        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status == "error")
        unavailable_count = sum(1 for r in results if r.status == "unavailable")
        
        # Determine overall status
        if success_count == len(results):
            status = "success"
        elif success_count > 0:
            status = "partial_success"
        elif unavailable_count > 0:
            status = "needs_feedback"
        else:
            status = "failed"
        
        # Build detailed results with user-friendly messages
        detailed_results = []
        for r in results:
            tool_info = {
                "tool_id": r.tool_id,
                "tool_name": self._get_tool_display_name(r.tool_id),
                "status": r.status,
                "status_message": self._get_status_message(r),
                "output": r.output,
                "error": r.error
            }
            
            # Add execution details for successful tools
            if r.status == "success" and r.output:
                tool_info["execution_summary"] = self._extract_execution_summary(r.output)
            
            detailed_results.append(tool_info)
        
        # Build response
        response = {
            "status": status,
            "status_message": self._get_overall_status_message(status, success_count, len(results)),
            "results": detailed_results,
            "summary": {
                "total_tools": len(results),
                "successful": success_count,
                "failed": error_count,
                "unavailable": unavailable_count,
                "execution_details": [
                    f"✅ {r.tool_id}: Success" if r.status == "success"
                    else f"❌ {r.tool_id}: {r.status.title()} - {r.error if r.error else 'Unknown error'}"
                    for r in results
                ]
            }
        }
        
        # Add user feedback request if needed
        if status == "needs_feedback":
            response["user_feedback_required"] = self._build_feedback_request(
                results, execution_plan
            )
        
        logger.info(f"Execution completed: {status} ({success_count}/{len(results)} succeeded)")
        
        return response
    
    def _get_tool_display_name(self, tool_id: str) -> str:
        """Get user-friendly display name for tool"""
        display_names = {
            "anomaly_zscore": "Anomaly Detection (Z-Score)",
            "timeseries_forecaster": "Time Series Forecaster",
            "classifier_regressor": "Classifier & Regressor",
            "cluster_feature_engineer": "Clustering & Feature Engineering",
            "geospatial_mapper": "Geospatial Mapper",
            "incident_detector": "Incident Detector",
            "stats_comparator": "Statistical Comparator"
        }
        return display_names.get(tool_id, tool_id.replace("_", " ").title())
    
    def _get_status_message(self, result: ToolInvocationResult) -> str:
        """Get user-friendly status message"""
        if result.status == "success":
            return "✅ Execution successful"
        elif result.status == "error":
            return f"❌ Execution failed: {result.error}"
        elif result.status == "unavailable":
            return f"⚠️ Tool unavailable: {result.error}"
        else:
            return f"ℹ️ Status: {result.status}"
    
    def _get_overall_status_message(self, status: str, success_count: int, total: int) -> str:
        """Get user-friendly overall status message"""
        if status == "success":
            return f"✅ All {total} tool(s) executed successfully"
        elif status == "partial_success":
            return f"⚠️ Partial success: {success_count}/{total} tool(s) succeeded"
        elif status == "needs_feedback":
            return "❓ User feedback required - some tools are unavailable"
        else:
            return f"❌ Execution failed: {total - success_count}/{total} tool(s) failed"
    
    def _extract_execution_summary(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from tool output for display"""
        if not isinstance(output, dict):
            return {"raw_output": str(output)}
        
        summary = {}
        
        # Extract common fields
        if "output" in output:
            tool_output = output["output"]
            
            # Anomaly detection specific
            if "anomalies_detected" in tool_output:
                summary["anomalies_detected"] = tool_output["anomalies_detected"]
                summary["anomaly_indices"] = tool_output.get("anomaly_indices", [])[:5]  # First 5
            
            # Forecasting specific
            if "forecast" in tool_output:
                summary["forecast_periods"] = len(tool_output["forecast"])
                summary["forecast_values"] = tool_output["forecast"][:5]  # First 5
            
            # Classification specific
            if "predictions" in tool_output:
                summary["predictions_count"] = len(tool_output["predictions"])
                summary["accuracy"] = tool_output.get("accuracy")
            
            # Clustering specific
            if "clusters" in tool_output:
                summary["num_clusters"] = tool_output["clusters"]
                summary["cluster_sizes"] = tool_output.get("cluster_sizes", [])
            
            # Generic fields
            if "rows_processed" in tool_output:
                summary["rows_processed"] = tool_output["rows_processed"]
            
            if "execution_time" in tool_output:
                summary["execution_time"] = tool_output["execution_time"]
        
        return summary if summary else {"message": "Execution completed successfully"}
    
    def _request_user_feedback(
        self,
        execution_plan: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build user feedback request"""
        
        conflicts = execution_plan.get("conflicts", [])
        
        feedback_request = {
            "status": "needs_feedback",
            "message": "User input required to proceed",
            "conflicts": conflicts,
            "options": []
        }
        
        # Build feedback options based on conflicts
        for conflict in conflicts:
            if conflict["type"] == "tool_unavailable":
                feedback_request["options"].append({
                    "option_id": "create_tool",
                    "message": f"Tool '{conflict['tool']}' is unavailable. Would you like to create it?",
                    "actions": ["create_new_tool", "use_alternative", "cancel"]
                })
            
            elif conflict["type"] == "missing_parameter":
                feedback_request["options"].append({
                    "option_id": "provide_param",
                    "message": f"Missing required parameter: {conflict['parameter']}",
                    "actions": ["provide_value", "use_default"]
                })
        
        # Add fallback options
        fallbacks = execution_plan.get("fallback_options", [])
        for i, fallback in enumerate(fallbacks):
            feedback_request["options"].append({
                "option_id": f"fallback_{i}",
                "message": fallback["option"],
                "actions": ["use_fallback"]
            })
        
        return feedback_request
    
    def _build_feedback_request(
        self,
        results: List[ToolInvocationResult],
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build feedback request for unavailable tools"""
        
        unavailable_tools = [r for r in results if r.status == "unavailable"]
        
        return {
            "message": f"{len(unavailable_tools)} tool(s) unavailable",
            "unavailable_tools": [r.tool_id for r in unavailable_tools],
            "options": [
                {
                    "option_id": "create_tools",
                    "message": "Create missing tools",
                    "action": "create_new_tools",
                    "tools": [r.tool_id for r in unavailable_tools]
                },
                {
                    "option_id": "use_alternatives",
                    "message": "Use alternative tools",
                    "action": "select_alternatives",
                    "fallbacks": execution_plan.get("fallback_options", [])
                },
                {
                    "option_id": "cancel",
                    "message": "Cancel execution",
                    "action": "cancel"
                }
            ]
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== MCP Tools Invocation Layer Examples ===\n")
    
    # Mock registry
    class MockRegistry:
        def get(self, tool_name):
            return {"endpoint": f"http://mock-{tool_name}:8000/run"}
    
    invocation_layer = MCPToolsInvocationLayer(MockRegistry())
    
    # Example 1: Execute single tool plan
    print("1. Single Tool Execution:")
    plan1 = {
        "execution_plan": {
            "strategy": "single",
            "tools": [
                {
                    "tool_id": "anomaly_zscore",
                    "tool_endpoint": "http://anomaly:8000/run",
                    "params": {"threshold": 2.5}
                }
            ]
        },
        "requires_user_feedback": False
    }
    
    request_data1 = {
        "input": {"rows": [{"value": 10}]},
        "params": {"metric": "value"}
    }
    
    # Note: This will fail in example since endpoints don't exist
    print("Plan structure:")
    print(json.dumps(plan1, indent=2))
    print()
    
    # Example 2: User feedback required
    print("2. User Feedback Required:")
    plan2 = {
        "execution_plan": {"strategy": "single", "tools": []},
        "requires_user_feedback": True,
        "conflicts": [
            {
                "type": "tool_unavailable",
                "tool": "custom_analyzer",
                "severity": "high"
            }
        ],
        "fallback_options": [
            {"option": "Use standard analyzer", "tools": ["anomaly_zscore"]}
        ]
    }
    
    result2 = invocation_layer.execute(plan2, request_data1)
    print(json.dumps(result2, indent=2))
