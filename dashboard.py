"""
Simplified Gradio Dashboard for AI-Powered Threat Intelligence
Focus: Clear display of AI analysis and database content
"""

import gradio as gr
import pandas as pd
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Tuple

try:
    from app.core.llm_service import get_llm_service
    from app.services.feed_processor import EnhancedFeedProcessor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class SimpleThreatDashboard:
    def __init__(self):
        self.db_path = "threat_intelligence.db"
        self.llm_service = get_llm_service() if AI_AVAILABLE else None
    
    def store_threat_in_db(self, threat_data):
        """Store processed threat data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if threat already exists (by URL to avoid duplicates)
            cursor.execute("SELECT id FROM threats WHERE url = ?", (threat_data['url'],))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return existing[0]  # Return existing threat ID
            
            # Get or create feed_id based on feed_name
            feed_name = threat_data.get('feed_name', 'Unknown')
            cursor.execute("SELECT id FROM feeds WHERE name LIKE ? OR name = ?", (f"%{feed_name}%", feed_name))
            feed_row = cursor.fetchone()
            
            if not feed_row:
                # Create a new feed entry if it doesn't exist
                cursor.execute("""
                    INSERT INTO feeds (name, url, feed_type, status)
                    VALUES (?, ?, ?, ?)
                """, (feed_name, threat_data.get('feed_url', ''), 'rss', 'active'))
                feed_id = cursor.lastrowid
            else:
                feed_id = feed_row[0]
            
            # Insert new threat
            cursor.execute("""
                INSERT INTO threats (feed_id, title, url, content, published_date, author)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                feed_id,
                threat_data['title'],
                threat_data['url'],
                threat_data['content'],
                threat_data['published_date'],
                threat_data.get('author', '')
            ))
            
            threat_id = cursor.lastrowid
            
            # Store IOCs if available
            if 'iocs' in threat_data and threat_data['iocs']:
                for ioc_type, ioc_list in threat_data['iocs'].items():
                    for ioc in ioc_list:
                        cursor.execute("""
                            INSERT INTO iocs (threat_id, ioc_type, value, confidence)
                            VALUES (?, ?, ?, ?)
                        """, (threat_id, ioc_type, ioc['value'], ioc['confidence']))
            
            # Store AI analysis if available
            if 'ai_summary' in threat_data and threat_data['ai_summary'] != 'AI analysis unavailable':
                cursor.execute("""
                    INSERT INTO threat_analysis 
                    (threat_id, summary, threat_category, severity_level, confidence_score, model_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    threat_id,
                    threat_data.get('ai_summary', ''),
                    threat_data.get('threat_type', 'unknown'),
                    threat_data.get('severity', 'medium'),
                    threat_data.get('confidence_score', 0.7),
                    threat_data.get('model_used', 'tinyllama')
                ))
            
            conn.commit()
            conn.close()
            return threat_id
            
        except Exception as e:
            print(f"Error storing threat: {e}")
            return None

    def get_database_stats(self):
        """Get simple database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM threats")
            threat_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM iocs")
            ioc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM threat_analysis")
            analysis_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM feeds")
            feed_count = cursor.fetchone()[0]
            
            conn.close()
            
            return f"""
            📊 **Database Statistics**
            - 🎯 Threats: {threat_count}
            - 🔍 IOCs: {ioc_count}
            - 🤖 AI Analysis: {analysis_count}
            - 📡 Feeds: {feed_count}
            """
        except Exception as e:
            return f"❌ Database Error: {str(e)}"
    
    def get_recent_threats(self, limit=10):
        """Get recent threats with AI analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                t.title,
                t.url,
                t.published_date,
                ta.summary,
                ta.threat_category,
                ta.severity_level,
                ta.confidence_score,
                ta.model_used
            FROM threats t
            LEFT JOIN threat_analysis ta ON t.id = ta.threat_id
            ORDER BY t.created_at DESC
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            
            if df.empty:
                return pd.DataFrame(columns=["Title", "URL", "Date", "AI Summary", "Category", "Severity", "Confidence", "Model"])
            
            # Fix datetime parsing - handle multiple formats
            if 'published_date' in df.columns and not df.empty:
                try:
                    # Convert to datetime with flexible parsing
                    df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce', utc=True)
                    # Format for display, handle NaT values
                    df['published_date'] = df['published_date'].apply(
                        lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else 'Unknown'
                    )
                except Exception:
                    # If datetime conversion fails completely, just use string representation
                    df['published_date'] = df['published_date'].astype(str).apply(
                        lambda x: x[:16] if len(str(x)) > 16 else str(x)
                    )
            
            df['confidence_score'] = df['confidence_score'].fillna(0).round(2)
            df = df.fillna("Not analyzed")
            
            return df
            
        except Exception as e:
            # Return empty DataFrame instead of error string
            print(f"Error loading threats: {e}")
            return pd.DataFrame(columns=["Title", "URL", "Date", "AI Summary", "Category", "Severity", "Confidence", "Model"])
    
    def get_iocs_summary(self, limit=20):
        """Get IOCs with threat context"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                i.ioc_type,
                i.value,
                i.confidence,
                t.title as threat_title
            FROM iocs i
            JOIN threats t ON i.threat_id = t.id
            ORDER BY i.confidence DESC, i.created_at DESC
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            
            if df.empty:
                return pd.DataFrame(columns=["Type", "Value", "Confidence", "Source Threat"])
            
            df['confidence'] = df['confidence'].round(2)
            return df
            
        except Exception as e:
            print(f"Error loading IOCs: {e}")
            return pd.DataFrame(columns=["Type", "Value", "Confidence", "Source Threat"])
    
    def analyze_threat_text(self, threat_text):
        """Analyze threat text with AI"""
        if not threat_text.strip():
            return "Please enter threat text to analyze"
        
        if not self.llm_service:
            return "❌ AI service not available"
        
        try:
            result = self.llm_service.summarize_threat("Manual Analysis", threat_text)
            
            # Format result for display
            formatted = f"""
            🤖 **AI Analysis Results**
            
            **Summary:** {result.get('summary', 'N/A')}
            
            **Threat Type:** {result.get('threat_type', 'Unknown')}
            
            **Severity:** {result.get('severity', 'Unknown')}
            
            **Processing Time:** {result.get('processing_time', 0):.2f} seconds
            
            **Model Used:** {result.get('model_used', 'Unknown')}
            
            **Confidence Score:** {result.get('confidence_score', 0):.2f}
            
            **Key Points:**
            {chr(10).join([f"• {point}" for point in result.get('key_points', [])])}
            
            **Recommendations:**
            {chr(10).join([f"• {rec}" for rec in result.get('recommendations', [])])}
            """
            
            return formatted
            
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def analyze_all_threats(self):
        """Generate AI summaries for all threats missing analysis"""
        if not self.llm_service:
            return "❌ AI service not available"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find threats without AI analysis
            cursor.execute("""
                SELECT t.id, t.title, t.content 
                FROM threats t
                LEFT JOIN threat_analysis ta ON t.id = ta.threat_id
                WHERE ta.id IS NULL
                LIMIT 10
            """)
            
            unanalyzed = cursor.fetchall()
            
            if not unanalyzed:
                conn.close()
                return "✅ All threats already have AI analysis!"
            
            results = []
            for threat_id, title, content in unanalyzed:
                try:
                    # Generate AI analysis
                    ai_result = self.llm_service.summarize_threat(title, content or title)
                    
                    # Insert analysis into database
                    cursor.execute("""
                        INSERT INTO threat_analysis 
                        (threat_id, summary, threat_category, severity_level, confidence_score, model_used)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        threat_id,
                        ai_result.get("summary", "AI-generated summary"),
                        ai_result.get("threat_type", "unknown"),
                        ai_result.get("severity", "medium"),
                        ai_result.get("confidence_score", 0.7),
                        ai_result.get("model_used", "tinyllama")
                    ))
                    
                    results.append(f"✅ {title[:50]}...")
                    
                except Exception as e:
                    results.append(f"❌ {title[:50]}... - Error: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return f"🤖 **AI Analysis Complete**\n\nProcessed {len(unanalyzed)} threats:\n" + "\n".join(results)
            
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def start_real_time_processing(self):
        """Start automated real-time threat processing"""
        try:
            import threading
            import time
            
            def process_feeds_continuously():
                processor = EnhancedFeedProcessor()
                feeds = [
                    {"name": "Krebs", "url": "https://krebsonsecurity.com/feed/"},
                    {"name": "SANS", "url": "https://isc.sans.edu/rssfeed.xml"},
                    {"name": "Schneier", "url": "https://www.schneier.com/feed/"}
                ]
                
                while True:
                    for feed in feeds:
                        try:
                            # Process feed and get threats
                            threats = processor.process_single_feed(feed["url"], feed["name"])
                            
                            # Store each threat in database
                            for threat in threats:
                                threat['feed_name'] = feed["name"]  # Add feed name
                                threat['feed_url'] = feed["url"]    # Add feed URL
                                self.store_threat_in_db(threat)
                            
                            time.sleep(5)  # 5 seconds between feeds
                        except Exception as e:
                            print(f"Feed processing error: {e}")
                    
                    time.sleep(10)  # 10 seconds between full cycles
            
            # Start background thread
            thread = threading.Thread(target=process_feeds_continuously, daemon=True)
            thread.start()
            
            return "🚀 **Real-time processing started!**\n\nFeeds will be checked every 10 seconds automatically.\nNew threats will appear in the database and get AI analysis."
            
        except Exception as e:
            return f"❌ Failed to start real-time processing: {str(e)}"
    
    def search_threats(self, search_term):
        """Search threats by title or content"""
        if not search_term.strip():
            return pd.DataFrame(columns=["Title", "URL", "Summary", "Severity", "Confidence"])
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                t.title,
                t.url,
                ta.summary,
                ta.severity_level,
                ta.confidence_score
            FROM threats t
            LEFT JOIN threat_analysis ta ON t.id = ta.threat_id
            WHERE t.title LIKE ? OR t.content LIKE ?
            ORDER BY ta.confidence_score DESC
            LIMIT 10
            """
            
            search_pattern = f"%{search_term}%"
            df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern))
            conn.close()
            
            if df.empty:
                return pd.DataFrame(columns=["Title", "URL", "Summary", "Severity", "Confidence"])
            
            df = df.fillna("N/A")
            df['confidence_score'] = pd.to_numeric(df['confidence_score'], errors='coerce').fillna(0).round(2)
            
            return df
            
        except Exception as e:
            print(f"Search error: {e}")
            return pd.DataFrame(columns=["Title", "URL", "Summary", "Severity", "Confidence"])

