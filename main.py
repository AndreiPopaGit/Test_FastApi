from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import shutil
import os
from openai import OpenAI
import json
import re
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Replace with your project URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Replace with your anon or service key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

def identify_food(image_url_supabase):
    """Send the image URL to OpenAI and return parsed JSON data."""
    
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = "Identify the food in the images and output them in JSON format. Try to identify as much foods as possible and only output the JSON. The JSON should contain: name, kcal, protein, carbs, fats in this order."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url_supabase}},
                    ],
                }
            ],
        )

        # Extract response text
        response_text = response.choices[0].message.content

        # Remove backticks and possible "json" annotation
        cleaned_json_text = re.sub(r"```json|```", "", response_text).strip()

        # Parse JSON safely
        try:
            food_data = json.loads(cleaned_json_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": response_text}  # Ensure function always returns

        return food_data  # ✅ Ensure this always runs

    except Exception as e:
        return {"error": str(e)}  # Ensure function always returns

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to Supabase Storage with a unique filename and return its public URL along with OpenAI analysis."""
    
    try:
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]  # Extract file extension (.jpg, .png, etc.)
        unique_filename = f"{uuid.uuid4().hex}_{int(time.time())}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save the file temporarily in `/tmp`
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Upload to Supabase Storage with the new unique filename
        with open(file_path, "rb") as f:
            supabase.storage.from_("Food_images").upload(unique_filename, f, {"content-type": file.content_type})

        # Get public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/Food_images/{unique_filename}"

        # Get food analysis from OpenAI
        json_food = identify_food(public_url)

        return {
            "message": "File uploaded successfully",
            "url": public_url,
            "json": json_food
        }

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