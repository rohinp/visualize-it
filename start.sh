#!/bin/bash

# Visualize-It Startup Script
# This script builds the frontend and starts the unified server

echo "=== Visualize-It Startup Script ==="
echo "Building frontend and starting unified server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed."
    exit 1
fi

# Build the frontend
echo "Building frontend..."
cd frontend || { echo "Error: frontend directory not found"; exit 1; }
npm install || { echo "Error: npm install failed"; exit 1; }
npm run build || { echo "Error: npm build failed"; exit 1; }
echo "Frontend build complete."

# Set up and start the backend
echo "Setting up backend..."
cd ../backend || { echo "Error: backend directory not found"; exit 1; }

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || { echo "Error: Failed to create virtual environment"; exit 1; }
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt || { echo "Error: Failed to install dependencies"; exit 1; }

# Start the server
echo "Starting unified server..."
echo "The application will be available at http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000

# Note: The script will not reach this point unless the server is stopped
echo "Server stopped."
