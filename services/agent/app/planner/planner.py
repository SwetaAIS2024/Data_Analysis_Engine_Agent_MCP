"""
Planning & Decision Maker (LLM-based)
Creates execution plans from extracted intents with 50-word limit
Determines whether tools should run in parallel or sequentially
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import json


class ExecutionStrategy(Enum):
    """Execution strategy for tools"""
    UNIFIED = "unified"  # Sequential execution
    PARALLEL = "parallel"  # Parallel execution
    CONDITIONAL = "conditional"  # Based on previous results


class TaskPlanner:
    """
    LLM-based Planning & Decision Maker
    
    Takes extracted intent/entities and creates an execution plan
    - Limited to 50 words for LLM prompts (efficiency)
    - Decides on unified (sequential) vs parallel execution
    - Handles multi-step workflows
    
    Example:
        planner = TaskPlanner()
        plan = planner.create_plan(
            intent="anomaly_detection",
            entities={"metric": "speed_kmh", "threshold": 2.5}
        )
    """
    
    def __init__(self, llm_endpoint: Optional[str] = None):
        """
        Initialize planner
        
        Args:
            llm_endpoint: Optional LLM API endpoint (OpenAI, Azure, local model)
                         If None, uses rule-based planning
        """
        self.llm_endpoint = llm_endpoint
        self.use_llm = llm_endpoint is not None
        
        # Tool dependency graph (for determining execution order)
        self.tool_dependencies = {
            "feature_engineering": [],  # No dependencies
            "anomaly_detection": [],  # No dependencies
            "clustering": ["feature_engineering"],  # Better with engineered features
            "classification": ["feature_engineering"],  # Needs features
            "regression": ["feature_engineering"],  # Needs features
            "timeseries_forecasting": ["feature_engineering"],  # Can benefit from features
            "stats_comparison": ["anomaly_detection"],  # Compare after detecting anomalies
            "incident_detection": ["anomaly_detection"],  # Based on anomalies
        }
    
    def create_plan(
        self,
        intent: str,
        entities: Dict[str, Any],
        data_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create execution plan from intent and entities
        
        Args:
            intent: Primary intent from extraction
            entities: Extracted entities (parameters)
            data_info: Information about the dataset (columns, size, etc.)
            context: Additional context (user preferences, history, etc.)
        
        Returns:
            Execution plan with:
            - tasks: List of tasks to execute
            - strategy: Execution strategy (unified/parallel)
            - reasoning: Brief explanation (max 50 words)
            - dependencies: Task dependencies
        """
        if self.use_llm:
            return self._llm_based_planning(intent, entities, data_info, context)
        else:
            return self._rule_based_planning(intent, entities, data_info, context)
    
    def _rule_based_planning(
        self,
        intent: str,
        entities: Dict[str, Any],
        data_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Rule-based planning (no LLM required)
        Fast and deterministic planning based on predefined rules
        """
        tasks = []
        strategy = ExecutionStrategy.UNIFIED
        reasoning = ""
        
        # Single intent case
        if intent != "unknown":
            task = {
                "tool": self._map_intent_to_tool(intent),
                "params": self._build_tool_params(intent, entities),
                "order": 1
            }
            tasks.append(task)
            strategy = ExecutionStrategy.UNIFIED
            reasoning = f"Single task: {intent}. Execute sequentially."
        
        # Check for implicit multi-task scenarios
        # Example: "detect anomalies and cluster" -> two tasks
        if self._is_multi_task(entities):
            tasks = self._decompose_multi_task(intent, entities, data_info)
            strategy = self._determine_strategy(tasks)
            reasoning = f"{len(tasks)} tasks identified. {'Parallel' if strategy == ExecutionStrategy.PARALLEL else 'Sequential'} execution."
        
        # Limit reasoning to 50 words
        reasoning_words = reasoning.split()
        if len(reasoning_words) > 50:
            reasoning = " ".join(reasoning_words[:50]) + "..."
        
        return {
            "tasks": tasks,
            "strategy": strategy.value,
            "reasoning": reasoning,
            "dependencies": self._build_dependency_graph(tasks),
            "estimated_time": self._estimate_execution_time(tasks, strategy)
        }
    
    def _llm_based_planning(
        self,
        intent: str,
        entities: Dict[str, Any],
        data_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LLM-based planning using 50-word prompt limit
        
        In production, this would call an LLM API with a concise prompt:
        - Intent and entities
        - Available tools
        - Data characteristics
        - Request: decompose into tasks, determine execution order
        
        Example LLM prompt (< 50 words):
        "Intent: anomaly_detection. Entities: {threshold: 2.5, metric: speed_kmh}.
         Tools: [anomaly_zscore, clustering, feature_engineering].
         Data: timeseries, 1000 rows. Plan: list tasks, order, parallel/sequential?"
        """
        # TODO: Implement actual LLM call
        # For now, use rule-based as fallback
        
        plan = self._rule_based_planning(intent, entities, data_info, context)
        plan["method"] = "llm_fallback"
        plan["note"] = "LLM not available, using rule-based planning"
        return plan
    
    def _map_intent_to_tool(self, intent: str) -> str:
        """Map intent to actual tool name"""
        intent_to_tool = {
            "anomaly_detection": "anomaly_zscore",
            "clustering": "clustering",
            "feature_engineering": "feature_engineering",
            "timeseries_forecasting": "timeseries_forecaster",
            "classification": "classifier_regressor",
            "regression": "classifier_regressor",
            "stats_comparison": "stats_comparator",
            "geospatial_analysis": "geospatial_mapper",
            "incident_detection": "incident_detector"
        }
        return intent_to_tool.get(intent, "unknown")
    
    def _build_tool_params(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Build tool-specific parameters from extracted entities"""
        params = {}
        
        # Common parameters
        if "threshold" in entities:
            params["threshold"] = entities["threshold"]
        if "metric" in entities:
            params["metric"] = entities["metric"]
        if "column_name" in entities:
            params["column"] = entities["column_name"]
        if "window" in entities:
            params["window"] = entities["window"]
        
        # Tool-specific parameters
        if intent == "anomaly_detection":
            params["zscore_threshold"] = entities.get("zscore", entities.get("threshold", 2.0))
            params["contamination"] = entities.get("contamination", 0.05)
        elif intent == "clustering":
            params["n_clusters"] = entities.get("n_clusters", 3)
            params["algorithm"] = entities.get("algorithm", "kmeans")
        elif intent == "timeseries_forecasting":
            params["forecast_horizon"] = entities.get("horizon", 10)
            params["seasonal_period"] = entities.get("seasonality", 7)
        
        return params
    
    def _is_multi_task(self, entities: Dict[str, Any]) -> bool:
        """Check if entities suggest multiple tasks"""
        # Look for keywords suggesting multiple tasks
        multi_task_indicators = [
            "and then", "followed by", "after that", "also",
            "additionally", "plus", "combine", "both"
        ]
        
        raw_input = entities.get("raw_input", "")
        return any(indicator in raw_input.lower() for indicator in multi_task_indicators)
    
    def _decompose_multi_task(
        self,
        primary_intent: str,
        entities: Dict[str, Any],
        data_info: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Decompose complex request into multiple tasks
        
        Example: "detect anomalies and cluster the normal points"
        -> Task 1: anomaly_detection
        -> Task 2: clustering (depends on Task 1)
        """
        tasks = []
        
        # Add primary task
        tasks.append({
            "tool": self._map_intent_to_tool(primary_intent),
            "params": self._build_tool_params(primary_intent, entities),
            "order": 1
        })
        
        # Check for secondary intents in entities
        raw_input = entities.get("raw_input", "").lower()
        
        if "cluster" in raw_input and primary_intent != "clustering":
            tasks.append({
                "tool": "clustering",
                "params": {"n_clusters": entities.get("n_clusters", 3)},
                "order": 2,
                "depends_on": [1]
            })
        
        if "feature" in raw_input and primary_intent != "feature_engineering":
            tasks.insert(0, {
                "tool": "feature_engineering",
                "params": {},
                "order": 0
            })
            # Update orders
            for i, task in enumerate(tasks[1:], start=1):
                task["order"] = i
        
        return tasks
    
    def _determine_strategy(self, tasks: List[Dict[str, Any]]) -> ExecutionStrategy:
        """
        Determine execution strategy based on task dependencies
        
        - If tasks are independent: PARALLEL
        - If tasks have dependencies: UNIFIED (sequential)
        - If conditional logic needed: CONDITIONAL
        """
        # Check for dependencies
        has_dependencies = any("depends_on" in task for task in tasks)
        
        if has_dependencies:
            return ExecutionStrategy.UNIFIED
        elif len(tasks) > 1:
            # Multiple independent tasks -> parallel
            return ExecutionStrategy.PARALLEL
        else:
            return ExecutionStrategy.UNIFIED
    
    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build dependency graph for task execution"""
        graph = {}
        for task in tasks:
            task_id = f"task_{task['order']}"
            dependencies = []
            if "depends_on" in task:
                dependencies = [f"task_{dep}" for dep in task["depends_on"]]
            graph[task_id] = dependencies
        return graph
    
    def _estimate_execution_time(
        self,
        tasks: List[Dict[str, Any]],
        strategy: ExecutionStrategy
    ) -> Dict[str, Any]:
        """
        Estimate execution time for the plan
        Useful for timeline tracking (2-person team)
        """
        # Rough time estimates per tool (in seconds)
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
        
        total_time = sum(tool_times.get(task["tool"], 2.0) for task in tasks)
        
        if strategy == ExecutionStrategy.PARALLEL:
            # Parallel execution: max of all task times
            total_time = max(tool_times.get(task["tool"], 2.0) for task in tasks)
        
        return {
            "estimated_seconds": total_time,
            "task_count": len(tasks),
            "strategy": strategy.value
        }


# Example usage and framework
if __name__ == "__main__":
    print("=== Planning & Decision Maker Examples ===\n")
    
    planner = TaskPlanner()
    
    # Example 1: Simple single-task plan
    print("1. Simple Anomaly Detection Plan:")
    plan1 = planner.create_plan(
        intent="anomaly_detection",
        entities={"threshold": 2.5, "metric": "speed_kmh", "contamination": 0.05}
    )
    print(f"   Tasks: {len(plan1['tasks'])}")
    print(f"   Strategy: {plan1['strategy']}")
    print(f"   Reasoning: {plan1['reasoning']}")
    print(f"   Estimated time: {plan1['estimated_time']['estimated_seconds']}s\n")
    
    # Example 2: Multi-task plan
    print("2. Multi-task Plan (Feature Engineering + Clustering):")
    plan2 = planner.create_plan(
        intent="clustering",
        entities={
            "n_clusters": 4,
            "raw_input": "first create features and then cluster the data into 4 groups"
        }
    )
    print(f"   Tasks: {len(plan2['tasks'])}")
    for i, task in enumerate(plan2['tasks'], 1):
        print(f"      Task {i}: {task['tool']} (order: {task['order']})")
    print(f"   Strategy: {plan2['strategy']}")
    print(f"   Dependencies: {plan2['dependencies']}")
    print(f"   Reasoning: {plan2['reasoning']}")
    print(f"   Estimated time: {plan2['estimated_time']['estimated_seconds']}s\n")
    
    # Example 3: Parallel execution plan
    print("3. Parallel Execution Plan:")
    plan3 = planner.create_plan(
        intent="anomaly_detection",
        entities={
            "raw_input": "detect anomalies in speed and also in temperature"
        }
    )
    print(f"   Tasks: {len(plan3['tasks'])}")
    print(f"   Strategy: {plan3['strategy']}")
    print(f"   Reasoning: {plan3['reasoning']}\n")
    
    print("=== Plan Structure Example ===")
    print(json.dumps(plan1, indent=2))
