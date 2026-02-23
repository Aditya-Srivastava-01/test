# CoachAI — Full Project Context Document

---

## 1. THE IDEA

### Problem Statement
Professional soccer coaching suffers from a critical lag problem: tactical breakdowns happen in real-time, but coaching decisions are often made reactively — after the damage is done. Coaches watching 22 players simultaneously cannot process spatial patterns fast enough to intervene at the right moment.

### The Vision
Build a system that:
- Watches every player's position every 100ms
- Automatically detects when a tactical pattern breaks down (e.g. a defensive line collapses)
- Instantly generates a specific, actionable coaching instruction using AI
- Delivers that instruction to the coach's screen before the opposition can exploit the gap

### Hackathon Angle
Frame it as **"AI that thinks like a defensive coordinator"** — the system doesn't just detect events, it reasons about *what to do next* and communicates it in natural language a real coach would use.

---

## 2. THE SOLUTION ARCHITECTURE

```
[Player Tracking Data]
        ↓
[Mock Data Generator] — generates 60 seconds of 22-player coordinates
        ↓
[FastAPI WebSocket Server] — streams frames at 10fps
        ↓
[Agentic Coach Module] — mock GNN detects tactical breakdown at frame 300
        ↓
[Gemini API] — generates 2-sentence coaching advice (fallback if no key)
        ↓
[WebSocket Push] — advice sent to browser client
        ↓
[Web Client Canvas] — live player visualization + red coaching alert banner
        ↓
[SQLite Database] — every tactical event stored with timestamp and advice
```

### Core Concept: Agentic Reasoning Loop
Each frame that arrives triggers an analysis function. This mimics what a Graph Neural Network (GNN) would do in production — model player relationships as a graph, detect when spatial patterns deviate from expected defensive shape, classify the event type. For the prototype, frame 300 (exactly 30 seconds) is hardcoded as the trigger, simulating what the GNN would detect.

---

## 3. TECH STACK — DECISIONS & REASONING

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend framework | FastAPI | Native async support, WebSocket built-in, auto docs at /docs |
| WebSocket | FastAPI + uvicorn | Same process, no separate WS server needed |
| LLM | Google Gemini API | Free tier available, good instruction-following for sports domain |
| HTTP client | httpx | Async-native, works cleanly inside FastAPI's event loop |
| Database | SQLite + SQLAlchemy | Zero setup, file-based, shows persistence without infra overhead |
| Data validation | Pydantic | Already bundled with FastAPI, enforces API response shapes |
| Environment | python-dotenv | Standard .env pattern, keeps API keys out of code |
| Frontend | Vanilla HTML/CSS/JS | No build step, opens as a file, easy to demo |
| Fonts | Bebas Neue + JetBrains Mono | Tactical/sports aesthetic, distinct from generic AI look |

---

## 4. FILE-BY-FILE BREAKDOWN

### `backend/mock_data_generator.py`
**What it does:**
- Defines 22 players (11 home, 11 away), each with a zone bounding box on a 100×100 coordinate field
- Each player moves using a random walk algorithm: pick a random target within their zone, walk toward it, pick a new one when close
- Adds slight noise (±0.1 per frame) to make movement look organic
- Generates 600 frames (60 seconds × 10fps)
- Outputs `mock_match.json` — a list of frame objects

**Output format per frame:**
```json
{
  "frame_index": 0,
  "timestamp": 0.0,
  "players": [
    {"id": 1, "team": "home", "x": 12.4, "y": 47.3},
    ...
  ]
}
```

**Formation zones (100×100 field):**
- Home team (left side): GK near x=5-20, defenders x=10-30, midfielders x=25-50, forwards x=45-70
- Away team (right side): mirrored

---

### `backend/agentic_coach.py`
**What it does:**
Two functions that together form the "agentic" reasoning layer:

**`analyze_frame(frame_index, player_data)`**
- Called on every frame
- Simulates a GNN that would analyze player graph topology
- Hardcoded: returns `(True, "Defensive Collapse", "Right flank exposed")` at frame 300
- All other frames return `(False, "", "")`
- In production: this would run a real GNN (e.g. PyTorch Geometric) computing edge features between players, detecting when defensive triangle distances exceed thresholds

**`get_coaching_advice(event_type, description)`**
- Async function, uses `httpx.AsyncClient` (non-blocking)
- Builds a prompt: *"You are an elite soccer coach mid-match. A tactical breakdown has occurred: 'Defensive Collapse' — Right flank exposed. Give a precise, urgent 2-sentence coaching instruction..."*
- POSTs to Gemini API endpoint: `generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`
- Parses `candidates[0].content.parts[0].text` from response
- On ANY failure (no key, network error, bad response): returns hardcoded fallback advice
- Fallback: *"Defensive Collapse detected! Instruct the right-back to tuck in and the central midfielder to drop deeper."*

---

### `backend/main.py`
**What it does:**
The central server. Responsibilities:

1. **Startup**: Loads `mock_match.json` into memory as `FRAMES` list. If file missing, generates on-the-fly and saves it.
2. **`GET /`**: Health check endpoint
3. **`GET /events`**: Returns all stored tactical events from SQLite as JSON
4. **`WS /ws/live-match/{match_id}`**: The main WebSocket endpoint

