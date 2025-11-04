#!/bin/bash

# Quick Start Script for Data Analysis Engine Agent
# This script helps you get started quickly on Linux/Mac

echo "========================================"
echo " Data Analysis Engine Agent - Quick Start"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker is not running!${NC}"
    echo "Please start Docker and try again."
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] Docker is running${NC}"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[ERROR] docker-compose is not installed!${NC}"
    echo "Please install docker-compose."
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] docker-compose is available${NC}"
echo ""

# Function to start all services
start_all() {
    echo ""
    echo "========================================"
    echo " Starting ALL services..."
    echo "========================================"
    echo ""

    echo "[1/3] Starting Docker services (tool microservices)..."
    docker-compose up -d --build
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to start Docker services${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Docker services started${NC}"
    echo ""

    echo "[2/3] Starting Backend (Agent service)..."
    echo ""
    echo "NOTE: Backend requires Python 3.11+"
    echo "Starting backend in background..."
    echo ""

    cd services/agent
    
    # Check if virtual environment exists
    if [ -d "../../t_venv" ]; then
        source ../../t_venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${YELLOW}[WARNING] No virtual environment found. Using system Python.${NC}"
    fi
    
    nohup uvicorn app.main:app --reload --port 8080 > ../../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../../logs/backend.pid
    
    cd ../..
    
    sleep 3
    echo -e "${GREEN}[OK] Backend started (PID: $BACKEND_PID)${NC}"
    echo ""

    echo "[3/3] Starting Frontend (React UI)..."
    echo ""
    echo "NOTE: Frontend requires Node.js 16+"
    echo "Starting frontend in background..."
    echo ""

    cd frontend
    nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..

    sleep 3
    echo -e "${GREEN}[OK] Frontend started (PID: $FRONTEND_PID)${NC}"
    echo ""

    echo "========================================"
    echo " Services Started!"
    echo "========================================"
    echo ""
    echo "Backend:  http://localhost:8080"
    echo "Frontend: http://localhost:3001"
    echo "API Docs: http://localhost:8080/docs"
    echo ""
    echo "Please wait 30-60 seconds for all services to fully start."
    echo ""
    echo "Logs:"
    echo "  Backend:  logs/backend.log"
    echo "  Frontend: logs/frontend.log"
    echo ""
    echo "To stop: Run this script again and choose option 3"
    echo ""
}

# Function to start only Docker services
start_docker() {
    echo ""
    echo "Starting Docker services only..."
    docker-compose up -d --build
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to start Docker services${NC}"
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[OK] Docker services started${NC}"
    echo ""
    echo "Tool microservices are now running on ports 8001-8008"
    echo ""
    echo "To start backend: cd services/agent && uvicorn app.main:app --reload --port 8080"
    echo "To start frontend: cd frontend && npm start"
    echo ""
}

# Function to stop all services
stop_all() {
    echo ""
    echo "Stopping all services..."
    echo ""
    
    # Stop Docker services
    docker-compose down
    echo -e "${GREEN}[OK] Docker services stopped${NC}"
    
    # Stop backend
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm logs/backend.pid
        echo -e "${GREEN}[OK] Backend stopped${NC}"
    fi
    
    # Stop frontend
    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm logs/frontend.pid
        echo -e "${GREEN}[OK] Frontend stopped${NC}"
    fi
    
    echo ""
}

# Function to view logs
view_logs() {
    echo ""
    echo "Which logs do you want to view?"
    echo ""
    echo "1. All Docker services"
    echo "2. Anomaly Detection service"
    echo "3. Clustering service"
    echo "4. Forecasting service"
    echo "5. Backend logs"
    echo "6. Frontend logs"
    echo "0. Back to main menu"
    echo ""
    
    read -p "Enter your choice (0-6): " log_choice
    
    case $log_choice in
        1)
            docker-compose logs --tail=50 -f
            ;;
        2)
            docker-compose logs --tail=50 -f anomaly-zscore
            ;;
        3)
            docker-compose logs --tail=50 -f clustering
            ;;
        4)
            docker-compose logs --tail=50 -f timeseries-forecaster
            ;;
        5)
            if [ -f "logs/backend.log" ]; then
                tail -f logs/backend.log
            else
                echo "Log file not found. Make sure backend has been started at least once."
            fi
            ;;
        6)
            if [ -f "logs/frontend.log" ]; then
                tail -f logs/frontend.log
            else
                echo "Log file not found. Make sure frontend has been started at least once."
            fi
            ;;
        0)
            return
            ;;
        *)
            echo "Invalid choice!"
            ;;
    esac
}

# Function to check status
check_status() {
    echo ""
    echo "Checking service status..."
    echo ""
    echo "Docker services:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    echo "Backend:"
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            echo -e "${GREEN}Running (PID: $BACKEND_PID)${NC}"
        else
            echo -e "${RED}Not running${NC}"
        fi
    else
        echo -e "${YELLOW}Unknown (no PID file)${NC}"
    fi
    
    echo ""
    echo "Frontend:"
    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            echo -e "${GREEN}Running (PID: $FRONTEND_PID)${NC}"
        else
            echo -e "${RED}Not running${NC}"
        fi
    else
        echo -e "${YELLOW}Unknown (no PID file)${NC}"
    fi
    
    echo ""
    echo "URLs:"
    echo "  Backend:  http://localhost:8080/health"
    echo "  Frontend: http://localhost:3001"
    echo ""
}

# Function to clean and rebuild
clean_rebuild() {
    echo ""
    echo "========================================"
    echo " WARNING: This will clean and rebuild"
    echo "========================================"
    echo ""
    echo "This will:"
    echo "- Stop all Docker containers"
    echo "- Remove all containers and images"
    echo "- Rebuild everything from scratch"
    echo ""
    echo "This may take several minutes."
    echo ""
    
    read -p "Are you sure? (y/n): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return
    fi
    
    echo ""
    echo "Cleaning up..."
    docker-compose down -v
    docker-compose rm -f
    
    echo ""
    echo "Rebuilding..."
    docker-compose build --no-cache
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}[OK] Clean rebuild complete${NC}"
    echo ""
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Main menu
while true; do
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "1. Start ALL services (Docker + Backend + Frontend)"
    echo "2. Start ONLY Docker services (tools microservices)"
    echo "3. Stop all services"
    echo "4. View logs"
    echo "5. Check service status"
    echo "6. Clean up and rebuild"
    echo "0. Exit"
    echo ""
    
    read -p "Enter your choice (0-6): " choice
    
    case $choice in
        1)
            start_all
            ;;
        2)
            start_docker
            ;;
        3)
            stop_all
            ;;
        4)
            view_logs
            ;;
        5)
            check_status
            ;;
        6)
            clean_rebuild
            ;;
        0)
            echo ""
            echo "Thank you for using Data Analysis Engine Agent!"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice!${NC}"
            ;;
    esac
    
    read -p "Press Enter to continue..."
done
