#!/bin/bash

# Start event subscription in background
curl -N -H "X-Domain-ID: test" -H "X-Sandbox-ID: test" http://localhost:8000/trans/event &
EVENT_PID=$!

sleep 2

# Create session and send prompt
SESSION_RESP=$(curl -s -X POST -H "X-Domain-ID: test" -H "X-Sandbox-ID: test" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test SSE"}' \
  http://localhost:8000/trans/session)

SESSION_ID=$(echo $SESSION_RESP | jq -r '.id')
echo "Session ID: $SESSION_ID"

# Send prompt
PROMPT_RESP=$(curl -s -X POST -H "X-Domain-ID: test" -H "X-Sandbox-ID: test" \
  -H "Content-Type: application/json" \
  -d "{\"sessionID\":\"$SESSION_ID\",\"parts\":[{\"type\":\"text\",\"text\":\"hello\"}]}" \
  http://localhost:8000/trans/session/$SESSION_ID/message)

echo "Prompt sent, waiting for events..."

# Wait for events
sleep 10

# Cleanup
kill $EVENT_PID 2>/dev/null
