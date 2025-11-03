# V2 Pipeline Testing Guide

## Prerequisites

1. **Start the backend agent:**
   ```bash
   cd services/agent
   uvicorn app.main:app --reload --port 8080
   ```

2. **Start the tool services** (in separate terminals or Docker Compose):
   ```bash
   docker-compose up
   ```

## Running the User Feedback Test

This test demonstrates the V2 pipeline handling missing tools and requesting user feedback.

### Test Scenario:
- **User Request:** "Detect anomalies and generate a comprehensive report"
- **Tool 1:** `anomaly_zscore` ✅ (Available)
- **Tool 2:** `anomaly_report_generator` ❌ (Not Available)
- **Expected:** System detects conflict and requests user feedback

### Run the Test:

```bash
cd test
python test_v2_user_feedback.py
```

### Expected Output:

```
████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█  V2 PIPELINE TEST SUITE - USER FEEDBACK & CONFLICT RESOLUTION              █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████

================================================================================
  TEST: V2 Pipeline with Available Tool (Success)
================================================================================

User Prompt: Detect anomalies in sensor data with threshold 2.5
Response Status: 200
Pipeline Status: success
✅ SUCCESS: Anomaly detection completed without issues!

📊 Detected 2 anomalies:
   - {'timestamp': '2025-01-01T00:15:00', ...}
   - {'timestamp': '2025-01-01T00:30:00', ...}

================================================================================
  TEST: V2 Pipeline with Missing Tool (User Feedback Required)
================================================================================

📝 STEP 1: Building request requiring two tools...
User Prompt: Detect anomalies in the sensor data using z-score method with threshold 2.5, 
    and then generate a comprehensive report with visualizations and statistics 
    about the detected anomalies.
Data: 8 rows

================================================================================
  STEP 2: Sending request to /v2/analyze
================================================================================

Response Status: 200
Request ID: 550e8400-e29b-41d4-a716-446655440000
Status: ok

Context Extraction:
{
  "goal": "anomaly_detection",
  "data_type": "timeseries",
  "constraints": ["threshold: 2.5"]
}

Execution Plan:
{
  "strategy": "sequential",
  "tools": ["anomaly_zscore", "anomaly_report_generator"],
  "conflicts": [
    {
      "type": "tool_unavailable",
      "tool": "anomaly_report_generator",
      "severity": "high"
    }
  ]
}

📋 Strategy: sequential
📦 Tools Planned: anomaly_zscore, anomaly_report_generator
⚠️  Conflicts Detected: 1

================================================================================
  STEP 4: Pipeline Results
================================================================================

Pipeline Status: needs_feedback

📊 Tool Results:

  Tool 1: anomaly_zscore
    Status: success
    Output: Available

  Tool 2: anomaly_report_generator
    Status: unavailable
    Error: Tool anomaly_report_generator endpoint not found

================================================================================
  STEP 5: User Feedback Check
================================================================================

🔔 USER FEEDBACK REQUIRED!

Feedback Request:
{
  "message": "1 tool(s) unavailable",
  "unavailable_tools": ["anomaly_report_generator"],
  "options": [
    {
      "option_id": "create_tools",
      "message": "Create missing tools",
      "action": "create_new_tools",
      "tools": ["anomaly_report_generator"]
    },
    {
      "option_id": "use_alternatives",
      "message": "Use alternative tools",
      "action": "select_alternatives",
      "fallbacks": [...]
    },
    {
      "option_id": "cancel",
      "message": "Cancel execution",
      "action": "cancel"
    }
  ]
}

📢 Message: 1 tool(s) unavailable

❌ Unavailable Tools:
   - anomaly_report_generator

📝 User Options:

   Option 1: Create missing tools
   Action: create_new_tools

   Option 2: Use alternative tools
   Action: select_alternatives

   Option 3: Cancel execution
   Action: cancel

────────────────────────────────────────────────────────────────────────────────
✅ SUCCESS: User feedback mechanism working correctly!
   - System detected missing tool: 'anomaly_report_generator'
   - Context extraction identified need for reporting
   - Chaining manager detected conflict
   - User presented with options to resolve
────────────────────────────────────────────────────────────────────────────────

================================================================================
  TEST SUMMARY
================================================================================

✅ PASSED - Available Tool Test
✅ PASSED - Missing Tool Test

================================================================================
🎉 ALL TESTS PASSED!
================================================================================
```

## What the Test Validates:

1. ✅ **Context Extraction** - Detects "report" keyword in prompt
2. ✅ **Tool Selection** - Identifies both anomaly_zscore and report_generator needed
3. ✅ **Conflict Detection** - Recognizes report_generator is unavailable
4. ✅ **Sequential Strategy** - Plans to run detection first, then reporting
5. ✅ **Partial Execution** - Runs available tool (anomaly_zscore) successfully
6. ✅ **User Feedback** - Presents clear options to resolve missing tool
7. ✅ **Fallback Options** - Suggests alternatives or tool creation

## Testing Other Scenarios:

### Test with different prompts:

```python
# Scenario 1: Simple detection (should succeed)
"Detect anomalies with threshold 3.0"

# Scenario 2: Multiple unavailable tools
"Cluster the data, visualize results, and generate PDF report"

# Scenario 3: Visualization request
"Show me a chart of anomalies over time"
```

### Modify the test file:

Edit `test/test_v2_user_feedback.py` and change the `user_prompt` variable to test different scenarios.

## Integration with Frontend:

The frontend (App.js) now handles user feedback responses:

```javascript
if (res.data.result && res.data.result.user_feedback) {
  // Display feedback options to user
  alert("User feedback required: " + 
    JSON.stringify(res.data.result.user_feedback, null, 2));
}
```

## Next Steps:

1. **Implement Tool Creation API** - Allow creating new tools on-the-fly
2. **Add More Tools** - Implement report_generator, visualizer, etc.
3. **Enhance Fallbacks** - Better alternative tool suggestions
4. **User Feedback UI** - Interactive dialog for choosing options

---

**Last Updated:** 2025-11-03  
**Branch:** DAA_v2
