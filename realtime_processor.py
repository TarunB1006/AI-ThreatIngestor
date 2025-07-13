#!/usr/bin/env python3
"""
Real-time Threat Intelligence Automation System
Continuously monitors RSS feeds and processes threats with AI
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, init_database
from app.models.database import Threat, IOC, Feed, ThreatAnalysis
from app.core.llm_service import get_llm_service
from app.services.feed_processor import EnhancedFeedProcessor

class RealTimeThreatProcessor:
    """Automated real-time threat intelligence processing"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.processor = EnhancedFeedProcessor(llm_service=self.llm_service)
        self.running = False
        
        # Initialize database
        init_database()
        
        # Configure feeds
        self.feeds = [
            {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "interval": 10},
            {"name": "SANS ISC", "url": "https://isc.sans.edu/rssfeed.xml", "interval": 15},
            {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/", "interval": 20}
        ]
    
    def process_single_feed_with_ai(self, feed_name, feed_url):
        """Process a single feed and generate AI analysis"""
        print(f"🔄 Processing: {feed_name}")
        
        try:
            # Process feed
            threats = self.processor.process_single_feed(feed_url, feed_name)
            
            # Generate AI analysis for new threats
            db = next(get_db())
            unanalyzed = db.query(Threat).join(ThreatAnalysis, isouter=True).filter(
                ThreatAnalysis.id.is_(None)
            ).limit(5).all()
            
            for threat in unanalyzed:
                try:
                    print(f"🤖 Analyzing: {threat.title[:50]}...")
                    
                    ai_result = self.llm_service.summarize_threat(
                        str(threat.title), 
                        str(threat.content or threat.title)
                    )
                    
                    # Save AI analysis
                    analysis = ThreatAnalysis(
                        threat_id=threat.id,
                        summary=ai_result.get("summary", "AI-generated summary"),
                        threat_category=ai_result.get("threat_type", "unknown"),
                        severity_level=ai_result.get("severity", "medium"),
                        confidence_score=ai_result.get("confidence_score", 0.7),
                        model_used=ai_result.get("model_used", "tinyllama")
                    )
                    
                    db.add(analysis)
                    db.commit()
                    
                    print(f"✅ AI analysis saved for: {threat.title[:50]}...")
                    
                except Exception as e:
                    print(f"❌ AI analysis failed: {e}")
            
            db.close()
            print(f"✅ Completed: {feed_name}")
            
        except Exception as e:
            print(f"❌ Feed processing failed for {feed_name}: {e}")
    
    def monitor_feeds_continuously(self):
        """Continuously monitor all feeds"""
        print("🚀 Starting real-time threat monitoring...")
        self.running = True
        
        while self.running:
            for feed in self.feeds:
                if not self.running:
                    break
                
                try:
                    self.process_single_feed_with_ai(feed["name"], feed["url"])
                    time.sleep(5)  # 5 seconds between feeds
                except Exception as e:
                    print(f"❌ Error processing {feed['name']}: {e}")
            
            if self.running:
                print(f"⏰ Cycle complete. Waiting 10 seconds before next cycle...")
                time.sleep(10)  # 10 seconds between cycles
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        if self.running:
            print("⚠️ Monitoring already running!")
            return
        
        thread = threading.Thread(target=self.monitor_feeds_continuously, daemon=True)
        thread.start()
        print("🚀 Real-time monitoring started in background")
        return thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        print("🛑 Stopping real-time monitoring...")
    
    def get_stats(self):
        """Get current database statistics"""
        try:
            conn = sqlite3.connect("threat_intelligence.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM threats")
            threat_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM threat_analysis")
            analysis_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM iocs")
            ioc_count = cursor.fetchone()[0]
            
            # Get recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM threats 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_threats = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_threats": threat_count,
                "ai_analyzed": analysis_count,
                "total_iocs": ioc_count,
                "recent_threats": recent_threats,
                "analysis_coverage": f"{(analysis_count/threat_count*100):.1f}%" if threat_count > 0 else "0%"
            }
            
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main automation interface"""
    processor = RealTimeThreatProcessor()
    
    print("🛡️ AI-Powered Threat Intelligence Automation")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. 🚀 Start real-time monitoring")
        print("2. 📊 Show statistics")
        print("3. 🔄 Process feeds once")
        print("4. 🤖 Analyze all threats with AI")
        print("5. 🛑 Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            thread = processor.start_monitoring()
            print("Monitoring started. Press Ctrl+C to stop or select option 5.")
            try:
                while processor.running:
                    time.sleep(10)
                    stats = processor.get_stats()
                    print(f"📊 Stats: {stats['total_threats']} threats, {stats['ai_analyzed']} analyzed ({stats['analysis_coverage']})")
            except KeyboardInterrupt:
                processor.stop_monitoring()
                
        elif choice == "2":
            stats = processor.get_stats()
            print(f"\n📊 Current Statistics:")
            print(f"   Total Threats: {stats['total_threats']}")
            print(f"   AI Analyzed: {stats['ai_analyzed']}")
            print(f"   Total IOCs: {stats['total_iocs']}")
            print(f"   Recent (1h): {stats['recent_threats']}")
            print(f"   Coverage: {stats['analysis_coverage']}")
            
        elif choice == "3":
            for feed in processor.feeds:
                processor.process_single_feed_with_ai(feed["name"], feed["url"])
                
        elif choice == "4":
            db = next(get_db())
            unanalyzed = db.query(Threat).join(ThreatAnalysis, isouter=True).filter(
                ThreatAnalysis.id.is_(None)
            ).all()
            
            print(f"🤖 Found {len(unanalyzed)} threats needing AI analysis...")
            
            for threat in unanalyzed:
                try:
                    print(f"Analyzing: {threat.title[:50]}...")
                    ai_result = processor.llm_service.summarize_threat(str(threat.title), str(threat.content or threat.title))
                    
                    analysis = ThreatAnalysis(
                        threat_id=threat.id,
                        summary=ai_result.get("summary", "AI-generated summary"),
                        threat_category=ai_result.get("threat_type", "unknown"),
                        severity_level=ai_result.get("severity", "medium"),
                        confidence_score=ai_result.get("confidence_score", 0.7),
                        model_used=ai_result.get("model_used", "tinyllama")
                    )
                    
                    db.add(analysis)
                    
                except Exception as e:
                    print(f"❌ Failed: {e}")
            
            db.commit()
            db.close()
            print("✅ AI analysis complete!")
            
        elif choice == "5":
            processor.stop_monitoring()
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
