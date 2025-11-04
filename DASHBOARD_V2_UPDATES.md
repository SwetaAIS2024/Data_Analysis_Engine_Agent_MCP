# Dashboard V2 - Complete Pipeline Implementation

## Overview
Updated the dashboard to support **complete end-to-end V2 pipeline execution** with two analysis modes:
1. **Natural Language Mode (AI-Powered)** - User describes their goal in plain English
2. **Manual Tool Selection Mode** - User manually selects specific tools to test

---

## 🎯 Key Features

### 1. **Dual Mode Interface**
- **🤖 Natural Language Mode**: 
  - User enters a prompt like "Find anomalies and cluster them, then forecast the next hour"
  - AI automatically extracts intent, selects appropriate tools, and chains them
  - Full V2 pipeline: Context Extraction → Chaining Manager → Tool Invocation
  
- **🔧 Manual Tool Selection Mode**:
  - User selects one or multiple tools via checkboxes
  - Useful for testing individual tools or specific combinations
  - Bypasses AI tool selection, forces specific tools to execute

### 2. **Multiple Tool Selection**
- 9 available tools with descriptions:
  - Anomaly Detection
  - Clustering
  - Classification
  - Regression
  - Time Series Forecasting
  - Feature Engineering
  - Statistical Comparison
  - Incident Detection
  - Geospatial Mapping

- Users can select any combination of tools
- Tools are displayed in a responsive grid with checkboxes

### 3. **Enhanced UI/UX**
- Modern, card-based design with clear visual hierarchy
- Color-coded mode selection (blue highlight for active mode)
- Improved file upload section with status indicators
- Disabled state handling for buttons based on prerequisites
- Loading states with clear messaging

### 4. **Comprehensive Result Display**
- **Pipeline Metadata**: Version, duration, status, strategy, tools used
- **Tool Invocation Log**: Shows each tool execution with:
  - Success/Error/Warning status icons
  - Tool-specific output summaries (anomaly count, cluster count, etc.)
  - Error messages for failed tools
  - Color-coded status badges

- **Visualizations**:
  - Anomaly scatter plot (normal vs anomaly points)
  - Clustering scatter plot (multi-colored clusters)
  - Forecasting line chart (historical + forecast with confidence bounds)

- **Detailed Results**: Collapsible section with full JSON output from each tool

### 5. **Smart Context Passing**
The frontend now passes either:
- **Prompt Mode**: `{ task: "user prompt text", data_type: "timeseries" }`
- **Manual Mode**: `{ task: "descriptive text", data_type: "...", force_tools: ["tool1", "tool2"] }`

---

## 🔧 Backend Changes

### 1. **main.py** (`/v2/analyze` endpoint)
```python
# Added support for forced_tools in manual mode
forced_tools = req.context.get("force_tools")
if forced_tools:
    logger.info(f"Manual tool selection mode - Forced tools: {forced_tools}")
    context_result["forced_tools"] = forced_tools
```

### 2. **chaining_manager.py** (`_select_tools` method)
```python
def _select_tools(self, goal, data_type, constraints):
    # Check for forced tools (manual mode)
    if "forced_tools" in constraints:
        forced = constraints["forced_tools"]
        logger.info(f"Using manually selected tools: {forced}")
        return forced
    
    # Otherwise, use AI-based tool selection
    ...
```

### 3. **context_extractor.py**
- Passes `forced_tools` through to constraints
- Maintains compatibility with existing AI-based extraction

---

## 📊 User Workflows

### Workflow 1: Natural Language Analysis (End-to-End)
1. User selects **"Natural Language (AI-Powered)"** mode
2. Uploads CSV file → clicks "Load CSV"
3. Enters prompt: *"Detect speed anomalies and cluster them by pattern"*
4. Clicks **"Run Analysis"**
5. Backend executes:
   - Context Extraction: Parses prompt → identifies goals (anomaly_detection, clustering)
   - Chaining Manager: Creates execution plan → sequential strategy
   - Tool Invocation: Runs anomaly_zscore → clustering → returns results
