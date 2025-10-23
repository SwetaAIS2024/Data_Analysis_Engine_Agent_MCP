run-agent:
	uvicorn services.agent.app.main:app --reload --port 8080
run-tool-anomaly:
	uvicorn services.tools.anomaly_zscore.app:app --reload --port 9091
compose:
	docker compose up --build
test:
	pytest -q
