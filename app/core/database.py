"""
Database configuration and connection management
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models to ensure they're registered
try:
    from app.models.database import Base, Feed
    MODELS_AVAILABLE = True
except ImportError:
    print("Warning: Models not available")
    MODELS_AVAILABLE = False

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./threat_intelligence.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("DEBUG") else False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    if MODELS_AVAILABLE:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    else:
        print("Models not available - skipping table creation")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables and sample data"""
    if not MODELS_AVAILABLE:
        print("Models not available - using basic initialization")
        return
        
    create_tables()
    
    # Add sample feeds if database is empty
    db = SessionLocal()
    try:
        if db.query(Feed).count() == 0:
            sample_feeds = [
                Feed(
                    name="Krebs on Security",
                    url="https://krebsonsecurity.com/feed/",
                    feed_type="rss"
                ),
                Feed(
                    name="Schneier on Security",
                    url="https://www.schneier.com/feed/",
                    feed_type="rss"
                ),
                Feed(
                    name="SANS Internet Storm Center",
                    url="https://isc.sans.edu/rssfeed.xml",
                    feed_type="rss"
                ),
                Feed(
                    name="Malware Traffic Analysis",
                    url="https://www.malware-traffic-analysis.net/blog-entries.rss",
                    feed_type="rss"
                ),
                Feed(
                    name="Threat Post",
                    url="https://threatpost.com/feed/",
                    feed_type="rss"
                )
            ]
            
            for feed in sample_feeds:
                db.add(feed)
            
            db.commit()
            print(f"Added {len(sample_feeds)} sample feeds to database")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
