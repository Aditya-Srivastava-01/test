import os
import asyncio
from google import genai
from google.genai import types

# Use Gemini API to generate coaching recommendation
# Ensure GOOGLE_API_KEY is set in the environment or passed appropriately
client = genai.Client()

async def generate_coaching_recommendation(match_state: dict) -> str:
    """
    Calls the Gemini API to get a tactical recommendation based on the provided match state.
    """
    prompt = f"You are an expert soccer coach analyzing a youth game. \
The following tactical breakdown just occurred: Defensive Collapse on the right flank. \
Match state details: {match_state}. \
Provide a 2-sentence coaching recommendation to fix this issue immediately."
    
    try:
        # Run synchronous API call in a thread pool to avoid blocking the event loop
        response = await asyncio.to_thread(
            client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
         return f"System Alert: Fix spacing on the right flank immediately. Cover the open zones."

def evaluate_tactical_state(frame: dict) -> dict:
    """
    Mock Graph Neural Network (GNN) evaluation.
    Triggers a 'Defensive Collapse' at exactly 30 seconds (frame 300 at 10fps).
    """
    # Assuming 10 FPS, timestamp 30.0 corresponds to frame 300
    if frame.get("frame") == 300:
         return {
             "trigger": True,
             "event": "Defensive Collapse",
             "location": "Right Flank",
             "timestamp": frame.get("timestamp")
         }
    return {"trigger": False}
