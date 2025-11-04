# Data Analysis Engine Agent (V2)

## 🎯 Overview

An **intelligent, multi-layer pipeline system** that analyzes data using natural language prompts. Simply describe what you want, upload your data, and let the AI agent automatically select and execute the right analytical tools.

### ✨ Key Features

- 🤖 **Natural Language Interface**: Describe your analysis in plain English
- 🔍 **Intelligent Tool Selection**: Automatic tool selection with consensus voting
- 📊 **Multiple Analysis Types**: Anomaly detection, clustering, forecasting, classification, and more
- 🔗 **Smart Tool Chaining**: Sequential or parallel tool execution
- 📈 **Real-time Results**: Instant insights with visualizations
- 🪵 **Complete Pipeline Visibility**: See exactly what the system is doing at each step

---

## 🚀 Quick Start

### For End Users (Easiest Way)

```bash
# 1. Clone the repository
git clone https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP.git
cd Data_Analysis_Engine_Agent_MCP
git checkout DAA_v2

# 2. Start everything with Docker
docker-compose up -d --build

# 3. Open your browser
# Frontend: http://localhost:3001
# API Docs: http://localhost:8080/docs
```

**That's it!** 🎉 Now you can:
1. Upload your CSV file
2. Type what you want (e.g., "detect anomalies")
3. View results and pipeline logs

📖 **Full Setup Guide**: See [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) for detailed instructions

---

## 📊 What Can You Analyze?

| Analysis Type | Example Prompts | Use Cases |
|--------------|----------------|-----------|
| **Anomaly Detection** | "detect anomalies", "find outliers" | IoT monitoring, fraud detection |
| **Clustering** | "cluster data", "group similar items" | Customer segmentation, pattern discovery |
| **Forecasting** | "forecast next 7 days", "predict future" | Sales prediction, demand planning |
| **Classification** | "classify data", "predict category" | Churn prediction, risk assessment |
| **Stats Comparison** | "compare statistics", "compare groups" | A/B testing, regional analysis |
| **Feature Engineering** | "engineer features", "create features" | ML preprocessing, data transformation |
| **Incident Detection** | "detect incidents", "find failures" | System monitoring, quality control |

---

## 🏗️ Architecture (V2 Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                               │
│  • CSV Data Upload                                          │
│  • Natural Language Prompt ("detect anomalies")            │
│  • Configuration (metric, timestamp, etc.)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: CONTEXT EXTRACTION                                │
│  • Intent understanding with consensus voting               │
│  • Goal extraction (anomaly_detection, clustering, etc.)    │
│  • Data type detection (timeseries, tabular, geospatial)    │
│  • Confidence scoring                                        │
│  • Methods: RULE_BASED → ML → LLM (majority vote)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: CHAINING MANAGER (Planning & Decision Making)    │
│  • Tool selection based on goal                             │
│  • Execution strategy (single/sequential/parallel)          │
│  • Conflict detection & resolution                          │
│  • Dependency management                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: INVOCATION LAYER (Tool Execution)                │
│  • REST API calls to tool microservices                     │
│  • Timeout & retry handling                                 │
│  • Result aggregation                                        │
│  • Detailed execution logging                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: OUTPUT PREPARATION                                │
│  • Result formatting                                         │
│  • Pipeline logs compilation                                │
│  • UI-friendly response                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER OUTPUT                              │
│  • Analysis results with visualizations                     │
│  • Complete pipeline execution logs                         │
│  • Tool invocation details                                  │
│  • Downloadable results                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend (Agent Service)
- **Framework**: FastAPI (Python 3.11+)
- **Features**: Auto-reload, async support, OpenAPI docs
- **Logging**: Loguru with structured logs
- **Observability**: OpenTelemetry ready

### Tool Microservices (8 Services)
- **Containerization**: Docker
- **Communication**: REST APIs
- **Tools**: 
  - anomaly_zscore (Z-Score anomaly detection)
  - clustering (K-means, DBSCAN)
  - classifier_regressor (ML predictions)
  - timeseries_forecaster (ARIMA, Prophet)
  - stats_comparator (Statistical analysis)
  - geospatial_mapper (Geographic analysis)
  - incident_detector (Event detection)
  - feature_engineering (Feature creation)

### Frontend
- **Framework**: React.js
- **Features**: Real-time updates, CSV upload, visualizations
- **Port**: 3001

### Infrastructure
- **Orchestration**: Docker Compose
- **Auto-scaling**: Ready for Kubernetes (KEDA)
- **Load Balancing**: nginx-ready

---

## 📁 Project Structure

