import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

from prompts import (
    NOT_A_DRINK_MESSAGE,
    RECIPE_SYSTEM_INSTRUCTION,
    RecipeResponse,
    build_recipe_prompt,
)

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
    # Freeform text: a drink name, a rambling description, slang, whatever the
    # customer types. The model is prompted to interpret it.
    order: str | None = None


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
    order = (req.order or "").strip()
    if not order:
        raise HTTPException(
            status_code=400,
            detail="Please tell me which drink you'd like a recipe for, then try again.",
        )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=build_recipe_prompt(order),
            config=types.GenerateContentConfig(
                system_instruction=RECIPE_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RecipeResponse,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {e}")

    result = response.parsed
    if result is None:
        raise HTTPException(
            status_code=502, detail="Gemini returned a response we couldn't read."
        )

    if not result.is_drink_order or not result.recipe:
        raise HTTPException(status_code=400, detail=NOT_A_DRINK_MESSAGE)

    return {
        "order": order,
        "drink_name": result.drink_name,
        "prep_time": result.prep_time,
        "recipe": result.recipe,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
