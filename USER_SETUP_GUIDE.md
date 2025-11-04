# Data Analysis Engine Agent - User Setup Guide

## 🎯 Overview

The **Data Analysis Engine Agent** is an intelligent, multi-layer pipeline system that analyzes data using natural language prompts. It automatically selects and executes the right analytical tools based on your intent.

### Key Features:
- 🤖 **Natural Language Interface**: Just describe what you want in plain English
- 🔍 **Intelligent Tool Selection**: Automatically picks the right analytical tools
- 📊 **Multiple Analysis Types**: Anomaly detection, clustering, forecasting, classification, and more
- 🔗 **Tool Chaining**: Executes multiple analyses in sequence or parallel
- 📈 **Real-time Results**: Get insights with visualizations
- 🪵 **Complete Pipeline Logs**: See exactly what the system is doing at each step

---

## 🚀 Quick Start (For End Users)

### Option 1: Using Hosted Version (If Available)

If someone has already deployed the system:

1. **Open the Web Interface**
   - Navigate to the provided URL (e.g., `http://your-domain.com:3001`)

2. **Upload Your CSV Data**
   - Click "Choose File" and select your CSV file
   - Ensure your CSV has proper column headers

3. **Configure Analysis**
   - **Task Prompt**: Describe what you want (e.g., "detect anomalies", "cluster the data")
   - **Metric Column**: Select the column to analyze
   - **Timestamp Field**: (Optional) For time-series data
   - **Key Fields**: (Optional) Entity identifiers

4. **Submit & View Results**
   - Click "Analyze"
   - View pipeline execution logs
   - See analysis results with visualizations
   - Download results if needed

### Option 2: Run Locally with Docker

**Prerequisites:**
- Docker Desktop installed
- At least 4GB RAM available
- 2GB free disk space

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP.git
cd Data_Analysis_Engine_Agent_MCP

# 2. Switch to the v2 branch
git checkout DAA_v2

# 3. Start all services with Docker Compose
docker-compose up -d --build

# 4. Wait for services to start (30-60 seconds)

# 5. Open your browser
# Frontend: http://localhost:3001
# Backend API: http://localhost:8080/docs
```

**To Stop:**
```bash
docker-compose down
```

---

## 🛠️ Full Installation Guide (For Developers)

### Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Node.js 16+**
   ```bash
   node --version  # Should be 16 or higher
   npm --version
   ```

3. **Docker & Docker Compose** (for microservices)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

4. **Git**
   ```bash
   git --version
   ```

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP.git
cd Data_Analysis_Engine_Agent_MCP
git checkout DAA_v2
```

#### 2. Backend Setup (Agent Service)

```bash
# Navigate to agent service
cd services/agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the agent (development mode with auto-reload)
uvicorn app.main:app --reload --port 8080
```

Backend will be available at: `http://localhost:8080`
API docs: `http://localhost:8080/docs`

#### 3. Tool Services (Docker)

```bash
# Go back to project root
cd ../..

# Build and start all tool microservices
docker-compose up -d --build

# Verify all services are running
docker ps
```

You should see 7 tool services running:
- `anomaly_zscore` (port 8001)
- `clustering` (port 8002)
- `classifier_regressor` (port 8003)
- `timeseries_forecaster` (port 8004)
- `stats_comparator` (port 8005)
- `geospatial_mapper` (port 8006)
- `incident_detector` (port 8007)
- `feature_engineering` (port 8008)

#### 4. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at: `http://localhost:3001`

---

## 📖 Usage Guide

### Supported Analysis Types

#### 1. **Anomaly Detection**
Detect unusual patterns or outliers in your data.

**Prompts:**
- "detect anomalies"
- "find outliers"
- "identify unusual patterns"
- "spot anomalies in speed column"

**Required Fields:**
- Metric Column: The numeric column to analyze
- Timestamp Field: (Optional) For time-series data

**Example:**
```
Task: "detect anomalies in the speed data"
Metric: speed_kmh
Timestamp: timestamp
```

#### 2. **Clustering**
Group similar data points together.

