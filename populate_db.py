#!/usr/bin/env python3
"""
Quick script to populate database with sample threat data for dashboard testing
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, init_database
from app.models.database import Threat, IOC, Feed, ThreatAnalysis
from app.core.llm_service import get_llm_service
from sqlalchemy.orm import Session

def create_sample_data():
    """Create sample threat data for testing"""
    
    # Initialize database
    init_database()
    db = next(get_db())
    llm_service = get_llm_service()
    
    # Sample feed data
    feeds = [
        {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "status": "active"},
        {"name": "SANS ISC", "url": "https://isc.sans.edu/rssfeed.xml", "status": "active"},
        {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/", "status": "active"}
    ]
    
    # Create feeds
    feed_objects = []
    for feed_data in feeds:
        # Check if feed already exists
        existing_feed = db.query(Feed).filter_by(name=feed_data["name"]).first()
        if existing_feed:
            feed_objects.append(existing_feed)
            print(f"✅ Using existing feed: {existing_feed.name}")
        else:
            feed = Feed(
                name=feed_data["name"],
                url=feed_data["url"],
                status=feed_data["status"],
                last_fetched=datetime.utcnow() - timedelta(minutes=30)
            )
            db.add(feed)
            db.flush()  # Get ID
            feed_objects.append(feed)
            print(f"➕ Created new feed: {feed.name}")
    
    db.commit()
    
    # Sample threats
    sample_threats = [
        {
            "title": "UK Arrests Four in 'Scattered Spider' Ransom Group",
            "content": "Law enforcement agencies have arrested four individuals connected to the Scattered Spider ransomware group. The group has been responsible for multiple high-profile attacks targeting major corporations.",
            "source_url": "https://krebsonsecurity.com/2025/07/uk-charges-four-in-scattered-spider-ransom-group/",
            "feed": feed_objects[0]
        },
        {
            "title": "Microsoft Patch Tuesday, July 2025 Edition",
            "content": "Microsoft released critical security updates addressing CVE-2025-49719 and CVE-2025-47981. These vulnerabilities affect Windows systems and could allow remote code execution.",
            "source_url": "https://krebsonsecurity.com/2025/07/microsoft-patch-tuesday-july-2025-edition/",
            "feed": feed_objects[0]
        },
        {
            "title": "SSH Tunneling Attack Campaign Detected",
            "content": "Security researchers have identified a new campaign using SSH tunneling techniques to establish persistent access to compromised systems. The attack uses malicious domains and IP addresses.",
            "source_url": "https://isc.sans.edu/diary/rss/32094",
            "feed": feed_objects[1]
        },
        {
            "title": "New Malware Family Targets Financial Institutions",
            "content": "A sophisticated malware family has been discovered targeting banking systems. The malware communicates with command and control servers at malicious-c2.example.com and uses various file hashes for persistence.",
            "source_url": "https://example.com/threat-report",
            "feed": feed_objects[2]
        }
    ]
    
    threat_objects = []
    for i, threat_data in enumerate(sample_threats):
        # Create threat
        threat = Threat(
            title=threat_data["title"],
            content=threat_data["content"],
            url=threat_data["source_url"],
            published_date=datetime.utcnow() - timedelta(hours=i*2),
            feed_id=threat_data["feed"].id,
            processed=True
        )
        db.add(threat)
        db.flush()  # Get ID
        
        # Generate AI analysis
        print(f"🤖 Analyzing: {threat_data['title'][:50]}...")
        ai_result = llm_service.summarize_threat(threat_data["title"], threat_data["content"])
        
        # Create threat analysis
        analysis = ThreatAnalysis(
            threat_id=threat.id,
            summary=ai_result.get("summary", "AI-generated threat summary"),
            threat_category=ai_result.get("threat_type", "unknown"),
            severity_level=ai_result.get("severity", "medium"),
            confidence_score=ai_result.get("confidence_score", 0.7),
            key_points=json.dumps(ai_result.get("key_points", [])),
            model_used=ai_result.get("model_used", "tinyllama")
        )
        db.add(analysis)
        
        threat_objects.append(threat)
    
    # Sample IOCs
    sample_iocs = [
        {"value": "CVE-2025-49719", "type": "CVE", "confidence": 0.9, "threat": threat_objects[1]},
        {"value": "CVE-2025-47981", "type": "CVE", "confidence": 0.9, "threat": threat_objects[1]},
        {"value": "malicious-c2.example.com", "type": "DOMAIN", "confidence": 0.8, "threat": threat_objects[3]},
        {"value": "192.168.100.50", "type": "IP", "confidence": 0.7, "threat": threat_objects[2]},
        {"value": "5d41402abc4b2a76b9719d911017c592", "type": "MD5", "confidence": 0.6, "threat": threat_objects[3]},
        {"value": "scattered-spider.onion", "type": "DOMAIN", "confidence": 0.8, "threat": threat_objects[0]}
    ]
    
    for ioc_data in sample_iocs:
        ioc = IOC(
            value=ioc_data["value"],
            ioc_type=ioc_data["type"],
            confidence=ioc_data["confidence"],
            threat_id=ioc_data["threat"].id
        )
        db.add(ioc)
    
    db.commit()
    print("✅ Database populated with sample data!")
    
    # Print summary
    print(f"\n📊 Database Summary:")
    print(f"   Feeds: {db.query(Feed).count()}")
    print(f"   Threats: {db.query(Threat).count()}")
    print(f"   IOCs: {db.query(IOC).count()}")
    print(f"   AI Analysis: {db.query(ThreatAnalysis).count()}")
    
    db.close()

if __name__ == "__main__":
    import json
    create_sample_data()