# Pipeline Execution Logging - User Guide

## Overview
The V2 Pipeline now provides comprehensive, real-time logging from ALL pipeline layers for complete visibility into the execution flow.

## Logging Architecture

### 1. **Backend Logging Structure**
All logs are captured and sent to the frontend in the `pipeline_logs` array within the API response.

#### Log Entry Format:
```json
{
  "timestamp": 1699123456.789,
  "layer": "CONTEXT_EXTRACTION",
  "level": "INFO",
  "message": "📋 Starting context extraction",
  "details": {
    "step": "1/4",
    "additional_info": "..."
  }
}
```

### 2. **Pipeline Layers**

#### 🚀 PIPELINE
- Overall pipeline initialization and completion
- Request tracking
- Total execution time

#### 📋 CONTEXT_EXTRACTION (Step 1/4)
- User prompt processing
- Data info extraction (rows, columns)
- Goal identification
- Confidence scoring
- Extraction method (RULE_BASED, ML, LLM, HYBRID)
- Clarification requirements

#### 🔗 CHAINING_MANAGER (Step 2/4)
- Execution plan creation
- Tool selection strategy
- Individual tool planning
- Dependency analysis
- Conflict detection
- Planning reasoning

#### ⚙️ INVOCATION_LAYER (Step 3/4)
- Request data preparation
- Individual tool invocations
- Tool execution status (success/error/warning)
- Execution summaries (anomalies detected, predictions made, etc.)
- Error handling

#### 📤 OUTPUT_PREPARATION (Step 4/4)
- Final result aggregation
- Output formatting
- Pipeline completion status

### 3. **Log Levels**