**Prompts:**
- "cluster the data"
- "group similar items"
- "find patterns with 3 clusters"
- "segment customers"

**Required Fields:**
- Metric Column(s): Features to use for clustering

**Example:**
```
Task: "cluster customers into 4 groups"
Metric: purchase_amount
Key Fields: customer_id
```

#### 3. **Time-Series Forecasting**
Predict future values based on historical trends.

**Prompts:**
- "forecast next 10 days"
- "predict future values"
- "project next week"

**Required Fields:**
- Metric Column: Value to forecast
- Timestamp Field: Time column
- Key Fields: Entity identifiers

**Example:**
```
Task: "forecast sales for next 7 days"
Metric: sales_amount
Timestamp: date
Key Fields: store_id
```

#### 4. **Classification/Regression**
Predict categorical or numeric outcomes.

**Prompts:**
- "classify the data"
- "predict category"
- "train a model"

**Required Fields:**
- Metric Column: Target variable
- Other columns: Features

**Example:**
```
Task: "classify customer churn"
Metric: churn_flag
Key Fields: customer_id
```

#### 5. **Statistical Comparison**
Compare metrics across groups.

**Prompts:**
- "compare statistics"
- "compare groups"
- "statistical analysis"

**Example:**
```
Task: "compare sales across regions"
Metric: sales_amount
Key Fields: region
```

#### 6. **Feature Engineering**
Create new features from existing data.

**Prompts:**
- "engineer features"
- "create new features"
- "feature extraction"

**Example:**
```
Task: "engineer features for machine learning"
Metric: all_columns
```

#### 7. **Incident Detection**
Detect and analyze incidents or events.

**Prompts:**
- "detect incidents"
- "find critical events"
- "identify failures"

**Example:**
```
Task: "detect system failures"
Metric: error_rate
Timestamp: timestamp
```

### Understanding the Dashboard

#### 1. **Pipeline Info Section**
Shows high-level pipeline execution details:
- Status: success/failed/warning
- Version: Pipeline version (v2_simplified)
- Duration: Total execution time
- Goal: What the system understood
- Data Type: Detected data type (timeseries/tabular/geospatial)
- Strategy: Execution strategy (single/sequential/parallel)
- Tools Used: List of tools executed

#### 2. **Pipeline Execution Logs Section** 🆕
Real-time logs from all pipeline layers:

**Layer Color Coding:**
- 🚀 **PIPELINE** (Purple): Overall pipeline events
- 📋 **CONTEXT EXTRACTION** (Blue): Intent understanding phase
- 🔗 **CHAINING MANAGER** (Orange): Tool selection & planning
- ⚙️ **INVOCATION LAYER** (Green): Tool execution
- 📤 **OUTPUT PREPARATION** (Cyan): Result formatting

**Log Levels:**
- **INFO** (Blue): Informational messages
- **SUCCESS** (Green): Successful operations
- **WARNING** (Orange): Warnings or clarifications
- **ERROR** (Red): Errors or failures

**Features:**
- Click "📋 Details" to expand additional information
- Timestamps show when each operation occurred
- Scrollable container for long logs
- Color-coded for easy visual scanning

#### 3. **Tool Invocation Log Section**
Detailed tool execution information:
- Tool display names (e.g., "Anomaly Detection (Z-Score)")
- Status badges (SUCCESS/ERROR/WARNING)
- Status messages with details
- Execution summaries (rows processed, anomalies found, etc.)
- Error messages if any

#### 4. **Results Section**
- **CSV Preview**: First 20 rows of your data
- **Analysis Results**: Tool-specific outputs
  - Anomalies detected with indices
  - Cluster assignments
  - Predictions and forecasts
  - Statistical summaries
  - Visualizations (if available)

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Backend
AGENT_PORT=8080
LOG_LEVEL=INFO

# Enable/Disable Features
ENABLE_FALLBACK_CHAIN=true
ENABLE_CONSENSUS_VOTING=true

# LLM Configuration (Optional)
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4

