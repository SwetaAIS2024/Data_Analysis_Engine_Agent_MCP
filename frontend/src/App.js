
import React, { useState } from "react";
import Papa from "papaparse";
import axios from "axios";
import { Chart, registerables } from "chart.js";
import 'chartjs-adapter-date-fns';
Chart.register(...registerables);

function App() {
  const [csvFile, setCsvFile] = useState(null);
  const [data, setData] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [task, setTask] = useState("anomaly_detection");
  const [dataType, setDataType] = useState("tabular");

  const handleFileChange = (e) => {
    setCsvFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (!csvFile) return;
    Papa.parse(csvFile, {
      header: true,
      complete: (results) => {
        // Filter out empty rows (e.g., missing timestamp or key fields)
        const filtered = results.data.filter(row => row.timestamp && row.timestamp.trim() !== "");
        setData(filtered);
      },
    });
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      // Debug: print loaded data
      console.log("Loaded CSV data:", data);
      
      // Build task description for V2 context extraction
      const taskDescription = `${task.replace('_', ' ')} on ${dataType} data`;
      
      const payload = {
        tenant_id: "dev-tenant",
        context: { 
          task: taskDescription,
          data_type: dataType 
        },
        data_pointer: {
          uri: "sample://in-memory",
          format: "inline",
          rows: data,
        },
        params: {
          metric: "speed_kmh",
          key_fields: ["segment_id", "sensor_id"],
          timestamp_field: "timestamp",
          threshold: 2.0,
          rolling_window: "2min",
          min_points: 2,
        },
      };
      
      console.log("Sending V2 request:", payload);
      const res = await axios.post("http://localhost:8080/v2/analyze", payload);
      console.log("V2 response:", res.data);
      
      // Handle V2 response format
      if (res.data.result && res.data.result.user_feedback) {
        // User feedback required
        alert("User feedback required: " + JSON.stringify(res.data.result.user_feedback, null, 2));
      }
      
      setResult(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      console.error("Analysis error:", err);
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
  };

  // Visualization function for Anomaly Detection
  const renderAnomalyChart = React.useCallback((toolResult) => {
    const anomalies = toolResult.output.anomalies || [];
    if (anomalies.length === 0) return;
    
    const ctx = document.getElementById("anomalyChart");
    if (!ctx) return;
    
    // Prepare anomaly points
    const anomalyPoints = anomalies.map((a) => ({
      x: new Date(a.timestamp),
      y: a.value !== undefined ? a.value : a.score
    }));
    
    // Prepare normal points from all data minus anomalies
    let allPoints = [];
    if (data && data.length > 0) {
      const anomalyTimestamps = new Set(anomalies.map(a => a.timestamp));
      allPoints = data
        .filter(row => !anomalyTimestamps.has(row.timestamp))
        .map(row => ({ x: new Date(row.timestamp), y: Number(row.speed_kmh) }));
    }
    
    window.anomalyChartInstance = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Normal Value",
            data: allPoints,
            backgroundColor: "blue",
            pointRadius: 2
          },
          {
            label: "Anomaly Value",
            data: anomalyPoints,
            backgroundColor: "red",
            pointRadius: 4
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Anomaly Detection Results"
          }
        },
        scales: {
          x: {
            type: "time",
            time: {
              parser: "yyyy-MM-dd'T'HH:mm:ss",
              tooltipFormat: "Pp",
              unit: "minute"
            },
            title: {
              display: true,
              text: "Timestamp"
            }
          },
          y: {
            title: {
              display: true,
              text: "Value"
            }
          }
        }
      }
    });
  }, [data]);

  // Visualization function for Clustering
  const renderClusterChart = React.useCallback((toolResult) => {
    const clusteredData = toolResult.output.clustered_data;
    const clusters = toolResult.output.clusters;
    const summary = toolResult.output.summary;
    
    if (!clusteredData || clusteredData.length === 0) return;
    
    const ctx = document.getElementById("clusterChart");
    if (!ctx) return;
    
    const features = summary.features_used || [];
    if (features.length < 2) return;
    
    const feature1 = features[0];
    const feature2 = features[1];
    
    // Define colors for clusters
    const colors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
      '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
    ];
    
    // Group data by cluster
    const datasets = {};
    clusteredData.forEach(point => {
      const clusterId = point.cluster;
      const clusterName = clusterId === -1 ? 'Noise' : `Cluster ${clusterId}`;
      
      if (!datasets[clusterId]) {
        datasets[clusterId] = {
          label: clusterName,
          data: [],
          backgroundColor: colors[clusterId % colors.length] || '#999',
          pointRadius: clusterId === -1 ? 3 : 5,
          pointStyle: clusterId === -1 ? 'cross' : 'circle'
        };
      }
      
      datasets[clusterId].data.push({
        x: point[feature1],
        y: point[feature2]
      });
    });
    
    window.clusterChartInstance = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: Object.values(datasets)
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: `Clustering Results: ${feature1} vs ${feature2}`
          },
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: feature1
            }
          },
          y: {
            title: {
              display: true,
              text: feature2
            }
          }
        }
      }
    });
  }, []);

  // Visualization function for Forecasting
  const renderForecastChart = React.useCallback((toolResult) => {
    const forecast = toolResult.output.forecast?.[0]; // First entity
    if (!forecast || !forecast.forecast_points || !data || data.length === 0) return;
    
    const ctx = document.getElementById("forecastChart");
    if (!ctx) return;
    
    // Historical data
    const historicalData = data.map(row => ({
      x: new Date(row.timestamp),
      y: Number(row.speed_kmh)
    }));
    
    // Forecast data
    const forecastData = forecast.forecast_points.map(point => ({
      x: new Date(point.timestamp),
      y: point.forecast_value
    }));
    
    // Confidence bounds
    const upperBound = forecast.forecast_points.map(point => ({
      x: new Date(point.timestamp),
      y: point.upper_bound
    }));
    
    const lowerBound = forecast.forecast_points.map(point => ({
      x: new Date(point.timestamp),
      y: point.lower_bound
    }));
    
    window.forecastChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Historical",
            data: historicalData,
            borderColor: "#2196f3",
            backgroundColor: "rgba(33, 150, 243, 0.1)",
            borderWidth: 2,
            pointRadius: 1
          },
          {
            label: "Forecast",
            data: forecastData,
            borderColor: "#ff9800",
            backgroundColor: "rgba(255, 152, 0, 0.1)",
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 3
          },
          {
            label: "Upper Bound",
            data: upperBound,
            borderColor: "rgba(255, 152, 0, 0.3)",
            backgroundColor: "transparent",
            borderWidth: 1,
            borderDash: [2, 2],
            pointRadius: 0
          },
          {
            label: "Lower Bound",
            data: lowerBound,
            borderColor: "rgba(255, 152, 0, 0.3)",
            backgroundColor: "transparent",
            borderWidth: 1,
            borderDash: [2, 2],
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Time Series Forecast"
          }
        },
        scales: {
          x: {
            type: "time",
            time: {
              parser: "yyyy-MM-dd'T'HH:mm:ss",
              tooltipFormat: "Pp"
            },
            title: {
              display: true,
              text: "Time"
            }
          },
          y: {
            title: {
              display: true,
              text: "Value"
            }
          }
        }
      }
    });
  }, [data]);

  // Render visualizations based on tool type
  React.useEffect(() => {
    if (!result) return;
    
    // Clear all previous charts first
    if (window.anomalyChartInstance) {
      window.anomalyChartInstance.destroy();
      window.anomalyChartInstance = null;
    }
    if (window.clusterChartInstance) {
      window.clusterChartInstance.destroy();
      window.clusterChartInstance = null;
    }
    if (window.forecastChartInstance) {
      window.forecastChartInstance.destroy();
      window.forecastChartInstance = null;
    }
    
    // Check which tools were used and render appropriate visualizations
    if (result.result && result.result.results) {
      result.result.results.forEach(toolResult => {
        if (toolResult.status === "success" && toolResult.output) {
          // Route to appropriate visualization function
          if (toolResult.output.anomalies) {
            renderAnomalyChart(toolResult);
          } else if (toolResult.output.clusters) {
            renderClusterChart(toolResult);
          } else if (toolResult.output.forecast) {
            renderForecastChart(toolResult);
          }
        }
      });
    }
  }, [result, data, renderAnomalyChart, renderClusterChart, renderForecastChart]);

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Data Analysis Engine Agent - V2</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Simplified pipeline with context extraction, chaining manager, and tool invocation
      </p>
      <div style={{ marginBottom: "1rem" }}>
        <label>Task:&nbsp;</label>
        <select value={task} onChange={e => setTask(e.target.value)}>
          <option value="anomaly_detection">Anomaly Detection</option>
          <option value="clustering">Clustering</option>
          <option value="feature_engineering">Feature Engineering</option>
          <option value="classification">Classification</option>
          <option value="forecasting">Forecasting</option>
          <option value="stats_comparison">Stats Comparison</option>
        </select>
        &nbsp;&nbsp;
        <label>Dataset Type:&nbsp;</label>
        <select value={dataType} onChange={e => setDataType(e.target.value)}>
          <option value="tabular">Tabular</option>
          <option value="timeseries">Timeseries</option>
          <option value="geospatial">Geospatial</option>
          <option value="categorical">Categorical</option>
        </select>
      </div>
      <input type="file" accept=".csv" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "1rem" }}>Preview CSV</button>
      <button onClick={handleAnalyze} style={{ marginLeft: "1rem" }} disabled={loading || !data.length}>Run Analysis</button>
      {loading && <div>Loading...</div>}
      {data.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>CSV Preview</h3>
          <table border="1" cellPadding="4" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {Object.keys(data[0]).map((col, idx) => (
                  <th key={idx}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 10).map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((val, i) => (
                    <td key={i}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Analysis Result</h3>
          
          {/* V2 Pipeline Metadata */}
          {result.tool_meta && (
            <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#f0f0f0", borderRadius: "4px" }}>
              <h4>Pipeline Info</h4>
              <p><strong>Status:</strong> <span style={{ 
                color: result.result?.status === 'success' ? 'green' : result.result?.status === 'failed' ? 'red' : 'orange',
                fontWeight: 'bold'
              }}>{result.result?.status || result.status}</span></p>
              <p><strong>Version:</strong> {result.tool_meta.pipeline_version}</p>
              <p><strong>Duration:</strong> {result.tool_meta.duration_seconds?.toFixed(2)}s</p>
              {result.tool_meta.context_extraction && (
                <>
                  <p><strong>Goal:</strong> {result.tool_meta.context_extraction.goal}</p>
                  <p><strong>Data Type:</strong> {result.tool_meta.context_extraction.data_type}</p>
                </>
              )}
              {result.tool_meta.execution_plan && (
                <>
                  <p><strong>Strategy:</strong> {result.tool_meta.execution_plan.strategy}</p>
                  <p><strong>Tools Used:</strong> {result.tool_meta.execution_plan.tools?.join(', ')}</p>
                  {result.tool_meta.execution_plan.reasoning && (
                    <p><strong>Reasoning:</strong> {result.tool_meta.execution_plan.reasoning}</p>
                  )}
                </>
              )}
            </div>
          )}
          
          {/* Tool Invocation Logs */}
          {result.result?.results && result.result.results.length > 0 && (
            <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#e3f2fd", borderRadius: "4px" }}>
              <h4>🔧 Tool Invocation Log</h4>
              <div style={{ fontFamily: "monospace", fontSize: "0.9em" }}>
                {result.result.results.map((toolResult, idx) => (
                  <div key={idx} style={{ 
                    marginBottom: "0.5rem", 
                    padding: "0.75rem", 
                    backgroundColor: "white",
                    borderLeft: `4px solid ${toolResult.status === "success" ? "#4caf50" : toolResult.status === "error" ? "#f44336" : "#ff9800"}`,
                    borderRadius: "2px"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", marginBottom: "0.25rem" }}>
                      <span style={{ 
                        fontSize: "1.2em", 
                        marginRight: "0.5rem"
                      }}>
                        {toolResult.status === "success" ? "✅" : toolResult.status === "error" ? "❌" : "⚠️"}
                      </span>
                      <strong style={{ flex: 1 }}>{toolResult.tool_id}</strong>
                      <span style={{ 
                        padding: "2px 8px", 
                        borderRadius: "3px",
                        fontSize: "0.85em",
                        backgroundColor: toolResult.status === "success" ? "#e8f5e9" : toolResult.status === "error" ? "#ffebee" : "#fff3e0",
                        color: toolResult.status === "success" ? "#2e7d32" : toolResult.status === "error" ? "#c62828" : "#e65100"
                      }}>
                        {toolResult.status}
                      </span>
                    </div>
                    {toolResult.error && (
                      <div style={{ color: "#d32f2f", marginTop: "0.25rem", fontSize: "0.9em" }}>
                        <strong>Error:</strong> {toolResult.error}
                      </div>
                    )}
                    {toolResult.output && toolResult.status === "success" && (
                      <div style={{ marginTop: "0.5rem", color: "#555" }}>
                        {/* Anomaly Detection */}
                        {toolResult.output.anomalies && (
                          <div>📊 <strong>{toolResult.output.anomalies.length}</strong> anomalies detected</div>
                        )}
                        
                        {/* Clustering */}
                        {toolResult.output.clusters && (
                          <div>🔵 <strong>{toolResult.output.clusters.length}</strong> clusters found</div>
                        )}
                        
                        {/* Classification/Regression */}
                        {toolResult.output.predictions && (
                          <div>🎯 <strong>{toolResult.output.predictions.length}</strong> predictions made</div>
                        )}
                        
                        {/* Forecasting */}
                        {toolResult.output.forecast && (
                          <div>📈 <strong>{toolResult.output.forecast.length}</strong> entities forecasted</div>
                        )}
                        
                        {/* Incidents */}
                        {toolResult.output.incidents && (
                          <div>⚠️ <strong>{toolResult.output.incidents.length}</strong> incidents detected</div>
                        )}
                        
                        {/* Feature Engineering */}
                        {toolResult.output.new_features && (
                          <div>🔧 <strong>{toolResult.output.new_features.length}</strong> new features created</div>
                        )}
                        
                        {/* Stats/Maps */}
                        {toolResult.output.maps && (
                          <div>🗺️ <strong>{toolResult.output.maps.length}</strong> map points</div>
                        )}
                        
                        {/* Summary */}
                        {toolResult.output.summary && (
                          <div style={{ fontSize: "0.85em", marginTop: "0.25rem" }}>
                            {Object.entries(toolResult.output.summary).map(([key, value]) => (
                              <span key={key} style={{ marginRight: "1rem" }}>
                                {key}: <strong>{typeof value === 'object' ? JSON.stringify(value) : value}</strong>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Chart */}
          <canvas id="anomalyChart" width="800" height="300" style={{ marginBottom: "2rem" }}></canvas>
          
          {/* Cluster Chart */}
          {result.result?.results && result.result.results.some(r => r.output?.clusters) && (
            <canvas id="clusterChart" width="800" height="400" style={{ marginBottom: "2rem" }}></canvas>
          )}
          
          {/* Forecast Chart */}
          {result.result?.results && result.result.results.some(r => r.output?.forecast) && (
            <canvas id="forecastChart" width="800" height="400" style={{ marginBottom: "2rem" }}></canvas>
          )}
          
          {/* Clustering Visualization */}
          {result.result?.results && result.result.results.some(r => r.output?.clusters) && (
            <div style={{ marginBottom: "2rem" }}>
              <h4>🔵 Clustering Results</h4>
              {result.result.results.filter(r => r.output?.clusters).map((toolResult, idx) => (
                <div key={idx}>
                  {toolResult.output.clusters.map((cluster, cidx) => (
                    <div key={cidx} style={{
                      padding: "0.75rem",
                      marginBottom: "0.5rem",
                      backgroundColor: "#f5f5f5",
                      borderLeft: "4px solid #2196f3",
                      borderRadius: "4px"
                    }}>
                      <strong>{cluster.cluster_name}</strong> - {cluster.size} points ({cluster.percentage.toFixed(1)}%)
                      {cluster.center && (
                        <div style={{ fontSize: "0.85em", marginTop: "0.25rem", color: "#666" }}>
                          Center: {Object.entries(cluster.center).map(([k, v]) => `${k}: ${v.toFixed(2)}`).join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
          
          {/* Detailed Tool Results (Collapsible) */}
          {result.result?.results && result.result.results.length > 0 && (
            <details style={{ marginBottom: "1rem" }}>
              <summary style={{ 
                cursor: "pointer", 
                padding: "0.5rem", 
                backgroundColor: "#f5f5f5", 
                borderRadius: "4px",
                fontWeight: "bold"
              }}>
                📋 Detailed Tool Outputs ({result.result.results.length} tools)
              </summary>
              <div style={{ marginTop: "0.5rem" }}>
                {result.result.results.map((toolResult, idx) => (
                  <div key={idx} style={{ 
                    marginBottom: "1rem", 
                    padding: "1rem", 
                    backgroundColor: "#fafafa",
                    border: "1px solid #ddd",
                    borderRadius: "4px"
                  }}>
                    <h5>{toolResult.tool_id}</h5>
                    {toolResult.output && (
                      <pre style={{ 
                        fontSize: "0.85em", 
                        backgroundColor: "white", 
                        padding: "0.75rem",
                        borderRadius: "3px",
                        overflow: "auto",
                        maxHeight: "400px"
                      }}>{JSON.stringify(toolResult.output, null, 2)}</pre>
                    )}
                  </div>
                ))}
              </div>
            </details>
          )}
          
          {/* Summary */}
          {result.result?.summary && (
            <>
              <h4>Summary</h4>
              <pre>{JSON.stringify(result.result.summary, null, 2)}</pre>
            </>
          )}
          
          {/* User Feedback Required */}
          {result.result?.user_feedback && (
            <div style={{ 
              marginTop: "1rem", 
              padding: "1rem", 
              backgroundColor: "#fff3e0", 
              borderRadius: "4px",
              border: "2px solid #ff9800"
            }}>
              <h4>⚠️ User Feedback Required</h4>
              <p>{result.result.user_feedback.message}</p>
              {result.result.user_feedback.options && (
                <div>
                  <strong>Options:</strong>
                  <ul>
                    {result.result.user_feedback.options.map((opt, idx) => (
                      <li key={idx}>{opt.message || opt.option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
