python backend/api/server.py

curl -s "http://127.0.0.1:5000/health" > health.json
if grep -q '"status": "healthy"' health.json; then
    echo "Healthy"
else
    echo "Unhealthy"
fi

curl -s "http://127.0.0.1:5000/api/businesses?lat=45.373824&lon=-75.775131&radius=20" > geolocation.json