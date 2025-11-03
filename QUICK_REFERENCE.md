# Quick Reference - DAA V2 Simplified Architecture

## 🚀 Quick Start

### Run the Agent
```bash
cd services/agent
uvicorn app.main:app --reload --port 8000
```

### Test Endpoint
```bash
curl -X POST http://localhost:8000/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test",
    "data_pointer": {
      "rows": [
        {"timestamp": "2025-01-01", "value": 100},
        {"timestamp": "2025-01-02", "value": 105},
        {"timestamp": "2025-01-03", "value": 500}
      ]
    },
    "params": {},
    "context": {
      "task": "Detect anomalies with threshold 2.5"
    }
  }'
```

---

## 📂 File Locations

| Component | File Path |
|-----------|-----------|
| Context Extractor | `services/agent/app/intent_extraction/context_extractor.py` |
| Chaining Manager | `services/agent/app/planner/chaining_manager.py` |
| Invocation Layer | `services/agent/app/dispatcher/invocation_layer.py` |
| Main API | `services/agent/app/main.py` |
| Architecture Docs | `ARCHITECTURE_V2_SIMPLIFIED.md` |
| Implementation Summary | `IMPLEMENTATION_SUMMARY.md` |

---

## 🔄 Pipeline Flow

```
1. INPUT
   ↓
2. ContextExtractor.extract(prompt, data_sample)
   → {goal, constraints, data_type, parameters, ...}
   ↓
3. MCPToolsChainingManager.create_execution_plan(context, tools)
   → {execution_plan, conflicts, requires_user_feedback, ...}
   ↓
4. MCPToolsInvocationLayer.execute(plan, request_data)
   → {status, results, summary, user_feedback_required}
   ↓
5. UI OUTPUT
```

---

## 🎯 Component Quick Reference

### ContextExtractor
```python
from app.intent_extraction.context_extractor import ContextExtractor

extractor = ContextExtractor()
result = extractor.extract(
    prompt="Detect anomalies in sales",
    data_sample=[{"value": 100}, ...]
)

# Returns:
# {
#   "goal": "detect_anomalies",
#   "data_type": "timeseries",
#   "constraints": [...],
#   "parameters": {...},
#   "data_characteristics": {...},
#   "user_preferences": {...}
# }
```

### MCPToolsChainingManager
```python
from app.planner.chaining_manager import MCPToolsChainingManager

manager = MCPToolsChainingManager(tool_registry)
plan = manager.create_execution_plan(
    context_metadata=context_result,
    available_tools=tool_registry.list_tools()
)

# Returns:
# {
#   "execution_plan": {
#     "strategy": "single|parallel|sequential",
#     "tools": [...]
#   },
#   "conflicts": [...],
#   "requires_user_feedback": bool,
#   "reasoning": "...",
#   "fallback_options": [...]
# }
```

### MCPToolsInvocationLayer
```python
from app.dispatcher.invocation_layer import MCPToolsInvocationLayer

invocation = MCPToolsInvocationLayer(tool_registry)
result = invocation.execute(
    execution_plan=plan,
    request_data={"input": {...}, "params": {...}}
)

# Returns:
# {
#   "status": "success|partial_success|failed|needs_feedback",
#   "results": [...],
#   "summary": {...},
#   "user_feedback_required": {...}  # Optional
# }
```

---

## 🏷️ Execution Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `single` | Execute one tool | Simple anomaly detection |
| `parallel` | Execute multiple tools concurrently | Compare multiple algorithms |
| `sequential` | Chain tools (output → input) | Clean data then forecast |

---

## ⚠️ Conflict Types

| Type | Description | Resolution Options |
|------|-------------|-------------------|
| `tool_unavailable` | Requested tool doesn't exist | USER_FEEDBACK, AUTO_SELECT, CREATE_NEW |
| `missing_parameter` | Required parameter not provided | USER_FEEDBACK, USE_DEFAULT |
| `data_type_mismatch` | Tool incompatible with data type | USER_FEEDBACK, AUTO_SELECT |
| `incompatible_tools` | Selected tools conflict | AUTO_SELECT, USER_FEEDBACK |

---

## 📊 Response Status Values

| Status | Meaning |
|--------|---------|
| `success` | All tools executed successfully |
| `partial_success` | Some tools succeeded, some failed |
| `failed` | All tools failed |
| `needs_feedback` | User input required to proceed |

