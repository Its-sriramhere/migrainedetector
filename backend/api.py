import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:Headachepps%40247@db.lrulmcudqdlidhldncok.supabase.co:5432/postgres")
os.environ.setdefault("SUPABASE_URL", "https://lrulmcudqdlidhldncok.supabase.co")
os.environ.setdefault("SUPABASE_PROJECT_REF", "lrulmcudqdlidhldncok")
from app.main import app

