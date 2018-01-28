GUNICORN=$HOME/local/python/virtualenv/bhs/bin/gunicorn

# Start Gunicorn server:
echo Starting Gunicorn...
exec $GUNICORN WebBHS.wsgi:application --bind 0.0.0.0:8081 --workers 3
