# DAEA Integration Guide - Plugging Into Other Systems

## 🎯 Overview

This guide explains how to integrate the Data Analysis Engine Agent (DAEA) into existing enterprise systems as a pluggable microservice.

---

## 🏗️ Architecture Patterns

### Pattern 1: REST API Integration (Recommended)

**Use When:**
- Parent system is any language (Python, Java, Node.js, C#, etc.)
- Simple integration needed
- Parent system has internet/network access to DAEA

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│           PARENT SYSTEM (Enterprise App)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │  │   Database   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│         │                  │                            │
│         └─────────┬────────┘                            │
└───────────────────┼─────────────────────────────────────┘
                    │ HTTP POST /v2/analyze
                    │ (tenant_id, data, context)
                    ↓
┌─────────────────────────────────────────────────────────┐
│                   DAEA MICROSERVICE                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Port 8080)                     │  │
│  │  • Context Extraction                            │  │
│  │  • Tool Selection                                │  │
│  │  • Execution                                     │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tool Microservices (Docker)                     │  │
│  │  • Anomaly Detection                             │  │
│  │  • Clustering                                    │  │
│  │  • Forecasting, etc.                             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📡 Integration Examples

### Example 1: Django Integration

```python
# Parent System: Django E-commerce Platform
# File: analytics/views.py

import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import AnalysisHistory

DAEA_URL = "http://daea-service:8080/v2/analyze"

@login_required
def analyze_sales_anomalies(request):
    """Detect anomalies in sales data using DAEA"""
    
    # Get user and organization info
    user = request.user
    organization = user.organization
    
    # Get sales data from database
    sales_data = get_sales_data(organization.id)
    
    # Call DAEA
    response = requests.post(DAEA_URL, json={
        "tenant_id": f"{organization.slug}_{user.id}",  # Track by org + user
        "data_pointer": {
            "uri": "inline://memory",
            "format": "csv",
            "rows": sales_data
        },
        "params": {
            "metric": "sales_amount",
            "timestamp_field": "date",
            "key_fields": ["product_id", "region"]
        },
        "context": {
            "task": "detect sales anomalies"
        }
    })
    
    if response.status_code == 200:
        result = response.json()
        
        # Store in database for audit trail
        AnalysisHistory.objects.create(
            user=user,
            organization=organization,
            daea_request_id=result['request_id'],  # Link to DAEA logs!
            analysis_type='anomaly_detection',
            status=result['status'],
            results=result['result'],
            duration_seconds=result['tool_meta']['duration_seconds']
        )
        
        return JsonResponse({
            'success': True,
            'request_id': result['request_id'],
            'anomalies': result['result']['results'][0]['output']['anomalies']
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'DAEA service unavailable'
        }, status=500)


# models.py
from django.db import models

class AnalysisHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    daea_request_id = models.CharField(max_length=100, db_index=True)  # For tracing!
    analysis_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    results = models.JSONField()
    duration_seconds = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['daea_request_id']),  # Quick lookup
            models.Index(fields=['organization', 'created_at']),
        ]
```

**Benefits:**
- ✅ User reports issue → Look up by `daea_request_id` in Django DB → Find DAEA logs
- ✅ Track which organization/user ran which analysis
- ✅ Audit trail for compliance
- ✅ Usage analytics per organization

---

### Example 2: Node.js/Express Integration

