from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import numpy as np

app = FastAPI(title="classifier_regressor", version="1.0.0")

class Schema(BaseModel):
    timestamp: Optional[str] = None
    entity_keys: Optional[List[str]] = []
    metric: Optional[str] = None

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    task: str = "classification"  # "classification" or "regression"
    target_column: str  # Column to predict
    feature_columns: Optional[List[str]] = None  # Columns to use as features
    test_size: float = 0.2
    random_state: int = 42

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

    # Validate target column
    if payload.params.target_column not in df.columns:
        raise HTTPException(400, f"Target column '{payload.params.target_column}' not found")
    
    # Select feature columns
    if payload.params.feature_columns:
        feature_cols = payload.params.feature_columns
    else:
        # Use all numeric columns except target
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col != payload.params.target_column]
    
    if not feature_cols:
        raise HTTPException(400, "No numeric features found")
    
    # Prepare features and target
    X = df[feature_cols].copy()
    y = df[payload.params.target_column].copy()
    
    # Handle missing values in features
    X = X.fillna(X.mean())
    
    # For classification, encode target labels
    label_encoder = None
    if payload.params.task == "classification":
        if y.dtype == 'object' or y.dtype.name == 'category':
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=payload.params.test_size,
        random_state=payload.params.random_state
    )
    
    # Train model
    if payload.params.task == "classification":
        model = RandomForestClassifier(n_estimators=100, random_state=payload.params.random_state)
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        # Decode labels if needed
        if label_encoder:
            y_test_labels = label_encoder.inverse_transform(y_test)
            y_pred_labels = label_encoder.inverse_transform(y_pred)
            unique_classes = label_encoder.classes_.tolist()
        else:
            y_test_labels = y_test
            y_pred_labels = y_pred
            unique_classes = np.unique(y).tolist()
        
        # Build predictions list
        predictions = []
        for i in range(len(X_test)):
            predictions.append({
                "index": int(X_test.index[i]),
                "actual": str(y_test_labels[i]) if label_encoder else float(y_test_labels[i]),
                "predicted": str(y_pred_labels[i]) if label_encoder else float(y_pred_labels[i]),
                "correct": bool(y_test[i] == y_pred[i])
            })
        
        # Feature importance
        feature_importance = {
            feature_cols[i]: float(model.feature_importances_[i])
            for i in range(len(feature_cols))
        }
        
        summary = {
            "task": "classification",
            "accuracy": float(accuracy),
            "n_samples": len(df),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "n_features": len(feature_cols),
            "classes": unique_classes,
            "feature_importance": feature_importance
        }
        
    elif payload.params.task == "regression":
        model = RandomForestRegressor(n_estimators=100, random_state=payload.params.random_state)
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Build predictions list
        predictions = []
        for i in range(len(X_test)):
            predictions.append({
                "index": int(X_test.index[i]),
                "actual": float(y_test.iloc[i]),
                "predicted": float(y_pred[i]),
                "error": float(abs(y_test.iloc[i] - y_pred[i]))
            })
        
        # Feature importance
        feature_importance = {
            feature_cols[i]: float(model.feature_importances_[i])
            for i in range(len(feature_cols))
        }
        
        summary = {
            "task": "regression",
            "mse": float(mse),
            "rmse": float(rmse),
            "r2_score": float(r2),
            "n_samples": len(df),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "n_features": len(feature_cols),
            "feature_importance": feature_importance
        }
    
    else:
        raise HTTPException(400, f"Unknown task: {payload.params.task}")
    
    return {
        "status": "success",
        "output": {
            "predictions": predictions[:100],  # Limit to first 100
            "summary": summary
        },
        "meta": {
            "tool": "classifier_regressor",
            "version": "1.0.0",
            "task": payload.params.task
        }
    }
