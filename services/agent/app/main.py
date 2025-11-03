from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from .schemas.api import AnalyzeRequest, AnalyzeResponse, RunResponse
from .router.rule_router import RuleRouter
from .dispatcher.dispatcher import Dispatcher
from .registry.registry import ToolRegistry
from .security.auth import verify_jwt_stub
from .observability.otel import init_tracing
from .observability.timeline import TimelineTracker
from .intent_extraction.extractor import IntentExtractor, ExtractionMethod
from .planner.planner import TaskPlanner


app = FastAPI(title="MCP Agent v2", version="v2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
tool_registry = ToolRegistry()
router = RuleRouter(tool_registry)
dispatcher = Dispatcher(tool_registry)
timeline_tracker = TimelineTracker()

# New v2 components
intent_extractor = IntentExtractor(method=ExtractionMethod.HYBRID)
task_planner = TaskPlanner()

init_tracing(service_name="mcp-agent-v2")


def _aggregate_results(execution_result: dict) -> dict:
    """
    Aggregate results from multiple tool executions
    Combines outputs from parallel or sequential tasks
    """
    results = execution_result.get("results", [])
    
    if not results:
        return {"status": "no_results", "message": "No tool results to aggregate"}
    
    # If single result, return it directly
    if len(results) == 1:
        return results[0].get("output", {})
    
    # Multiple results: combine them
    aggregated = {
        "combined_results": [],
        "summary": {
            "total_tasks": len(results),
            "successful_tasks": sum(1 for r in results if r.get("status") == "success"),
            "failed_tasks": sum(1 for r in results if r.get("status") == "error")
        }
    }
    
    for result in results:
        if result.get("status") == "success":
            tool_output = result.get("output", {})
            aggregated["combined_results"].append({
                "tool": result.get("tool"),
                "output": tool_output
            })
    
    return aggregated


@app.post("/v2/analyze", response_model=AnalyzeResponse)
def analyze_v2(req: AnalyzeRequest, authorization: str | None = Header(default=None)):
    """
    Enhanced v2 endpoint with full pipeline:
    User Input (500 words) -> Intent Extraction (RLB/Regex/ML/Hybrid) 
    -> Planning (LLM, 50 words) -> Tool Invocation (Dispatcher, unified/parallel)
    """
    # Auth (stub)
    verify_jwt_stub(authorization)
    
    # Start timeline tracking
    timeline = timeline_tracker.start_request(req.tenant_id)
    
    try:
        # Step 1: Intent Extraction (Person 1)
        timeline_tracker.log_task_start(timeline, "intent", "Intent & Entity Extraction")
        
        # Extract user input from context or use task
        user_input = req.context.get("user_input") or req.context.get("task", "")
        if not user_input:
            user_input = f"{req.context.get('task', 'analyze')} with metric {req.params.get('metric', 'unknown')}"
        
        extraction_result = intent_extractor.extract(user_input)
        timeline_tracker.log_task_complete(
            timeline, "intent",
            metadata={
                "intent": extraction_result["intent"],
                "confidence": extraction_result["confidence"],
                "method": extraction_result["method_used"]
            }
        )
        logger.info(f"Intent extraction: {extraction_result['intent']} (confidence: {extraction_result['confidence']})")
        
        # Step 2: Planning & Decision Making (Person 1)
        timeline_tracker.log_task_start(timeline, "planning", "Planning & Decision Making")
        
        plan = task_planner.create_plan(
            intent=extraction_result["intent"],
            entities=extraction_result["entities"],
            data_info={"row_count": len(req.data_pointer.rows) if req.data_pointer.rows else 0},
            context=req.context
        )
        timeline_tracker.log_task_complete(
            timeline, "planning",
            metadata={
                "task_count": len(plan["tasks"]),
                "strategy": plan["strategy"],
                "reasoning": plan["reasoning"]
            }
        )
        logger.info(f"Plan created: {len(plan['tasks'])} tasks, strategy={plan['strategy']}")
        
        # Step 3: Tool Invocation (Person 2)
        timeline_tracker.log_task_start(timeline, "execution", "Tool Execution (Dispatcher)")
        
        # Execute plan
        plan["trace_id"] = timeline.request_id
        execution_result = dispatcher.execute_plan(plan, req)
        
        timeline_tracker.log_task_complete(
            timeline, "execution",
            metadata={
                "results_count": len(execution_result.get("results", [])),
                "strategy_used": execution_result.get("strategy")
            }
        )
        
        # Step 4: Result Aggregation (Person 2)
        timeline_tracker.log_task_start(timeline, "aggregation", "Result Aggregation")
        
        # Aggregate results from all tasks
        aggregated_output = _aggregate_results(execution_result)
        
        timeline_tracker.log_task_complete(timeline, "aggregation")
        
        # Complete timeline
        completed_timeline = timeline_tracker.complete_request(req.tenant_id)
        
        return AnalyzeResponse(
            request_id=timeline.request_id,
            status="ok",
            result=aggregated_output,
            tool_meta={
                "pipeline_version": "v2",
                "intent": extraction_result["intent"],
                "confidence": extraction_result["confidence"],
                "extraction_method": extraction_result["method_used"],
                "plan": plan,
                "execution_strategy": execution_result.get("strategy"),
                "timeline": completed_timeline.to_dict() if completed_timeline else None,
                "duration_seconds": completed_timeline.get_duration() if completed_timeline else 0
            }
        )
    
    except Exception as e:
        timeline_tracker.log_task_failed(timeline, "pipeline", str(e))
        timeline_tracker.complete_request(req.tenant_id)
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, authorization: str | None = Header(default=None)):
    """
    Legacy v1 endpoint (backward compatibility)
    Uses simple rule-based routing without full pipeline
    """
    # auth (stub)
    verify_jwt_stub(authorization)

    # route
    decision = router.route(req)
    if not decision.tool:
        raise HTTPException(status_code=400, detail="No matching tool for request")

    # dispatch (sync path)
    result = dispatcher.invoke(decision, req)
    logger.info(f"Decision={decision.model_dump()}")
    return AnalyzeResponse(
        request_id=decision.request_id,
        status="ok",
        result=result.get("output", {}),
        tool_meta={"invoked":[f"{decision.tool}@{decision.version}"], "trace_id": decision.trace_id}
    )

@app.get("/v1/tools")
def list_tools():
    return tool_registry.list_tools()

@app.get("/v1/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str):
    # stub for now
    return RunResponse(run_id=run_id, status="SUCCEEDED", steps=[])
