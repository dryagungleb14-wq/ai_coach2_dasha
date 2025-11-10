from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Ошибка создания engine: {e}")
    raise

Base = declarative_base()

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    audio_url = Column(String)
    transcription = Column(Text)
    duration = Column(Float)
    manager = Column(String)
    call_date = Column(DateTime)
    call_identifier = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    progress = Column(Integer, default=0)
    
    evaluations = relationship("Evaluation", back_populates="call")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"), nullable=False)
    scores = Column(JSON)
    итоговая_оценка = Column(Integer)
    нарушения = Column(Boolean, default=False)
    комментарии = Column(Text)
    is_retest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    call = relationship("Call", back_populates="evaluations")

def init_db():
    Base.metadata.create_all(bind=engine)

