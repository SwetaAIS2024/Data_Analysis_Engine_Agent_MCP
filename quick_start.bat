@echo off
REM Quick Start Script for Data Analysis Engine Agent
REM This script helps you get started quickly on Windows

echo ========================================
echo  Data Analysis Engine Agent - Quick Start
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker-compose is not installed!
    echo Please install Docker Desktop which includes docker-compose.
    echo.
    pause
    exit /b 1
)

echo [OK] docker-compose is available
echo.

REM Prompt user for what to do
echo What would you like to do?
echo.
echo 1. Start ALL services (Docker + Backend + Frontend)
echo 2. Start ONLY Docker services (tools microservices)
echo 3. Stop all services
echo 4. View logs
echo 5. Check service status
echo 6. Clean up and rebuild
echo 0. Exit
echo.

set /p choice="Enter your choice (0-6): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_docker
if "%choice%"=="3" goto stop_all
if "%choice%"=="4" goto view_logs
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto clean_rebuild
if "%choice%"=="0" goto end

echo Invalid choice!
pause
exit /b 1

:start_all
echo.
echo ========================================
echo  Starting ALL services...
echo ========================================
echo.

echo [1/3] Starting Docker services (tool microservices)...
docker-compose up -d --build
if errorlevel 1 (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)
echo [OK] Docker services started
echo.

echo [2/3] Starting Backend (Agent service)...
echo.
echo NOTE: Backend requires Python 3.11+
echo The backend will start in a new window.
echo Keep that window open while using the system.
echo.

cd services\agent
start "Backend - Agent Service" cmd /k "call ..\..\t_venv\Scripts\activate && uvicorn app.main:app --reload --port 8080"
cd ..\..

timeout /t 5 /nobreak >nul
echo [OK] Backend starting...
echo.

echo [3/3] Starting Frontend (React UI)...
echo.
echo NOTE: Frontend requires Node.js 16+
echo The frontend will start in a new window.
echo Keep that window open while using the system.
echo.

cd frontend
start "Frontend - React UI" cmd /k "npm start"
cd ..

echo.
echo ========================================
echo  Services Starting!
echo ========================================
echo.
echo Backend will be available at:  http://localhost:8080
echo Frontend will be available at: http://localhost:3001
echo API Docs will be available at: http://localhost:8080/docs
echo.
echo Please wait 30-60 seconds for all services to fully start.
echo.
echo Once started:
echo 1. Open http://localhost:3001 in your browser
echo 2. Upload a CSV file
echo 3. Enter your analysis prompt (e.g., "detect anomalies")
echo 4. Click Analyze and view results!
echo.
echo To stop: Run this script again and choose option 3
echo.
pause
goto end

:start_docker
echo.
echo Starting Docker services only...
docker-compose up -d --build
if errorlevel 1 (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)
echo.
echo [OK] Docker services started
echo.
echo Tool microservices are now running on ports 8001-8008
echo.
echo To start backend: cd services\agent && uvicorn app.main:app --reload --port 8080
echo To start frontend: cd frontend && npm start
echo.
pause
goto end

:stop_all
echo.
echo Stopping all services...
echo.
docker-compose down
echo [OK] Docker services stopped
echo.
echo Please manually close the Backend and Frontend windows if they are open.
echo.
pause
goto end

:view_logs
echo.
echo Which logs do you want to view?
echo.
echo 1. All Docker services
echo 2. Anomaly Detection service
echo 3. Clustering service
echo 4. Forecasting service
echo 5. Backend logs (from file)
echo 0. Back to main menu
echo.

set /p log_choice="Enter your choice (0-5): "

if "%log_choice%"=="1" (
    docker-compose logs --tail=50 -f
) else if "%log_choice%"=="2" (
    docker-compose logs --tail=50 -f anomaly-zscore
) else if "%log_choice%"=="3" (
    docker-compose logs --tail=50 -f clustering
) else if "%log_choice%"=="4" (
    docker-compose logs --tail=50 -f timeseries-forecaster
) else if "%log_choice%"=="5" (
    if exist services\agent\logs\agent_v2.log (
        type services\agent\logs\agent_v2.log | more
    ) else (
        echo Log file not found. Make sure backend has been started at least once.
    )
) else if "%log_choice%"=="0" (
    goto start
) else (
    echo Invalid choice!
)

pause
goto end

:check_status
echo.
echo Checking service status...
echo.
echo Docker services:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Backend: Check if http://localhost:8080/health responds
echo Frontend: Check if http://localhost:3001 is accessible
echo.
pause
goto end

:clean_rebuild
echo.
echo ========================================
echo  WARNING: This will clean and rebuild
echo ========================================
echo.
echo This will:
echo - Stop all Docker containers
echo - Remove all containers and images
echo - Rebuild everything from scratch
echo.
echo This may take several minutes.
echo.
set /p confirm="Are you sure? (y/n): "

if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    goto end
)

echo.
echo Cleaning up...
docker-compose down -v
docker-compose rm -f

echo.
echo Rebuilding...
docker-compose build --no-cache
docker-compose up -d

echo.
echo [OK] Clean rebuild complete
echo.
pause
goto end

:end
echo.
echo Thank you for using Data Analysis Engine Agent!
echo.
