from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from backend.mock_data_generator import generate_match_frames
from backend.services.agentic_coach import evaluate_tactical_state, generate_coaching_recommendation
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Coaching Engine")

# Allow all origins for the hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Only try to create tables if we connect successfully, typically use alembic.
    # We will log the error if postgres isn't running.
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables initialized")
    except Exception as e:
        logging.error(f"Failed to connect to database on startup: {e}")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend engine is running"}

@app.websocket("/ws/live-match/{match_id}")
async def websocket_live_match(websocket: WebSocket, match_id: int):
    await websocket.accept()
    logging.info(f"WebSocket connected for match {match_id}")
    try:
        frames = generate_match_frames(duration_seconds=60, fps=10)
        for frame in frames:
            await websocket.send_json(frame)
            
            # Agentic Brain Integration
            tactical_eval = evaluate_tactical_state(frame)
            if tactical_eval.get("trigger"):
                recommendation = await generate_coaching_recommendation(tactical_eval)
                alert_payload = {
                    "type": "insight",
                    "event": tactical_eval["event"],
                    "location": tactical_eval["location"],
                    "timestamp": tactical_eval["timestamp"],
                    "recommendation": recommendation
                }
                await websocket.send_json(alert_payload)
                
            await asyncio.sleep(0.1) # Simulate 10 FPS
        # After 60 seconds
        await websocket.close()
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for match {match_id}")
