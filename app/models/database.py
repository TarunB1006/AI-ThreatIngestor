"""
Database models for the AI-Powered Threat Intelligence Aggregator
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Feed(Base):
    """RSS/Atom feed sources"""
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    feed_type = Column(String(50), default="rss")
    status = Column(String(50), default="active")
    last_fetched = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    threats = relationship("Threat", back_populates="feed")


class Threat(Base):
    """Individual threat intelligence items"""
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    
    # Basic threat info
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    author = Column(String(255))
    published_date = Column(DateTime)
    
    # Content analysis
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary
    threat_type = Column(String(100))  # malware, phishing, apt, etc.
    severity_score = Column(Float, default=0.0)  # 0-10 scale
    
    # Processing status
    processed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feed = relationship("Feed", back_populates="threats")
    iocs = relationship("IOC", back_populates="threat")
    analysis = relationship("ThreatAnalysis", back_populates="threat", uselist=False)


class IOC(Base):
    """Indicators of Compromise extracted from threats"""
    __tablename__ = "iocs"
    
    id = Column(Integer, primary_key=True)
    threat_id = Column(Integer, ForeignKey("threats.id"), nullable=False)
    
    # IOC details
    ioc_type = Column(String(50), nullable=False)  # ip, domain, url, hash, email, cve
    value = Column(String(500), nullable=False)
    confidence = Column(Float, default=0.0)  # 0-1 confidence score
    context = Column(Text)  # surrounding text where IOC was found
    
    # Metadata
    is_malicious = Column(Boolean, default=True)
    false_positive = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    threat = relationship("Threat", back_populates="iocs")


class ThreatAnalysis(Base):
    """AI-powered analysis results for threats"""
    __tablename__ = "threat_analysis"
    
    id = Column(Integer, primary_key=True)
    threat_id = Column(Integer, ForeignKey("threats.id"), nullable=False)
    
    # AI Analysis Results
    summary = Column(Text)  # Concise AI summary
    key_points = Column(Text)  # JSON array of key points
    threat_actors = Column(Text)  # JSON array of identified threat actors
    ttps = Column(Text)  # JSON array of tactics, techniques, procedures
    affected_systems = Column(Text)  # JSON array of affected systems/software
    recommendations = Column(Text)  # JSON array of recommended actions
    
    # Classification
    threat_category = Column(String(100))  # malware, phishing, vulnerability, etc.
    severity_level = Column(String(50))  # low, medium, high, critical
    urgency = Column(String(50))  # immediate, high, medium, low
    
    # AI Metadata
    model_used = Column(String(100))  # LLM model used for analysis
    processing_time = Column(Float)  # seconds taken for analysis
    confidence_score = Column(Float)  # overall confidence in analysis
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    threat = relationship("Threat", back_populates="analysis")


class ThreatTag(Base):
    """Tags for categorizing threats"""
    __tablename__ = "threat_tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100))  # technical, business, geographic, etc.
    color = Column(String(7))  # hex color for UI
    created_at = Column(DateTime, default=datetime.utcnow)


class ThreatTagAssociation(Base):
    """Many-to-many relationship between threats and tags"""
    __tablename__ = "threat_tag_associations"
    
    id = Column(Integer, primary_key=True)
    threat_id = Column(Integer, ForeignKey("threats.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("threat_tags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingLog(Base):
    """Log of processing activities"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True)
    activity_type = Column(String(100), nullable=False)  # feed_fetch, ioc_extraction, summarization
    status = Column(String(50), nullable=False)  # success, error, warning
    message = Column(Text)
    details = Column(Text)  # JSON details
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
