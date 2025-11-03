from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

app = FastAPI(title="timeseries_forecaster", version="1.0.0")

class Schema(BaseModel):
    timestamp: str
    entity_keys: Optional[List[str]] = []
    metric: str

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    forecast_periods: int = 10  # Number of periods to forecast
    method: str = "linear"  # "linear" or "moving_average"
    confidence_level: float = 0.95

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
    
    forecast_results = []
    
    # Group by entities if specified
    if entity_keys:
        groups = df.groupby(entity_keys)
    else:
        groups = [(None, df)]
    
    for entity_vals, group in groups:
        group = group.copy()
        group = group.sort_values(ts_col)
        
        # Get time series values
        ts_values = group[metric].values
        timestamps = group[ts_col].values
        
        if len(ts_values) < 3:
            continue  # Need at least 3 points
        
        # Forecast based on method
        if payload.params.method == "linear":
            # Simple linear regression forecast
            X = np.arange(len(ts_values)).reshape(-1, 1)
            y = ts_values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Forecast future values
            future_X = np.arange(len(ts_values), len(ts_values) + payload.params.forecast_periods).reshape(-1, 1)
            forecast_values = model.predict(future_X)
            
            # Calculate residuals for confidence intervals
            predictions = model.predict(X)
            residuals = y - predictions
            std_error = np.std(residuals)
            
            # Confidence interval (simple approximation)
            z_score = 1.96 if payload.params.confidence_level >= 0.95 else 1.645
            margin = z_score * std_error
            
        elif payload.params.method == "moving_average":
            # Moving average forecast
            window = min(5, len(ts_values))
            ma = np.mean(ts_values[-window:])
            
            forecast_values = np.full(payload.params.forecast_periods, ma)
            
            # Confidence based on recent variance
            std_error = np.std(ts_values[-window:])
            z_score = 1.96 if payload.params.confidence_level >= 0.95 else 1.645
            margin = z_score * std_error
            
        else:
            raise HTTPException(400, f"Unknown method: {payload.params.method}")
        
        # Generate future timestamps
        freq = pd.infer_freq(timestamps)
        if freq is None:
            # Estimate frequency from first two points
            time_diff = timestamps[1] - timestamps[0]
            freq = time_diff
        
        last_timestamp = pd.Timestamp(timestamps[-1])
        future_timestamps = pd.date_range(
            start=last_timestamp, 
            periods=payload.params.forecast_periods + 1,
            freq=freq
        )[1:]  # Exclude the start point
        
        # Build forecast points
        forecast_points = []
        for i, (ts, value) in enumerate(zip(future_timestamps, forecast_values)):
            point = {
                "timestamp": str(ts),
                "forecast_value": float(value),
                "lower_bound": float(value - margin),
                "upper_bound": float(value + margin),
                "period": i + 1
            }
            
            if entity_keys and entity_vals is not None:
                if isinstance(entity_vals, tuple):
                    for key, val in zip(entity_keys, entity_vals):
                        point[key] = val
                else:
                    point[entity_keys[0]] = entity_vals
            
            forecast_points.append(point)
        
        # Entity summary
        entity_result = {
            "entity": dict(zip(entity_keys, entity_vals)) if entity_keys and entity_vals else None,
            "historical_points": len(ts_values),
            "forecast_points": forecast_points,
            "method": payload.params.method,
            "last_actual_value": float(ts_values[-1]),
            "trend": "increasing" if forecast_values[-1] > ts_values[-1] else "decreasing"
        }
        
        forecast_results.append(entity_result)
    
    # Overall summary
    total_forecast_points = sum(len(r["forecast_points"]) for r in forecast_results)
    
    summary = {
        "method": payload.params.method,
        "forecast_periods": payload.params.forecast_periods,
        "entities_forecasted": len(forecast_results),
        "total_forecast_points": total_forecast_points,
        "confidence_level": payload.params.confidence_level
    }
    
    return {
        "status": "success",
        "output": {
            "forecast": forecast_results,
            "summary": summary
        },
        "meta": {
            "tool": "timeseries_forecaster",
            "version": "1.0.0",
            "method": payload.params.method
        }
    }
