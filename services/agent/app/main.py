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
    
    # Initialize pipeline logs for UI display
    pipeline_logs = []
    
    def add_log(layer: str, level: str, message: str, details: dict = None):
        """Add a log entry for UI display"""
        pipeline_logs.append({
            "timestamp": time.time(),
            "layer": layer,
            "level": level,
            "message": message,
            "details": details or {}
        })
    
    logger.info(f"[REQUEST {request_id}] Starting V2 pipeline")
    logger.info(f"[REQUEST {request_id}] Tenant: {req.tenant_id}")
    
    add_log("PIPELINE", "INFO", "🚀 V2 Pipeline started", {
        "request_id": request_id,
        "tenant_id": req.tenant_id
    })
    
    try:
        # STEP 1: CONTEXT EXTRACTION
        logger.info(f"[REQUEST {request_id}] STEP 1: Context Extraction - START")
        add_log("CONTEXT_EXTRACTION", "INFO", "📋 Starting context extraction", {
            "step": "1/4"
        })
        
        # Build user prompt from request
        user_prompt = req.context.get("task", "")
        if not user_prompt:
            user_prompt = f"Analyze data with metric: {req.params.get('metric', 'unknown')}"
        
        add_log("CONTEXT_EXTRACTION", "INFO", f"📝 User prompt: '{user_prompt}'")
        
        # Prepare data info for context extraction
        data_info = None
        if req.data_pointer.rows:
            data_info = {
                "rows": req.data_pointer.rows[:5],  # Sample first 5 rows
                "row_count": len(req.data_pointer.rows),
                "columns": list(req.data_pointer.rows[0].keys()) if req.data_pointer.rows else []
            }
            add_log("CONTEXT_EXTRACTION", "INFO", f"📊 Data loaded: {len(req.data_pointer.rows)} rows, {len(data_info['columns'])} columns", {
                "columns": data_info['columns']
            })
        
        # Extract context metadata
        context_result = context_extractor.extract(
            user_prompt=user_prompt,
            data_info=data_info
        )
        
        add_log("CONTEXT_EXTRACTION", "SUCCESS", f"✅ Context extracted successfully", {
            "goal": context_result['goal'],
            "data_type": context_result.get('data_type'),
            "confidence": context_result.get('confidence', 0.0),
            "extraction_method": context_result.get('extraction_method'),
            "constraints": context_result.get('constraints', {})
        })
        
        # Check if clarification is required
        if context_result.get("requires_clarification"):
            logger.warning(f"[REQUEST {request_id}] User clarification required - ambiguous prompt")
            logger.info(f"[REQUEST {request_id}] Original prompt: {user_prompt}")
            logger.info(f"[REQUEST {request_id}] Suggested options: {[opt['id'] for opt in context_result.get('suggested_options', [])]}")
            
            add_log("CONTEXT_EXTRACTION", "WARNING", "⚠️ Clarification required - ambiguous prompt", {
                "suggested_options": [opt['id'] for opt in context_result.get('suggested_options', [])]
            })
            
            duration = time.time() - start_time
            
            return AnalyzeResponse(
                request_id=request_id,
                status="clarification_required",
                result={
                    "status": "clarification_required",
                    "user_feedback": {
                        "message": context_result.get("clarification_message"),
                        "type": "clarification",
                        "options": context_result.get("suggested_options", [])
                    },
                    "pipeline_logs": pipeline_logs
                },
                tool_meta={
                    "pipeline_version": "v2_simplified",
                    "context_extraction": {
                        "goal": context_result["goal"],
                        "confidence": context_result.get("confidence", 0.0),
                        "ambiguous_prompt": True
                    },
                    "duration_seconds": duration
                }
            )
        
        # Check if forced tools are specified (for manual mode)
        forced_tools = req.context.get("force_tools")
        if forced_tools:
            logger.info(f"[REQUEST {request_id}] Manual tool selection mode - Forced tools: {forced_tools}")
            context_result["forced_tools"] = forced_tools
            add_log("CONTEXT_EXTRACTION", "INFO", "🔧 Manual tool selection mode", {
                "forced_tools": forced_tools
            })
        
        logger.info(f"[REQUEST {request_id}] Context extracted - Goal: {context_result['goal']}")
        logger.info(f"[REQUEST {request_id}] Data type: {context_result['data_type']}")
        logger.info(f"[REQUEST {request_id}] Constraints: {context_result['constraints']}")
        logger.info(f"[REQUEST {request_id}] Parameters: {context_result['parameters']}")
        logger.info(f"[REQUEST {request_id}] STEP 1: Context Extraction - COMPLETE")
        
        # STEP 2: MCP TOOLS CHAINING MANAGER (Planning & Decision Making)
        logger.info(f"[REQUEST {request_id}] STEP 2: MCP Tools Chaining Manager - START")
        add_log("CHAINING_MANAGER", "INFO", "🔗 Starting execution plan creation", {
            "step": "2/4",
            "goal": context_result['goal']
        })
        
        execution_plan = chaining_manager.create_execution_plan(
            metadata=context_result
        )
        
        add_log("CHAINING_MANAGER", "SUCCESS", f"✅ Execution plan created", {
            "strategy": execution_plan['execution_plan']['strategy'],
            "tools_count": len(execution_plan['execution_plan']['tools']),
            "tools": [t['tool_id'] for t in execution_plan['execution_plan']['tools']],
            "conflicts_detected": len(execution_plan['conflicts']),
            "requires_user_feedback": execution_plan['requires_user_feedback']
        })
        
        logger.info(f"[REQUEST {request_id}] Execution plan created")
        logger.info(f"[REQUEST {request_id}] Strategy: {execution_plan['execution_plan']['strategy']}")
        logger.info(f"[REQUEST {request_id}] Tools: {[t['tool_id'] for t in execution_plan['execution_plan']['tools']]}")
        logger.info(f"[REQUEST {request_id}] Conflicts detected: {len(execution_plan['conflicts'])}")
        logger.info(f"[REQUEST {request_id}] Requires user feedback: {execution_plan['requires_user_feedback']}")
        
        if execution_plan.get("reasoning"):
            logger.info(f"[REQUEST {request_id}] Reasoning: {execution_plan['reasoning']}")
            add_log("CHAINING_MANAGER", "INFO", f"💭 Planning reasoning: {execution_plan['reasoning']}")
        
        # Log individual tools
        for idx, tool in enumerate(execution_plan['execution_plan']['tools'], 1):
            add_log("CHAINING_MANAGER", "INFO", f"🔧 Tool {idx}: {tool['tool_id']}", {
                "tool_id": tool['tool_id'],
                "priority": tool.get('priority'),
                "dependencies": tool.get('dependencies', [])
            })
        
        if execution_plan['conflicts']:
            for conflict in execution_plan['conflicts']:
                add_log("CHAINING_MANAGER", "WARNING", f"⚠️ Conflict detected: {conflict}")
        
        logger.info(f"[REQUEST {request_id}] STEP 2: MCP Tools Chaining Manager - COMPLETE")
        
        # STEP 3: TOOLS INVOCATION
        logger.info(f"[REQUEST {request_id}] STEP 3: Tools Invocation - START")
        add_log("INVOCATION_LAYER", "INFO", "⚙️ Starting tool invocation", {
            "step": "3/4",
            "tools_to_invoke": [t['tool_id'] for t in execution_plan['execution_plan']['tools']]
        })
        
        # Build request data for tools - must match tool schema expectations
        request_data = {
            "input": {
                "frame_uri": req.data_pointer.uri or "inline://memory",
                "rows": req.data_pointer.rows or [],
                "schema": {
                    "timestamp": req.params.get("timestamp_field", "timestamp"),
                    "entity_keys": req.params.get("key_fields", []),
                    "metric": req.params.get("metric", "value")
                }
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
        
        add_log("INVOCATION_LAYER", "INFO", f"📦 Request data prepared", {
            "input_rows": len(request_data['input']['rows']),
            "params": list(request_data['params'].keys()),
            "context_goal": request_data['context']['goal']
        })
        
        # Execute tools
        invocation_result = invocation_layer.execute(
            execution_plan=execution_plan,
            request_data=request_data
        )
        
        add_log("INVOCATION_LAYER", "SUCCESS" if invocation_result['status'] == 'success' else "WARNING", 
                f"✅ Invocation completed - Status: {invocation_result['status']}", {
            "status": invocation_result['status'],
            "results_count": len(invocation_result.get('results', [])),
            "summary": invocation_result.get('summary', {})
        })
        
        # Log individual tool results
        for result in invocation_result.get('results', []):
            status_emoji = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'error' else "⚠️"
            add_log("INVOCATION_LAYER", "SUCCESS" if result['status'] == 'success' else "ERROR",
                    f"{status_emoji} {result.get('tool_name', result['tool_id'])}: {result.get('status_message', result['status'])}", {
                "tool_id": result['tool_id'],
                "status": result['status'],
                "execution_summary": result.get('execution_summary', {})
            })
        
        logger.info(f"[REQUEST {request_id}] Invocation status: {invocation_result['status']}")
        logger.info(f"[REQUEST {request_id}] Results: {invocation_result.get('summary', {})}")
        
        if invocation_result.get("user_feedback_required"):
            logger.warning(f"[REQUEST {request_id}] User feedback required")
            logger.info(f"[REQUEST {request_id}] Feedback options: {invocation_result['user_feedback_required']}")
            add_log("INVOCATION_LAYER", "WARNING", "⚠️ User feedback required", {
                "feedback_options": invocation_result['user_feedback_required']
            })
        
        logger.info(f"[REQUEST {request_id}] STEP 3: Tools Invocation - COMPLETE")
        
        # STEP 4: UI OUTPUT PREPARATION
        logger.info(f"[REQUEST {request_id}] STEP 4: UI Output Preparation - START")
        add_log("OUTPUT_PREPARATION", "INFO", "📤 Preparing final output", {
            "step": "4/4"
        })
        
        # Aggregate tool results
        final_output = {
            "status": invocation_result["status"],
            "results": invocation_result.get("results", []),
            "summary": invocation_result.get("summary", {}),
            "user_feedback": invocation_result.get("user_feedback_required"),
            "pipeline_logs": pipeline_logs
        }
        
        duration = time.time() - start_time
        add_log("OUTPUT_PREPARATION", "SUCCESS", f"✅ Output prepared successfully", {
            "total_results": len(final_output['results']),
            "status": final_output['status']
        })
        
        add_log("PIPELINE", "SUCCESS", f"🎉 Pipeline completed successfully in {duration:.2f}s", {
            "duration_seconds": duration,
            "status": invocation_result['status']
        })
        
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
        
        add_log("PIPELINE", "ERROR", f"❌ Pipeline failed: {str(e)}", {
            "error": str(e),
            "duration_seconds": duration
        })
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tools")
def list_tools():
    """Get list of available tools"""
    return tool_registry.list_tools()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "v2.0.0"}

