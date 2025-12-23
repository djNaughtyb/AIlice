"""
PostgreSQL database configuration and connection management for AIlice.
"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()

class DatabaseManager:
    """
    Manages PostgreSQL database connections for AIlice.
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None):
        """
        Initialize the database connection.
        
        Args:
            database_url: PostgreSQL connection URL. If not provided, reads from environment.
                         Format: postgresql://user:password@host:port/dbname
        """
        if self._initialized:
            logger.warning("Database already initialized, skipping...")
            return
        
        # Get database URL from parameter or environment variable
        db_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://ailice:ailice@localhost:5432/ailice"
        )
        
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                db_url,
                poolclass=pool.QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=False  # Set to True for SQL query logging
            )
            
            # Create sessionmaker
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._initialized = True
            logger.info(f"Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self):
        """
        Create all tables defined in the ORM models.
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        
        Usage:
            with db_manager.get_session() as session:
                # Use session here
                pass
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """
        Close the database connection and cleanup resources.
        """
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager()


# Example ORM models (can be extended as needed)
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime

class ChatSession(Base):
    """
    Example model for storing chat sessions.
    """
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(255), index=True, nullable=False)
    agent_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)


class ChatMessage(Base):
    """
    Example model for storing chat messages.
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class AgentExecution(Base):
    """
    Example model for tracking agent executions.
    """
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    agent_name = Column(String(255), nullable=False)
    task = Column(Text)
    status = Column(String(50))  # pending, running, completed, failed
    result = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    metadata = Column(JSON)


# Convenience functions
def initialize_database(database_url: Optional[str] = None):
    """
    Initialize the database connection and create tables.
    
    Args:
        database_url: PostgreSQL connection URL
    """
    db_manager.initialize(database_url)
    db_manager.create_tables()


def get_db_session() -> Session:
    """
    Get a database session. Should be used with context manager.
    
    Usage:
        with get_db_session() as session:
            # Use session here
            pass
    """
    return db_manager.get_session()
