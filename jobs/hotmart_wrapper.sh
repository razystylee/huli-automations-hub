#!/bin/bash
# Wrapper script to capture all output from hotmart_to_sheets.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/hotmart_debug.log"

echo "Starting hotmart extraction at $(date)" > "$LOG_FILE"
echo "Python path: $(which python3)" >> "$LOG_FILE"
echo "Working directory: $(pwd)" >> "$LOG_FILE"
echo "Script path: $SCRIPT_DIR/hotmart_to_sheets.py" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

# Run the script and capture both stdout and stderr
python3 "$SCRIPT_DIR/hotmart_to_sheets.py" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?
echo "---" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "Completed at $(date)" >> "$LOG_FILE"

exit $EXIT_CODE
