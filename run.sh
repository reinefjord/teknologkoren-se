gunicorn -w 4 -b unix:/tmp/teknologkoren-se.sock app:app
