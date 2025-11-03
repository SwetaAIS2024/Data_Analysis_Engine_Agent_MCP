from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats

app = FastAPI(title="stats_comparator", version="1.0.0")

class Schema(BaseModel):
    timestamp: Optional[str] = None
    entity_keys: Optional[List[str]] = []
    metric: str

class Input(BaseModel):
    frame_uri: str
    rows: Optional[List[Dict[str, Any]]] = None
    schema: Schema

class Params(BaseModel):
    compare_by: Optional[str] = None  # Column to group by for comparison
    metrics: Optional[List[str]] = None  # Metrics to compute stats for
    statistical_tests: bool = True  # Whether to run statistical tests

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

    metric = payload.input.schema.metric
    
    if metric not in df.columns:
        raise HTTPException(400, f"Metric column '{metric}' not found")
    
    # Determine which columns to analyze
    if payload.params.metrics:
        analyze_cols = [col for col in payload.params.metrics if col in df.columns]
    else:
        analyze_cols = [metric]
    
    # Overall statistics
    overall_stats = {}
    for col in analyze_cols:
        values = df[col].dropna()
        
        overall_stats[col] = {
            "count": int(len(values)),
            "mean": float(values.mean()),
            "median": float(values.median()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
            "q25": float(values.quantile(0.25)),
            "q75": float(values.quantile(0.75)),
            "skewness": float(values.skew()),
            "kurtosis": float(values.kurtosis())
        }
    
    # Comparison by groups
    comparison = {}
    statistical_tests = {}
    
    if payload.params.compare_by and payload.params.compare_by in df.columns:
        compare_col = payload.params.compare_by
        groups = df.groupby(compare_col)
        
        group_stats = {}
        group_values = {}
        
        for group_name, group_df in groups:
            group_stats[str(group_name)] = {}
            group_values[str(group_name)] = {}
            
            for col in analyze_cols:
                values = group_df[col].dropna()
                group_values[str(group_name)][col] = values.tolist()
                
                group_stats[str(group_name)][col] = {
                    "count": int(len(values)),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max())
                }
        
        comparison["groups"] = group_stats
        comparison["group_count"] = len(group_stats)
        
        # Statistical tests (if enabled and we have exactly 2 groups)
        if payload.params.statistical_tests and len(group_stats) == 2:
            group_names = list(group_stats.keys())
            
            for col in analyze_cols:
                vals1 = np.array(group_values[group_names[0]][col])
                vals2 = np.array(group_values[group_names[1]][col])
                
                # T-test
                t_stat, t_pvalue = scipy_stats.ttest_ind(vals1, vals2)
                
                # Mann-Whitney U test (non-parametric)
                u_stat, u_pvalue = scipy_stats.mannwhitneyu(vals1, vals2, alternative='two-sided')
                
                statistical_tests[col] = {
                    "comparison": f"{group_names[0]} vs {group_names[1]}",
                    "t_test": {
                        "statistic": float(t_stat),
                        "p_value": float(t_pvalue),
                        "significant": bool(t_pvalue < 0.05)
                    },
                    "mann_whitney_u": {
                        "statistic": float(u_stat),
                        "p_value": float(u_pvalue),
                        "significant": bool(u_pvalue < 0.05)
                    },
                    "mean_difference": float(vals1.mean() - vals2.mean()),
                    "percent_difference": float((vals1.mean() - vals2.mean()) / vals2.mean() * 100) if vals2.mean() != 0 else None
                }
    
    # Correlation analysis (if multiple metrics)
    correlations = {}
    if len(analyze_cols) > 1:
        corr_matrix = df[analyze_cols].corr()
        
        for i, col1 in enumerate(analyze_cols):
            for col2 in analyze_cols[i+1:]:
                key = f"{col1}_vs_{col2}"
                correlations[key] = {
                    "correlation": float(corr_matrix.loc[col1, col2]),
                    "strength": "strong" if abs(corr_matrix.loc[col1, col2]) > 0.7 else 
                               "moderate" if abs(corr_matrix.loc[col1, col2]) > 0.4 else "weak"
                }
    
    summary = {
        "total_rows": len(df),
        "metrics_analyzed": analyze_cols,
        "groups_compared": comparison.get("group_count", 0),
        "statistical_tests_performed": len(statistical_tests),
        "correlations_computed": len(correlations)
    }
    
    output = {
        "stats": overall_stats,
        "comparison": comparison,
        "summary": summary
    }
    
    if statistical_tests:
        output["statistical_tests"] = statistical_tests
    
    if correlations:
        output["correlations"] = correlations
    
    return {
        "status": "success",
        "output": output,
        "meta": {
            "tool": "stats_comparator",
            "version": "1.0.0"
        }
    }
