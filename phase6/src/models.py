"""
Phase 6 Database Models
Advanced Automation and Analytics data models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class AutomationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"

class DeliveryFrequency(Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"

class ReportType(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    TREND_REPORT = "trend_report"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    CUSTOM = "custom"

class AutomationRule(Base):
    """Automation rules for scheduled report generation and delivery"""
    __tablename__ = "automation_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    product_id = Column(String(100), nullable=False)
    
    # Rule configuration
    conditions = Column(JSON, nullable=False)  # Trigger conditions
    actions = Column(JSON, nullable=False)    # Actions to execute
    
    # Scheduling
    frequency = Column(String(50), nullable=False)
    schedule_config = Column(JSON)  # Cron-like schedule
    next_run = Column(DateTime)
    last_run = Column(DateTime)
    
    # Status
    status = Column(String(20), default=AutomationStatus.ACTIVE.value)
    enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    executions = relationship("AutomationExecution", back_populates="rule")

class AutomationExecution(Base):
    """Track execution history of automation rules"""
    __tablename__ = "automation_executions"
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("automation_rules.id"))
    
    # Execution details
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), nullable=False)  # running, completed, failed
    
    # Results
    result = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)  # seconds
    
    # Relationships
    rule = relationship("AutomationRule", back_populates="executions")

class AnalyticsReport(Base):
    """Generated analytics reports"""
    __tablename__ = "analytics_reports"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(String(100), unique=True, nullable=False)
    
    # Report metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)
    product_id = Column(String(100), nullable=False)
    
    # Data and content
    data = Column(JSON, nullable=False)  # Analytics data
    content = Column(Text)  # Generated report content
    insights = Column(JSON)  # Key insights and recommendations
    
    # Time range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # File information
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Status
    status = Column(String(20), default="generated")
    is_published = Column(Boolean, default=False)
    
    # Relationships
    deliveries = relationship("ReportDelivery", back_populates="report")

class ReportDelivery(Base):
    """Track report delivery to stakeholders"""
    __tablename__ = "report_deliveries"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("analytics_reports.id"))
    
    # Delivery details
    recipient = Column(String(255), nullable=False)
    delivery_method = Column(String(50), nullable=False)  # email, drive, docs
    
    # Status
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime)
    error_message = Column(Text)
    
    # Tracking
    delivery_id = Column(String(255))  # Email ID, Drive file ID, etc.
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("AnalyticsReport", back_populates="deliveries")

class Dashboard(Base):
    """Custom analytics dashboards"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True)
    dashboard_id = Column(String(100), unique=True, nullable=False)
    
    # Dashboard metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner = Column(String(255), nullable=False)
    
    # Configuration
    layout = Column(JSON, nullable=False)  # Dashboard layout
    widgets = Column(JSON, nullable=False)  # Widget configurations
    filters = Column(JSON)  # Default filters
    
    # Settings
    is_public = Column(Boolean, default=False)
    refresh_interval = Column(Integer, default=3600)  # seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shares = relationship("DashboardShare", back_populates="dashboard")

class DashboardShare(Base):
    """Dashboard sharing permissions"""
    __tablename__ = "dashboard_shares"
    
    id = Column(Integer, primary_key=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    
    # Share details
    user_email = Column(String(255), nullable=False)
    permission = Column(String(20), nullable=False)  # view, edit, admin
    
    # Metadata
    shared_at = Column(DateTime, default=datetime.utcnow)
    shared_by = Column(String(255))
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="shares")

class TrendAnalysis(Base):
    """Trend analysis results"""
    __tablename__ = "trend_analyses"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(String(100), unique=True, nullable=False)
    
    # Analysis metadata
    product_id = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # sentiment, volume, rating
    
    # Time range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Analysis results
    current_value = Column(Float)
    previous_value = Column(Float)
    change_percent = Column(Float)
    trend_direction = Column(String(20))  # up, down, stable
    
    # Predictions
    predicted_value = Column(Float)
    confidence_score = Column(Float)
    prediction_date = Column(DateTime)
    
    # Detailed data
    data_points = Column(JSON)  # Time series data
    insights = Column(JSON)  # Generated insights
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))

class IntegrationConfig(Base):
    """Third-party integration configurations"""
    __tablename__ = "integration_configs"
    
    id = Column(Integer, primary_key=True)
    integration_id = Column(String(100), unique=True, nullable=False)
    
    # Integration details
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # slack, teams, salesforce, jira
    
    # Configuration
    config = Column(JSON, nullable=False)  # API keys, webhooks, settings
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_status = Column(String(20))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    # Context
    product_id = Column(String(100))
    metric_type = Column(String(50))  # performance, usage, error
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional data
    extra_data = Column(JSON)

# Database initialization
def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

def drop_tables(engine):
    """Drop all database tables"""
    Base.metadata.drop_all(engine)
