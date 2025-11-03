# Data Analysis Engine Agent - Architecture v2 (DAA_v2)

## Overview

This is the **enhanced architecture** for the Data Analysis Engine Agent with:
- **User Input Processing** (up to 500 words via VP - Voice/Text)
- **Intent/Entity Extraction** (RLB, Regex, ML, Hybrid)
- **LLM-based Planning** (50-word limit for efficiency)
- **Parallel/Sequential Tool Invocation**
- **Timeline Tracking** for 2-person teams

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User VP (500 words)                      │
│                    Voice/Text Interface Input                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Intent / Entity Extraction                          │
│  ┌──────────┐  ┌─────────┐  ┌──────┐  ┌─────────┐             │
│  │   RLB    │  │  Regex  │  │  ML  │  │ Hybrid  │             │
│  │(examples)│  │(patterns)│  │(BERT)│  │(combine)│             │
│  └──────────┘  └─────────┘  └──────┘  └─────────┘             │
│           Extract: intent, entities, confidence                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼ (50 words LLM)
┌─────────────────────────────────────────────────────────────────┐
│          Planning & Decision Maker (LLM-based)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Unified    │  │   Parallel   │  │ Conditional  │          │
│  │ (sequential) │  │  (concurrent)│  │(if-then-else)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  Output: Task list, execution strategy, dependencies            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                Tool Invocation (Dispatcher)                      │
│  Execute tasks based on strategy:                                │
│  • Sequential: Task1 → Task2 → Task3                            │
│  • Parallel:   Task1 ║ Task2 ║ Task3                            │
│  • Pipeline:   Task1 → Task2(uses Task1 output)                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       If Tools Block                             │
│  Conditional logic:                                              │
│  • If anomalies found → trigger incident detector                │
│  • If clusters < threshold → suggest feature engineering         │
│  • If accuracy low → recommend more data                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Result Aggregation                            │
│  Combine outputs, format response, return to user               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Intent/Entity Extraction (`services/agent/app/intent_extraction/`)
- **Purpose**: Parse user input (up to 500 words) and extract structured information
- **Methods**:
  - **RLB (Rule-based)**: Pattern matching with predefined rules
  - **Regex**: Regular expression-based entity extraction
  - **ML**: Machine learning (BERT, NER models)
  - **Hybrid**: Combination of multiple methods (recommended)
- **Output**: `{intent, entities, confidence, method_used}`
- **Timeline**: 0.1-2 seconds
- **Owner**: Person 1 (AI/ML Engineer)

**Example**:
```python
from services.agent.app.intent_extraction import IntentExtractor, ExtractionMethod

extractor = IntentExtractor(method=ExtractionMethod.HYBRID)
result = extractor.extract("Detect anomalies in speed_kmh with threshold 2.5")
# Output: {intent: "anomaly_detection", entities: {threshold: 2.5, metric: "speed_kmh"}}
```

---

### 2. Planning & Decision Maker (`services/agent/app/planner/`)
- **Purpose**: Create execution plan from extracted intent with LLM (50-word limit)
- **Strategies**:
  - **Unified**: Sequential execution (Task1 → Task2 → Task3)
  - **Parallel**: Concurrent execution (Task1 ║ Task2 ║ Task3)
  - **Conditional**: Based on previous results
- **Output**: `{tasks, strategy, reasoning, dependencies, estimated_time}`
- **Timeline**: 0.2-3 seconds
- **Owner**: Person 1 (AI/ML Engineer)

**Example**:
```python
from services.agent.app.planner import TaskPlanner

planner = TaskPlanner()
plan = planner.create_plan(
    intent="anomaly_detection",
    entities={"threshold": 2.5},
    data_info={"row_count": 1000}
)
# Output: {tasks: [...], strategy: "unified", reasoning: "Single task: anomaly_detection. Execute sequentially."}
```

---

### 3. Enhanced Dispatcher (`services/agent/app/dispatcher/dispatcher.py`)
- **Purpose**: Execute tools based on plan (parallel/sequential)
- **Features**:
  - Sequential execution with result pipelining
  - Parallel execution with thread pool
  - HMAC signing for security
  - Error handling and result aggregation
- **Timeline**: 1-10 seconds per tool
- **Owner**: Person 2 (Backend Engineer)

**Example**:
```python
from services.agent.app.dispatcher import Dispatcher

dispatcher = Dispatcher(tool_registry)
result = dispatcher.execute_plan(plan, request)
# Output: {strategy: "sequential", results: [...], status: "completed"}
```

---

### 4. Timeline Tracking (`services/agent/app/observability/timeline.py`)
- **Purpose**: Track execution timeline for 2-person teams
- **Features**:
  - Event logging (start, complete, failed)
  - Duration tracking
  - Rough time estimates for each component
  - Statistics and reporting
- **Timeline**: Always running in background
- **Owner**: Both Person 1 & Person 2

**Example**:
```python
from services.agent.app.observability import TimelineTracker

tracker = TimelineTracker()
timeline = tracker.start_request("req-123")
tracker.log_task_start(timeline, "intent", "Intent Extraction")
# ... work happens ...
tracker.log_task_complete(timeline, "intent", metadata={"intent": "anomaly_detection"})
```

---

## API Endpoints

### POST `/v2/analyze` (New Enhanced Pipeline)
Full pipeline with intent extraction → planning → tool invocation

**Request**:
```json
{
  "tenant_id": "dev-tenant",
  "mode": "sync",
  "context": {
    "user_input": "Detect anomalies in sensor data with threshold 2.5 and group similar patterns"
  },
  "data_pointer": {
    "uri": "inline://rows",
    "format": "inline",
    "rows": [...]
  },
  "params": {
    "metric": "speed_kmh",
    "timestamp_field": "timestamp"
  }
}
```

