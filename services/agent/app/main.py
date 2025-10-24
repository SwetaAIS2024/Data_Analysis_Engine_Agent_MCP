from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from .schemas.api import AnalyzeRequest, AnalyzeResponse, RunResponse
from .router.rule_router import RuleRouter
from .dispatcher.dispatcher import Dispatcher
from .registry.registry import ToolRegistry
from .security.auth import verify_jwt_stub
from .observability.otel import init_tracing


app = FastAPI(title="MCP Agent", version="v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tool_registry = ToolRegistry()
router = RuleRouter(tool_registry)
dispatcher = Dispatcher(tool_registry)

init_tracing(service_name="mcp-agent")

@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, authorization: str | None = Header(default=None)):
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