6. Frontend displays:
   - Pipeline info (duration, strategy, tools used)
   - Tool invocation log (both tools, success status, counts)
   - Anomaly chart + Cluster chart
   - Detailed JSON results (collapsible)

### Workflow 2: Manual Tool Testing
1. User selects **"Manual Tool Selection"** mode
2. Uploads CSV file → clicks "Load CSV"
3. Checks: ☑ Anomaly Detection, ☑ Forecasting
4. Clicks **"Run Analysis"**
5. Backend:
   - Receives `force_tools: ["anomaly_detection", "forecasting"]`
   - Skips AI tool selection, directly uses forced tools
   - Executes both tools in appropriate order
6. Frontend displays results for both tools with visualizations

### Workflow 3: Single Tool Testing
1. User selects **"Manual Tool Selection"** mode
2. Uploads CSV file
3. Checks only: ☑ Clustering
4. Runs analysis
5. Only clustering tool executes → cluster chart displayed

---

## 🎨 UI Components

### Mode Selection Card
- Radio buttons for mode switching
- Descriptions under each mode
- Dataset type dropdown (common to both modes)

### Prompt Input (Natural Language Mode)
- Large textarea for user prompt
- Placeholder with example
- Helpful tip below

### Tool Selection Grid (Manual Mode)
- 9 tool cards in responsive grid
- Each card shows: checkbox, label, description
- Selected count indicator

### File Upload Section
- File input + Load CSV button
- Run Analysis button (green, disabled when prerequisites not met)
- Success indicator showing row count

### Results Section
- Pipeline Info card (metadata)
- Tool Invocation Log (detailed per-tool status)
- Canvas elements for charts (anomaly, cluster, forecast)
- Clustering details (if applicable)
- Collapsible detailed JSON output

---

## 🧪 Testing Recommendations

### Test Case 1: Natural Language - Single Goal
**Input**: "Find anomalies in the speed data"
**Expected**: 
- Context extraction identifies: goal=anomaly_detection
- Chaining manager selects: ["anomaly_zscore"]
- Tool executes successfully
- Anomaly chart displays

### Test Case 2: Natural Language - Multiple Goals
**Input**: "Detect anomalies, cluster the data, and forecast the next hour"
**Expected**:
- Context extraction identifies 3 goals
- Chaining manager selects: ["anomaly_zscore", "clustering", "timeseries_forecaster"]
- All 3 tools execute in sequence
- All 3 visualizations display

### Test Case 3: Manual - Single Tool
**Input**: Manual mode, select only "Clustering"
**Expected**:
- force_tools: ["clustering"] passed to backend
- Only clustering tool executes
- Cluster chart displays

### Test Case 4: Manual - Multiple Tools
**Input**: Manual mode, select "Anomaly Detection" + "Feature Engineering"
**Expected**:
- force_tools: ["anomaly_detection", "feature_engineering"] passed
- Both tools execute
- Anomaly results + enriched features returned

### Test Case 5: Error Handling
**Input**: Natural Language - "blah blah random text"
**Expected**:
- Context extraction returns goal="unknown"
- Chaining manager may warn about no tools found
- Graceful error message to user

---

## 📝 Configuration

### Tool Registry (`tools.json`)
Ensure all 9 tools are registered with correct endpoints:
- `anomaly_zscore` → `http://localhost:9091`
- `clustering` → `http://localhost:9092`
- `classifier_regressor` → `http://localhost:9093`
- `feature_engineering` → `http://localhost:9094`
- `timeseries_forecaster` → `http://localhost:9095`
- `stats_comparator` → `http://localhost:9096`
- `geospatial_mapper` → `http://localhost:9097`
- `incident_detector` → `http://localhost:9098`

### Docker Services
All tool containers must be running:
```bash
docker-compose up -d --build
```

### Backend Service
Agent service on port 8080:
```bash
cd services/agent
uvicorn app.main:app --reload --port 8080
```