**WebSocket flow:**
```
Client connects
  → Create Match record in DB
  → Loop through all 600 frames:
      → Send frame JSON to client
      → Call analyze_frame()
      → If triggered: call get_coaching_advice() (async, non-blocking)
                    → Send coaching JSON to client
                    → Save TacticalEvent to DB
      → asyncio.sleep(0.1)   ← maintains 10fps without blocking
  → Send match_end signal
  → Update Match status in DB
  → On disconnect: graceful exit via WebSocketDisconnect exception
```

**Critical fix applied:** FastAPI's `Depends(get_db)` dependency injection does NOT work in WebSocket endpoints. The session is created manually inside the handler and closed in a `finally` block.

---

### `backend/database.py`
- Creates SQLite engine at path from `DATABASE_URL` env variable (default: `./coach.db`)
- `SessionLocal` factory for creating DB sessions
- `get_db()` generator used as FastAPI dependency for regular HTTP endpoints
- `Base` class (SQLAlchemy DeclarativeBase) for model inheritance

---

### `backend/models.py`
Three SQLAlchemy ORM models:

**`Match`**: Tracks each WebSocket session
- `id`, `start_time` (auto datetime), `status` (live/finished/disconnected/error)

**`TacticalEvent`**: Core data record
- `id`, `match_id` (FK to Match), `timestamp` (float, seconds into match), `event_type` (string), `description` (string), `advice` (full text of AI recommendation), `created_at`

**`Player`** (defined but not actively used in streaming — placeholder for future roster management)

---

### `backend/schemas.py`
Pydantic schema for `TacticalEventResponse`:
- Maps SQLAlchemy model to API response shape
- `model_config = {"from_attributes": True}` enables ORM mode (Pydantic v2 syntax)
- Used by `GET /events` to serialize DB records to JSON

---

### `web_client/index.html`
**Single file, no dependencies, no build step.**

