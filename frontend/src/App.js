
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

  // Simple chart rendering (anomalies)
  React.useEffect(() => {
    if (!result) return;
    
    // Handle V2 response format
    let anomalies = [];
    if (result.result && result.result.results) {
      // V2 format: result.results is array of tool results
      result.result.results.forEach(toolResult => {
        if (toolResult.status === "success" && toolResult.output) {
          if (toolResult.output.anomalies) {
            anomalies = anomalies.concat(toolResult.output.anomalies);
          } else if (toolResult.output.output && toolResult.output.output.anomalies) {
            anomalies = anomalies.concat(toolResult.output.output.anomalies);
          }
        }
      });
    }
    
    if (anomalies.length > 0) {
      const ctx = document.getElementById("anomalyChart");
      if (ctx) {
        // Destroy previous chart instance if exists
        if (window.anomalyChartInstance) {
          window.anomalyChartInstance.destroy();
        }
        // Prepare anomaly points
        const anomalyPoints = anomalies.map((a) => ({
          x: new Date(a.timestamp),
          y: a.value !== undefined ? a.value : a.score
        }));
        // Prepare normal points from all data minus anomalies
        let allPoints = [];
        if (data && data.length > 0) {
          // Build a Set of anomaly timestamps for fast lookup
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
      }
    }
  }, [result, data]);

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
              <p><strong>Status:</strong> {result.result?.status || result.status}</p>
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
                </>
              )}
            </div>
          )}
          
          {/* Chart */}
          <canvas id="anomalyChart" width="800" height="300" style={{ marginBottom: "2rem" }}></canvas>
          
          {/* Tool Results */}
          {result.result?.results && result.result.results.length > 0 && (
            <div style={{ marginBottom: "1rem" }}>
              <h4>Tool Results</h4>
              {result.result.results.map((toolResult, idx) => (
                <div key={idx} style={{ 
                  marginBottom: "1rem", 
                  padding: "1rem", 
                  backgroundColor: toolResult.status === "success" ? "#e8f5e9" : "#ffebee",
                  borderRadius: "4px"
                }}>
                  <p><strong>Tool:</strong> {toolResult.tool_id}</p>
                  <p><strong>Status:</strong> {toolResult.status}</p>
                  {toolResult.error && <p style={{ color: "red" }}><strong>Error:</strong> {toolResult.error}</p>}
                  {toolResult.output && (
                    <details>
                      <summary>Output</summary>
                      <pre style={{ fontSize: "0.85em" }}>{JSON.stringify(toolResult.output, null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
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
