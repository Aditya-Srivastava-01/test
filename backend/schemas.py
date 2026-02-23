from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PlayerBase(BaseModel):
    name: str
    team: str
    jersey_number: int

class PlayerCreate(PlayerBase):
    pass

class PlayerResponse(PlayerBase):
    id: int
    match_id: int
    
    class Config:
        from_attributes = True

class TacticalEventBase(BaseModel):
    event_type: str
    description: str
    x_coord: Optional[float] = None
    y_coord: Optional[float] = None

class TacticalEventCreate(TacticalEventBase):
    pass

class TacticalEventResponse(TacticalEventBase):
    id: int
    match_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class MatchBase(BaseModel):
    name: str

class MatchCreate(MatchBase):
    pass

class MatchResponse(MatchBase):
    id: int
    start_time: datetime
    players: List[PlayerResponse] = []
    events: List[TacticalEventResponse] = []
    
    class Config:
        from_attributes = True
