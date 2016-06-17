#!/usr/bin/env python3
import sys
from app import app

if len(sys.argv) > 1:
    debug = sys.argv[1] == 'debug'
else:
    debug = False

app.run(debug=debug)
