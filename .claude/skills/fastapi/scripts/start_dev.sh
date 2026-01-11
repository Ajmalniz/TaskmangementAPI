#!/bin/bash
# FastAPI Development Server Starter
#
# Usage:
#   ./start_dev.sh [main_file] [options]
#
# Examples:
#   ./start_dev.sh                    # Defaults to app/main.py or main.py
#   ./start_dev.sh app/main.py
#   ./start_dev.sh main.py --port 8080

set -e

# Default values
MAIN_FILE=""
PORT="8000"
HOST="127.0.0.1"
RELOAD="--reload"

# Find main.py if not specified
if [ -z "$1" ] || [[ "$1" == --* ]]; then
    if [ -f "app/main.py" ]; then
        MAIN_FILE="app/main.py"
    elif [ -f "main.py" ]; then
        MAIN_FILE="main.py"
    else
        echo "Error: Could not find main.py. Please specify the path."
        echo "Usage: $0 [main_file] [options]"
        exit 1
    fi
else
    MAIN_FILE="$1"
    shift
fi

# Check if file exists
if [ ! -f "$MAIN_FILE" ]; then
    echo "Error: File '$MAIN_FILE' not found!"
    exit 1
fi

# Parse additional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --no-reload)
            RELOAD=""
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Starting FastAPI development server..."
echo "File: $MAIN_FILE"
echo "URL: http://$HOST:$PORT"
echo "Docs: http://$HOST:$PORT/docs"
echo ""

# Check if fastapi CLI is available
if command -v fastapi &> /dev/null; then
    echo "Using FastAPI CLI (recommended)"
    fastapi dev "$MAIN_FILE" --port "$PORT" --host "$HOST"
else
    echo "Using uvicorn directly (install 'fastapi[standard]' for better experience)"
    # Extract app variable from file
    APP_VAR=$(grep -E "^app\s*=\s*FastAPI" "$MAIN_FILE" | head -1 | cut -d'=' -f1 | xargs)
    if [ -z "$APP_VAR" ]; then
        APP_VAR="app"
    fi

    # Convert file path to module path
    MODULE_PATH="${MAIN_FILE%.py}"
    MODULE_PATH="${MODULE_PATH//\//.}"

    uvicorn "$MODULE_PATH:$APP_VAR" --host "$HOST" --port "$PORT" $RELOAD
fi
