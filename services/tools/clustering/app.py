from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np

app = FastAPI(title="clustering", version="1.0.0")

class Schema(BaseModel):
    timestamp: Optional[str] = None
    entity_keys: Optional[List[str]] = []
    metric: Optional[str] = None

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    algorithm: str = "kmeans"  # "kmeans" or "dbscan"
    n_clusters: int = 3  # For kmeans
    features: Optional[List[str]] = None  # Columns to use for clustering
    eps: float = 0.5  # For DBSCAN
    min_samples: int = 5  # For DBSCAN

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

    # Select features for clustering
    if payload.params.features:
        feature_cols = [col for col in payload.params.features if col in df.columns]
    elif payload.input.schema.metric:
        # Use metric column if specified
        feature_cols = [payload.input.schema.metric] if payload.input.schema.metric in df.columns else []
    else:
        # Use all numeric columns, excluding timestamps and entity keys
        exclude_cols = set()
        if payload.input.schema.timestamp:
            exclude_cols.add(payload.input.schema.timestamp)
        if payload.input.schema.entity_keys:
            exclude_cols.update(payload.input.schema.entity_keys)
        
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col not in exclude_cols]
    
    if not feature_cols:
        raise HTTPException(400, "No numeric features found for clustering")
    
    # Prepare feature matrix - ensure all columns are numeric and drop non-convertible
    numeric_df = df[feature_cols].copy()
    for col in feature_cols:
        numeric_df[col] = pd.to_numeric(numeric_df[col], errors='coerce')
    
    # Drop rows with NaN values after conversion
    numeric_df = numeric_df.dropna()
    
    if len(numeric_df) == 0:
        raise HTTPException(400, "No valid numeric data remaining after cleaning")
    
    X = numeric_df.values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Perform clustering
    if payload.params.algorithm == "kmeans":
        model = KMeans(n_clusters=payload.params.n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
        centers = scaler.inverse_transform(model.cluster_centers_)
    elif payload.params.algorithm == "dbscan":
        model = DBSCAN(eps=payload.params.eps, min_samples=payload.params.min_samples)
        labels = model.fit_predict(X_scaled)
        centers = None
    else:
        raise HTTPException(400, f"Unknown algorithm: {payload.params.algorithm}")
    
    # Add cluster labels to the cleaned dataframe
    numeric_df['cluster'] = labels
    
    # Build cluster summary
    cluster_info = []
    unique_labels = np.unique(labels)
    
    for label in unique_labels:
        if label == -1:  # DBSCAN noise points
            cluster_name = "noise"
        else:
            cluster_name = f"cluster_{label}"
        
        cluster_mask = (labels == label)
        cluster_size = np.sum(cluster_mask)
        
        cluster_data = {
            "cluster_id": int(label),
            "cluster_name": cluster_name,
            "size": int(cluster_size),
            "percentage": float(cluster_size / len(numeric_df) * 100)
        }
        
        # Add center coordinates if available
        if centers is not None and label >= 0:
            cluster_data["center"] = {
                feature_cols[i]: float(centers[label][i]) 
                for i in range(len(feature_cols))
            }
        
        # Add feature statistics for this cluster
        cluster_df = numeric_df[cluster_mask]
        cluster_data["statistics"] = {
            col: {
                "mean": float(cluster_df[col].mean()),
                "std": float(cluster_df[col].std()),
                "min": float(cluster_df[col].min()),
                "max": float(cluster_df[col].max())
            }
            for col in feature_cols
        }
        
        cluster_info.append(cluster_data)
    
    # Prepare output
    clustered_rows = numeric_df.to_dict(orient="records")
    
    summary = {
        "algorithm": payload.params.algorithm,
        "n_clusters": len(unique_labels) if payload.params.algorithm == "dbscan" else payload.params.n_clusters,
        "features_used": feature_cols,
        "total_points": len(numeric_df),
        "noise_points": int(np.sum(labels == -1)) if payload.params.algorithm == "dbscan" else 0
    }
    
    return {
        "status": "success",
        "output": {
            "clusters": cluster_info,
            "clustered_data": clustered_rows,
            "summary": summary
        },
        "meta": {
            "tool": "clustering",
            "version": "1.0.0",
            "algorithm": payload.params.algorithm
        }
    }