```javascript
// Parent System: Node.js E-commerce Backend
// File: routes/analytics.js

const express = require('express');
const axios = require('axios');
const router = express.Router();
const { AnalysisHistory } = require('../models');

const DAEA_URL = 'http://daea-service:8080/v2/analyze';

router.post('/analyze-customer-behavior', authenticateToken, async (req, res) => {
  try {
    const { userId, organizationId } = req.user;
    const { customerData, analysisType } = req.body;
    
    // Build tenant_id: organization_user
    const tenantId = `org_${organizationId}_user_${userId}`;
    
    // Call DAEA
    const response = await axios.post(DAEA_URL, {
      tenant_id: tenantId,
      data_pointer: {
        uri: 'inline://memory',
        format: 'csv',
        rows: customerData
      },
      params: {
        metric: 'purchase_amount',
        key_fields: ['customer_id']
      },
      context: {
        task: analysisType  // e.g., "cluster customers"
      }
    });
    
    const result = response.data;
    
    // Store in MongoDB for audit
    await AnalysisHistory.create({
      userId,
      organizationId,
      daeaRequestId: result.request_id,  // Link to DAEA!
      analysisType,
      status: result.status,
      results: result.result,
      durationSeconds: result.tool_meta.duration_seconds,
      createdAt: new Date()
    });
    
    res.json({
      success: true,
      requestId: result.request_id,
      results: result.result
    });
    
  } catch (error) {
    console.error('DAEA integration error:', error);
    res.status(500).json({
      success: false,
      error: 'Analysis service unavailable'
    });
  }
});

module.exports = router;
```

---

### Example 3: Microservices with Message Queue

**Use When:**
- Asynchronous processing needed
- High volume of requests
- Decoupled architecture

```python
# Parent System publishes to RabbitMQ/Kafka
# DAEA consumes messages, processes, publishes results

# Parent System (Publisher)
import pika
import json

def request_analysis(user_id, org_id, data, analysis_type):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    
    message = {
        "tenant_id": f"org_{org_id}_user_{user_id}",
        "data": data,
        "analysis_type": analysis_type,
        "callback_url": f"https://parent-system.com/api/analysis-callback",
        "parent_request_id": generate_parent_request_id()  # Parent's tracking ID
    }
    
    channel.basic_publish(
        exchange='daea_requests',
        routing_key='analyze',
        body=json.dumps(message)
    )
    
    connection.close()


# DAEA (Consumer) - Add to main.py
from fastapi import BackgroundTasks
import pika

def process_queue_message(message):
    """Process message from queue"""
    data = json.loads(message)
    
    # Call existing /v2/analyze logic
    result = analyze_v2(AnalyzeRequest(
        tenant_id=data['tenant_id'],
        data_pointer=DataPointer(
            uri="inline://memory",
            rows=data['data']
        ),
        context={"task": data['analysis_type']}
    ))
    
    # Post results back to parent system
    requests.post(data['callback_url'], json={
        "parent_request_id": data['parent_request_id'],
        "daea_request_id": result.request_id,  # Link!
        "results": result.result
    })
```

---

## 🔐 Authentication & Security

### Scenario: Parent System Validates Tenant

```python
# DAEA Enhancement: Add authentication middleware

from fastapi import HTTPException, Header
import jwt

VALID_TENANTS = {
    "org_salesforce": {"quota": 1000, "api_key": "sk_live_abc123"},
    "org_hubspot": {"quota": 5000, "api_key": "sk_live_def456"},
    "org_internal": {"quota": 10000, "api_key": "sk_live_ghi789"}
}

async def verify_tenant(
    authorization: str = Header(...),
    tenant_id: str = None
):
    """Verify tenant has permission"""
    
    # Extract API key from header
    api_key = authorization.replace("Bearer ", "")
    
    # Validate
    if tenant_id not in VALID_TENANTS:
        raise HTTPException(status_code=403, detail="Invalid tenant")
    
    if VALID_TENANTS[tenant_id]["api_key"] != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check quota
    usage_today = count_requests(tenant_id, today)
    if usage_today >= VALID_TENANTS[tenant_id]["quota"]:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    
    return tenant_id


# Use in endpoint
@app.post("/v2/analyze", dependencies=[Depends(verify_tenant)])
def analyze_v2(req: AnalyzeRequest):
    # Now validated!
    ...
```

**Parent System Request:**
```javascript
fetch('http://daea-service:8080/v2/analyze', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk_live_abc123',  // Parent's API key
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    tenant_id: 'org_salesforce',
    data_pointer: {...},
    context: {...}
  })
});
```

