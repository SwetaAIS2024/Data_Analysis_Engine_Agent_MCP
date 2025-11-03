from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

app = FastAPI(title="incident_detector", version="1.0.0")

class Schema(BaseModel):
    timestamp: str
    entity_keys: Optional[List[str]] = []
    metric: str

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    threshold_type: str = "absolute"  # "absolute", "percentage", "sigma"
    threshold_value: float = 100.0
    min_duration: int = 1  # Minimum number of consecutive violations
    incident_types: Optional[List[str]] = ["spike", "drop", "sustained_high", "sustained_low"]

class Payload(BaseModel):
    input: Input
    params: Params
    context: Dict[str, Any]


@app.post("/run")
def run(payload: Payload, request: Request):
    # Load data
    if payload.input.rows:
        df = pd.DataFrame(payload.input.rows)
    else:
        raise HTTPException(400, "For skeleton, supply input.rows inline.")

    ts_col = payload.input.schema.timestamp
    metric = payload.input.schema.metric
    entity_keys = payload.input.schema.entity_keys or []
    
    if ts_col not in df.columns:
        raise HTTPException(400, f"Timestamp column '{ts_col}' not found")
    if metric not in df.columns:
        raise HTTPException(400, f"Metric column '{metric}' not found")
    
    # Convert timestamp
    df[ts_col] = pd.to_datetime(df[ts_col])
    df = df.sort_values(ts_col)
    
    incidents = []
    
    # Group by entities
    if entity_keys:
        groups = df.groupby(entity_keys)
    else:
        groups = [(None, df)]
    
    for entity_vals, group in groups:
        group = group.copy().sort_values(ts_col)
        values = group[metric].values
        timestamps = group[ts_col].values
        
        if len(values) < 2:
            continue
        
        # Calculate baseline statistics
        baseline_mean = np.mean(values)
        baseline_std = np.std(values)
        baseline_median = np.median(values)
        
        # Determine threshold based on type
        if payload.params.threshold_type == "absolute":
            upper_threshold = payload.params.threshold_value
            lower_threshold = -payload.params.threshold_value
        elif payload.params.threshold_type == "percentage":
            upper_threshold = baseline_mean * (1 + payload.params.threshold_value / 100)
            lower_threshold = baseline_mean * (1 - payload.params.threshold_value / 100)
        elif payload.params.threshold_type == "sigma":
            upper_threshold = baseline_mean + (payload.params.threshold_value * baseline_std)
            lower_threshold = baseline_mean - (payload.params.threshold_value * baseline_std)
        else:
            raise HTTPException(400, f"Unknown threshold_type: {payload.params.threshold_type}")
        
        # Detect incidents
        incident_types = payload.params.incident_types or ["spike", "drop"]
        
        # 1. Spike detection (sudden increase)
        if "spike" in incident_types:
            for i in range(1, len(values)):
                if values[i] > upper_threshold and values[i] > values[i-1] * 1.5:
                    incident = {
                        "type": "spike",
                        "timestamp": str(timestamps[i]),
                        "value": float(values[i]),
                        "baseline": float(baseline_mean),
                        "deviation": float(values[i] - baseline_mean),
                        "severity": "high" if values[i] > upper_threshold * 1.5 else "medium"
                    }
                    
                    if entity_keys and entity_vals is not None:
                        if isinstance(entity_vals, tuple):
                            incident["entity"] = dict(zip(entity_keys, entity_vals))
                        else:
                            incident["entity"] = {entity_keys[0]: entity_vals}
                    
                    incidents.append(incident)
        
        # 2. Drop detection (sudden decrease)
        if "drop" in incident_types:
            for i in range(1, len(values)):
                if values[i] < lower_threshold and values[i] < values[i-1] * 0.5:
                    incident = {
                        "type": "drop",
                        "timestamp": str(timestamps[i]),
                        "value": float(values[i]),
                        "baseline": float(baseline_mean),
                        "deviation": float(baseline_mean - values[i]),
                        "severity": "high" if values[i] < lower_threshold * 0.5 else "medium"
                    }
                    
                    if entity_keys and entity_vals is not None:
                        if isinstance(entity_vals, tuple):
                            incident["entity"] = dict(zip(entity_keys, entity_vals))
                        else:
                            incident["entity"] = {entity_keys[0]: entity_vals}
                    
                    incidents.append(incident)
        
        # 3. Sustained high (consecutive values above threshold)
        if "sustained_high" in incident_types:
            consecutive = 0
            start_idx = None
            
            for i in range(len(values)):
                if values[i] > upper_threshold:
                    if consecutive == 0:
                        start_idx = i
                    consecutive += 1
                else:
                    if consecutive >= payload.params.min_duration:
                        incident = {
                            "type": "sustained_high",
                            "start_timestamp": str(timestamps[start_idx]),
                            "end_timestamp": str(timestamps[i-1]),
                            "duration_points": consecutive,
                            "avg_value": float(np.mean(values[start_idx:i])),
                            "baseline": float(baseline_mean),
                            "severity": "high"
                        }
                        
                        if entity_keys and entity_vals is not None:
                            if isinstance(entity_vals, tuple):
                                incident["entity"] = dict(zip(entity_keys, entity_vals))
                            else:
                                incident["entity"] = {entity_keys[0]: entity_vals}
                        
                        incidents.append(incident)
                    
                    consecutive = 0
        
        # 4. Sustained low (consecutive values below threshold)
        if "sustained_low" in incident_types:
            consecutive = 0
            start_idx = None
            
            for i in range(len(values)):
                if values[i] < lower_threshold:
                    if consecutive == 0:
                        start_idx = i
                    consecutive += 1
                else:
                    if consecutive >= payload.params.min_duration:
                        incident = {
                            "type": "sustained_low",
                            "start_timestamp": str(timestamps[start_idx]),
                            "end_timestamp": str(timestamps[i-1]),
                            "duration_points": consecutive,
                            "avg_value": float(np.mean(values[start_idx:i])),
                            "baseline": float(baseline_mean),
                            "severity": "medium"
                        }
                        
                        if entity_keys and entity_vals is not None:
                            if isinstance(entity_vals, tuple):
                                incident["entity"] = dict(zip(entity_keys, entity_vals))
                            else:
                                incident["entity"] = {entity_keys[0]: entity_vals}
                        
                        incidents.append(incident)
                    
                    consecutive = 0
    
    # Incident summary
    incident_counts = {}
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    
    for incident in incidents:
        inc_type = incident.get("type", "unknown")
        incident_counts[inc_type] = incident_counts.get(inc_type, 0) + 1
        
        severity = incident.get("severity", "low")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    summary = {
        "total_incidents": len(incidents),
        "incident_types": incident_counts,
        "severity_distribution": severity_counts,
        "detection_method": payload.params.threshold_type,
        "threshold_value": payload.params.threshold_value
    }
    
    return {
        "status": "success",
        "output": {
            "incidents": incidents,
            "summary": summary
        },
        "meta": {
            "tool": "incident_detector",
            "version": "1.0.0"
        }
    }
