from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

app = FastAPI(title="geospatial_mapper", version="1.0.0")

class Schema(BaseModel):
    timestamp: Optional[str] = None
    entity_keys: Optional[List[str]] = []
    metric: Optional[str] = None

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    lat_column: str = "latitude"
    lon_column: str = "longitude"
    aggregation: str = "mean"  # "mean", "sum", "count"
    grid_size: Optional[float] = None  # For spatial binning

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

    lat_col = payload.params.lat_column
    lon_col = payload.params.lon_column
    
    if lat_col not in df.columns:
        raise HTTPException(400, f"Latitude column '{lat_col}' not found")
    if lon_col not in df.columns:
        raise HTTPException(400, f"Longitude column '{lon_col}' not found")
    
    # Filter out invalid coordinates
    df = df.dropna(subset=[lat_col, lon_col])
    df = df[(df[lat_col] >= -90) & (df[lat_col] <= 90)]
    df = df[(df[lon_col] >= -180) & (df[lon_col] <= 180)]
    
    if len(df) == 0:
        raise HTTPException(400, "No valid geospatial coordinates found")
    
    # Get metric column
    metric = payload.input.schema.metric
    if metric and metric not in df.columns:
        metric = None
    
    # Geospatial analysis
    analysis = {
        "bounding_box": {
            "min_lat": float(df[lat_col].min()),
            "max_lat": float(df[lat_col].max()),
            "min_lon": float(df[lon_col].min()),
            "max_lon": float(df[lon_col].max())
        },
        "center": {
            "lat": float(df[lat_col].mean()),
            "lon": float(df[lon_col].mean())
        },
        "total_points": len(df)
    }
    
    # Create map points
    map_points = []
    for idx, row in df.iterrows():
        point = {
            "lat": float(row[lat_col]),
            "lon": float(row[lon_col])
        }
        
        if metric:
            point["value"] = float(row[metric]) if pd.notna(row[metric]) else None
        
        # Add entity info if available
        entity_keys = payload.input.schema.entity_keys or []
        for key in entity_keys:
            if key in row:
                point[key] = row[key]
        
        map_points.append(point)
    
    # Spatial binning (if grid_size specified)
    grid_data = None
    if payload.params.grid_size:
        grid_size = payload.params.grid_size
        
        # Create grid bins
        df['lat_bin'] = (df[lat_col] // grid_size) * grid_size
        df['lon_bin'] = (df[lon_col] // grid_size) * grid_size
        
        # Aggregate by grid
        if metric:
            if payload.params.aggregation == "mean":
                grid_agg = df.groupby(['lat_bin', 'lon_bin'])[metric].mean()
            elif payload.params.aggregation == "sum":
                grid_agg = df.groupby(['lat_bin', 'lon_bin'])[metric].sum()
            elif payload.params.aggregation == "count":
                grid_agg = df.groupby(['lat_bin', 'lon_bin'])[metric].count()
            else:
                grid_agg = df.groupby(['lat_bin', 'lon_bin'])[metric].mean()
            
            grid_data = []
            for (lat_bin, lon_bin), value in grid_agg.items():
                grid_data.append({
                    "lat": float(lat_bin + grid_size/2),  # Center of grid cell
                    "lon": float(lon_bin + grid_size/2),
                    "value": float(value),
                    "count": int(len(df[(df['lat_bin'] == lat_bin) & (df['lon_bin'] == lon_bin)]))
                })
        
        analysis["grid_cells"] = len(grid_data) if grid_data else 0
    
    # Hotspot detection (simple density-based)
    if metric:
        hotspots = df.nlargest(min(10, len(df)), metric)
        hotspot_points = []
        for idx, row in hotspots.iterrows():
            hotspot_points.append({
                "lat": float(row[lat_col]),
                "lon": float(row[lon_col]),
                "value": float(row[metric]),
                "rank": len(hotspot_points) + 1
            })
        
        analysis["hotspots"] = hotspot_points
    
    summary = {
        "total_points": len(df),
        "bounding_box_area_sq_degrees": float(
            (analysis["bounding_box"]["max_lat"] - analysis["bounding_box"]["min_lat"]) *
            (analysis["bounding_box"]["max_lon"] - analysis["bounding_box"]["min_lon"])
        ),
        "has_metric": metric is not None,
        "grid_binning_applied": grid_data is not None
    }
    
    output = {
        "maps": map_points[:1000],  # Limit to 1000 points for performance
        "analysis": analysis,
        "summary": summary
    }
    
    if grid_data:
        output["grid_data"] = grid_data
    
    return {
        "status": "success",
        "output": output,
        "meta": {
            "tool": "geospatial_mapper",
            "version": "1.0.0"
        }
    }
