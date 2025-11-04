
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
  
  // Mode selection: 'prompt' for natural language, 'manual' for tool selection
  const [mode, setMode] = useState("prompt");
  
  // For prompt-based mode
  const [userPrompt, setUserPrompt] = useState("");
  
  // For manual tool selection mode
  const [selectedTools, setSelectedTools] = useState([]);
  const [dataType, setDataType] = useState("tabular");
  
  // Available tools
  const availableTools = [
    { id: "anomaly_detection", label: "Anomaly Detection", description: "Detect outliers and anomalies" },
    { id: "clustering", label: "Clustering", description: "Group similar data points" },
    { id: "classification", label: "Classification", description: "Predict categorical outcomes" },
    { id: "regression", label: "Regression", description: "Predict continuous values" },
    { id: "forecasting", label: "Time Series Forecasting", description: "Predict future values" },
    { id: "feature_engineering", label: "Feature Engineering", description: "Create derived features" },
    { id: "stats_comparison", label: "Statistical Comparison", description: "Compare groups statistically" },
    { id: "incident_detection", label: "Incident Detection", description: "Detect spikes, drops, anomalies" },
    { id: "geospatial_mapping", label: "Geospatial Mapping", description: "Analyze spatial patterns" }
  ];

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

  const handleToolToggle = (toolId) => {
    setSelectedTools(prev => 
      prev.includes(toolId) 
        ? prev.filter(id => id !== toolId)
        : [...prev, toolId]
    );
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setResult(null); // Clear previous results
    
    try {
      console.log("Loaded CSV data:", data);
      
      let payload;
      
      if (mode === "prompt") {
        // Natural language prompt mode - full V2 pipeline
        payload = {
          tenant_id: "dev-tenant",
          context: { 
            task: userPrompt,
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
      } else {
        // Manual tool selection mode
        if (selectedTools.length === 0) {
          alert("Please select at least one tool");
          setLoading(false);
          return;
        }
        
        // Build task description from selected tools
        const taskDescription = selectedTools.map(toolId => {
          const tool = availableTools.find(t => t.id === toolId);
          return tool ? tool.label : toolId;
        }).join(", ");
        
        payload = {
          tenant_id: "dev-tenant",
          context: { 
            task: `Perform ${taskDescription} on ${dataType} data`,
            data_type: dataType,
            force_tools: selectedTools // Force specific tools to be used
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
      }
      
      console.log("Sending V2 request:", payload);
      const res = await axios.post("http://localhost:8080/v2/analyze", payload);
      console.log("V2 response:", res.data);
      console.log("Response status:", res.data.status);
      console.log("Response result:", res.data.result);
      console.log("User feedback:", res.data.result?.user_feedback);
      
      setResult(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      console.error("Analysis error:", err);
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleClarificationSelection = async (selectedGoal) => {
    // User selected a clarification option, re-run with specific goal
    setLoading(true);
    
    try {
      const goalLabels = {
        "anomaly_detection": "Find anomalies and outliers in the data",
        "clustering": "Cluster and group similar data points",
        "timeseries_forecasting": "Forecast future values based on trends",
        "classification": "Classify data into categories",
        "stats_comparison": "Perform statistical comparison of groups"
      };
      
      const clarifiedPrompt = goalLabels[selectedGoal] || selectedGoal.replace("_", " ");
      
      const payload = {
        tenant_id: "dev-tenant",
        context: { 
          task: clarifiedPrompt,
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
      
      console.log("Sending clarified request:", payload);
      const res = await axios.post("http://localhost:8080/v2/analyze", payload);
      console.log("V2 response:", res.data);
      
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
    <div style={{ padding: "2rem", maxWidth: "1400px", margin: "0 auto" }}>
      <h2>🚀 Data Analysis Engine Agent </h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Complete AI-powered data analysis pipeline with context extraction, intelligent tool selection, and visualization
      </p>
      
      {/* Mode Selection */}
      <div style={{ 
        marginBottom: "2rem", 
        padding: "1.5rem", 
        backgroundColor: "#f5f5f5", 
        borderRadius: "8px",
        border: "2px solid #ddd"
      }}>
        <h3 style={{ marginTop: 0 }}>Analysis Mode</h3>
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
          <label style={{ 
            flex: 1, 
            padding: "1rem", 
            backgroundColor: mode === "prompt" ? "#2196f3" : "white",
            color: mode === "prompt" ? "white" : "black",
            border: "2px solid #2196f3",
            borderRadius: "6px",
            cursor: "pointer",
            textAlign: "center",
            fontWeight: "bold",
            transition: "all 0.3s"
          }}>
            <input 
              type="radio" 
              value="prompt" 
              checked={mode === "prompt"}
              onChange={(e) => setMode(e.target.value)}
              style={{ marginRight: "0.5rem" }}
            />
            🤖 Natural Language (AI-Powered)
            <div style={{ fontSize: "0.85em", fontWeight: "normal", marginTop: "0.25rem" }}>
              Describe your analysis goal in plain English
            </div>
          </label>
          
          <label style={{ 
            flex: 1, 
            padding: "1rem", 
            backgroundColor: mode === "manual" ? "#2196f3" : "white",
            color: mode === "manual" ? "white" : "black",
            border: "2px solid #2196f3",
            borderRadius: "6px",
            cursor: "pointer",
            textAlign: "center",
            fontWeight: "bold",
            transition: "all 0.3s"
          }}>
            <input 
              type="radio" 
              value="manual" 
              checked={mode === "manual"}
              onChange={(e) => setMode(e.target.value)}
              style={{ marginRight: "0.5rem" }}
            />
            🔧 Manual Tool Selection
            <div style={{ fontSize: "0.85em", fontWeight: "normal", marginTop: "0.25rem" }}>
              Choose specific analysis tools to apply
            </div>
          </label>
        </div>
        
        {/* Dataset Type - Common to both modes */}
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontWeight: "bold", marginRight: "0.5rem" }}>Dataset Type:</label>
          <select 
            value={dataType} 
            onChange={e => setDataType(e.target.value)}
            style={{ 
              padding: "0.5rem", 
              borderRadius: "4px", 
              border: "1px solid #ccc",
              fontSize: "1em"
            }}
          >
            <option value="tabular">Tabular</option>
            <option value="timeseries">Time Series</option>
            <option value="geospatial">Geospatial</option>
            <option value="categorical">Categorical</option>
          </select>
        </div>
        
        {/* Prompt Input for Natural Language Mode */}
        {mode === "prompt" && (
          <div>
            <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.5rem" }}>
              💬 Describe your analysis goal:
            </label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Example: Find anomalies in the speed data and cluster them by pattern. Also forecast the next hour's values."
              style={{
                width: "100%",
                minHeight: "100px",
                padding: "0.75rem",
                borderRadius: "4px",
                border: "1px solid #ccc",
                fontSize: "1em",
                fontFamily: "inherit",
                resize: "vertical"
              }}
            />
            <div style={{ fontSize: "0.85em", color: "#666", marginTop: "0.5rem" }}>
              💡 Tip: Be specific about what you want to analyze. The AI will automatically select and chain the appropriate tools.
            </div>
          </div>
        )}
        
        {/* Tool Selection for Manual Mode */}
        {mode === "manual" && (
          <div>
            <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.75rem" }}>
              🔧 Select Tools to Apply:
            </label>
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "0.75rem"
            }}>
              {availableTools.map(tool => (
                <label 
                  key={tool.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    padding: "0.75rem",
                    backgroundColor: selectedTools.includes(tool.id) ? "#e3f2fd" : "white",
                    border: `2px solid ${selectedTools.includes(tool.id) ? "#2196f3" : "#ddd"}`,
                    borderRadius: "6px",
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedTools.includes(tool.id)}
                    onChange={() => handleToolToggle(tool.id)}
                    style={{ marginRight: "0.5rem", marginTop: "0.2rem" }}
                  />
                  <div>
                    <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
                      {tool.label}
                    </div>
                    <div style={{ fontSize: "0.85em", color: "#666" }}>
                      {tool.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
            <div style={{ fontSize: "0.85em", color: "#666", marginTop: "0.75rem" }}>
              ✅ Selected: <strong>{selectedTools.length}</strong> tool(s)
            </div>
          </div>
        )}
      </div>
      
      {/* File Upload Section */}
      <div style={{ 
        marginBottom: "2rem", 
        padding: "1.5rem", 
        backgroundColor: "#fff", 
        borderRadius: "8px",
        border: "2px solid #ddd"
      }}>
        <h3 style={{ marginTop: 0 }}>📁 Data Upload</h3>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileChange}
            style={{ flex: 1 }}
          />
          <button 
            onClick={handleUpload}
            disabled={!csvFile}
            style={{
              padding: "0.75rem 1.5rem",
              backgroundColor: csvFile ? "#2196f3" : "#ccc",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: csvFile ? "pointer" : "not-allowed",
              fontWeight: "bold",
              fontSize: "1em"
            }}
          >
            📊 Load CSV
          </button>
          <button 
            onClick={handleAnalyze}
            disabled={loading || !data.length || (mode === "prompt" && !userPrompt.trim()) || (mode === "manual" && selectedTools.length === 0)}
            style={{
              padding: "0.75rem 1.5rem",
              backgroundColor: (loading || !data.length || (mode === "prompt" && !userPrompt.trim()) || (mode === "manual" && selectedTools.length === 0)) ? "#ccc" : "#4caf50",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: (loading || !data.length || (mode === "prompt" && !userPrompt.trim()) || (mode === "manual" && selectedTools.length === 0)) ? "not-allowed" : "pointer",
              fontWeight: "bold",
              fontSize: "1em"
            }}
          >
            {loading ? "⏳ Analyzing..." : "🚀 Run Analysis"}
          </button>
        </div>
        {data.length > 0 && (
          <div style={{ marginTop: "1rem", padding: "0.5rem", backgroundColor: "#e8f5e9", borderRadius: "4px" }}>
            ✅ <strong>{data.length}</strong> rows loaded
          </div>
        )}
      </div>
      
      {loading && (
        <div style={{
          padding: "2rem",
          textAlign: "center",
          backgroundColor: "#fff3e0",
          borderRadius: "8px",
          marginBottom: "2rem"
        }}>
          <h3>⏳ Processing your request...</h3>
          <p>The AI is analyzing your data and executing the pipeline. This may take a few moments.</p>
        </div>
      )}
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
          
          {/* User Feedback / Clarification Required - Show FIRST */}
          {result.result?.user_feedback && (
            <div style={{ 
              marginBottom: "2rem",
              padding: "1.5rem", 
              backgroundColor: result.result.user_feedback.type === "clarification" ? "#e3f2fd" : "#fff3e0", 
              borderRadius: "8px",
              border: `3px solid ${result.result.user_feedback.type === "clarification" ? "#2196f3" : "#ff9800"}`
            }}>
              <h4 style={{ marginTop: 0 }}>
                {result.result.user_feedback.type === "clarification" ? "🤔 Please Clarify Your Request" : "⚠️ User Feedback Required"}
              </h4>
              <p style={{ fontSize: "1.1em", marginBottom: "1.5rem" }}>
                {result.result.user_feedback.message}
              </p>
              
              {result.result.user_feedback.type === "clarification" && result.result.user_feedback.options && (
                <div>
                  <strong style={{ display: "block", marginBottom: "1rem" }}>Please select what you want to do:</strong>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
                    gap: "1rem"
                  }}>
                    {result.result.user_feedback.options.map((opt, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleClarificationSelection(opt.id)}
                        style={{
                          padding: "1rem",
                          backgroundColor: "white",
                          border: "2px solid #2196f3",
                          borderRadius: "6px",
                          cursor: "pointer",
                          textAlign: "left",
                          transition: "all 0.2s",
                          fontFamily: "inherit"
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = "#e3f2fd";
                          e.currentTarget.style.transform = "translateY(-2px)";
                          e.currentTarget.style.boxShadow = "0 4px 8px rgba(0,0,0,0.1)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = "white";
                          e.currentTarget.style.transform = "translateY(0)";
                          e.currentTarget.style.boxShadow = "none";
                        }}
                      >
                        <div style={{ fontWeight: "bold", fontSize: "1.1em", marginBottom: "0.5rem", color: "#2196f3" }}>
                          {opt.label}
                        </div>
                        <div style={{ fontSize: "0.9em", color: "#666" }}>
                          {opt.description}
                        </div>
                      </button>
                    ))}
                  </div>
                  <div style={{ 
                    marginTop: "1.5rem", 
                    padding: "1rem", 
                    backgroundColor: "#f5f5f5", 
                    borderRadius: "4px",
                    fontSize: "0.9em",
                    color: "#666"
                  }}>
                    💡 <strong>Tip:</strong> You can also use the "Manual Tool Selection" mode to test specific tools directly without writing prompts.
                  </div>
                </div>
              )}
              
              {result.result.user_feedback.type !== "clarification" && result.result.user_feedback.options && (
                <div>
                  <strong>Options:</strong>
                  <ul>
                    {result.result.user_feedback.options.map((opt, idx) => (
                      <li key={idx}>{opt.message || opt.label || opt.option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          
          {/* V2 Pipeline Metadata - Only show if NOT clarification required */}
          {result.tool_meta && result.status !== "clarification_required" && result.result?.status !== "clarification_required" && (
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
          
          {/* Pipeline Execution Logs - NEW SECTION */}
          {result.result?.pipeline_logs && result.result.pipeline_logs.length > 0 && (
            <div style={{ 
              marginBottom: "1rem", 
              padding: "1rem", 
              backgroundColor: "#f5f5f5", 
              borderRadius: "4px",
              maxHeight: "600px",
              overflowY: "auto"
            }}>
              <h4 style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "1.2em" }}>
                📊 Pipeline Execution Logs
                <span style={{ 
                  fontSize: "0.75em", 
                  fontWeight: "normal", 
                  color: "#666",
                  backgroundColor: "#e0e0e0",
                  padding: "3px 10px",
                  borderRadius: "12px"
                }}>
                  {result.result.pipeline_logs.length} events
                </span>
              </h4>
              
              <div style={{ fontFamily: "monospace", fontSize: "0.95em" }}>
                {result.result.pipeline_logs.map((log, idx) => {
                  const layerColors = {
                    "PIPELINE": "#9c27b0",
                    "CONTEXT_EXTRACTION": "#2196f3",
                    "CHAINING_MANAGER": "#ff9800",
                    "INVOCATION_LAYER": "#4caf50",
                    "OUTPUT_PREPARATION": "#00bcd4"
                  };
                  
                  const levelColors = {
                    "INFO": "#2196f3",
                    "SUCCESS": "#4caf50",
                    "WARNING": "#ff9800",
                    "ERROR": "#f44336"
                  };
                  
                  const levelBackgrounds = {
                    "INFO": "#e3f2fd",
                    "SUCCESS": "#e8f5e9",
                    "WARNING": "#fff3e0",
                    "ERROR": "#ffebee"
                  };
                  
                  return (
                    <div key={idx} style={{ 
                      marginBottom: "0.6rem", 
                      padding: "0.85rem",
                      backgroundColor: levelBackgrounds[log.level] || "#ffffff",
                      borderLeft: `4px solid ${levelColors[log.level] || "#666"}`,
                      borderRadius: "4px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.35rem"
                    }}>
                      {/* Log Header */}
                      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                        <span style={{ 
                          backgroundColor: layerColors[log.layer] || "#666",
                          color: "white",
                          padding: "3px 10px",
                          borderRadius: "4px",
                          fontSize: "0.85em",
                          fontWeight: "bold",
                          whiteSpace: "nowrap"
                        }}>
                          {log.layer.replace(/_/g, ' ')}
                        </span>
                        
                        <span style={{ 
                          color: levelColors[log.level] || "#666",
                          fontWeight: "bold",
                          fontSize: "0.85em"
                        }}>
                          {log.level}
                        </span>
                        
                        <span style={{ 
                          color: "#999",
                          fontSize: "0.8em",
                          marginLeft: "auto"
                        }}>
                          {new Date(log.timestamp * 1000).toLocaleTimeString()}
                        </span>
                      </div>
                      
                      {/* Log Message */}
                      <div style={{ 
                        fontSize: "1em",
                        color: "#222",
                        paddingLeft: "0.5rem",
                        fontWeight: "500",
                        lineHeight: "1.5"
                      }}>
                        {log.message}
                      </div>
                      
                      {/* Log Details (if any) */}
                      {log.details && Object.keys(log.details).length > 0 && (
                        <details style={{ paddingLeft: "0.5rem", marginTop: "0.3rem" }}>
                          <summary style={{ 
                            cursor: "pointer", 
                            fontSize: "0.9em",
                            color: "#666",
                            userSelect: "none",
                            fontWeight: "500"
                          }}>
                            📋 Details ({Object.keys(log.details).length} items)
                          </summary>
                          <div style={{ 
                            marginTop: "0.6rem",
                            padding: "0.7rem",
                            backgroundColor: "rgba(0,0,0,0.03)",
                            borderRadius: "4px",
                            fontSize: "0.95em"
                          }}>
                            {Object.entries(log.details).map(([key, value]) => (
                              <div key={key} style={{ marginBottom: "0.35rem", lineHeight: "1.5" }}>
                                <strong style={{ color: "#555" }}>{key}:</strong>{' '}
                                <span style={{ color: "#333" }}>
                                  {typeof value === 'object' 
                                    ? JSON.stringify(value, null, 2) 
                                    : String(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Tool Invocation Logs */}
          {result.result?.results && result.result.results.length > 0 && result.result?.status !== "clarification_required" && (
            <div style={{ marginBottom: "1rem", padding: "1rem", backgroundColor: "#e3f2fd", borderRadius: "4px" }}>
              <h4>🔧 Tool Invocation Log</h4>
              
              {/* Overall Status Message */}
              {result.result?.status_message && (
                <div style={{ 
                  marginBottom: "1rem", 
                  padding: "0.75rem", 
                  backgroundColor: result.result.status === "success" ? "#e8f5e9" : "#fff3e0",
                  borderRadius: "4px",
                  fontWeight: "bold",
                  fontSize: "1.05em"
                }}>
                  {result.result.status_message}
                </div>
              )}
              
              <div style={{ fontFamily: "monospace", fontSize: "0.9em" }}>
                {result.result.results.map((toolResult, idx) => (
                  <div key={idx} style={{ 
                    marginBottom: "0.75rem", 
                    padding: "1rem", 
                    backgroundColor: "white",
                    borderLeft: `4px solid ${toolResult.status === "success" ? "#4caf50" : toolResult.status === "error" ? "#f44336" : "#ff9800"}`,
                    borderRadius: "4px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                  }}>
                    {/* Tool Header */}
                    <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "1.3em", marginRight: "0.5rem" }}>
                        {toolResult.status === "success" ? "✅" : toolResult.status === "error" ? "❌" : "⚠️"}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: "bold", fontSize: "1.1em" }}>
                          {toolResult.tool_name || toolResult.tool_id}
                        </div>
                        {toolResult.tool_name && toolResult.tool_name !== toolResult.tool_id && (
                          <div style={{ fontSize: "0.85em", color: "#666" }}>
                            ({toolResult.tool_id})
                          </div>
                        )}
                      </div>
                      <span style={{ 
                        padding: "4px 12px", 
                        borderRadius: "12px",
                        fontSize: "0.85em",
                        fontWeight: "bold",
                        backgroundColor: toolResult.status === "success" ? "#e8f5e9" : toolResult.status === "error" ? "#ffebee" : "#fff3e0",
                        color: toolResult.status === "success" ? "#2e7d32" : toolResult.status === "error" ? "#c62828" : "#e65100"
                      }}>
                        {toolResult.status.toUpperCase()}
                      </span>
                    </div>
                    
                    {/* Status Message */}
                    {toolResult.status_message && (
                      <div style={{ 
                        marginBottom: "0.5rem", 
                        padding: "0.5rem", 
                        backgroundColor: "#f5f5f5", 
                        borderRadius: "3px",
                        fontSize: "0.95em"
                      }}>
                        {toolResult.status_message}
                      </div>
                    )}
                    
                    {/* Error Details */}
                    {toolResult.error && (
                      <div style={{ 
                        color: "#d32f2f", 
                        marginTop: "0.5rem", 
                        padding: "0.5rem",
                        backgroundColor: "#ffebee",
                        borderRadius: "3px",
                        fontSize: "0.9em"
                      }}>
                        <strong>❌ Error:</strong> {toolResult.error}
                      </div>
                    )}
                    
                    {/* Execution Summary (NEW - from backend) */}
                    {toolResult.execution_summary && Object.keys(toolResult.execution_summary).length > 0 && (
                      <div style={{ 
                        marginTop: "0.75rem", 
                        padding: "0.75rem", 
                        backgroundColor: "#e8f5e9", 
                        borderRadius: "4px" 
                      }}>
                        <div style={{ fontWeight: "bold", marginBottom: "0.5rem", color: "#2e7d32" }}>
                          📊 Execution Summary:
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.5rem" }}>
                          {Object.entries(toolResult.execution_summary).map(([key, value]) => (
                            <div key={key} style={{ fontSize: "0.9em" }}>
                              <span style={{ color: "#666" }}>{key.replace(/_/g, ' ')}:</span>{' '}
                              <strong>{Array.isArray(value) ? `[${value.slice(0, 3).join(', ')}${value.length > 3 ? '...' : ''}]` : String(value)}</strong>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Legacy Output Display (Fallback) */}
                    {toolResult.output && toolResult.status === "success" && !toolResult.execution_summary && (
                      <div style={{ marginTop: "0.5rem", color: "#555", fontSize: "0.9em" }}>
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
          
          {/* Visualizations - Only show if NOT clarification required */}
          {result.result?.status !== "clarification_required" && (
            <>
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
            </>
          )}
          
          {/* Clustering Visualization */}
          {result.result?.results && result.result.results.some(r => r.output?.clusters) && result.result?.status !== "clarification_required" && (
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
          {result.result?.results && result.result.results.length > 0 && result.result?.status !== "clarification_required" && (
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
          {result.result?.summary && result.result?.status !== "clarification_required" && (
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
