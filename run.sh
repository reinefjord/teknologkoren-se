gunicorn -w 4 -b unix:/tmp/teknologkoren-se.sock teknologkoren_se:app
