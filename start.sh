#!/bin/bash

# Multi-Agent Negotiator Startup Script
echo "🚀 Starting Multi-Agent Negotiator Platform..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis not running. Starting Redis..."
    brew services start redis
fi

# Function to cleanup processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $backend_pid $frontend_pid 2>/dev/null
    exit
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "🔧 Starting Backend Server (FastAPI)..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
backend_pid=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "🎨 Starting Frontend Server (Vite)..."
cd frontend
npm run dev &
frontend_pid=$!
cd ..

echo "✅ Servers started successfully!"
echo "📊 Backend API: http://localhost:8000"
echo "🎯 Frontend App: http://localhost:5173"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait $backend_pid $frontend_pid 