def create_dashboard():
    """Create the simplified Gradio dashboard"""
    dashboard = SimpleThreatDashboard()
    
    with gr.Blocks(title="🛡️ AI Threat Intelligence Dashboard") as demo:
        
        gr.Markdown("# 🛡️ AI-Powered Threat Intelligence Dashboard")
        gr.Markdown("### Simplified interface for threat analysis and database browsing")
        
        with gr.Tabs():
            
            # Tab 1: Overview & Stats
            with gr.Tab("📊 Overview"):
                gr.Markdown("## Database Overview")
                
                stats_display = gr.Markdown(dashboard.get_database_stats())
                refresh_stats_btn = gr.Button("🔄 Refresh Stats", variant="secondary")
                refresh_stats_btn.click(
                    dashboard.get_database_stats,
                    outputs=stats_display
                )
                
                gr.Markdown("## Recent Threats with AI Analysis")
                threats_display = gr.Dataframe(
                    dashboard.get_recent_threats(),
                    headers=["Title", "URL", "Date", "AI Summary", "Category", "Severity", "Confidence", "Model"]
                )
                
                refresh_threats_btn = gr.Button("🔄 Refresh Threats", variant="primary")
                refresh_threats_btn.click(
                    dashboard.get_recent_threats,
                    outputs=threats_display
                )
            
            # Tab 2: AI Analysis
            with gr.Tab("🤖 AI Analysis"):
                gr.Markdown("## Manual Threat Analysis")
                gr.Markdown("Paste threat intelligence content below for AI analysis:")
                
                with gr.Row():
                    with gr.Column():
                        threat_input = gr.Textbox(
                            label="Threat Content",
                            placeholder="Paste threat article, alert, or intelligence here...",
                            lines=8
                        )
                        analyze_btn = gr.Button("🔍 Analyze with AI", variant="primary")
                    
                    with gr.Column():
                        analysis_output = gr.Markdown(
                            label="AI Analysis Results",
                            value="Results will appear here after analysis..."
                        )
                
                analyze_btn.click(
                    dashboard.analyze_threat_text,
                    inputs=threat_input,
                    outputs=analysis_output
                )
                
                # Quick test examples
                gr.Markdown("### 📝 Quick Test Examples")
                
                example1 = gr.Button("Test: Ransomware Alert")
                example2 = gr.Button("Test: Phishing Campaign")
                example3 = gr.Button("Test: CVE Alert")
                
                example1.click(
                    lambda: "WannaCry ransomware variant detected encrypting files with .wcry extension. Ransom note demands 0.3 Bitcoin payment to decrypt files. Attack spreading through SMB vulnerability.",
                    outputs=threat_input
                )
                
                example2.click(
                    lambda: "Phishing campaign targeting banking customers with fake login pages at suspicious-bank-login.com. Emails impersonate legitimate bank notifications requesting credential verification.",
                    outputs=threat_input
                )
                
                example3.click(
                    lambda: "Critical vulnerability CVE-2025-12345 discovered in Apache web server allowing remote code execution. Proof-of-concept exploit code published on GitHub. Immediate patching recommended.",
                    outputs=threat_input
                )
            
            # Tab 3: IOCs & Indicators
            with gr.Tab("🔍 IOCs & Indicators"):
                gr.Markdown("## Extracted Indicators of Compromise")
                
                iocs_display = gr.Dataframe(
                    dashboard.get_iocs_summary(),
                    headers=["Type", "Value", "Confidence", "Source Threat"]
                )
                
                refresh_iocs_btn = gr.Button("🔄 Refresh IOCs", variant="secondary")
                refresh_iocs_btn.click(
                    dashboard.get_iocs_summary,
                    outputs=iocs_display
                )
            
            # Tab 4: Search & Browse
            with gr.Tab("🔎 Search & Browse"):
                gr.Markdown("## Search Threat Database")
                
                with gr.Row():
                    search_input = gr.Textbox(
                        label="Search Terms",
                        placeholder="Enter keywords to search threats...",
                        scale=3
                    )
                    search_btn = gr.Button("🔍 Search", variant="primary", scale=1)
                
                search_results = gr.Dataframe(
                    label="Search Results",
                    headers=["Title", "URL", "Summary", "Severity", "Confidence"]
                )
                
                search_btn.click(
                    dashboard.search_threats,
                    inputs=search_input,
                    outputs=search_results
                )
            
            # Tab 5: Real-time Processing
            with gr.Tab("🚀 Real-time & Automation"):
                gr.Markdown("## Automated Threat Processing")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### AI Analysis for All Threats")
                        analyze_all_btn = gr.Button("🤖 Analyze All DB Threats", variant="primary")
                        analysis_status = gr.Markdown("Click to generate AI summaries for all threats in database")
                        
                        analyze_all_btn.click(
                            dashboard.analyze_all_threats,
                            outputs=analysis_status
                        )
                    
                    with gr.Column():
                        gr.Markdown("### Real-time Feed Processing")
                        start_realtime_btn = gr.Button("🚀 Start Real-time Processing", variant="secondary")
                        realtime_status = gr.Markdown("Click to start automated feed monitoring")
                        
                        start_realtime_btn.click(
                            dashboard.start_real_time_processing,
                            outputs=realtime_status
                        )
                
                gr.Markdown("### Manual Feed Refresh")
                manual_refresh_output = gr.Markdown("Click refresh to process latest threat feeds manually...")
                manual_refresh_btn = gr.Button("🔄 Manual Refresh", variant="secondary")
                
                def manual_refresh():
                    try:
                        processor = EnhancedFeedProcessor()
                        feeds = [
                            {"name": "Krebs", "url": "https://krebsonsecurity.com/feed/"},
                            {"name": "SANS", "url": "https://isc.sans.edu/rssfeed.xml"},
                            {"name": "Schneier", "url": "https://www.schneier.com/feed/"},
                            {"name": "ThreatPost", "url": "https://threatpost.com/feed/"},
                            {"name": "DarkReading", "url": "https://www.darkreading.com/rss.xml"},
                            {"name": "SecurityWeek", "url": "https://www.securityweek.com/feed/"},
                            {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/"},
                            {"name": "Cyware", "url": "https://cyware.com/news/feed"}
                        ]
                        
                        results = []
                        total_new_threats = 0
                        
                        for feed in feeds:
                            try:
                                # Process feed and get threats (limit to 5 per feed for manual refresh)
                                threats = processor.process_single_feed(feed["url"], feed["name"])
                                
                                # Limit to first 5 threats per feed to avoid overwhelming
                                limited_threats = threats[:5] if len(threats) > 5 else threats
                                
                                # Store each threat in database
                                stored_count = 0
                                for threat in limited_threats:
                                    threat['feed_name'] = feed["name"]  # Add feed name
                                    threat['feed_url'] = feed["url"]    # Add feed URL
                                    threat_id = dashboard.store_threat_in_db(threat)
                                    if threat_id:
                                        stored_count += 1
                                
                                total_new_threats += stored_count
                                results.append(f"✅ {feed['name']}: {len(threats)} processed, {stored_count} new threats stored (limited to 5)")
                                
                            except Exception as e:
                                results.append(f"❌ {feed['name']}: Error - {str(e)}")
                        
                        return f"🔄 **Manual Refresh Results:**\n{chr(10).join(results)}\n\n📊 **Total: {total_new_threats} new threats added to database**"
                        
                    except Exception as e:
                        return f"❌ Manual refresh failed: {str(e)}"
                
                manual_refresh_btn.click(
                    manual_refresh,
                    outputs=manual_refresh_output
                )
                
                gr.Markdown("### Current Feeds")
                gr.Markdown("""
                **Main Security Feeds:**
                - 🌐 **Krebs on Security**: https://krebsonsecurity.com/feed/
                - 🛡️ **SANS ISC**: https://isc.sans.edu/rssfeed.xml
                - 🔒 **Schneier on Security**: https://www.schneier.com/feed/
                
                **Additional Threat Intelligence Feeds:**
                - 🚨 **ThreatPost**: https://threatpost.com/feed/
                - 🎯 **Dark Reading**: https://www.darkreading.com/rss.xml
                - 📰 **Security Week**: https://www.securityweek.com/feed/
                - 💻 **Bleeping Computer**: https://www.bleepingcomputer.com/feed/
                - 🔍 **Cyware Threat Intel**: https://cyware.com/news/feed
                
                **Note:** Manual refresh limits to 5 threats per feed for optimal performance
                """)
    
    return demo

if __name__ == "__main__":
    demo = create_dashboard()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True
    )