```
Data_Analysis_Engine_Agent/
├── services/
│   ├── agent/                      # Main agent service
│   │   ├── app/
│   │   │   ├── main.py            # FastAPI app + V2 pipeline
│   │   │   ├── intent_extraction/  # Context extraction layer
│   │   │   │   └── context_extractor.py  # Consensus voting
│   │   │   ├── planner/            # Chaining manager
│   │   │   │   └── chaining_manager.py
│   │   │   ├── dispatcher/         # Tool invocation
│   │   │   │   └── invocation_layer.py
│   │   │   ├── registry/           # Tool registry
│   │   │   ├── schemas/            # Pydantic models
│   │   │   └── observability/      # Tracing & metrics
│   │   └── requirements.txt
│   │
│   └── tools/                      # Microservices
│       ├── anomaly_zscore/
│       ├── clustering/
│       ├── classifier_regressor/
│       ├── timeseries_forecaster/
│       ├── stats_comparator/
│       ├── geospatial_mapper/
│       ├── incident_detector/
│       └── feature_engineering/
│
├── frontend/                       # React UI
│   ├── src/
│   │   ├── App.js                 # Main component
│   │   └── index.js
│   ├── package.json
│   └── public/
│
├── docker-compose.yml              # Orchestration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── USER_SETUP_GUIDE.md            # Complete setup guide
├── PIPELINE_LOGGING.md            # Logging documentation
└── FALLBACK_CHAIN.md              # Consensus voting guide
```

---

## 🚦 Getting Started (Development Mode)

### Prerequisites
- Python 3.11+
- Node.js 16+
- Docker & Docker Compose
- Git

### Backend Setup

```bash
# Navigate to agent service
cd services/agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --port 8080
```

### Tool Services Setup

```bash
# From project root
docker-compose up -d --build

# Verify services
docker ps
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

**Access Points:**
- Frontend: http://localhost:3001
- Backend API: http://localhost:8080
- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health

---

## 📖 Documentation

**📌 Choose Your Path:**

| I am a... | Start Here |
|-----------|------------|
| 👤 **End User** (Want to analyze data) | [User Setup Guide](USER_SETUP_GUIDE.md) - Quick start & usage |
| 💻 **Developer** (API integration, technical details) | [Developer Guide](USER_GUIDE.md) - API reference & architecture |
| 🚀 **Sharing/Deploying** (Setup for team/cloud) | [How to Share Guide](HOW_TO_SHARE.md) - Deployment options |

**📚 Additional Resources:**

| Document | Description |
|----------|-------------|
| [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) | Complete installation and usage guide for end users |
| [USER_GUIDE.md](USER_GUIDE.md) | Technical deep-dive, API reference, and developer documentation |
| [HOW_TO_SHARE.md](HOW_TO_SHARE.md) | Distribution and deployment methods |
| [PIPELINE_LOGGING.md](PIPELINE_LOGGING.md) | Pipeline execution logging details |
| [FALLBACK_CHAIN.md](FALLBACK_CHAIN.md) | Consensus voting mechanism |
| [API Docs](http://localhost:8080/docs) | Interactive OpenAPI documentation |

---

## 🎨 Dashboard Features

### 1. Pipeline Execution Logs
Real-time visibility into all pipeline layers:
- 🚀 **PIPELINE** (Purple): Overall pipeline events
- 📋 **CONTEXT EXTRACTION** (Blue): Intent understanding
- 🔗 **CHAINING MANAGER** (Orange): Tool selection & planning  
- ⚙️ **INVOCATION LAYER** (Green): Tool execution
- 📤 **OUTPUT PREPARATION** (Cyan): Result formatting

### 2. Tool Invocation Details
- Tool display names and status badges
- Execution summaries (rows processed, anomalies found)
- Status messages with detailed information
- Error handling and retry logic

### 3. Analysis Results
- CSV data preview
- Visualizations (charts, graphs)
- Downloadable results
- Tool-specific outputs

---

## 🔧 Configuration

### Environment Variables

```env
# Backend
AGENT_PORT=8080
LOG_LEVEL=INFO

# Features
ENABLE_FALLBACK_CHAIN=true        # Consensus voting
ENABLE_CONSENSUS_VOTING=true

# Optional: LLM Integration
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4
```

### Advanced Features

**Consensus Voting** (Default: Enabled)
- Tries multiple extraction methods (RULE, ML, LLM)
- Uses weighted voting (LLM=2 votes, others=1 vote)
- Returns result with highest agreement
- Adjusts confidence based on consensus level

**Manual Tool Selection**
```json
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

