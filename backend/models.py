from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    
    players = relationship("Player", back_populates="match")
    events = relationship("TacticalEvent", back_populates="match")

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    name = Column(String)
    team = Column(String)  # e.g., "home" or "away"
    jersey_number = Column(Integer)
    
    match = relationship("Match", back_populates="players")

class TacticalEvent(Base):
    __tablename__ = "tactical_events"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)
    description = Column(String)
    x_coord = Column(Float, nullable=True)
    y_coord = Column(Float, nullable=True)
    
    match = relationship("Match", back_populates="events")
