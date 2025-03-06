from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import shutil
import os

# Supabase Credentials
SUPABASE_URL = "https://hokhefdiqrmkoozdvgmz.supabase.co"  # Replace with your project URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhva2hlZmRpcXJta29vemR2Z216Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MDQxNTE5OSwiZXhwIjoyMDU1OTkxMTk5fQ.0pdB_fsElgL_694oTiiELwFeGJR5xAukkjbKEH7_MsE"  # Replace with your anon or service key

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use `/tmp` for temporary storage (Vercel's only writable directory)
UPLOAD_DIR = "/tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to Supabase Storage and return its public URL"""

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        # Save the file temporarily in `/tmp`
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Upload to Supabase Storage
        with open(file_path, "rb") as f:
            supabase.storage.from_("Food_images").upload(file.filename, f, {"content-type": file.content_type})

        # Get public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/Food_images/{file.filename}"

        return {"message": "File uploaded successfully", "url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Always clean up after upload
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/buckets/")
def list_buckets():
    """List all available storage buckets in Supabase."""
    return supabase.storage.list_buckets()