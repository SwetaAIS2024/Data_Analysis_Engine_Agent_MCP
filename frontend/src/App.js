import React, { useState } from "react";
import Papa from "papaparse";
import axios from "axios";
import { Chart, registerables } from "chart.js";
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
    if (result && result.result && result.result.anomalies && result.result.anomalies.length > 0) {
      const ctx = document.getElementById("anomalyChart");
      if (ctx) {
        const timestamps = result.result.anomalies.map((a) => a.timestamp);
        const values = result.result.anomalies.map((a) => a.value);
        new Chart(ctx, {
          type: "scatter",
          data: {
            labels: timestamps,
            datasets: [
              {
                label: "Anomaly Value",
                data: result.result.anomalies.map((a) => ({ x: a.timestamp, y: a.value })),
                backgroundColor: "red",
              },
            ],
          },
        });
      }
    }
  }, [result]);

  return (
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h2>MCP Agent Anomaly Detection Demo</h2>
      <input type="file" accept=".csv" onChange={handleFileChange} />
      <button onClick={handleUpload}>Load CSV</button>
      <button onClick={handleAnalyze} disabled={!data.length || loading}>
        {loading ? "Analyzing..." : "Run Anomaly Detection"}
      </button>
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
