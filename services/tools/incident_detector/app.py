from fastapi import FastAPI
app = FastAPI(title="incident_detector", version="1.0.0")

@app.post("/run")
def run():
    return {"status": "success", "output": {"incidents": [], "summary": {}}, "meta": {"tool": "incident_detector", "version": "1.0.0"}}
# TODO: Add gRPC server implementation