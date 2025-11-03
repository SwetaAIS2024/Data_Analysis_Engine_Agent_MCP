from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import uuid
import time
from .schemas.api import AnalyzeRequest, AnalyzeResponse, RunResponse
from .dispatcher.invocation_layer import MCPToolsInvocationLayer
from .registry.registry import ToolRegistry
from .observability.otel import init_tracing
from .intent_extraction.context_extractor import ContextExtractor
from .planner.chaining_manager import MCPToolsChainingManager

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/agent_v2.log",
    rotation="100 MB",
    retention="7 days",
    level="DEBUG"
)

app = FastAPI(title="MCP Agent v2 - Simplified Architecture", version="v2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
tool_registry = ToolRegistry()

# V2 Simplified Pipeline Components
context_extractor = ContextExtractor()
chaining_manager = MCPToolsChainingManager(tool_registry)
invocation_layer = MCPToolsInvocationLayer(tool_registry)

init_tracing(service_name="mcp-agent-v2")


@app.post("/v2/analyze", response_model=AnalyzeResponse)
def analyze_v2(req: AnalyzeRequest):
    """
    Simplified V2 Pipeline:
    Input (Data + Prompt) → Context Extraction → MCP Tools Chaining Manager → Tools Invocation → UI Output
    
    Each step has comprehensive logging.
    """
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[REQUEST {request_id}] Starting V2 pipeline")
    logger.info(f"[REQUEST {request_id}] Tenant: {req.tenant_id}")
    
    try:
        # STEP 1: CONTEXT EXTRACTION
        logger.info(f"[REQUEST {request_id}] STEP 1: Context Extraction - START")
        
        # Build user prompt from request
        user_prompt = req.context.get("task", "")
        if not user_prompt:
            user_prompt = f"Analyze data with metric: {req.params.get('metric', 'unknown')}"
        
        # Extract context metadata
        context_result = context_extractor.extract(
            prompt=user_prompt,
            data_sample=req.data_pointer.rows[:5] if req.data_pointer.rows else []
        )
        
        logger.info(f"[REQUEST {request_id}] Context extracted - Goal: {context_result['goal']}")
        logger.info(f"[REQUEST {request_id}] Data type: {context_result['data_type']}")
        logger.info(f"[REQUEST {request_id}] Constraints: {context_result['constraints']}")
        logger.info(f"[REQUEST {request_id}] Parameters: {context_result['parameters']}")
        logger.info(f"[REQUEST {request_id}] STEP 1: Context Extraction - COMPLETE")
        
        # STEP 2: MCP TOOLS CHAINING MANAGER (Planning & Decision Making)
        logger.info(f"[REQUEST {request_id}] STEP 2: MCP Tools Chaining Manager - START")
        
        execution_plan = chaining_manager.create_execution_plan(
            context_metadata=context_result,
            available_tools=tool_registry.list_tools()
        )
        
        logger.info(f"[REQUEST {request_id}] Execution plan created")
        logger.info(f"[REQUEST {request_id}] Strategy: {execution_plan['execution_plan']['strategy']}")
        logger.info(f"[REQUEST {request_id}] Tools: {[t['tool_id'] for t in execution_plan['execution_plan']['tools']]}")
        logger.info(f"[REQUEST {request_id}] Conflicts detected: {len(execution_plan['conflicts'])}")
        logger.info(f"[REQUEST {request_id}] Requires user feedback: {execution_plan['requires_user_feedback']}")
        
        if execution_plan.get("reasoning"):
            logger.info(f"[REQUEST {request_id}] Reasoning: {execution_plan['reasoning']}")
        
        logger.info(f"[REQUEST {request_id}] STEP 2: MCP Tools Chaining Manager - COMPLETE")
        
        # STEP 3: TOOLS INVOCATION
        logger.info(f"[REQUEST {request_id}] STEP 3: Tools Invocation - START")
        
        # Build request data for tools
        request_data = {
            "input": {
                "rows": req.data_pointer.rows or [],
                "columns": list(req.data_pointer.rows[0].keys()) if req.data_pointer.rows else []
            },
            "params": {
                **req.params,
                **context_result["parameters"]
            },
            "context": {
                **req.context,
                "goal": context_result["goal"],
                "data_type": context_result["data_type"]
            }
        }
        
        # Execute tools
        invocation_result = invocation_layer.execute(
            execution_plan=execution_plan,
            request_data=request_data
        )
        
        logger.info(f"[REQUEST {request_id}] Invocation status: {invocation_result['status']}")
        logger.info(f"[REQUEST {request_id}] Results: {invocation_result.get('summary', {})}")
        
        if invocation_result.get("user_feedback_required"):
            logger.warning(f"[REQUEST {request_id}] User feedback required")
            logger.info(f"[REQUEST {request_id}] Feedback options: {invocation_result['user_feedback_required']}")
        
        logger.info(f"[REQUEST {request_id}] STEP 3: Tools Invocation - COMPLETE")
        
        # STEP 4: UI OUTPUT PREPARATION
        logger.info(f"[REQUEST {request_id}] STEP 4: UI Output Preparation - START")
        
        # Aggregate tool results
        final_output = {
            "status": invocation_result["status"],
            "results": invocation_result.get("results", []),
            "summary": invocation_result.get("summary", {}),
            "user_feedback": invocation_result.get("user_feedback_required")
        }
        
        duration = time.time() - start_time
        logger.info(f"[REQUEST {request_id}] Pipeline duration: {duration:.2f}s")
        logger.info(f"[REQUEST {request_id}] STEP 4: UI Output Preparation - COMPLETE")
        logger.info(f"[REQUEST {request_id}] Pipeline FINISHED - Status: {invocation_result['status']}")
        
        return AnalyzeResponse(
            request_id=request_id,
            status="ok",
            result=final_output,
            tool_meta={
                "pipeline_version": "v2_simplified",
                "context_extraction": {
                    "goal": context_result["goal"],
                    "data_type": context_result["data_type"],
                    "constraints": context_result["constraints"]
                },
                "execution_plan": {
                    "strategy": execution_plan["execution_plan"]["strategy"],
                    "tools": [t["tool_id"] for t in execution_plan["execution_plan"]["tools"]],
                    "conflicts": execution_plan["conflicts"]
                },
                "invocation_status": invocation_result["status"],
                "duration_seconds": duration
            }
        )
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[REQUEST {request_id}] Pipeline FAILED after {duration:.2f}s")
        logger.error(f"[REQUEST {request_id}] Error: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tools")
def list_tools():
    """Get list of available tools"""
    return tool_registry.list_tools()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "v2.0.0"}

