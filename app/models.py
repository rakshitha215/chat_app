from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer)
    receiver_id = Column(Integer)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)