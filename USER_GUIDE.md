# Data Analysis Engine Agent - Developer Guide & API Reference

> **📘 Note:** This is the technical/developer documentation. If you're an end user looking to get started quickly, see [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) instead.

---

## 📖 Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [System Architecture](#system-architecture)
4. [Installation & Setup](#installation--setup)
5. [Using the Application](#using-the-application)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## 🎯 Overview

The **Data Analysis Engine Agent** is an AI-powered system that understands natural language requests and automatically performs complex data analysis tasks. It supports **9 specialized tools** for various analytics workflows.

### Key Features
- 🤖 **Natural Language Processing**: Describe your analysis in plain English
- 🔄 **Intelligent Tool Chaining**: Automatically sequences multiple tools
- 🎨 **Dual-Mode Interface**: AI-powered OR manual tool selection
- 💬 **Interactive Clarification**: Asks for details when input is ambiguous
- 📊 **9 Specialized Tools**: Anomaly detection, forecasting, clustering, and more

### Supported Analysis Types
1. **Anomaly Detection** (Z-Score)
2. **Classification & Regression**
3. **Clustering & Feature Engineering**
4. **Geospatial Mapping**
5. **Incident Detection**
6. **Statistical Comparison**
7. **Time Series Forecasting**

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (for Windows/Mac) or **Docker Engine** (for Linux)
- **Node.js** 14+ and **npm**
- **Python** 3.9+
- **Git**

### 1. Clone Repository
```bash
git clone https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP.git
cd Data_Analysis_Engine_Agent_MCP
git checkout DAA_v2
```

### 2. Start Tool Services (Docker)
```bash
# Start all 9 tool containers
docker-compose up -d --build

# Verify all containers are running
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                      STATUS         PORTS
abc123def456   anomaly_zscore            Up 10 seconds   0.0.0.0:9091->8000/tcp
def456ghi789   classifier_regressor      Up 10 seconds   0.0.0.0:9092->8000/tcp
...
```

### 3. Start Backend (Agent)
```bash
# Option A: Using virtual environment
cd services/agent
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Option B: Direct run
cd services/agent
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

**Backend Running:** `http://localhost:8080`

### 4. Start Frontend (React Dashboard)
```bash
# Open new terminal
cd frontend
npm install
npm start
```

**Dashboard Running:** `http://localhost:3001`

### 5. Access the Application
Open your browser: **`http://localhost:3001`**

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Browser)                            │
│              http://localhost:3001                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (React Dashboard)                      │
│  - Dual Mode: Natural Language / Manual Selection           │
│  - Interactive Clarification UI                             │
│  - Pipeline Visualization                                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP POST /api/process
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         BACKEND AGENT (FastAPI - Port 8080)                 │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 1. Intent Extraction (Context Extractor)        │        │
│  │    - Adaptive Method Selection                  │        │
│  │    - 5 Methods: RULE/REGEX/ML/LLM/HYBRID        │        │
│  │    - Ambiguity Detection                        │        │
│  └─────────────────────────────────────────────────┘        │
│                         │                                    │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 2. Tool Selection (Chaining Manager)            │        │
│  │    - Multi-tool orchestration                   │        │
│  │    - Dependency resolution                      │        │
│  │    - Execution order planning                   │        │
│  └─────────────────────────────────────────────────┘        │
│                         │                                    │
│  ┌─────────────────────────────────────────────────┐        │
│  │ 3. Tool Invocation (Dispatcher)                 │        │
│  │    - Sequential execution                       │        │
│  │    - Result passing between tools               │        │
│  │    - Error handling                             │        │
│  └─────────────────────────────────────────────────┘        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Tool 1      │  │  Tool 2      │  │  Tool N      │
│  (Docker)    │  │  (Docker)    │  │  (Docker)    │
│  Port 9091   │  │  Port 9092   │  │  Port 909N   │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📦 Installation & Setup

### Step-by-Step Installation

#### Step 1: Install Prerequisites

**Docker Desktop (Windows/Mac):**
1. Download from https://www.docker.com/products/docker-desktop
2. Install and restart computer
3. Start Docker Desktop
4. Verify: `docker --version`

**Node.js:**
1. Download from https://nodejs.org (LTS version)
2. Install with default settings
3. Verify: `node --version` and `npm --version`

**Python:**
1. Download from https://www.python.org/downloads (3.9+)
2. ✅ Check "Add Python to PATH" during installation
3. Verify: `python --version`

**Git:**
1. Download from https://git-scm.com
2. Install with default settings
3. Verify: `git --version`

---

#### Step 2: Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP.git
cd Data_Analysis_Engine_Agent_MCP

# Switch to V2 branch
git checkout DAA_v2

# Verify directory structure
ls
# Should see: docker-compose.yml, frontend/, services/, test/
```

---

#### Step 3: Configure Environment Variables (Optional)

Create a `.env` file in the root directory for advanced features:

```bash
# .env file (optional)

# Enable Adaptive Intent Extraction
ADAPTIVE_EXTRACTION=true

# LLM Provider for complex queries (optional)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Or use Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your-key-here

# Or use Local LLM (Ollama)
# LLM_PROVIDER=local
# LOCAL_LLM_URL=http://localhost:11434
# LOCAL_LLM_MODEL=llama2
```

**Note:** The system works perfectly **without** any environment variables using the default HYBRID extraction method.

**Advanced Features (Optional):**

```bash
# Enable Fallback Chain (tries RULE → ML → LLM → Clarification)
ENABLE_FALLBACK_CHAIN=true

# Enable Adaptive Mode (auto-selects best single method)
ADAPTIVE_EXTRACTION=true

# Note: Don't enable both - they use different strategies
```

---

#### Step 4: Start Tool Services

```bash
# Build and start all Docker containers
docker-compose up -d --build

# This starts 9 tool services:
# - anomaly_zscore (Port 9091)
# - classifier_regressor (Port 9092)
# - cluster_feature_engineer (Port 9093)
# - geospatial_mapper (Port 9094)
# - incident_detector (Port 9095)
# - stats_comparator (Port 9096)
# - timeseries_forecaster (Port 9097)
# Plus: Redis (6379), Agent (8080)

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Troubleshooting:**
- If ports are in use, stop conflicting services
- If Docker is slow, allocate more resources in Docker Desktop settings
- If containers fail, check logs: `docker-compose logs <service_name>`

---

#### Step 5: Start Backend Agent

```bash
# Navigate to agent directory
cd services/agent

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8080
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is ready when you see:**
- ✅ "Application startup complete"
- ✅ No error messages
- ✅ Can access http://localhost:8080/docs (API documentation)

---

#### Step 6: Start Frontend Dashboard

```bash
# Open NEW terminal (keep backend running)
cd frontend

# Install Node dependencies
npm install

# Start React development server
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view the app in the browser.

  Local:            http://localhost:3001
  On Your Network:  http://192.168.1.x:3001
```

**Dashboard auto-opens in browser at:** `http://localhost:3001`

---

## 🎮 Using the Application

### Interface Overview

The dashboard has **two modes:**

#### **Mode 1: Natural Language (AI-Powered)** 🤖
- Describe your analysis in plain English
- AI automatically selects and chains tools
- Handles complex multi-step workflows

#### **Mode 2: Manual Tool Selection** 🔧
- Select specific tools using checkboxes
- Full control over execution
- Useful for debugging or specific workflows

---

### Mode 1: Natural Language Analysis

#### Example 1: Simple Anomaly Detection
```
1. Upload your CSV file (or use test data)
2. Enter prompt: "detect anomalies in the data"
3. Click "Analyze Data"
```

**What Happens:**
1. ✅ Intent extracted: `goal="detect_anomalies"`
2. ✅ Tool selected: `anomaly_zscore`
3. ✅ Tool executed on your data
4. ✅ Results displayed with outliers highlighted

**Result:**
```json
{
  "anomalies_detected": 15,
  "anomaly_indices": [23, 45, 67, ...],
  "visualization": "scatter plot with outliers in red"
}
```

---

#### Example 2: Multi-Step Analysis
```
Prompt: "Find outliers in sales data, then forecast next month's trends"
```

**What Happens:**
1. ✅ Intent: `goal="detect_and_forecast"`
2. ✅ Tools chained: `anomaly_zscore` → `timeseries_forecaster`
3. ✅ Pipeline executed:
   - Step 1: Detect anomalies
   - Step 2: Pass cleaned data to forecaster
   - Step 3: Generate forecast
4. ✅ Results from both tools displayed

**Pipeline Visualization:**
```
[Anomaly Detection] → [Data Cleaning] → [Forecasting] ✓
```

---

#### Example 3: Ambiguous Input (Clarification Flow)
```
Prompt: "do detection"
```

**What Happens:**
1. ⚠️ System detects ambiguity
2. 💬 Clarification options displayed:
   - Detect anomalies (outliers)
   - Detect incidents
   - Detect patterns (clustering)
   - Detect geographic patterns
   - Detect classification patterns
3. ✅ Click your intended option
4. ✅ System auto-resubmits with clarified prompt

**Interactive Clarification UI:**
```
┌─────────────────────────────────────────────────┐
│ ℹ️ Your request needs clarification             │
│                                                 │
│ What type of detection do you want?            │
│                                                 │
│ ┌─────────────────────────────────────┐        │
│ │ 🔍 Detect anomalies (outliers)      │ [Click]│
│ └─────────────────────────────────────┘        │
│ ┌─────────────────────────────────────┐        │
│ │ 🚨 Detect incidents                 │ [Click]│
│ └─────────────────────────────────────┘        │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

---

#### Example 4: Complex Conditional Query
```
Prompt: "Classify customer segments, but exclude weekends, and if high-value customers are found, show their geographic distribution"
```

**What Happens:**
1. ✅ LLM-powered extraction (auto-selected due to complexity)
2. ✅ Tools chained: `classifier_regressor` → `geospatial_mapper`
3. ✅ Filters applied: Exclude weekends
4. ✅ Conditional logic: Geographic mapping for high-value only
5. ✅ Multi-tool results displayed

---

### Mode 2: Manual Tool Selection

#### When to Use Manual Mode
- ✅ Testing specific tool functionality
- ✅ Debugging tool performance
- ✅ Learning which tools to use
- ✅ Complex workflows you want to control

#### How to Use
1. **Switch to Manual Mode:** Click "Manual Tool Selection" tab
2. **Select Tools:** Check boxes for tools you want to run
   ```
   ☑️ Anomaly Detection (Z-Score)
   ☑️ Time Series Forecaster
   ☐ Classifier & Regressor
   ☐ Clustering & Feature Engineering
   ```
3. **Upload Data:** Choose CSV file
4. **Click "Run Selected Tools"**

**Result:** Each selected tool runs independently, results shown separately.

---

### Working with Data

#### Supported Data Formats
- ✅ **CSV files** (primary format)
- ✅ **JSON** (via API)
- ✅ Test data provided in `test/test_data_final.csv`

#### Data Requirements
- **Minimum rows:** 10 (some tools require more)
- **Columns:** At least 2 (one for features, one for target/values)
- **Data types:** Numeric (for analysis), timestamps (for forecasting)

#### Sample Data Structure
```csv
date,sales,temperature,region
2024-01-01,1500,25,North
2024-01-02,1600,26,North
2024-01-03,2500,27,South
...
```

#### Using Test Data
```bash
# Test data already included
cd test
ls test_data_final.csv

# Upload this file in the dashboard
```

---

### Understanding Results

#### Result Structure
```json
{
  "status": "success",
  "pipeline": [
    {
      "tool": "anomaly_zscore",
      "status": "completed",
      "result": {
        "anomalies_detected": 15,
        "outlier_indices": [23, 45, 67],
        "z_scores": [...],
        "threshold": 3.0
      }
    },
    {
      "tool": "timeseries_forecaster",
      "status": "completed",
      "result": {
        "forecast": [2100, 2200, 2300],
        "confidence_interval": "95%",
        "model": "ARIMA(1,1,1)"
      }
    }
  ],
  "execution_time": "2.3s"
}
```

#### Interpreting Tool Outputs

**Anomaly Detection:**
- `anomalies_detected`: Count of outliers found
- `outlier_indices`: Row numbers with anomalies
- `z_scores`: Statistical deviation scores
- **Action:** Investigate flagged rows for data quality issues

**Time Series Forecasting:**
- `forecast`: Predicted values for future periods
- `confidence_interval`: Prediction reliability (higher = more confident)
- `model`: Algorithm used (ARIMA, Prophet, etc.)
- **Action:** Use forecast for planning/budgeting

**Classification:**
- `predictions`: Class labels for each row
- `accuracy`: Model performance (0-1 scale)
- `features_used`: Columns used for prediction
- **Action:** Segment data based on predicted classes

**Clustering:**
- `clusters`: Number of groups found
- `cluster_assignments`: Which cluster each row belongs to
- `centroids`: Center point of each cluster
- **Action:** Group similar items for targeted strategies

---

## 🎓 Advanced Features

### Feature 1: Adaptive Intent Extraction

**What It Does:** Automatically selects the best extraction method based on prompt complexity.

**Enable:**
```bash
export ADAPTIVE_EXTRACTION=true
```

**How It Works:**
- Simple prompts (< 10 words, clear keywords) → **RULE_BASED** (fastest, 2ms)
- Medium complexity → **HYBRID** (balanced, 10ms)
- Complex prompts (> 50 words, conditions) → **LLM** (accurate, 800ms)

**Example:**
```
"detect anomalies" → RULE_BASED (fast)
"Find outliers but exclude weekends if..." → LLM (accurate)
```

**See:** `ADAPTIVE_METHOD_SELECTION.md` for full details.

---

### Feature 2: Tool Chaining & Dependencies

**What It Does:** Automatically sequences tools based on data flow requirements.

**Example Chains:**

**Chain 1: Anomaly → Forecasting**
```
Input: "Detect outliers then forecast trends"
Pipeline: [Anomaly Detection] → [Clean Data] → [Forecasting]
```

**Chain 2: Classification → Geographic Analysis**
```
Input: "Classify customers and show their distribution"
Pipeline: [Classification] → [Geospatial Mapping]
```

**Chain 3: Feature Engineering → Clustering**
```
Input: "Engineer features and group similar items"
Pipeline: [Feature Engineering] → [Clustering]
```

---

### Feature 3: Interactive Clarification

**Triggered When:**
- Ambiguous verbs: "do detection", "analyze", "process"
- Missing details: "show me data"
- Vague requests: "do something with sales"

**Clarification UI:**
- Displays 3-5 relevant options
- Clickable buttons (no typing needed)
- Auto-resubmits with clarified prompt

**Example Flow:**
```
User: "do detection"
  ↓
System: "What type of detection?"
  - Detect anomalies
  - Detect incidents
  - Detect patterns
  ↓
User: [Clicks "Detect anomalies"]
  ↓
System: Runs anomaly detection tool
```

---

### Feature 4: Custom Tool Configuration

**Modify Tool Parameters:**

Each tool accepts configuration in the prompt:

**Anomaly Detection:**
```
"detect anomalies with threshold 2.5"
→ Uses z_threshold=2.5 instead of default 3.0
```

**Forecasting:**
```
"forecast next 7 days"
→ Sets forecast_periods=7
```

**Clustering:**
```
"cluster into 5 groups"
→ Sets n_clusters=5
```

---

### Feature 5: API Access (Programmatic)

**Direct API Calls:**

```python
import requests

# Process data via API
response = requests.post(
    "http://localhost:8080/api/process",
    json={
        "prompt": "detect anomalies in sales data",
        "data": [
            {"date": "2024-01-01", "sales": 1500},
            {"date": "2024-01-02", "sales": 1600},
            # ... more rows
        ],
        "force_tools": []  # Optional: ["anomaly_zscore"]
    }
)

result = response.json()
print(result)
```

**API Documentation:**
Visit `http://localhost:8080/docs` for interactive Swagger UI.

---

## 🛠️ Troubleshooting

### Issue 1: Docker Containers Not Starting

**Symptoms:**
```
Error: Cannot start service anomaly_zscore: port 9091 already in use
```

**Solution:**
```bash
# Find process using port
netstat -ano | findstr :9091  # Windows
lsof -i :9091                 # Linux/Mac

# Kill process
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Linux/Mac

# Or change port in docker-compose.yml
ports:
  - "9191:8000"  # Changed from 9091
```

---

### Issue 2: Frontend Shows Old Code

**Symptoms:**
- Dashboard doesn't match described features
- Clarification UI not appearing

**Solution:**
```bash
# Clear React cache and rebuild
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start

# Or force refresh in browser
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

---

### Issue 3: Backend 500 Error

**Symptoms:**
```
Error: Internal Server Error when clicking "Analyze Data"
```

**Solution:**
```bash
# Check backend logs
cd services/agent
uvicorn app.main:app --reload --port 8080 --log-level debug

# Look for errors in terminal
# Common issues:
# - Tool container not responding
# - Invalid data format
# - Missing dependencies

# Verify tool containers are up
docker-compose ps
# All should show "Up" status
```

---

### Issue 4: "Clarification Required" Loop

**Symptoms:**
- Prompt keeps asking for clarification
- Never proceeds to execution

**Solution:**
```bash
# Your prompt might be too vague
# Instead of: "do something"
# Try: "detect anomalies in sales data"

# Or use Manual Mode:
# Click "Manual Tool Selection" tab
# Check specific tools
# Click "Run Selected Tools"
```

---

### Issue 5: LLM Not Working (Adaptive Mode)

**Symptoms:**
```
Warning: LLM selected but falling back to HYBRID
```

**Solution:**
```bash
# Check API key is set
echo $OPENAI_API_KEY  # Should show sk-...

# If not set:
export OPENAI_API_KEY=sk-your-key-here

# Or disable adaptive mode (use default HYBRID)
export ADAPTIVE_EXTRACTION=false

# Restart backend
cd services/agent
uvicorn app.main:app --reload --port 8080
```

---

### Issue 6: Data Upload Fails

**Symptoms:**
```
Error: Invalid file format
```

**Solution:**
```bash
# Verify CSV format
# ✅ Good:
date,sales,region
2024-01-01,1500,North

# ❌ Bad (no header):
2024-01-01,1500,North

# ❌ Bad (mixed delimiters):
date;sales|region

# Use test data to verify system works:
cd test
# Upload test_data_final.csv
```

---

### Issue 7: Slow Performance

**Symptoms:**
- Taking > 10 seconds for simple queries

**Solution:**
```bash
# Check Docker resource allocation
# Docker Desktop → Settings → Resources
# Recommended: CPU: 4 cores, RAM: 4GB

# Disable adaptive mode if using LLM
export ADAPTIVE_EXTRACTION=false

# Use simpler prompts
# Instead of: "Analyze everything and..."
# Try: "detect anomalies"

# Check tool logs for bottlenecks
docker-compose logs -f anomaly_zscore
```

---

## 📡 API Reference

### Endpoint: POST /api/process

**Request:**
```json
{
  "prompt": "detect anomalies in sales data",
  "data": [
    {"date": "2024-01-01", "sales": 1500, "region": "North"},
    {"date": "2024-01-02", "sales": 1600, "region": "South"}
  ],
  "force_tools": []  // Optional: Force specific tools
}
```

**Response (Success):**
```json
{
  "status": "success",
  "pipeline": [
    {
      "tool": "anomaly_zscore",
      "status": "completed",
      "result": {
        "anomalies_detected": 5,
        "outlier_indices": [12, 23, 45, 67, 89]
      }
    }
  ],
  "execution_time": "1.2s",
  "intent": {
    "goal": "detect_anomalies",
    "data_type": "timeseries",
    "extraction_method": "rule_based"
  }
}
```

**Response (Clarification Needed):**
```json
{
  "status": "clarification_required",
  "message": "Your request needs clarification",
  "clarification_options": [
    "Detect anomalies (outliers) in your data",
    "Detect incidents or events",
    "Detect patterns through clustering"
  ],
  "original_prompt": "do detection"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "Tool execution failed",
  "details": "anomaly_zscore returned 500: Insufficient data"
}
```

---

### Endpoint: GET /health

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0",
  "tools_available": 9,
  "extraction_method": "hybrid"
}
```

---

### Endpoint: GET /docs

**Interactive API Documentation** (Swagger UI)
- Visit: `http://localhost:8080/docs`
- Test endpoints directly in browser
- View request/response schemas

---

## 📚 Additional Resources

### Documentation Files
- `ADAPTIVE_METHOD_SELECTION.md` - Intelligent extraction method selection
- `INTENT_EXTRACTION_METHODS.md` - Deep dive into 5 extraction methods (if exists)
- `docker-compose.yml` - Tool service configuration
- `README.md` - Project overview

### Configuration Files
- `.env` - Environment variables (create if needed)
- `services/agent/app/main.py` - Backend entry point
- `frontend/src/App.js` - Dashboard UI

### Test Files
- `test/test_data_final.csv` - Sample dataset
- `test/test_script_anomaly_detection.py` - Example Python script

---

## 🎯 Common Workflows

### Workflow 1: Quick Anomaly Check
```
1. Start system (Docker + Backend + Frontend)
2. Upload CSV file
3. Prompt: "detect anomalies"
4. Review results (< 5 seconds)
```

---

### Workflow 2: Sales Forecasting
```
1. Upload sales data (date + sales columns)
2. Prompt: "forecast sales for next 30 days"
3. System auto-selects timeseries_forecaster
4. View forecast chart + confidence intervals
```

---

### Workflow 3: Customer Segmentation
```
1. Upload customer data (features + demographics)
2. Prompt: "cluster customers into 5 groups"
3. System chains: feature_engineer → clustering
4. View cluster assignments + characteristics
```

---

### Workflow 4: Multi-Step Analysis
```
1. Upload sales data
2. Prompt: "Find outliers, remove them, then forecast trends"
3. System auto-chains:
   - anomaly_zscore (detect outliers)
   - data cleaning (remove flagged rows)
   - timeseries_forecaster (forecast clean data)
4. View pipeline results + execution trace
```

---

## 🚦 System Status Check

**Before reporting issues, verify:**

✅ **Docker:** `docker ps` shows 9+ containers running  
✅ **Backend:** `http://localhost:8080/health` returns `{"status": "healthy"}`  
✅ **Frontend:** `http://localhost:3001` loads dashboard  
✅ **Tools:** Each tool responds at `http://localhost:909X/health`  

**Quick Health Check:**
```bash
# Check all tool services
for port in {9091..9099}; do
  curl -s http://localhost:$port/health && echo " - Port $port: OK"
done
```

---

## 📞 Support & Feedback

### Getting Help
1. Check **Troubleshooting** section above
2. Review logs: `docker-compose logs -f`
3. Check GitHub Issues: https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP/issues
4. API Docs: `http://localhost:8080/docs`

### Reporting Bugs
Include:
- Steps to reproduce
- Expected vs actual behavior
- Error logs (backend + frontend + Docker)
- System info (OS, Docker version, Python version)

---

## 🎉 You're Ready!

The system is now ready to use. Start with simple prompts like:
- `"detect anomalies"`
- `"forecast trends"`
- `"cluster data"`

Then progress to complex multi-step workflows:
- `"Find outliers, classify the rest, and show geographic distribution"`

**Happy Analyzing! 🚀📊**