**Backend won't start:**
```bash
# Check port availability
netstat -ano | findstr :8080

# Change port if needed
uvicorn app.main:app --reload --port 8090
```

**Tool services not available:**
```bash
# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs
docker-compose logs anomaly-zscore
```

**Frontend issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**More help:** See [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) troubleshooting section

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Test with Docker Compose before submitting

---

## 📊 Example Workflows

### Workflow 1: Detect Anomalies in IoT Sensors
```
1. Upload sensor_data.csv
2. Task: "detect temperature anomalies"
3. Metric: temperature
4. Timestamp: timestamp
5. Key Fields: sensor_id
6. View results: 15 anomalies detected in 1000 rows
```

### Workflow 2: Customer Segmentation
```
1. Upload customer_data.csv
2. Task: "cluster customers into 4 groups"
3. Metric: purchase_amount, frequency
4. Key Fields: customer_id
5. View results: 4 clusters with characteristics
```

### Workflow 3: Sales Forecasting
```
1. Upload sales_history.csv
2. Task: "forecast sales for next 7 days"
3. Metric: sales_amount
4. Timestamp: date
5. Key Fields: store_id
6. View results: Predictions with confidence intervals
```

---

## 🔐 Security

For production deployments:
- Enable JWT authentication
- Configure HTTPS/SSL
- Implement rate limiting
- Add data encryption
- Set up audit logging
- Configure CORS properly

See [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) for security details.

---

## 📞 Support

- **Documentation**: Check docs in this repo
- **Issues**: [GitHub Issues](https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP/issues)
- **Logs**: 
  - Backend: `services/agent/logs/agent_v2.log`
  - Docker: `docker-compose logs <service-name>`

---

## 📋 System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 2GB free
- OS: Windows 10+, Linux, macOS

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 5GB+ free

---

## 🚀 What's New in V2

✅ **Consensus Voting**: Multiple extraction methods with majority voting  
✅ **Enhanced Logging**: Complete pipeline visibility with color-coded layers  
✅ **Improved UI**: Better tool invocation display with execution summaries  
✅ **Conflict Resolution**: Smart conflict detection and auto-resolution  
✅ **Better Accuracy**: Higher confidence in intent extraction  
✅ **Zero False Positives**: Removed incorrect conflict checks  

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

Built with:
- FastAPI for high-performance APIs
- React for responsive UI
- Docker for containerization
- OpenTelemetry for observability

---

**Version**: v2.0.0  
**Last Updated**: November 4, 2025  
**Maintained by**: SwetaAIS2024

---

## 🎯 Quick Links

