from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

# This avoids a circular import
from app import views # flake8: noqa
# for ./test_api_calls.py
from app import api_calls
