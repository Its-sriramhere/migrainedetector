import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from mangum import Mangum
from app.main import app as fastapi_app

handler = Mangum(fastapi_app)
