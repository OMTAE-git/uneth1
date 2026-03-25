#!/bin/bash
# Autonomous ADA Compliance Engine Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check for config file
if [ ! -f ".env" ] && [ -z "$SMTP_HOST" ]; then
    echo "Warning: No .env file found. Emails will not be sent."
    echo "Create .env with SMTP_HOST, SMTP_USER, SMTP_PASS, FROM_EMAIL to enable email."
fi

# Load .env if exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "Starting Autonomous ADA Compliance Engine..."
echo "Press Ctrl+C to stop"

# Run in background with logging
exec python src/autonomous_engine.py --interval 24 >> autonomous.log 2>&1
