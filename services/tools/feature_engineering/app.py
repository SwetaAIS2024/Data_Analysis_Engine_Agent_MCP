from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

app = FastAPI(title="feature_engineering", version="1.0.0")

class Schema(BaseModel):
    timestamp: Optional[str] = None
    entity_keys: Optional[List[str]] = []
    metric: Optional[str] = None

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    operations: Optional[List[str]] = ["rolling_stats", "lag_features"]  
    # Available: "rolling_stats", "lag_features", "time_features", "aggregations"
    window_size: int = 5
    lag_periods: Optional[List[int]] = [1, 2, 3]

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

    original_columns = df.columns.tolist()
    new_features = []
    
    # Get metric column
    metric = payload.input.schema.metric
    if not metric or metric not in df.columns:
        # Use first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            metric = numeric_cols[0]
        else:
            raise HTTPException(400, "No numeric column found for feature engineering")
    
    # Convert timestamp if exists
    ts_col = payload.input.schema.timestamp
    if ts_col and ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col])
        df = df.sort_values(ts_col)
    
    # Get entity keys for grouping
    entity_keys = payload.input.schema.entity_keys or []
    
    operations = payload.params.operations or ["rolling_stats"]
    
    # Operation 1: Rolling Statistics
    if "rolling_stats" in operations:
        window = payload.params.window_size
        
        if entity_keys:
            # Group by entities
            for entity_combo, group in df.groupby(entity_keys):
                indices = group.index
                
                # Rolling mean
                df.loc[indices, f"{metric}_rolling_mean_{window}"] = group[metric].rolling(window=window, min_periods=1).mean()
                # Rolling std
                df.loc[indices, f"{metric}_rolling_std_{window}"] = group[metric].rolling(window=window, min_periods=1).std()
                # Rolling min/max
                df.loc[indices, f"{metric}_rolling_min_{window}"] = group[metric].rolling(window=window, min_periods=1).min()
                df.loc[indices, f"{metric}_rolling_max_{window}"] = group[metric].rolling(window=window, min_periods=1).max()
        else:
            # No grouping
            df[f"{metric}_rolling_mean_{window}"] = df[metric].rolling(window=window, min_periods=1).mean()
            df[f"{metric}_rolling_std_{window}"] = df[metric].rolling(window=window, min_periods=1).std()
            df[f"{metric}_rolling_min_{window}"] = df[metric].rolling(window=window, min_periods=1).min()
            df[f"{metric}_rolling_max_{window}"] = df[metric].rolling(window=window, min_periods=1).max()
        
        new_features.extend([
            f"{metric}_rolling_mean_{window}",
            f"{metric}_rolling_std_{window}",
            f"{metric}_rolling_min_{window}",
            f"{metric}_rolling_max_{window}"
        ])
    
    # Operation 2: Lag Features
    if "lag_features" in operations:
        lag_periods = payload.params.lag_periods or [1, 2, 3]
        
        for lag in lag_periods:
            if entity_keys:
                df[f"{metric}_lag_{lag}"] = df.groupby(entity_keys)[metric].shift(lag)
            else:
                df[f"{metric}_lag_{lag}"] = df[metric].shift(lag)
            
            new_features.append(f"{metric}_lag_{lag}")
    
    # Operation 3: Time Features
    if "time_features" in operations and ts_col and ts_col in df.columns:
        df['hour'] = df[ts_col].dt.hour
        df['day_of_week'] = df[ts_col].dt.dayofweek
        df['day_of_month'] = df[ts_col].dt.day
        df['month'] = df[ts_col].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        new_features.extend(['hour', 'day_of_week', 'day_of_month', 'month', 'is_weekend'])
    
    # Operation 4: Aggregations by entity
    if "aggregations" in operations and entity_keys:
        for entity_combo, group in df.groupby(entity_keys):
            indices = group.index
            
            # Entity-level statistics
            df.loc[indices, f"{metric}_entity_mean"] = group[metric].mean()
            df.loc[indices, f"{metric}_entity_std"] = group[metric].std()
            df.loc[indices, f"{metric}_entity_count"] = len(group)
        
        new_features.extend([
            f"{metric}_entity_mean",
            f"{metric}_entity_std",
            f"{metric}_entity_count"
        ])
    
    # Fill NaN values created by rolling/lag
    df = df.fillna(method='bfill').fillna(0)
    
    # Prepare output
    enriched_data = df.to_dict(orient="records")
    
    summary = {
        "original_features": len(original_columns),
        "new_features_created": len(new_features),
        "total_features": len(df.columns),
        "operations_applied": operations,
        "new_feature_names": new_features,
        "rows_processed": len(df)
    }
    
    return {
        "status": "success",
        "output": {
            "enriched_data": enriched_data,
            "new_features": new_features,
            "summary": summary
        },
        "meta": {
            "tool": "feature_engineering",
            "version": "1.0.0"
        }
    }

