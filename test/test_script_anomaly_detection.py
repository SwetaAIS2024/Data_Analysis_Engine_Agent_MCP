"""
Simple V2 Anomaly Detection Test Script
Tests the V2 pipeline with real CSV data
"""
import requests
import pandas as pd
import json

# Load your dataset
df = pd.read_csv("test/test_data_final.csv")

# Convert DataFrame rows to list of dicts
rows = df.to_dict(orient="records")

print(f"Loaded {len(rows)} rows from test_data_final.csv")
print(f"Columns: {df.columns.tolist()}\n")

# Prepare the V2 request payload
payload = {
    "tenant_id": "dev-tenant",
    "context": {
        "task": "Detect anomalies in speed data with z-score threshold 2.0"
    },
    "data_pointer": {
        "uri": "sample://in-memory",
        "format": "inline",
        "rows": rows
    },
    "params": {
        "metric": "speed_kmh",
        "key_fields": ["segment_id", "sensor_id"],
        "timestamp_field": "timestamp",
        "threshold": 2.0,
        "rolling_window": "2min",
        "min_points": 2
    }
}

print("=" * 80)
print("Sending request to V2 endpoint...")
print("=" * 80 + "\n")

# Send the request to the V2 agent
try:
    response = requests.post(
        "http://localhost:8080/v2/analyze",
        json=payload,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        result = response.json()
        
        # Display pipeline metadata
        print("=" * 80)
        print("PIPELINE METADATA")
        print("=" * 80)
        if result.get('tool_meta'):
            meta = result['tool_meta']
            print(f"Version: {meta.get('pipeline_version')}")
            print(f"Duration: {meta.get('duration_seconds', 0):.2f}s")
            
            if meta.get('context_extraction'):
                ctx = meta['context_extraction']
                print(f"Goal: {ctx.get('goal')}")
                print(f"Data Type: {ctx.get('data_type')}")
            
            if meta.get('execution_plan'):
                plan = meta['execution_plan']
                print(f"Strategy: {plan.get('strategy')}")
                print(f"Tools: {', '.join(plan.get('tools', []))}")
        
        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        pipeline_result = result.get('result', {})
        print(f"Status: {pipeline_result.get('status')}")
        
        if pipeline_result.get('results'):
            for tool_result in pipeline_result['results']:
                print(f"\n Tool: {tool_result.get('tool_id')}")
                print(f" Status: {tool_result.get('status')}")
                
                if tool_result.get('output'):
                    output = tool_result['output']
                    # Handle nested output structure
                    if isinstance(output, dict) and 'output' in output:
                        output = output['output']
                    
                    if isinstance(output, dict):
                        if 'anomalies' in output:
                            anomalies = output['anomalies']
                            print(f" Anomalies Found: {len(anomalies)}")
                            
                            if anomalies:
                                print("\n First 5 Anomalies:")
                                for i, anomaly in enumerate(anomalies[:5], 1):
                                    print(f"  {i}. {anomaly}")
                        
                        if 'summary' in output:
                            print(f"\n Summary: {json.dumps(output['summary'], indent=2)}")
        
        # User feedback check
        if pipeline_result.get('user_feedback'):
            print("\n" + "=" * 80)
            print("⚠️  USER FEEDBACK REQUIRED")
            print("=" * 80)
            feedback = pipeline_result['user_feedback']
            print(json.dumps(feedback, indent=2))
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
    
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to backend")
    print("Make sure the agent is running: uvicorn app.main:app --reload --port 8080")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()