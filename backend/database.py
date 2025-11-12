"""
Database models and connection for feedback storage
Uses PostgreSQL on Railway for persistent storage
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

Base = declarative_base()


class Feedback(Base):
    """
    Feedback model for storing user ratings and comments
    """
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    telegram_sent = Column(Boolean, default=False, nullable=False)  # Track if sent to Telegram
    telegram_error = Column(Text, nullable=True)  # Store error if Telegram failed

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'telegram_sent': self.telegram_sent,
            'telegram_error': self.telegram_error
        }


# Database connection
engine = None
SessionLocal = None
db_available = False


def init_database():
    """
    Initialize database connection
    Returns: (engine, SessionLocal, db_available)
    """
    global engine, SessionLocal, db_available

    # Get DATABASE_URL from Railway environment
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("\n" + "=" * 80)
        print("⚠️  DATABASE_URL not found in environment")
        print("=" * 80)
        print("ℹ️  PostgreSQL database is optional but recommended")
        print("ℹ️  Without it, feedback will only be saved to files (lost on redeploy)")
        print("\nHow to setup:")
        print("1. Railway Dashboard → New → Database → PostgreSQL")
        print("2. Link database to your service")
        print("3. Railway will automatically add DATABASE_URL variable")
        print("4. Redeploy your service")
        print("=" * 80)
        print()
        return None, None, False

    try:
        print("\n" + "=" * 80)
        print("🔗 Connecting to PostgreSQL database...")
        print("=" * 80)

        # PostgreSQL URL from Railway
        # Fix: Railway provides postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        # Create engine
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10
        )

        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")

        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        print("✅ Database tables initialized")

        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db_available = True
        print("✅ PostgreSQL is ready for feedback storage")
        print("=" * 80)
        print()

        return engine, SessionLocal, True

    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  Feedback will be saved to files only (temporary storage)")
        print("=" * 80)
        print()
        return None, None, False

    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  Feedback will be saved to files only (temporary storage)")
        print("=" * 80)
        print()
        return None, None, False


def save_feedback_to_db(rating, comment, timestamp, session_id, ip_address, telegram_sent=False, telegram_error=None):
    """
    Save feedback to PostgreSQL database

    Args:
        rating: User rating (1-5)
        comment: User comment (optional)
        timestamp: ISO format timestamp
        session_id: Session ID (optional)
        ip_address: User IP address
        telegram_sent: Whether Telegram notification was sent successfully
        telegram_error: Error message if Telegram failed

    Returns:
        tuple: (success: bool, feedback_id: int or None, error: str or None)
    """
    if not db_available or not SessionLocal:
        return False, None, "Database not available"

    db = SessionLocal()
    try:
        # Parse timestamp
        if isinstance(timestamp, str):
            timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            timestamp_dt = timestamp

        # Create feedback record
        feedback = Feedback(
            rating=rating,
            comment=comment,
            timestamp=timestamp_dt,
            session_id=session_id,
            ip_address=ip_address,
            telegram_sent=telegram_sent,
            telegram_error=telegram_error
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        print(f"[DATABASE] ✅ Saved feedback to PostgreSQL: ID={feedback.id}, rating={rating}")
        return True, feedback.id, None

    except Exception as e:
        db.rollback()
        error_msg = f"Database save failed: {str(e)}"
        print(f"[DATABASE] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, None, error_msg

    finally:
        db.close()


def get_unsent_telegram_feedbacks():
    """
    Get all feedbacks that weren't successfully sent to Telegram
    Useful for retry mechanism or manual review

    Returns:
        list: List of Feedback objects
    """
    if not db_available or not SessionLocal:
        return []

    db = SessionLocal()
    try:
        feedbacks = db.query(Feedback).filter(Feedback.telegram_sent == False).all()
        return feedbacks
    except Exception as e:
        print(f"[DATABASE] ❌ Error fetching unsent feedbacks: {e}")
        return []
    finally:
        db.close()


def mark_telegram_sent(feedback_id, success=True, error=None):
    """
    Mark a feedback as sent to Telegram

    Args:
        feedback_id: ID of feedback record
        success: Whether send was successful
        error: Error message if failed
    """
    if not db_available or not SessionLocal:
        return

    db = SessionLocal()
    try:
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if feedback:
            feedback.telegram_sent = success
            feedback.telegram_error = error
            db.commit()
            print(f"[DATABASE] ✅ Updated telegram status for feedback {feedback_id}: sent={success}")
    except Exception as e:
        db.rollback()
        print(f"[DATABASE] ❌ Error updating telegram status: {e}")
    finally:
        db.close()


# Initialize database on module import (works with gunicorn)
engine, SessionLocal, db_available = init_database()
