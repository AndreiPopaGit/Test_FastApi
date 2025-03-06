from main import app  # Import FastAPI app from main.py
from mangum import Mangum  # Mangum is required to run FastAPI on Vercel

handler = Mangum(app)
