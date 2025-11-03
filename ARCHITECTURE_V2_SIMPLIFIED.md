# Data Analysis Engine Agent - V2 Simplified Architecture

## Overview
This document describes the **simplified V2 architecture** that focuses on metadata-driven tool chaining with planning, decision making, and conflict resolution.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Data + User Prompt                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 1: Context Extraction                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Extract structured metadata from prompt + data:            │  │
│  │ • goal: What user wants to accomplish                      │  │
│  │ • constraints: Limitations/requirements                    │  │
│  │ • data_type: timeseries/geospatial/categorical/etc         │  │
│  │ • parameters: Key-value parameters                         │  │
│  │ • data_characteristics: Stats about the data               │  │
│  │ • user_preferences: Output format, thresholds, etc         │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Component: ContextExtractor                                    │
│  Methods: rule_based, regex, hybrid                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│            STEP 2: MCP Tools Chaining Manager                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Planning:                                                  │  │
│  │ • Select appropriate tools based on goal + data_type      │  │
│  │ • Determine execution strategy (single/parallel/sequence) │  │
│  │                                                            │  │
│  │ Decision Making:                                           │  │
│  │ • Choose optimal tool combinations                        │  │
│  │ • Set tool parameters and dependencies                    │  │
│  │                                                            │  │
│  │ Conflict Handling:                                         │  │
│  │ • Detect: tool_unavailable, missing_parameter, etc        │  │
│  │ • Resolve: USER_FEEDBACK / AUTO_SELECT / CREATE_NEW       │  │
│  │ • Generate fallback options                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Component: MCPToolsChainingManager                             │
│  Output: Structured JSON execution plan                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│               STEP 3: Tools Invocation Layer                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Execute tools based on plan:                              │  │
│  │ • Single tool execution                                   │  │
│  │ • Parallel execution (independent tools)                  │  │
│  │ • Sequential execution (chained tools)                    │  │
│  │                                                            │  │
│  │ Handle scenarios:                                          │  │
│  │ • Tool combinations                                       │  │
│  │ • Tool unavailability → request user feedback            │  │
│  │ • Create new tool with user specifications               │  │
│  │ • Retry on failure                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Component: MCPToolsInvocationLayer                             │
│  Features: Concurrent execution, retry logic, feedback         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 4: UI Output + Logging                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ • Aggregate tool results                                  │  │
│  │ • Format for UI display                                   │  │
│  │ • Include user feedback requests if needed                │  │
│  │ • Log each step comprehensively                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Format: JSON with status, results, metadata                    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. ContextExtractor
**File:** `services/agent/app/intent_extraction/context_extractor.py`

**Purpose:** Extract structured metadata from user prompt and data sample

**Input:**
- User prompt (string)
- Data sample (optional)

**Output:**
```python
{
    "goal": str,  # What user wants to accomplish
    "constraints": [str],  # Limitations like time limits, thresholds
    "data_type": str,  # "timeseries", "geospatial", "categorical", etc
    "data_characteristics": {
        "row_count": int,
        "has_timestamps": bool,
        "numeric_columns": [str],
        "categorical_columns": [str]
    },
    "parameters": {
        "metric": str,
        "threshold": float,
        # ... other extracted parameters
    },
    "user_preferences": {
        "output_format": str,
        "visualization": bool
    }
}
```

**Methods:**
- `rule_based`: Pattern matching on keywords
- `regex`: Regex-based parameter extraction
- `hybrid`: Combination approach (default)

---

### 2. MCPToolsChainingManager
**File:** `services/agent/app/planner/chaining_manager.py`

**Purpose:** Planning, decision making, and conflict handling for tool execution

**Input:**
- Context metadata (from ContextExtractor)
- Available tools list

**Output:**
```python
{
    "execution_plan": {
        "strategy": str,  # "single", "parallel", "sequential"
        "tools": [
            {
                "tool_id": str,
                "tool_endpoint": str,
                "params": dict,
                "order": int,  # For sequential execution
                "retry_count": int
            }
        ]
    },
    "conflicts": [
        {
            "type": str,  # "tool_unavailable", "missing_parameter", etc
            "severity": str,  # "high", "medium", "low"
            "description": str,
            "resolution": str  # "USER_FEEDBACK", "AUTO_SELECT", "CREATE_NEW"
        }
    ],
    "requires_user_feedback": bool,
    "reasoning": str,  # Brief explanation of decisions
    "fallback_options": [
        {"option": str, "tools": [str]}
    ]
}
```

**Capabilities:**
- **Planning:** Select tools based on goal and data type
- **Decision Making:** Determine execution strategy
- **Conflict Detection:** Identify issues before execution
- **Conflict Resolution:** Auto-resolve or request user feedback
- **Fallback Generation:** Provide alternatives

---

### 3. MCPToolsInvocationLayer
**File:** `services/agent/app/dispatcher/invocation_layer.py`

**Purpose:** Execute tools based on structured plan

**Features:**
- **Single Execution:** Run one tool
- **Parallel Execution:** Run independent tools concurrently
- **Sequential Execution:** Chain tools (output → input)
- **Retry Logic:** Automatic retry on transient failures
- **User Feedback:** Request input when tools unavailable
- **Tool Creation:** Support creating new tools

**Input:**
- Execution plan (from MCPToolsChainingManager)
- Request data (original user data)

