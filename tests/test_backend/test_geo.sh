#!/bin/bash

# Use first argument as radius, second as latitude, third as longitude
RADIUS=${1:-20}
LAT1=${2:-45.382865}
LON1=${3:--75.732837} # Negative number
# Location is at Merivale HS: Default radius set to 20 km

python backend/api/server.py & SERVER_PID=$!

sleep 3 && curl -s "http://127.0.0.1:5000/health" > ./tests/JSON/health.json
if grep -q '"status": "healthy"' ./tests/JSON/health.json; then
    echo "Healthy"
else
    echo "Unhealthy"
fi
sleep 3 && curl -s "http://127.0.0.1:5000/api/businesses?lat1=$LAT1&lon1=$LON1&radius=$RADIUS" > ./tests/JSON/geolocation.json
if grep -q '"count":' ./tests/JSON/geolocation.json; then
    echo "Geolocation API working"
else
    echo "Geolocation API not working"
fi
COUNT=$(jq -r '.count' ./tests/JSON/geolocation.json)
echo "Found $COUNT businesses within $RADIUS km radius."

# Kill server and any child processes
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
echo "Server stopped."