---

## 📊 Real-World Integration Scenarios

### Scenario 1: Salesforce CRM Integration

```
Salesforce (Parent)
├─ Sales Dashboard
│  └─ "Analyze Opportunity Pipeline" button
│      └─ Calls DAEA with tenant_id="salesforce_sales_team"
│
├─ Marketing Dashboard
│  └─ "Cluster Leads" button
│      └─ Calls DAEA with tenant_id="salesforce_marketing_team"
│
└─ Admin Panel
   └─ Shows usage per team (tenant_id)
   └─ Shows all request_ids for audit
```

**Implementation:**
```javascript
// Salesforce Lightning Component
handleAnalyzeClick() {
  const orgId = this.organizationId;
  const userId = this.userId;
  
  fetch(`https://daea-service.company.com/v2/analyze`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tenant_id: `salesforce_${orgId}_${userId}`,  // Unique per user!
      data_pointer: {
        uri: 'inline://memory',
        rows: this.opportunityData
      },
      context: {
        task: 'detect anomalies in opportunity close rates'
      }
    })
  })
  .then(response => response.json())
  .then(data => {
    // Store request_id in Salesforce custom object
    this.createAnalysisRecord({
      DAEA_Request_ID__c: data.request_id,
      User__c: userId,
      Status__c: data.status,
      Results__c: JSON.stringify(data.result)
    });
    
    this.displayResults(data.result);
  });
}
```

---

### Scenario 2: Enterprise Data Platform

```
Enterprise Data Platform
├─ Data Lake (S3, Azure Blob)
├─ ETL Pipelines (Airflow)
├─ Reporting (Tableau, Power BI)
└─ DAEA Integration ← Automated analysis
```

**Airflow DAG:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

def run_daily_anomaly_detection(**context):
    """Run DAEA analysis daily"""
    
    # Get data from data lake
    data = fetch_from_s3('s3://company-data/daily-metrics.csv')
    
    # Call DAEA
    response = requests.post('http://daea:8080/v2/analyze', json={
        "tenant_id": "airflow_daily_pipeline",  # Track automated runs
        "data_pointer": {
            "uri": "s3://company-data/daily-metrics.csv",
            "rows": data
        },
        "context": {
            "task": "detect anomalies in daily metrics"
        }
    })
    
    result = response.json()
    
    # Store in data warehouse
    store_in_redshift(
        table='analysis_results',
        data={
            'daea_request_id': result['request_id'],
            'execution_date': context['execution_date'],
            'anomalies_found': len(result['result']['results'][0]['output']['anomalies']),
            'results': result['result']
        }
    )
    
    # Send alert if anomalies found
    if result['result']['results'][0]['output']['anomalies']:
        send_slack_alert(f"Anomalies detected! Request ID: {result['request_id']}")


dag = DAG('daily_anomaly_detection', schedule_interval='@daily')

task = PythonOperator(
    task_id='run_daea_analysis',
    python_callable=run_daily_anomaly_detection,
    dag=dag
)
```

---

## 🎯 How tenant_id and request_id Help

### Problem Without Them:

```
Parent System Log:
❌ "User clicked analyze button"
❌ "Called analysis service"
❌ "Got error"
❌ Can't find DAEA logs → Dead end

DAEA Log:
❌ "[ERROR] Analysis failed"
❌ Which user? Which parent system call?
❌ Can't trace back → Dead end
```

### Solution With Them:

```
Parent System Log:
✅ "User john@company.com clicked analyze"
✅ "Called DAEA with tenant_id=company_sales"
✅ "Got request_id=abc-123-xyz"
✅ "Stored in DB: analysis_id=789, daea_request_id=abc-123-xyz"

DAEA Log:
✅ "[REQUEST abc-123-xyz] Tenant: company_sales"
✅ "[REQUEST abc-123-xyz] Context extraction started"
✅ "[REQUEST abc-123-xyz] ERROR: Invalid CSV format"

Linking:
Parent DB → daea_request_id=abc-123-xyz → DAEA logs
Found exact error! User uploaded invalid CSV.
```

