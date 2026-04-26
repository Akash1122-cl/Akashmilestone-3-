"""
Database connection and session management for Phase 1
"""

import os
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime
import yaml

Base = declarative_base()


class Product(Base):
    """Product model for fintech apps"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    app_store_id = Column(String(100))
    play_store_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Review(Base):
    """Review model for storing app store and play store reviews"""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    source = Column(String(50), nullable=False)
    external_review_id = Column(String(255), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    author_name = Column(String(255))
    review_date = Column(DateTime, nullable=False)
    review_url = Column(Text)
    version = Column(String(50))
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("source IN ('app_store', 'google_play')", name='check_source'),
    )


class IngestionLog(Base):
    """Ingestion log model for tracking data collection runs"""
    __tablename__ = 'ingestion_logs'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    source = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    reviews_collected = Column(Integer, default=0)
    reviews_processed = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    __table_args__ = (
        CheckConstraint("status IN ('success', 'partial', 'failed')", name='check_status'),
        CheckConstraint("source IN ('app_store', 'google_play')", name='check_source'),
    )


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        db_config = self.config['database']
        db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=db_config['pool_size'],
            max_overflow=db_config['max_overflow'],
            pool_pre_ping=True,
            echo=False
        )
        return engine
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all tables from the database"""
        Base.metadata.drop_all(self.engine)
    
    def close(self):
        """Close the database connection"""
        self.engine.dispose()


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_database(config_path: str = 'config/config.yaml') -> DatabaseManager:
    """Initialize the global database manager"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(config_path)
    return db_manager


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    if db_manager is None:
        init_database()
    return db_manager.get_session()
