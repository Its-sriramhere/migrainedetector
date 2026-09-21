import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:Headachepps%40247@db.lrulmcudqdlidhldncok.supabase.co:5432/postgres")
os.environ.setdefault("SUPABASE_URL", "https://lrulmcudqdlidhldncok.supabase.co")
os.environ.setdefault("SUPABASE_PROJECT_REF", "lrulmcudqdlidhldncok")
from mangum import Mangum
from app.main import app as fastapi_app

app = Mangum(fastapi_app)