# Tool Service Endpoints (if not using Docker)
ANOMALY_ZSCORE_URL=http://localhost:8001
CLUSTERING_URL=http://localhost:8002
CLASSIFIER_REGRESSOR_URL=http://localhost:8003
TIMESERIES_FORECASTER_URL=http://localhost:8004
```

### Advanced Features

#### Consensus Voting (Enabled by Default)
The system uses multiple extraction methods (RULE_BASED, ML, LLM) and votes on the best interpretation.

To disable:
```env
ENABLE_FALLBACK_CHAIN=false
```

#### Manual Tool Selection
For advanced users who want to force specific tools:

```json
// In API request
{
  "context": {
    "task": "analyze data",
    "force_tools": ["anomaly_zscore", "clustering"]
  }
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Connection Refused" or "Tool Not Available"

**Problem:** Tool microservices not running

**Solution:**
```bash
# Check Docker containers
docker ps

# If containers are not running:
docker-compose up -d --build

# Check logs
docker-compose logs anomaly-zscore
```

#### 2. Backend Not Starting

**Problem:** Port 8080 already in use

**Solution:**
```bash
# Windows: Find and kill process on port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8080 | xargs kill -9

# Or change the port:
uvicorn app.main:app --reload --port 8090
```

#### 3. Frontend Not Loading

**Problem:** Node modules not installed or port conflict

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

#### 4. "Clarification Required" for Clear Prompts

**Problem:** Ambiguity detection too sensitive

**Solution:** Be more specific in your prompt:
- ❌ "analyze"
- ✅ "detect anomalies in speed column"

#### 5. No Results or Empty Output

**Problem:** 
- CSV format issues
- Missing required columns
- Tool execution timeout

**Solution:**
- Ensure CSV has proper headers
- Check Pipeline Execution Logs for errors
- Verify metric column exists in data
- Check tool service logs: `docker-compose logs <service-name>`

---

## 📊 Example Use Cases

### Use Case 1: IoT Sensor Monitoring

**Scenario:** Monitor temperature sensors for anomalies

**Data Format:**
```csv
timestamp,sensor_id,temperature,humidity
2024-11-01 10:00:00,S001,22.5,45
2024-11-01 10:05:00,S001,23.1,46
2024-11-01 10:10:00,S001,45.8,44  # Anomaly
```

**Configuration:**
- Task: "detect temperature anomalies"
- Metric: temperature
- Timestamp: timestamp
- Key Fields: sensor_id

### Use Case 2: Customer Segmentation

**Scenario:** Group customers by behavior

**Data Format:**
```csv
customer_id,total_purchases,avg_order_value,days_since_last_purchase
C001,25,150.50,5
C002,120,89.20,1
C003,3,200.00,180
```

**Configuration:**
- Task: "cluster customers into 3 segments"
- Metric: total_purchases,avg_order_value
- Key Fields: customer_id

### Use Case 3: Sales Forecasting

**Scenario:** Predict next week's sales

**Data Format:**
```csv
date,store_id,sales_amount
2024-10-01,ST001,15000
2024-10-02,ST001,16200
2024-10-03,ST001,14800
```

**Configuration:**
- Task: "forecast sales for next 7 days"
- Metric: sales_amount
- Timestamp: date
- Key Fields: store_id

---

## 🔐 Security Considerations

### For Production Deployment:

1. **Enable Authentication**
   - Add JWT token validation
   - Implement user roles and permissions

2. **HTTPS/SSL**
   - Use reverse proxy (nginx/Apache)
   - Configure SSL certificates

3. **Rate Limiting**
   - Add API rate limiting
   - Implement request throttling

4. **Data Privacy**
   - Encrypt sensitive data
   - Implement data retention policies
   - Add audit logging

5. **CORS Configuration**
   - Restrict allowed origins
   - Update CORS settings in `services/agent/app/main.py`

---

## 📚 API Documentation

### REST API Endpoint

**POST** `/v2/analyze`

**Request Body:**
```json
{
  "tenant_id": "user123",
  "data_pointer": {
    "uri": "inline://memory",
    "rows": [
      {"timestamp": "2024-11-01", "value": 100},
      {"timestamp": "2024-11-02", "value": 105}
    ]
  },
  "params": {
    "metric": "value",
    "timestamp_field": "timestamp",
    "key_fields": []
  },
  "context": {
    "task": "detect anomalies"
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
    "results": [
      {
        "tool_id": "anomaly_zscore",
        "tool_name": "Anomaly Detection (Z-Score)",
        "status": "success",
        "status_message": "✅ Execution successful - Found 5 anomalies",
        "execution_summary": {
          "anomalies_detected": 5,
          "rows_processed": 100
        },
        "output": {
          "anomalies": [...]
        }
      }
    ],
    "pipeline_logs": [...]
  }
}
```

Interactive API docs: `http://localhost:8080/docs`

---

## 🤝 Contributing

### How to Contribute:

1. **Fork the Repository**
2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make Changes**
4. **Test Thoroughly**
5. **Commit with Clear Messages**
   ```bash
   git commit -m "Add: Feature description"
   ```
6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create Pull Request**

### Development Guidelines:

- Follow existing code style
- Add tests for new features
- Update documentation
- Test with Docker Compose before submitting

---

## 📞 Support & Contact

### Getting Help:

1. **Check Documentation**
   - README.md
   - PIPELINE_LOGGING.md
   - FALLBACK_CHAIN.md

2. **GitHub Issues**
   - Report bugs
   - Request features
   - Ask questions

3. **Logs**
   - Backend logs: `services/agent/logs/agent_v2.log`
   - Docker logs: `docker-compose logs <service-name>`
   - Browser console: F12 → Console tab

---

## 📋 System Requirements

### Minimum Requirements:
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 2GB free space
- **OS**: Windows 10+, Linux, macOS

### Recommended Requirements:
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 5GB+ free space
- **Network**: Stable internet for API calls

---

## 🎓 Learning Resources

### Understanding the Pipeline:

1. **V2 Pipeline Architecture**
   ```
   Input → Context Extraction → Chaining Manager → Tool Invocation → Output
   ```

2. **Consensus Voting**
   - System tries multiple methods (RULE, ML, LLM)
   - Uses majority voting for best accuracy
   - See FALLBACK_CHAIN.md for details

3. **Tool Microservices**
   - Each analysis type is a separate service
   - REST API communication
   - Horizontally scalable

### Advanced Topics:

- **Adding New Tools**: See `services/tools/` for examples
- **Custom Extraction Methods**: Extend `context_extractor.py`
- **Tool Chaining Logic**: Study `chaining_manager.py`
- **Frontend Customization**: Modify `frontend/src/App.js`

---

## 🚀 Deployment Guide

### Docker Deployment (Recommended)

1. **Build Production Images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Deploy to Server**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Setup Reverse Proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3001;
       }
       
       location /api {
           proxy_pass http://localhost:8080;
       }
   }
   ```

### Cloud Deployment

#### AWS:
- Use ECS with Docker Compose
- Or deploy to EC2 instances
- Use RDS for database (if needed)
- Configure security groups

#### Azure:
- Use Azure Container Instances
- Or Azure App Service
- Configure networking and firewall

#### Google Cloud:
- Use Cloud Run for containers
- Or GKE for Kubernetes deployment

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## ⚡ Quick Reference

### Start Everything:
```bash
# Backend
cd services/agent && uvicorn app.main:app --reload --port 8080

# Tools (separate terminal)
docker-compose up -d

# Frontend (separate terminal)
cd frontend && npm start
```

### Check Status:
```bash
# Backend: http://localhost:8080/health
# Frontend: http://localhost:3001
# Docker: docker ps
```

### View Logs:
```bash
# Backend
tail -f services/agent/logs/agent_v2.log

# Docker services
docker-compose logs -f anomaly-zscore

# Frontend
# Check browser console (F12)
```

---

**Version**: v2.0.0  
**Last Updated**: November 4, 2025  
**Maintained by**: SwetaAIS2024