---

## 📈 Usage Analytics Dashboard

With tenant_id and request_id, you can build powerful analytics:

```sql
-- Parent System Analytics Query

-- 1. Usage by department
SELECT 
    tenant_id,
    COUNT(*) as total_requests,
    AVG(duration_seconds) as avg_duration,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
FROM analysis_history
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY tenant_id
ORDER BY total_requests DESC;

Result:
tenant_id           | total_requests | avg_duration | successful | failed
--------------------|----------------|--------------|------------|-------
sales_team          | 450            | 2.3s         | 445        | 5
marketing_team      | 320            | 3.1s         | 315        | 5
data_science_team   | 180            | 4.5s         | 178        | 2


-- 2. Most common analysis types
SELECT 
    analysis_type,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration
FROM analysis_history
WHERE tenant_id = 'sales_team'
GROUP BY analysis_type
ORDER BY count DESC;

Result:
analysis_type           | count | avg_duration
------------------------|-------|-------------
anomaly_detection       | 280   | 2.1s
forecasting             | 95    | 4.8s
clustering              | 75    | 3.2s


-- 3. Error tracking
SELECT 
    daea_request_id,
    tenant_id,
    analysis_type,
    error_message,
    created_at
FROM analysis_history
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Development/Small Scale)

```yaml
# Parent system's docker-compose.yml
services:
  parent-app:
    image: company/parent-app:latest
    environment:
      - DAEA_URL=http://daea:8080
    depends_on:
      - daea
  
  daea:
    image: daea:v2
    ports:
      - "8080:8080"
    environment:
      - ENABLE_AUTH=true
      - VALID_TENANTS=org1,org2,org3
    depends_on:
      - daea-tools
  
  daea-tools:
    image: daea-tools:v2
    # Tool microservices
```

### Option 2: Kubernetes (Production)

```yaml
# daea-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: daea-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: daea
  template:
    metadata:
      labels:
        app: daea
    spec:
      containers:
      - name: daea
        image: daea:v2
        ports:
        - containerPort: 8080
        env:
        - name: ENABLE_AUTH
          value: "true"
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: daea-service
spec:
  selector:
    app: daea
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

**Parent system connects:**
```python
DAEA_URL = "http://daea-service.default.svc.cluster.local:8080"
```

---

## ✅ Benefits Summary

| Benefit | How tenant_id Helps | How request_id Helps |
|---------|---------------------|---------------------|
| **Tracing** | Know which organization/team | Track exact request through pipeline |
| **Debugging** | Filter logs by tenant | Find all logs for specific request |
| **Billing** | Charge per tenant usage | Track individual request costs |
| **Quotas** | Enforce limits per tenant | Count requests per tenant |
| **Audit** | Track who did what | Exact execution trail |
| **Support** | "Which customer reported issue?" | "Show me logs for request X" |
| **Analytics** | Usage patterns per tenant | Performance metrics per request |
| **Security** | Isolate tenant data | Trace security incidents |

---

## 🎯 Conclusion

When DAEA is plugged into another system:

1. **tenant_id** = "Who is making the request?" (organization, team, user)
2. **request_id** = "What is this specific request?" (unique tracking ID)

Together they enable:
- ✅ Full traceability from parent system to DAEA logs
- ✅ Multi-tenant support (multiple organizations using same DAEA)
- ✅ Usage analytics and billing
- ✅ Error tracking and debugging
- ✅ Security and access control
- ✅ Audit trails for compliance

**Without them:** DAEA is a black box with no way to track who's using it or trace errors back to source.

**With them:** DAEA is a fully integrated, traceable, multi-tenant microservice ready for enterprise deployment! 🚀
