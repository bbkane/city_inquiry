#!/usr/bin/env python3

try:
    from app import app
except ImportError as e:
    raise SystemExit("Missing module {}.Use `source activate city_inquiry`".format(str(e)))

app.run(host='0.0.0.0', debug=True)
