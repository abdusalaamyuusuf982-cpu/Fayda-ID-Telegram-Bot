from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class ProcessingMode(str, enum.Enum):
    COLOR = "color"
    BW = "bw"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    credits = Column(Integer, default=0)
    trials = Column(Integer, default=2)
    mode = Column(Enum(ProcessingMode), default=ProcessingMode.COLOR)
    total_generated = Column(Integer, default=0)
