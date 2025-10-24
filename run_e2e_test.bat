@echo off
REM Build and start all services
docker-compose up --build -d

REM Wait for services to start (adjust time as needed)
timeout /t 20

REM Activate Python venv and run test script
call t_venv\Scripts\activate
python test\test_script_anomaly_detection.py

REM (Optional) Start frontend
REM cd frontend
REM start npm start

REM Deactivate venv
deactivate

REM Stop all containers after test
docker-compose down
