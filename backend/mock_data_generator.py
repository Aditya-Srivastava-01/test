import random
import asyncio

def generate_match_frames(duration_seconds: int = 60, fps: int = 10):
    total_frames = duration_seconds * fps
    # 22 players: 1-11 Team A, 12-22 Team B
    # Pitch dimensions scaled for web canvas (e.g., 800x600)
    pitch_width = 800
    pitch_height = 600
    
    # Initialize random starting positions
    players = []
    for i in range(22):
        team = "A" if i < 11 else "B"
        jersey = (i % 11) + 1
        # Team A on left, Team B on right initially
        x = random.uniform(50, pitch_width / 2 - 50) if team == "A" else random.uniform(pitch_width / 2 + 50, pitch_width - 50)
        y = random.uniform(50, pitch_height - 50)
        
        players.append({
            "id": i + 1,
            "team": team,
            "jersey": jersey,
            "x": x,
            "y": y
        })
        
    frames = []
    for frame_idx in range(total_frames):
        current_frame = {
            "type": "telemetry",
            "frame": frame_idx,
            "timestamp": frame_idx / fps,
            "players": []
        }
        for p in players:
            # Simulate movement: Random walk with boundaries
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            
            p["x"] = max(0, min(pitch_width, p["x"] + dx))
            p["y"] = max(0, min(pitch_height, p["y"] + dy))
            
            current_frame["players"].append({
                "id": p["id"],
                "team": p["team"],
                "jersey": p["jersey"],
                "x": round(p["x"], 2),
                "y": round(p["y"], 2)
            })
        frames.append(current_frame)
        
    return frames
