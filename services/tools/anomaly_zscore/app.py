from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd

app = FastAPI(title="anomaly_zscore", version="1.1.0")

class Schema(BaseModel):
    timestamp: str
    entity_keys: List[str]
    metric: str

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str,Any]]] = None
    schema: Schema

class Params(BaseModel):
    rolling_window: str = "15min"
    zscore_threshold: float = 3.0
    min_points: int = 30

class Payload(BaseModel):
    input: Input
    params: Params
    context: Dict[str,Any]

@app.post("/run")
def run(payload: Payload, request: Request):
    # Load data
    if payload.input.rows:
        df = pd.DataFrame(payload.input.rows)
    else:
        # In a real system, load from storage via payload.input.frame_uri
        raise HTTPException(400, "For skeleton, supply input.rows inline.")

    ts = payload.input.schema.timestamp
    metric = payload.input.schema.metric
    keys = payload.input.schema.entity_keys

    df[ts] = pd.to_datetime(df[ts])
    df = df.sort_values(keys + [ts]).set_index(ts)

    results = []
    for key_vals, g in df.groupby(keys):
        g = g.copy()
        roll = g[metric].rolling(payload.params.rolling_window, min_periods=payload.params.min_points)
        mu = roll.mean()
        sd = roll.std(ddof=0)
        z = (g[metric] - mu) / sd
        anomalies = z.abs() >= payload.params.zscore_threshold
        for t in g[anomalies].index:
            results.append({
                "entity": dict(zip(keys, key_vals if isinstance(key_vals, tuple) else (key_vals,))),
                "timestamp": t.isoformat(),
                "value": float(g.loc[t, metric]),
                "zscore": float(z.loc[t]) if pd.notnull(z.loc[t]) else None,
                "rolling_mean": float(mu.loc[t]) if pd.notnull(mu.loc[t]) else None,
                "rolling_std": float(sd.loc[t]) if pd.notnull(sd.loc[t]) else None
            })

    summary = {
        "total_entities": int(df.groupby(keys).ngroups),
        "total_points": int(len(df)),
        "anomaly_count": int(len(results))
    }
    return {"status":"success","output":{"anomalies":results,"summary":summary},"meta":{"tool":"anomaly_zscore","version":"1.1.0"}}
