import requests
import pandas as pd

# Load your dataset
df = pd.read_csv("test/test_data_final.csv")

# Convert DataFrame rows to list of dicts
rows = df.to_dict(orient="records")

# Prepare the request payload
payload = {
    "tenant_id": "dev-tenant",
    "mode": "sync",
    "context": {"task": "anomaly_detection", "data_type": "tabular"},
    "data_pointer": {
        "uri": "sample://in-memory",
        "format": "inline",
        "rows": rows
    },
    "params": {
        "metric": "speed_kmh",           # Change as per your dataset
    "key_fields": ["segment_id", "sensor_id"],    # Group by both segment_id and sensor_id
        "timestamp_field": "timestamp",  # Change as per your dataset
        "zscore_threshold": 2.0,
        "rolling_window": "2min",
        "min_points": 2
    }
}

# Send the request to the agent
response = requests.post(
    "http://localhost:8080/v1/analyze",
    json=payload
)

# Print the results
print("Status:", response.status_code)
print("Response:", response.json())