**Output:**
```python
{
    "status": str,  # "success", "partial_success", "failed", "needs_feedback"
    "results": [
        {
            "tool_id": str,
            "status": str,
            "output": dict,
            "error": str
        }
    ],
    "summary": {
        "total_tools": int,
        "successful": int,
        "failed": int,
        "unavailable": int
    },
    "user_feedback_required": {  # Optional
        "message": str,
        "options": [...]
    }
}
```

---

## API Endpoint

### POST /v2/analyze

**Request:**
```json
{
    "tenant_id": "string",
    "data_pointer": {
        "rows": [...]
    },
    "params": {},
    "context": {
        "task": "string"
    }
}
```

**Response:**
```json
{
    "request_id": "uuid",
    "status": "ok",
    "result": {
        "status": "success",
        "results": [...],
        "summary": {},
        "user_feedback": null
    },
    "tool_meta": {
        "pipeline_version": "v2_simplified",
        "context_extraction": {},
        "execution_plan": {},
        "invocation_status": "success",
        "duration_seconds": 2.34
    }
}
```

---

## Logging

Each step logs comprehensively:

```
[REQUEST <uuid>] Starting V2 pipeline
[REQUEST <uuid>] STEP 1: Context Extraction - START
[REQUEST <uuid>] Context extracted - Goal: detect anomalies
[REQUEST <uuid>] Data type: timeseries
[REQUEST <uuid>] STEP 1: Context Extraction - COMPLETE
[REQUEST <uuid>] STEP 2: MCP Tools Chaining Manager - START
[REQUEST <uuid>] Strategy: single
[REQUEST <uuid>] Tools: ['anomaly_zscore']
[REQUEST <uuid>] STEP 2: MCP Tools Chaining Manager - COMPLETE
[REQUEST <uuid>] STEP 3: Tools Invocation - START
[REQUEST <uuid>] Invoking tool: anomaly_zscore
[REQUEST <uuid>] Tool anomaly_zscore succeeded
[REQUEST <uuid>] STEP 3: Tools Invocation - COMPLETE
[REQUEST <uuid>] Pipeline duration: 1.23s
[REQUEST <uuid>] Pipeline FINISHED - Status: success
```

Logs saved to: `logs/agent_v2.log` with rotation

---

## Key Improvements Over V1

1. **Metadata-Driven:** Context extraction provides structured metadata instead of verbose VP input
2. **Unified Planning:** Single component handles planning, decisions, and conflicts
3. **Conflict Resolution:** Proactive detection and resolution of issues
4. **User Feedback:** Clear mechanism for requesting user input when needed
5. **Comprehensive Logging:** Every step logged with request ID tracing
6. **Tool Combinations:** Support for parallel and sequential tool execution
7. **Fallback Options:** Alternative plans when primary plan fails

---

## Configuration

No configuration files needed. Components are initialized in `main.py`:

```python
context_extractor = ContextExtractor()
chaining_manager = MCPToolsChainingManager(tool_registry)
invocation_layer = MCPToolsInvocationLayer(tool_registry)
```

---

## Example Scenarios

### Scenario 1: Simple Anomaly Detection
**Input:** "Detect anomalies in sales data with threshold 2.5"

**Flow:**
1. Context: `{goal: "detect_anomalies", data_type: "timeseries", parameters: {threshold: 2.5}}`
2. Plan: `{strategy: "single", tools: ["anomaly_zscore"]}`
3. Execute: Run anomaly_zscore tool
4. Output: Anomaly detection results

### Scenario 2: Tool Unavailable
**Input:** "Analyze customer segments"

**Flow:**
1. Context: `{goal: "segment_analysis", data_type: "categorical"}`
2. Plan: Detects "cluster_segmentation" tool unavailable
3. Conflict: `{type: "tool_unavailable", resolution: "USER_FEEDBACK"}`
4. Feedback: Request user to create tool or use alternative

### Scenario 3: Sequential Pipeline
**Input:** "Forecast sales after detecting outliers"

**Flow:**
1. Context: `{goal: "forecast_with_cleaning", data_type: "timeseries"}`
2. Plan: `{strategy: "sequential", tools: ["anomaly_zscore", "timeseries_forecaster"]}`
3. Execute: anomaly_zscore → timeseries_forecaster (chained)
4. Output: Combined results

---

## Development

### Running Locally
```bash
cd services/agent
python -m app.main
```

### Testing
```bash
# Test context extraction
python -m app.intent_extraction.context_extractor

# Test chaining manager
python -m app.planner.chaining_manager

# Test invocation layer
python -m app.dispatcher.invocation_layer
```

---

## Migration from V1

V1 components deprecated:
- `intent_extraction/extractor.py` → Use `context_extractor.py`
- `planner/planner.py` → Use `chaining_manager.py`
- `observability/timeline.py` → Removed (use logging instead)

V1 endpoint still available at `/v1/analyze` for backward compatibility.

---

## Future Enhancements

1. **LLM Integration:** Use LLM for advanced context extraction
2. **Tool Creation API:** Programmatically create new tools
3. **Learning System:** Learn from user feedback to improve planning
4. **Advanced Conflict Resolution:** ML-based conflict resolution
5. **Distributed Execution:** Support distributed tool execution

---

**Last Updated:** 2025-01-20  
**Version:** 2.0 Simplified  
**Branch:** DAA_v2