---

## 🔍 Logging Format

```
[REQUEST {uuid}] {message}
```

**Example:**
```
[REQUEST 12345] Starting V2 pipeline
[REQUEST 12345] STEP 1: Context Extraction - START
[REQUEST 12345] Context extracted - Goal: detect anomalies
[REQUEST 12345] Data type: timeseries
[REQUEST 12345] STEP 1: Context Extraction - COMPLETE
```

**Log Files:**
- Console: `stdout`
- File: `logs/agent_v2.log` (rotates at 100 MB, keeps 7 days)

---

## 🛠️ Testing Components

```bash
# Test Context Extractor
python -m app.intent_extraction.context_extractor

# Test Chaining Manager
python -m app.planner.chaining_manager

# Test Invocation Layer
python -m app.dispatcher.invocation_layer
```

---

## 📝 Example Scenarios

### Scenario 1: Simple Tool Execution
**Input:** "Detect anomalies with threshold 2.5"

**Flow:**
1. Context: `{goal: "detect_anomalies", parameters: {threshold: 2.5}}`
2. Plan: `{strategy: "single", tools: ["anomaly_zscore"]}`
3. Execute: Run anomaly_zscore
4. Output: Anomalies detected

### Scenario 2: Tool Unavailable
**Input:** "Analyze sentiment"

**Flow:**
1. Context: `{goal: "sentiment_analysis"}`
2. Plan: Detect tool unavailable
3. Conflict: `{type: "tool_unavailable", resolution: "USER_FEEDBACK"}`
4. Feedback: Offer to create tool or use alternative

### Scenario 3: Sequential Execution
**Input:** "Clean data and forecast"

**Flow:**
1. Context: `{goal: "forecast_with_cleaning"}`
2. Plan: `{strategy: "sequential", tools: ["anomaly_zscore", "timeseries_forecaster"]}`
3. Execute: anomaly_zscore → timeseries_forecaster
4. Output: Forecast results

---

## 🔗 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/analyze` | POST | New simplified pipeline |
| `/v1/analyze` | POST | Legacy endpoint (backward compatible) |
| `/v1/tools` | GET | List available tools |

---

## 🌿 Git Branch

**Current Branch:** `DAA_v2`

```bash
# Check current branch
git branch

# View commits
git log --oneline

# Push to remote (when ready)
git push origin DAA_v2
```

---

## 📚 Documentation Files

1. **ARCHITECTURE_V2_SIMPLIFIED.md** - Full architecture documentation
2. **IMPLEMENTATION_SUMMARY.md** - Implementation details and features
3. **QUICK_REFERENCE.md** - This file (quick reference)
4. **README.md** - Project overview

---

## 🎯 Key Points to Remember

1. **Context Extraction** replaces verbose VP input → structured metadata
2. **Chaining Manager** handles planning, decisions, AND conflicts in one component
3. **Invocation Layer** supports single/parallel/sequential execution
4. **User Feedback** mechanism for unavailable tools or missing parameters
5. **Logging** is comprehensive with request ID tracking
6. **V1 endpoint** still works for backward compatibility

---

## 🚨 Common Issues

### Issue: Import errors
**Solution:** Make sure you're in the correct directory:
```bash
cd services/agent
python -m app.main
```

### Issue: Tool not found
**Solution:** Check tool registry:
```bash
curl http://localhost:8000/v1/tools
```

### Issue: Logs not appearing
**Solution:** Check logs directory exists:
```bash
mkdir -p logs
```

---

## 📞 Component Interaction

```
┌─────────────────┐
│   main.py       │
│  (FastAPI)      │
└────────┬────────┘
         │
    ┌────▼────────────────────────┐
    │   /v2/analyze endpoint      │
    └────┬────────────────────────┘
         │
    ┌────▼───────────────────┐
    │  ContextExtractor      │
    └────┬───────────────────┘
         │
    ┌────▼───────────────────┐
    │ MCPToolsChainingManager│
    └────┬───────────────────┘
         │
    ┌────▼───────────────────┐
    │ MCPToolsInvocationLayer│
    └────┬───────────────────┘
         │
    ┌────▼───────────────────┐
    │   Tool Services        │
    │ (anomaly, forecast,..) │
    └────────────────────────┘
```

---

**Last Updated:** 2025-01-20  
**Version:** 2.0 Simplified  
**Branch:** DAA_v2
