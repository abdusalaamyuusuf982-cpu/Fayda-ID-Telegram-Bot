from models import User, ProcessingMode, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_or_create_user(telegram_id: int) -> User:
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, credits=0, trials=2)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

def update_user_credits(telegram_id: int, delta: int) -> int:
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.credits += delta
            session.commit()
            return user.credits
        return 0

def update_user_mode(telegram_id: int, mode: ProcessingMode):
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.mode = mode
            session.commit()

def increment_user_generated(telegram_id: int):
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.total_generated += 1
            session.commit()

def update_user_trials(telegram_id: int, delta: int) -> int:
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.trials += delta
            session.commit()
            return user.trials
        return 0
