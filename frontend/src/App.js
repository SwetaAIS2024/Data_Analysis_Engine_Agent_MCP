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
      const payload = {
        tenant_id: "dev-tenant",
        mode: "sync",
        context: { task: "anomaly_detection", data_type: "tabular" },
        data_pointer: {
          uri: "sample://in-memory",
          format: "inline",
          rows: data,
        },
        params: {
          metric: "speed_kmh",
          key_fields: ["segment_id", "sensor_id"],
          timestamp_field: "timestamp",
          zscore_threshold: 2.0,
          rolling_window: "2min",
          min_points: 2,
        },
      };
      const res = await axios.post("http://localhost:8080/v1/analyze", payload);
      setResult(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      alert("Error: " + err.message);
    }
  };

  // Simple chart rendering (anomalies)
  React.useEffect(() => {
    if (result && result.result && result.result.anomalies) {
      const ctx = document.getElementById("anomalyChart");
      if (ctx) {
        // Destroy previous chart instance if exists
        if (window.anomalyChartInstance) {
          window.anomalyChartInstance.destroy();
        }
        // Prepare anomaly points
        const anomalyPoints = result.result.anomalies.map((a) => ({
          x: new Date(a.timestamp),
          y: a.value !== undefined ? a.value : a.score
        }));
        // Prepare normal points from all data minus anomalies
        let allPoints = [];
        if (data && data.length > 0) {
          // Build a Set of anomaly timestamps for fast lookup
          const anomalyTimestamps = new Set(result.result.anomalies.map(a => a.timestamp));
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
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h2>MCP Agent Anomaly Detection Demo</h2>
      <input type="file" accept=".csv" onChange={handleFileChange} />
      <button onClick={handleUpload}>Load CSV</button>
      <button onClick={handleAnalyze} disabled={!data.length || loading}>
        {loading ? "Analyzing..." : "Run Anomaly Detection"}
      </button>
      {/* Preview top 10 rows of uploaded CSV */}
      {data && data.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>CSV Preview (Top 10 Rows)</h3>
          <table border="1" cellPadding="4">
            <thead>
              <tr>
                {Object.keys(data[0]).map((col, idx) => (
                  <th key={idx}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 10).map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => (
                    <td key={j}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {result && (
        <div style={{ marginTop: 32 }}>
          <h3>Detected Anomalies</h3>
          <canvas id="anomalyChart" width={600} height={200}></canvas>
          <table border="1" cellPadding="4" style={{ marginTop: 16 }}>
            <thead>
              <tr>
                <th>Entity</th>
                <th>Timestamp</th>
                <th>Value</th>
                <th>Z-Score</th>
              </tr>
            </thead>
            <tbody>
              {result.result.anomalies.map((a, i) => (
                <tr key={i}>
                  <td>{JSON.stringify(a.entity)}</td>
                  <td>{a.timestamp}</td>
                  <td>{a.value}</td>
                  <td>{a.zscore}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h4>Summary</h4>
          <pre>{JSON.stringify(result.result.summary, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