- 📖 [Complete Setup Guide](USER_SETUP_GUIDE.md)
- 🪵 [Pipeline Logging Guide](PIPELINE_LOGGING.md)
- 🔗 [Consensus Voting Guide](FALLBACK_CHAIN.md)
- 🔧 [API Documentation](http://localhost:8080/docs)
- 🐛 [Report Issues](https://github.com/SwetaAIS2024/Data_Analysis_Engine_Agent_MCP/issues)

---

## 🧱 Core Components

### 1. Agent API Layer
**Tech:** Python (FastAPI/Flask), Docker  
**Purpose:** Exposes REST endpoints (e.g., `/analyze`) to accept input data and context

**Responsibilities:**
- Parse & validate request payloads
- Forward to Router for tool assignment
- Manage response formatting, chaining, and error handling
- Emit job/run events for visualization dashboards

### 2. Router Module
**Modes:**
- Rule-Based Routing: Based on input types, keywords, metadata
- ML-Based Routing: Intent classification using ML/LLM
- Hybrid Routing: Fast rules + fallback to model-driven dispatch

**Responsibilities:**
- Decide best-fit MCP tool or tool chain
- Send routing metadata to Dispatcher
- Generate trace identifiers and step metadata for visualization

### 3. Tool Dispatcher
**Function:** Orchestrates tool invocations

**Protocols Supported:**
- REST (default)
- gRPC (for low-latency/high-throughput)
- Kafka/RabbitMQ (for async workloads)

**Responsibilities:**
- Handles retries, timeouts
- Resolves tool endpoint from Tool Registry
- Loads authentication headers + payloads
- Publishes step progress and results for visualization and tracing

### 4. Tool Chaining Manager
**Purpose:** Executes tool pipelines

**Approach:**
- DAG-based chaining (e.g., Anomaly Detection -> Clustering)
- Agent-guided dynamic chaining

**Responsibilities:**
- Manage data hand-off between tools
- Track intermediate results and state
- Report stage transitions to the visualization subsystem

### 5. Tool Registry
**Storage:** Local JSON file or database

**Fields:**
- Tool name, task type, supported data types
- Endpoint URL & communication protocol
- Version, metadata, health status
- Visualization metadata: category, icon, color code, owner

### 6. MCP Tool Interface
**Standardized Schema:**
```json
{
	"input": { ... },
	"context": { ... }
}
```
**Returns:**
```json
{
	"status": "success",
	"output": { ... },
	"meta": { ... }
}
```

---

*This architecture enables scalable, flexible, and intelligent data analysis for diverse and demanding workloads.*

---

## Visualization & Monitoring Layer

**Purpose:** Provide full transparency into running processes and tool interactions.

**Components:**
- **Run Service / Jobs API:** Tracks all runs, jobs, steps, and statuses; exposes REST + WebSocket endpoints (e.g., `/v1/runs`, `/ws/runs/{id}`)
- **Dashboard UI:** Shows tool catalog, live runs, DAG visualizer (tool chaining), job progress, and metrics
- **Tracing:** OpenTelemetry + Jaeger/Tempo for distributed traces
- **Logs:** ELK/OpenSearch for structured logs (linked to runs)
- **Metrics:** Prometheus + Grafana for latency, throughput, error rate
- **Lineage:** OpenLineage/Marquez integration for dataset–tool–output provenance

**User View:**
- Tool catalog with capabilities, schema, and status
- Real-time run status, progress bars, ETA, per-step logs, and trace links
- DAG view showing current pipeline execution flow

---

## Communication & Throughput Management

**Options:**
- REST (development, small-scale)
- gRPC (binary RPCs, high throughput)
- Kafka (buffered, async tasks)

**Concurrency:**
- Python asyncio / Celery for parallel calls
- K8s for container auto-scaling
- KEDA for queue-based scaling

---

## Security Layer

**Auth:**
- JWT-based access control
- HMAC signing for internal tool calls

**Transport:**
- TLS encryption for REST/gRPC
- Kafka: TLS + SASL

**Audit Logging:**
- Request, tool, user, timestamp, result status
- Integrated into visualization UI for admin access

---

## Observability & Governance

**Tracing:** OpenTelemetry spans per request and tool
**Metrics:** Prometheus collectors for latency, throughput, queue lag
**Logging:** Structured, tenant-aware JSON logs
**SLOs & Alerts:** Alertmanager for anomalies and health checks

**Governance:**
- Versioning, tool lifecycle tracking
- Canary releases and shadow runs
- UI displays deprecation notices and tool change logs

---

## 🗃 Data & Task Support

**Input Types:**
- Tabular (CSV, Excel, SQL result)
- Text (incident reports, logs)
- JSON/XML (API or IoT device input)
- Images (traffic cams)
- Geo (GeoJSON, GPS points)

**Supported Tasks:**
- Anomaly Detection
- Incident Detection
- Time-Series Forecasting
- Descriptive Stats & Comparison
- Classification / Regression
- Clustering & Feature Engineering
- Geospatial Mapping & Analysis

---

## Deployment Notes

- Containerized with Docker for each tool and core module
- Use Docker Compose or Kubernetes for orchestration
- Includes visualization stack (Grafana, Jaeger, ELK) and UI dashboard
- Designed to plug into larger systems as a callable API service
- Future-proofed for more advanced ML planning agents (e.g., LLM planner)

---

## Next Steps

---

## Frontend Visualization

This project includes a React-based frontend for uploading datasets, running anomaly detection, and visualizing results.

### How to Run the Frontend

1. Open a terminal and navigate to the `frontend` folder:
	```
	cd frontend
	```
2. Install dependencies:
	```
	npm install
	```
3. Start the development server:
	```
	npm start
	```
4. Open your browser and go to:
	```
	http://localhost:3000
	```

**Note:** Make sure the MCP agent backend is running at `http://localhost:8080` before using the frontend.

### Features
- Upload CSV dataset
- Run anomaly detection
- View detected anomalies in a table and chart
- See summary statistics

You can extend the UI for more tools, real-time updates, and advanced visualizations as needed.

1. Scaffold base API + agent logic
2. Implement router (rule-based first)
3. Add 3–5 MCP tools with REST endpoints
4. Integrate Run Service + WebSocket for real-time progress
5. Add UI layer for visualization (DAG, runs, logs)
6. Package with Docker Compose for local testing
7. Extend with gRPC + Kafka for async cases


# Create a virtual environment named .venv
python -m venv t_venv

# Activate the virtual environment
t_venv\Scripts\activate

# (Optional) Upgrade pip
python -m pip install --upgrade pip

# (Optional) Install dependencies from requirements.txt
pip install -r requirements.txt