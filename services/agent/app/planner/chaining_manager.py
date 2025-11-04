"""
MCP Tools Chaining Manager
Planning-based or LLM layer for:
- Planning: Determine which tools to use and in what order
- Decision Making: Choose between tool combinations
- Conflict Handling: Resolve tool conflicts and unavailability

Outputs structured JSON format for the MCP Tools Invocation Layer
"""
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    USER_FEEDBACK = "user_feedback"  # Ask user for clarification
    AUTO_SELECT = "auto_select"  # Automatically select best option
    CREATE_NEW = "create_new"  # Create new tool if needed


class MCPToolsChainingManager:
    """
    MCP Tools Chaining Manager
    
    Input: Structured metadata from Context Extraction Layer
    Output: Structured JSON with tool execution plan
    
    Responsibilities:
    1. Planning: Determine tool chain (sequence or parallel)
    2. Decision Making: Choose optimal tools based on goal and constraints
    3. Conflict Handling: Resolve unavailability, ambiguity, or conflicts
    
    Example Output:
    {
        "execution_plan": {
            "strategy": "sequential",
            "tools": [
                {
                    "tool_id": "anomaly_zscore",
                    "order": 1,
                    "params": {...},
                    "depends_on": []
                }
            ]
        },
        "conflicts": [],
        "requires_user_feedback": false,
        "reasoning": "Single anomaly detection task, no conflicts"
    }
    """
    
    def __init__(
        self,
        tool_registry: Dict[str, Any],
        llm_endpoint: Optional[str] = None,
        conflict_strategy: ConflictResolution = ConflictResolution.AUTO_SELECT
    ):
        """
        Initialize chaining manager
        
        Args:
            tool_registry: Registry of available tools
            llm_endpoint: Optional LLM API endpoint for planning
            conflict_strategy: How to handle conflicts
        """
        self.tool_registry = tool_registry
        self.llm_endpoint = llm_endpoint
        self.use_llm = llm_endpoint is not None
        self.conflict_strategy = conflict_strategy
        
        # Tool capability mapping
        self.goal_to_tools = self._build_goal_tool_mapping()
        
        logger.info(f"MCPToolsChainingManager initialized with {len(self.tool_registry.list_tools())} tools")
    
    def _build_goal_tool_mapping(self) -> Dict[str, List[str]]:
        """Map goals to available tools"""
        return {
            "anomaly_detection": ["anomaly_zscore"],
            "clustering": ["clustering"],
            "feature_engineering": ["feature_engineering"],
            "timeseries_forecasting": ["timeseries_forecaster"],
            "classification": ["classifier_regressor"],
            "regression": ["classifier_regressor"],
            "stats_comparison": ["stats_comparator"],
            "geospatial_analysis": ["geospatial_mapper"],
            "incident_detection": ["incident_detector"],
            # Reporting and visualization (these don't exist yet)
            "report_generation": ["anomaly_report_generator"],
            "visualization": ["visualization_generator"],
            "summary_report": ["report_summarizer"]
        }
    
    def create_execution_plan(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create execution plan from extracted metadata
        
        Args:
            metadata: Structured metadata from Context Extraction Layer
                     Contains: goal, constraints, data_type, parameters, etc.
        
        Returns:
            Structured JSON with:
            - execution_plan: Tool chain with order and dependencies
            - conflicts: List of conflicts found
            - requires_user_feedback: Whether user input is needed
            - reasoning: Explanation of the plan
            - fallback_options: Alternative plans if primary fails
        """
        logger.info(f"Creating execution plan for goal: {metadata.get('goal')}")
        
        goal = metadata.get("goal", "unknown")
        constraints = metadata.get("constraints", {})
        data_type = metadata.get("data_type", "tabular")
        parameters = metadata.get("parameters", {})
        
        # Step 1: Planning - Determine tools
        tools = self._select_tools(goal, data_type, constraints)
        
        # Step 2: Decision Making - Choose execution strategy
        strategy = self._determine_strategy(tools, constraints)
        
        # Step 3: Conflict Handling - Check for issues
        conflicts = self._detect_conflicts(tools, metadata)
        
        # Step 4: Build execution plan
        execution_plan = self._build_execution_plan(
            tools, strategy, parameters, conflicts
        )
        
        # Step 5: Handle conflicts
        requires_feedback, resolved_plan = self._handle_conflicts(
            execution_plan, conflicts, metadata
        )
        
        result = {
            "execution_plan": resolved_plan,
            "conflicts": conflicts,
            "requires_user_feedback": requires_feedback,
            "reasoning": self._generate_reasoning(goal, tools, strategy, conflicts),
            "fallback_options": self._generate_fallbacks(goal, tools),
            "metadata": {
                "goal": goal,
                "data_type": data_type,
                "tool_count": len(tools)
            }
        }
        
        logger.info(f"Plan created: {len(tools)} tools, strategy={strategy}, conflicts={len(conflicts)}")
        return result
    
    def _select_tools(
        self,
        goal: str,
        data_type: str,
        constraints: Dict[str, Any]
    ) -> List[str]:
        """Select appropriate tools based on goal and constraints"""
        
        selected_tools = []
        
        # Check if clarification is required - don't select any tools
        if goal == "clarification_required":
            logger.warning("Clarification required - no tools will be selected")
            return []
        
        # Check for forced tools (manual mode)
        if "forced_tools" in constraints:
            forced = constraints["forced_tools"]
            logger.info(f"Using manually selected tools: {forced}")
            return forced
        
        # Check for composite goals (e.g., "detect anomalies and generate report")
        # Look for keywords that indicate multiple goals
        goal_lower = goal.lower()
        
        # Primary goal tools
        candidate_tools = self.goal_to_tools.get(goal, [])
        
        if not candidate_tools:
            logger.warning(f"No tools found for goal: {goal}")
        else:
            selected_tools.extend(candidate_tools)
        
        # Secondary goal detection (report, visualization, summary)
        if any(keyword in goal_lower for keyword in ["report", "reporting", "document"]):
            if "report_generation" in self.goal_to_tools:
                selected_tools.extend(self.goal_to_tools["report_generation"])
        
        if any(keyword in goal_lower for keyword in ["visualiz", "chart", "graph", "plot"]):
            if "visualization" in self.goal_to_tools:
                selected_tools.extend(self.goal_to_tools["visualization"])
        
        if any(keyword in goal_lower for keyword in ["summary", "summarize"]):
            if "summary_report" in self.goal_to_tools:
                selected_tools.extend(self.goal_to_tools["summary_report"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in selected_tools:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        
        # Only add feature_engineering if explicitly mentioned in the goal
        if "feature" in goal_lower or "engineer" in goal_lower:
            fe_tool = self.tool_registry.get_tool("feature_engineering")
            if fe_tool and "feature_engineering" not in unique_tools:
                unique_tools.insert(0, "feature_engineering")
        
        logger.info(f"Selected {len(unique_tools)} tools for goal '{goal}': {unique_tools}")
        return unique_tools
    
    def _determine_strategy(
        self,
        tools: List[str],
        constraints: Dict[str, Any]
    ) -> str:
        """Determine execution strategy"""
        
        if len(tools) <= 1:
            return "single"
        
        # Check if tools can run in parallel
        # (e.g., multiple independent analyses on same data)
        if all(tool in ["anomaly_zscore", "clustering", "stats_comparator"] for tool in tools):
            return "parallel"
        
        # Check for dependencies
        if "feature_engineering" in tools:
            return "sequential"  # FE must run first
        
        # Default to sequential for safety
        return "sequential"
    
    def _detect_conflicts(
        self,
        tools: List[str],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts in tool selection"""
        conflicts = []
        
        # Conflict 1: Tool unavailable
        for tool in tools:
            if not self.tool_registry.get_tool(tool):
                conflicts.append({
                    "type": "tool_unavailable",
                    "tool": tool,
                    "message": f"Tool {tool} not available in registry",
                    "severity": "high"
                })
        
        # Conflict 2: Missing required parameters
        # NOTE: We don't check for missing 'metric' here because:
        # 1. Metric is typically provided via form input (req.params), not extracted from prompt
        # 2. The invocation layer will use req.params which merges form inputs
        # 3. False positive conflicts confuse users when everything is actually fine
        goal = metadata.get("goal")
        parameters = metadata.get("parameters", {})
        
        # Only check for parameters that MUST come from the prompt text
        # (not form inputs like metric, timestamp_field, key_fields)
        if goal == "clustering" and "n_clusters" not in parameters:
            # n_clusters should be in prompt or will use default
            pass  # This is actually OK, we have defaults
        
        # Conflict 3: Data type mismatch
        data_type = metadata.get("data_type")
        if goal == "timeseries_forecasting" and data_type != "timeseries":
            conflicts.append({
                "type": "data_type_mismatch",
                "expected": "timeseries",
                "actual": data_type,
                "message": "Forecasting requires timeseries data",
                "severity": "medium"
            })
        
        # Conflict 4: Constraint violations
        constraints = metadata.get("constraints", {})
        if "max_time" in constraints:
            # Check if tool execution might exceed time limit
            pass  # TODO: Implement time estimation
        
        return conflicts
    
    def _build_execution_plan(
        self,
        tools: List[str],
        strategy: str,
        parameters: Dict[str, Any],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build detailed execution plan"""
        
        tool_chain = []
        
        for i, tool_name in enumerate(tools):
            tool_info = self.tool_registry.get_tool(tool_name)
            if not tool_info:
                continue
            
            # Extract REST endpoint from endpoints object
            endpoints = tool_info.get("endpoints", {})
            rest_endpoint = endpoints.get("REST") if isinstance(endpoints, dict) else None
            
            tool_spec = {
                "tool_id": tool_name,
                "tool_endpoint": rest_endpoint,
                "order": i + 1,
                "params": self._build_tool_params(tool_name, parameters),
                "depends_on": [i] if i > 0 and strategy == "sequential" else [],
                "timeout": 30,  # seconds
                "retry_count": 2
            }
            
            tool_chain.append(tool_spec)
        
        return {
            "strategy": strategy,
            "tools": tool_chain,
            "estimated_duration": self._estimate_duration(tool_chain, strategy)
        }
    
    def _build_tool_params(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build tool-specific parameters"""
        params = {}
        
        # Common parameters
        if "metric" in parameters:
            params["metric"] = parameters["metric"]
        if "column" in parameters:
            params["column"] = parameters["column"]
        if "window" in parameters:
            params["window"] = parameters["window"]
        
        # Tool-specific parameters
        if tool_name == "anomaly_zscore":
            params["zscore_threshold"] = parameters.get("threshold", 2.0)
            params["contamination"] = 0.05
        elif tool_name == "clustering":
            params["n_clusters"] = parameters.get("n_clusters", 3)
            params["algorithm"] = parameters.get("algorithm", "kmeans")
        elif tool_name == "timeseries_forecaster":
            params["forecast_horizon"] = parameters.get("horizon", 10)
        
        return params
    
    def _handle_conflicts(
        self,
        execution_plan: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Handle conflicts based on strategy
        
        Returns:
            (requires_user_feedback, resolved_plan)
        """
        if not conflicts:
            return False, execution_plan
        
        high_severity_conflicts = [c for c in conflicts if c.get("severity") == "high"]
        
        if self.conflict_strategy == ConflictResolution.USER_FEEDBACK:
            if high_severity_conflicts:
                logger.info("High severity conflicts detected, requesting user feedback")
                return True, execution_plan
        
        elif self.conflict_strategy == ConflictResolution.AUTO_SELECT:
            # Try to resolve automatically
            resolved_plan = self._auto_resolve_conflicts(execution_plan, conflicts, metadata)
            return False, resolved_plan
        
        elif self.conflict_strategy == ConflictResolution.CREATE_NEW:
            # Suggest creating new tool
            logger.info("Suggesting new tool creation for unavailable tools")
            return True, execution_plan
        
        return False, execution_plan
    
    def _auto_resolve_conflicts(
        self,
        execution_plan: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatically resolve conflicts"""
        
        resolved_plan = execution_plan.copy()
        
        for conflict in conflicts:
            if conflict["type"] == "missing_parameter":
                # Add default parameter
                param = conflict["parameter"]
                if param == "metric":
                    # Try to infer from data characteristics
                    data_chars = metadata.get("data_characteristics", {})
                    columns = data_chars.get("columns", [])
                    if columns and len(columns) > 1:
                        # Use first numeric-looking column
                        resolved_plan["tools"][0]["params"]["metric"] = columns[-1]
                        logger.info(f"Auto-resolved missing metric to: {columns[-1]}")
            
            elif conflict["type"] == "tool_unavailable":
                # Remove unavailable tool from chain
                tool_name = conflict["tool"]
                resolved_plan["tools"] = [
                    t for t in resolved_plan["tools"] if t["tool_id"] != tool_name
                ]
                logger.warning(f"Removed unavailable tool: {tool_name}")
        
        return resolved_plan
    
    def _generate_reasoning(
        self,
        goal: str,
        tools: List[str],
        strategy: str,
        conflicts: List[Dict[str, Any]]
    ) -> str:
        """Generate explanation for the plan"""
        
        reasoning = f"Goal: {goal}. "
        
        if len(tools) == 0:
            reasoning += "No suitable tools found. "
        elif len(tools) == 1:
            reasoning += f"Single tool ({tools[0]}) selected. "
        else:
            reasoning += f"{len(tools)} tools chained: {', '.join(tools)}. "
        
        reasoning += f"Execution strategy: {strategy}. "
        
        if conflicts:
            reasoning += f"{len(conflicts)} conflicts detected. "
        else:
            reasoning += "No conflicts. "
        
        return reasoning
    
    def _generate_fallbacks(
        self,
        goal: str,
        primary_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate fallback options"""
        fallbacks = []
        
        # Fallback 1: Simpler alternative
        if goal == "clustering" and "clustering" in primary_tools:
            fallbacks.append({
                "option": "Use simpler k-means with default params",
                "tools": ["clustering"],
                "params_override": {"algorithm": "kmeans", "n_clusters": 3}
            })
        
        # Fallback 2: Manual analysis
        fallbacks.append({
            "option": "Export data for manual analysis",
            "tools": [],
            "action": "export_data"
        })
        
        return fallbacks
    
    def _estimate_duration(
        self,
        tool_chain: List[Dict[str, Any]],
        strategy: str
    ) -> float:
        """Estimate execution duration in seconds"""
        
        tool_times = {
            "anomaly_zscore": 2.0,
            "clustering": 3.0,
            "feature_engineering": 1.5,
            "timeseries_forecaster": 4.0,
            "classifier_regressor": 3.5,
            "stats_comparator": 1.5,
            "geospatial_mapper": 2.5,
            "incident_detector": 1.0
        }
        
        if strategy == "parallel":
            return max(tool_times.get(t["tool_id"], 2.0) for t in tool_chain)
        else:
            return sum(tool_times.get(t["tool_id"], 2.0) for t in tool_chain)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== MCP Tools Chaining Manager Examples ===\n")
    
    # Mock tool registry
    class MockRegistry:
        def list_tools(self):
            return ["anomaly_zscore", "clustering", "feature_engineering"]
        
        def get(self, tool_name):
            tools = {
                "anomaly_zscore": {"endpoint": "http://anomaly:8000/run"},
                "clustering": {"endpoint": "http://clustering:8000/run"},
                "feature_engineering": {"endpoint": "http://feature:8000/run"}
            }
            return tools.get(tool_name)
    
    manager = MCPToolsChainingManager(
        tool_registry=MockRegistry(),
        conflict_strategy=ConflictResolution.AUTO_SELECT
    )
    
    # Example 1: Simple anomaly detection
    print("1. Simple Anomaly Detection:")
    metadata1 = {
        "goal": "anomaly_detection",
        "constraints": {"threshold": 2.5},
        "data_type": "timeseries",
        "parameters": {"metric": "speed_kmh"},
        "data_characteristics": {"row_count": 1000}
    }
    plan1 = manager.create_execution_plan(metadata1)
    print(json.dumps(plan1, indent=2))
    print()
    
    # Example 2: Multi-tool with conflict
    print("2. Multi-tool with Missing Parameter:")
    metadata2 = {
        "goal": "anomaly_detection",
        "constraints": {},
        "data_type": "timeseries",
        "parameters": {},  # Missing metric
        "data_characteristics": {"row_count": 1000, "columns": ["timestamp", "value"]}
    }
    plan2 = manager.create_execution_plan(metadata2)
    print(json.dumps(plan2, indent=2))