**Response**:
```json
{
  "request_id": "req-123",
  "status": "ok",
  "result": {...},
  "tool_meta": {
    "pipeline_version": "v2",
    "intent": "anomaly_detection",
    "confidence": 0.9,
    "extraction_method": "hybrid",
    "plan": {
      "tasks": [...],
      "strategy": "sequential",
      "reasoning": "..."
    },
    "timeline": {
      "duration_seconds": 5.2,
      "events": [...]
    }
  }
}
```

### POST `/v1/analyze` (Legacy)
Backward-compatible endpoint with simple rule-based routing

---

## Rough Timeline Estimates (2-Person Team)

| Component | Time (seconds) | Owner |
|-----------|----------------|-------|
| User Input (VP) | 0-2 | User |
| Intent Extraction | 0.1-2 | Person 1 (AI/ML) |
| Planning (LLM, 50 words) | 0.2-3 | Person 1 (AI/ML) |
| Tool Invocation | 1-10 per tool | Person 2 (Backend) |
| If Tools (conditional) | 0.1-1 | Person 2 (Backend) |
| Result Aggregation | 0.1-2 | Person 2 (Backend) |
| **Total** | **2-20 seconds** | **Team** |

---

## Framework Examples

### 1. Rule-Based Extraction (RLB)
```python
# Define keyword patterns
patterns = {
    "anomaly_detection": ["detect anomalies", "find outliers", "unusual patterns"],
    "clustering": ["cluster", "group data", "segment"]
}

# Match against user input
if "detect anomalies" in user_input.lower():
    intent = "anomaly_detection"
```

### 2. Regex Entity Extraction
```python
import re

# Extract threshold
threshold_match = re.search(r"threshold\s+(?:of\s+)?(\d+\.?\d*)", user_input, re.I)
if threshold_match:
    entities["threshold"] = float(threshold_match.group(1))

# Extract window
window_match = re.search(r"window\s+(?:of\s+)?(\d+\s*(?:min|hour|day))", user_input, re.I)
if window_match:
    entities["window"] = window_match.group(1)
```

### 3. LLM Planning (50-word prompt)
```text
Intent: anomaly_detection. Entities: {threshold: 2.5, metric: speed_kmh}.
Available tools: [anomaly_zscore, clustering, feature_engineering].
Data: timeseries, 1000 rows, 3 columns.
Question: Decompose into tasks. Specify execution order. Parallel or sequential?
```

### 4. Parallel Execution
```python
# Submit tasks to thread pool
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(invoke_tool, "anomaly_zscore", params1),
        executor.submit(invoke_tool, "clustering", params2),
        executor.submit(invoke_tool, "stats_comparator", params3)
    ]
    
    # Collect results
    results = [f.result() for f in futures]
```

---

## Running the New Architecture

### 1. Start Services
```bash
cd Data_Analysis_Engine_Agent
docker-compose up -d
```

### 2. Test v2 Endpoint
```bash
curl -X POST http://localhost:8080/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "dev",
    "mode": "sync",
    "context": {
      "user_input": "Find anomalies in sensor data with zscore 2.5"
    },
    "data_pointer": {
      "uri": "inline://rows",
      "format": "inline",
      "rows": [...]
    },
    "params": {
      "metric": "speed_kmh"
    }
  }'
```

### 3. Run Examples
```bash
# Intent extraction example
python -m services.agent.app.intent_extraction.extractor

# Planning example
python -m services.agent.app.planner.planner

# Timeline tracking example
python -m services.agent.app.observability.timeline
```

---

## Development Workflow (2-Person Team)

### Person 1 (AI/ML Engineer)
- **Focus**: Intent extraction, Planning, LLM integration
- **Files**:
  - `services/agent/app/intent_extraction/`
  - `services/agent/app/planner/`
- **Tasks**:
  1. Improve extraction accuracy (add more patterns, train ML models)
  2. Enhance planning logic (better task decomposition)
  3. Integrate actual LLM API (OpenAI, Azure, local)

### Person 2 (Backend Engineer)
- **Focus**: Dispatcher, Tool execution, Result aggregation
- **Files**:
  - `services/agent/app/dispatcher/dispatcher.py`
  - `services/agent/app/main.py`
  - `services/tools/*/`
- **Tasks**:
  1. Optimize parallel execution (async, better thread management)
  2. Implement conditional execution logic
  3. Add more tools and improve existing ones

---

## Migration from v1 to v2

| Feature | v1 (Legacy) | v2 (New) |
|---------|-------------|----------|
| User Input | Context field | `context.user_input` (500 words) |
| Intent Detection | Rule-based router | RLB/Regex/ML/Hybrid extraction |
| Planning | Implicit | Explicit LLM-based planner (50 words) |
| Execution | Single tool | Multiple tools (parallel/sequential) |
| Timeline | No tracking | Full timeline with estimates |
| Endpoint | `/v1/analyze` | `/v2/analyze` |

**Backward Compatibility**: `/v1/analyze` still works for legacy clients.

---

## Next Steps

1. **ML Model Integration**: Train and deploy actual ML models for intent classification
2. **LLM Integration**: Connect to OpenAI/Azure for planning
3. **Conditional Logic**: Implement "If Tools" block for smart decision-making
4. **Performance Optimization**: Async execution, caching, batching
5. **UI Enhancement**: Update frontend to use v2 endpoint and show timeline

---

## Contact

- **Person 1 (AI/ML)**: Focus on `intent_extraction/` and `planner/`
- **Person 2 (Backend)**: Focus on `dispatcher/` and `main.py`

For questions or issues, check the framework examples in each module's `__main__` block.
