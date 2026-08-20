import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel

# 1. Load the secret variables from your local .env file
load_dotenv()

# 2. Check if the key exists in your system's memory
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "No GEMINI_API_KEY found! Check that your .env file exists and is formatted correctly."
    )

MODEL = "gemini-3.6-flash"

# 3. Initialize the client using the environment variable
client = genai.Client()

app = FastAPI(title="Barista Backend")


class RecipeRequest(BaseModel):
    drink: str | None = None
    notes: str | None = None


@app.get("/health")
def health():
    """Cheap check that the server is up and a key was loaded."""
    return {"status": "ok", "model": MODEL, "api_key_loaded": True}


@app.get("/ping-gemini")
def ping_gemini():
    """Fire a real request at Gemini to confirm the API connection works."""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents="Reply with the single word: pong",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {e}")

    return {"connected": True, "response": response.text}


@app.post("/recipe")
def recipe(req: RecipeRequest):
    """Ask Gemini for a recipe with specific measurements."""
    drink = (req.drink or "").strip()
    if not drink:
        raise HTTPException(
            status_code=400,
            detail="Please tell me which drink you'd like a recipe for, then try again.",
        )

    notes = (req.notes or "").strip()

    prompt = f"Give me a recipe for {drink} with specific measurements"
    if notes:
        prompt += f". Additional requirements: {notes}"

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {e}")

    return {"drink": drink, "recipe": response.text}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