| Level | Color | Background | Usage |
|-------|-------|------------|-------|
| **INFO** | Blue (#2196f3) | Light Blue (#e3f2fd) | General information, progress updates |
| **SUCCESS** | Green (#4caf50) | Light Green (#e8f5e9) | Successful operations |
| **WARNING** | Orange (#ff9800) | Light Orange (#fff3e0) | Warnings, clarifications needed |
| **ERROR** | Red (#f44336) | Light Red (#ffebee) | Errors, failures |

## Frontend Display

### Pipeline Execution Logs Section
Located after "Pipeline Info" in the results display:

```
📊 Pipeline Execution Logs [N events]
┌──────────────────────────────────────────────────────┐
│ [LAYER] LEVEL  timestamp                             │
│ 🚀 Log message with emoji                            │
│ 📋 Details (expandable)                              │
└──────────────────────────────────────────────────────┘
```

### Features:
- **Color-coded layers**: Each pipeline layer has a unique color
- **Expandable details**: Click "📋 Details" to see additional info
- **Timestamps**: All logs show execution time
- **Scrollable**: Max height 500px with scroll for long logs
- **Emoji indicators**: Visual cues for quick scanning

### Layer Color Coding:
- 🚀 **PIPELINE**: Purple (#9c27b0)
- 📋 **CONTEXT_EXTRACTION**: Blue (#2196f3)
- 🔗 **CHAINING_MANAGER**: Orange (#ff9800)
- ⚙️ **INVOCATION_LAYER**: Green (#4caf50)
- 📤 **OUTPUT_PREPARATION**: Cyan (#00bcd4)

## Example Log Flow

### Successful Execution:
```
1. 🚀 PIPELINE - INFO: V2 Pipeline started
2. 📋 CONTEXT_EXTRACTION - INFO: Starting context extraction
3. 📋 CONTEXT_EXTRACTION - INFO: User prompt: 'detect anomaly'
4. 📋 CONTEXT_EXTRACTION - INFO: Data loaded: 100 rows, 5 columns
5. 📋 CONTEXT_EXTRACTION - SUCCESS: Context extracted successfully
6. 🔗 CHAINING_MANAGER - INFO: Starting execution plan creation
7. 🔗 CHAINING_MANAGER - SUCCESS: Execution plan created
8. 🔗 CHAINING_MANAGER - INFO: Tool 1: anomaly_zscore
9. ⚙️ INVOCATION_LAYER - INFO: Starting tool invocation
10. ⚙️ INVOCATION_LAYER - INFO: Request data prepared
11. ⚙️ INVOCATION_LAYER - SUCCESS: Invocation completed
12. ⚙️ INVOCATION_LAYER - SUCCESS: ✅ Anomaly Detection: Found 15 anomalies
13. 📤 OUTPUT_PREPARATION - INFO: Preparing final output
14. 📤 OUTPUT_PREPARATION - SUCCESS: Output prepared successfully
15. 🚀 PIPELINE - SUCCESS: Pipeline completed successfully in 2.34s
```

### Clarification Required:
```
1. 🚀 PIPELINE - INFO: V2 Pipeline started
2. 📋 CONTEXT_EXTRACTION - INFO: Starting context extraction
3. 📋 CONTEXT_EXTRACTION - INFO: User prompt: 'analyze data'
4. 📋 CONTEXT_EXTRACTION - WARNING: Clarification required - ambiguous prompt
```

### Error Handling:
```
...
10. ⚙️ INVOCATION_LAYER - ERROR: ❌ Anomaly Detection: Connection timeout
11. 🚀 PIPELINE - ERROR: Pipeline failed: Tool invocation error
```

## Log Details

Each log entry can include additional details that are hidden by default and expandable:

### Context Extraction Details:
- `goal`: Extracted goal (e.g., "anomaly_detection")
- `data_type`: Data type (e.g., "timeseries")
- `confidence`: Confidence score (0.0-1.0)
- `extraction_method`: Method used (RULE_BASED, ML, LLM, HYBRID)
- `constraints`: Extracted constraints

### Chaining Manager Details:
- `strategy`: Execution strategy (e.g., "single_tool")
- `tools_count`: Number of tools selected
- `tools`: List of tool IDs
- `conflicts_detected`: Number of conflicts
- `requires_user_feedback`: Whether feedback is needed

### Invocation Layer Details:
- `tool_id`: Tool identifier
- `status`: Execution status
- `execution_summary`: Key metrics (anomalies_detected, rows_processed, etc.)
- `input_rows`: Number of input rows
- `params`: Parameters used

## Benefits

### For Users:
1. **Complete Visibility**: See exactly what the system is doing at each step
2. **Debugging**: Quickly identify where issues occur
3. **Understanding**: Learn how the pipeline processes requests
4. **Confidence**: Verify that the system understood your intent correctly

### For Developers:
1. **Troubleshooting**: Detailed execution flow for debugging
2. **Performance**: Identify bottlenecks in the pipeline
3. **Auditing**: Complete audit trail of all operations
4. **Testing**: Verify each layer is working correctly

## Configuration

### Backend (services/agent/app/main.py):
Logs are automatically collected using the `add_log()` helper function:

```python
def add_log(layer: str, level: str, message: str, details: dict = None):
    """Add a log entry for UI display"""
    pipeline_logs.append({
        "timestamp": time.time(),
        "layer": layer,
        "level": level,
        "message": message,
        "details": details or {}
    })
```

### Frontend (frontend/src/App.js):
Logs are displayed in the "Pipeline Execution Logs" section with:
- Color-coded layers and levels
- Expandable details
- Timestamp display
- Scrollable container

## API Response Structure

```json
{
  "request_id": "uuid",
  "status": "ok",
  "result": {
    "status": "success",
    "results": [...],
    "summary": {...},
    "pipeline_logs": [
      {
        "timestamp": 1699123456.789,
        "layer": "CONTEXT_EXTRACTION",
        "level": "INFO",
        "message": "📋 Starting context extraction",
        "details": {
          "step": "1/4"
        }
      },
      ...
    ]
  },
  "tool_meta": {...}
}
```

## Best Practices

### Adding New Logs:
1. Use descriptive emojis for quick visual scanning
2. Include relevant details in the `details` object
3. Use appropriate log levels (INFO, SUCCESS, WARNING, ERROR)
4. Keep messages concise but informative

### Reading Logs:
1. Look for color patterns - red/orange indicate issues
2. Expand details for in-depth information
3. Check timestamps to identify slow operations
4. Follow the 4-step pipeline flow (Context → Chaining → Invocation → Output)

## Troubleshooting

### No Logs Displayed:
- Check that backend is running (port 8080)
- Verify API response includes `pipeline_logs` array
- Check browser console for errors

### Missing Details:
- Some logs may not have details (normal)
- Click "📋 Details" to expand when available

### Performance Issues:
- Logs are limited to 500px height with scroll
- Very large datasets may generate many logs
- Consider filtering or pagination for production use

## Future Enhancements

### Planned Features:
- [ ] Log filtering by layer/level
- [ ] Log export (JSON/CSV)
- [ ] Real-time streaming for long operations
- [ ] Log search functionality
- [ ] Performance metrics visualization
- [ ] Historical log comparison

---

**Last Updated**: November 4, 2025  
**Version**: v2.0.0
