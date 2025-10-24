
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
      const payload = {
        tenant_id: "dev-tenant",
        mode: "sync",
        context: { task, data_type: dataType },
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
    <div style={{ padding: "2rem" }}>
      <h2>Data Analysis Engine Agent</h2>
      <div style={{ marginBottom: "1rem" }}>
        <label>Task:&nbsp;</label>
        <select value={task} onChange={e => setTask(e.target.value)}>
          <option value="anomaly_detection">Anomaly Detection</option>
          <option value="clustering">Clustering</option>
          <option value="feature_engineering">Feature Engineering</option>
        </select>
        &nbsp;&nbsp;
        <label>Dataset Type:&nbsp;</label>
        <select value={dataType} onChange={e => setDataType(e.target.value)}>
          <option value="tabular">Tabular</option>
          <option value="timeseries">Timeseries</option>
          <option value="geospatial">Geospatial</option>
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
      {result && result.result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Analysis Result</h3>
          <canvas id="anomalyChart" width="800" height="300" style={{ marginBottom: "2rem" }}></canvas>
          {result.result.summary && (
            <>
              <h4>Summary</h4>
              <pre>{JSON.stringify(result.result.summary, null, 2)}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