### Frontend Service
React app on port 3000:
```bash
cd frontend
npm start
```

---

## 🔄 Data Flow

```
User Input (Prompt/Tools + CSV)
    ↓
Frontend (App.js)
    ↓ POST /v2/analyze
    ↓ { context: { task, force_tools?, data_type }, data_pointer: { rows }, params }
    ↓
Backend (main.py)
    ↓
Context Extractor (context_extractor.py)
    ↓ Extracts: goal, constraints (incl. forced_tools), data_type, parameters
    ↓
Chaining Manager (chaining_manager.py)
    ↓ If forced_tools → use them directly
    ↓ Else → AI-based tool selection based on goal
    ↓ Creates execution plan: tools[], strategy, dependencies
    ↓
Invocation Layer (invocation_layer.py)
    ↓ Executes each tool via HTTP POST
    ↓ Collects results from all tools
    ↓
Backend Response
    ↓ { result: { status, results[], summary }, tool_meta: { pipeline_version, context_extraction, execution_plan } }
    ↓
Frontend Rendering
    ↓ Displays: Pipeline Info, Tool Log, Visualizations, Detailed Results
```

---

## 🚀 Next Steps

### Immediate
1. ✅ Restart backend with updated code
2. ✅ Test both modes with sample CSV
3. ✅ Verify forced tools work correctly
4. ✅ Check visualizations render properly

### Future Enhancements
- [ ] Add tool parameter customization in Manual Mode
- [ ] Support for saving/loading analysis configurations
- [ ] Historical analysis comparison view
- [ ] Export results to PDF/CSV
- [ ] Real-time streaming analysis
- [ ] WebSocket support for live updates
- [ ] User authentication and session management
- [ ] Collaborative analysis (multiple users)

---

## 📚 Related Files

### Frontend
- `frontend/src/App.js` - Main dashboard component (updated)

### Backend
- `services/agent/app/main.py` - V2 endpoint (updated)
- `services/agent/app/planner/chaining_manager.py` - Tool selection (updated)
- `services/agent/app/intent_extraction/context_extractor.py` - Context extraction

### Tools
- `services/tools/*/app.py` - All 9 tool implementations

### Configuration
- `services/agent/registry/tools.json` - Tool registry
- `docker-compose.yml` - Container orchestration
- `frontend/package.json` - React dependencies

---

## 💡 Tips for Users

1. **Start with Natural Language Mode** - Let the AI handle tool selection
2. **Be specific in prompts** - "Find anomalies and cluster them" works better than "analyze data"
3. **Use Manual Mode for testing** - Test individual tools or specific combinations
4. **Check Tool Invocation Log** - See exactly which tools ran and their outputs
5. **Expand Detailed Results** - View full JSON output for debugging

---

## 🐛 Troubleshooting

### Issue: "No tools selected"
**Solution**: In Manual Mode, check at least one tool checkbox before running

### Issue: Charts not rendering
**Solution**: 
- Ensure Chart.js is imported
- Check browser console for errors
- Verify tool outputs contain required data fields

### Issue: Backend returns "Unknown goal"
**Solution**: 
- In Prompt Mode: Use clearer keywords (anomaly, cluster, forecast, etc.)
- In Manual Mode: Ensure force_tools is passed correctly

### Issue: Tools fail with errors
**Solution**:
- Check Docker containers are running: `docker ps`
- Verify tools.json has correct endpoints
- Check tool logs: `docker logs <container_name>`

---

## ✨ Summary

The updated dashboard now provides:
- ✅ **Complete V2 pipeline** execution from UI
- ✅ **Dual modes** (AI-powered + Manual) for flexibility
- ✅ **Multiple tool support** with easy selection
- ✅ **Rich visualizations** for results
- ✅ **Comprehensive logging** for transparency
- ✅ **Modern, intuitive UI** for better UX

This implementation enables both **production use** (Natural Language Mode) and **development/testing** (Manual Tool Selection Mode) through a single, unified interface.