**Layout:**
- Dark tactical theme (deep greens, accent yellow #d4f72a, red alerts)
- 2-column grid: pitch canvas (left) + sidebar (right)
- Header with live status pill
- Footer with WebSocket connection status

**Canvas pitch rendering:**
- Alternating grass stripe pattern (10 stripes)
- White field lines: outline, halfway line, center circle, penalty areas, goals
- Players drawn as colored circles with glow effect
  - Home: blue (#3b82f6) with blue glow
  - Away: red (#ef4444) with red glow
  - Jersey number displayed inside circle
- `drawPitch()` called on resize via ResizeObserver
- `renderFrame(players)` called on every incoming frame message

**WebSocket handling:**
```javascript
ws.onopen    → hide overlay, update status pill to LIVE
ws.onerror   → show error (only restore start overlay if match never started)
ws.onclose   → show small ↺ Replay button on pitch (NOT the full start overlay)
ws.onmessage → parse JSON:
               type="frame"    → update canvas + stats sidebar
               type="coaching" → show red banner with advice
               type="match_end"→ log completion
```

**Coaching Banner:**
- Hidden by default (`display: none`)
- On coaching message: becomes visible with pulsing red border animation
- Shows: event name, full advice text, timestamp + description
- Blinking red dot indicator (CSS animation)

**Key bug fix:** `matchStarted` boolean flag tracks whether `onopen` was ever called. `onerror` and `onclose` only restore the start overlay if `matchStarted === false`, preventing the screen from resetting mid-match.

---

## 5. BUGS FIXED DURING DEVELOPMENT

### Bug 1: Screen resetting after 1-2 seconds
**Root cause:** `ws.onclose` was restoring the start overlay unconditionally. Since the server was crashing (Bug 2), the WebSocket was closing immediately after connecting, triggering the overlay restore.

**Fix:** Added `matchStarted` flag. Overlay only shown again if connection never succeeded. After a legitimate match ends, a small Replay button appears on the pitch instead.

### Bug 2: Server crashing silently
**Root cause:** `Depends(get_db)` was used as a parameter in the WebSocket endpoint function signature. FastAPI's dependency injection system is designed for HTTP request/response cycles, not persistent WebSocket connections. The dependency would resolve incorrectly and the DB session would be closed prematurely, causing the frame loop to crash on the first DB write.

**Fix:** Removed `Depends(get_db)` from the WebSocket handler. Replaced with manual `db = SessionLocal()` at the top of the handler and `db.close()` in a `finally` block, ensuring the session stays alive for the full connection duration.

### Bug 3: Console spam slowing the loop
**Root cause:** Every single frame was being logged (`logger.info` 600 times in 60 seconds), which was creating I/O pressure on the event loop.

**Fix:** Log only every 50th frame (`if frame_index % 50 == 0`).

---

## 6. DATA FLOW — END TO END

```
1. Server starts
   └── Loads mock_match.json (600 frames, 22 players each) into RAM

2. User opens index.html, clicks "▶ START MATCH"
   └── JS creates: new WebSocket("ws://localhost:8000/ws/live-match/123")

3. Server accepts connection
   └── Creates Match(status="live") in SQLite

4. Frame loop begins (10fps for 60 seconds)
   └── Every 100ms:
       ├── Server sends: {"type":"frame", "timestamp":N, "players":[...]}
       ├── Client receives → draws 22 dots on canvas
       └── Server checks: analyze_frame(frame_index)

5. At frame 300 (t=30.0s):
   ├── analyze_frame returns (True, "Defensive Collapse", "Right flank exposed")
   ├── get_coaching_advice() called async:
   │   ├── If GEMINI_API_KEY set → POST to Gemini API → parse response text
   │   └── If not set / error → return fallback advice string
   ├── Server sends: {"type":"coaching", "event":"...", "advice":"...", "timestamp":30.0}
   ├── TacticalEvent saved to SQLite
   └── Client receives → red banner appears with advice text

6. At frame 599 (t=59.9s):
   ├── Server sends: {"type":"match_end", "message":"Match simulation complete."}
   ├── Match(status="finished") saved to SQLite
   └── Client logs completion, shows ↺ Replay button

7. Querying history:
   └── GET http://localhost:8000/events → returns all TacticalEvents as JSON
```

---

## 7. REAL DATA INTEGRATION

To replace mock data with real tracking data, only `mock_data_generator.py` needs to change. The rest of the stack is format-agnostic.

**Required output format:**
```json
[
  {
    "frame_index": 0,
    "timestamp": 0.0,
    "players": [
      {"id": 1, "team": "home", "x": 12.4, "y": 47.3},
      {"id": 12, "team": "away", "x": 87.6, "y": 52.1}
    ]
  }
]
```

**Real data sources:**

| Source | Access | Format | Notes |
|--------|--------|--------|-------|
| StatsBomb Open Data | Free, GitHub | JSON events + freeze frames | No continuous tracking, but rich event data |
| Metrica Sports Sample | Free, GitHub | CSV: player_id, team, x, y, time | Best drop-in for this project |
| SkillCorner | Free sample available | JSON tracking 10fps | Closest to production format |
| Tracab | Paid license | Binary/XML | Used by Bundesliga, EPL |
| Second Spectrum | Paid | JSON | Used by NBA, select EPL clubs |
| FIFA EPTS | Standard | XML | Official FIFA tracking standard |

**Metrica adapter (drop-in replacement):**
```python
import pandas as pd

def load_metrica_data(csv_path: str) -> list[dict]:
    df = pd.read_csv(csv_path)
    frames = []
    for frame_idx, group in df.groupby("frame"):
        frames.append({
            "frame_index": int(frame_idx),
            "timestamp": round(frame_idx / 25, 2),  # Metrica is 25fps
            "players": [
                {
                    "id": int(row.player_id),
                    "team": row.team,
                    "x": float(row.x) * 100,   # Metrica uses 0-1, scale to 0-100
                    "y": float(row.y) * 100
                }
                for _, row in group.iterrows()
            ]
        })
    return frames
```

---

## 8. PRODUCTION UPGRADE PATH

| Feature | Current (Prototype) | Production |
|---------|-------------------|------------|
| Tactical detection | Hardcoded at frame 300 | Real GNN (PyTorch Geometric) on live tracking |
| Player data | Random walk simulation | Live feed from Tracab/SkillCorner via licensed API |
| LLM | Gemini (single call) | Fine-tuned model on coaching transcripts |
| Database | SQLite file | PostgreSQL with connection pooling |
| WebSocket | Single server, single match | Redis pub/sub for multi-match fan-out |
| Auth | None | JWT tokens for coach dashboard |
| Latency | ~100ms simulated | Target <200ms end-to-end on real data |
| Frontend | Static HTML file | React dashboard with historical event timeline |

---

## 9. QUICK REFERENCE — COMMANDS

```powershell
# First time setup (Windows PowerShell)
cd C:\path\to\coach-ai\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add GEMINI_API_KEY

# Generate match data
python mock_data_generator.py

# Start server
uvicorn main:app --reload

# Every time after
venv\Scripts\activate
uvicorn main:app --reload
```

```
API endpoints:
  GET  http://localhost:8000/         → health check
  GET  http://localhost:8000/docs     → auto-generated API docs
  GET  http://localhost:8000/events   → past tactical events from DB
  WS   ws://localhost:8000/ws/live-match/123  → live match stream
```

---

## 10. PROJECT FILE STRUCTURE

```
coach-ai/
├── backend/
│   ├── main.py                 ← FastAPI app, WebSocket server, startup logic
│   ├── mock_data_generator.py  ← 22-player simulation, outputs mock_match.json
│   ├── agentic_coach.py        ← GNN trigger logic + Gemini API call
│   ├── models.py               ← SQLAlchemy ORM (Match, TacticalEvent)
│   ├── schemas.py              ← Pydantic response models
│   ├── database.py             ← SQLite engine + session factory
│   ├── requirements.txt        ← All Python dependencies with versions
│   ├── .env.example            ← Template for environment variables
│   └── mock_match.json         ← Generated file (600 frames, created by generator)
├── web_client/
│   └── index.html              ← Full client: canvas + WebSocket + coaching banner
└── CONTEXT.md                  ← This file
```
