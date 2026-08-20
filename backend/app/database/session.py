from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping helps rebuild connections if PostgreSQL restarts
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
