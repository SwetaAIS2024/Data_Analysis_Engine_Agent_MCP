from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from sklearn.ensemble import IsolationForest

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
    contamination: float = 0.05  # Proportion of anomalies expected

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
        raise HTTPException(400, "For skeleton, supply input.rows inline.")

    ts = payload.input.schema.timestamp
    metric = payload.input.schema.metric
    keys = payload.input.schema.entity_keys

    df[ts] = pd.to_datetime(df[ts])
    df = df.sort_values(keys + [ts]).set_index(ts)

    results = []
    for key_vals, g in df.groupby(keys):
        g = g.copy()
        # Isolation Forest expects 2D array
        X = g[[metric]].values
        clf = IsolationForest(contamination=payload.params.contamination, random_state=42)
        preds = clf.fit_predict(X)
        for idx, pred in enumerate(preds):
            if pred == -1:
                t = g.index[idx]
                results.append({
                    "entity": dict(zip(keys, key_vals if isinstance(key_vals, tuple) else (key_vals,))),
                    "timestamp": t.isoformat(),
                    "value": float(g.iloc[idx][metric]),
                    "score": float(clf.decision_function([X[idx]])[0])
                })

    summary = {
        "total_entities": int(df.groupby(keys).ngroups),
        "total_points": int(len(df)),
        "anomaly_count": int(len(results))
    }
    return {"status":"success","output":{"anomalies":results,"summary":summary},"meta":{"tool":"anomaly_zscore","version":"1.1.0"}}
