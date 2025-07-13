"""
Gradio-based web dashboard for the AI-Powered Threat Intelligence Aggregator
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json
import os

# Import your services (these will give import errors until packages are installed)
try:
    from app.core.database import get_db, init_database
    from app.models.database import Threat, IOC, Feed, ThreatAnalysis
    from app.core.llm_service import get_llm_service
    from sqlalchemy.orm import Session
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Database not available - using demo mode")


class ThreatIntelDashboard:
    """Main dashboard class for the threat intelligence aggregator"""
    
    def __init__(self):
        self.llm_service = get_llm_service() if DATABASE_AVAILABLE else None
        
    def get_dashboard_stats(self) -> Dict:
        """Get high-level statistics for dashboard"""
        if not DATABASE_AVAILABLE:
            return {
                "total_threats": 1234,
                "total_iocs": 5678,
                "active_feeds": 25,
                "critical_threats": 12
            }
        
        # Real database queries would go here
        db = next(get_db())
        try:
            stats = {
                "total_threats": db.query(Threat).count(),
                "total_iocs": db.query(IOC).count(),
                "active_feeds": db.query(Feed).filter(Feed.status == "active").count(),
                "critical_threats": db.query(ThreatAnalysis).filter(
                    ThreatAnalysis.severity_level == "critical"
                ).count()
            }
            return stats
        finally:
            db.close()
    
    def get_recent_threats(self, limit: int = 10) -> pd.DataFrame:
        """Get recent threats as DataFrame"""
        if not DATABASE_AVAILABLE:
            # Demo data
            demo_data = [
                {
                    "title": "New APT29 Campaign Targeting Government Agencies",
                    "threat_type": "APT",
                    "severity": "Critical",
                    "published_date": "2025-07-12 10:30:00",
                    "source": "CyberScoop",
                    "ioc_count": 23
                },
                {
                    "title": "Ransomware Group Exploiting Exchange Vulnerabilities",
                    "threat_type": "Ransomware",
                    "severity": "High",
                    "published_date": "2025-07-12 08:15:00",
                    "source": "Bleeping Computer",
                    "ioc_count": 15
                },
                {
                    "title": "Phishing Campaign Targeting Financial Institutions",
                    "threat_type": "Phishing",
                    "severity": "Medium",
                    "published_date": "2025-07-12 06:45:00",
                    "source": "KrebsOnSecurity",
                    "ioc_count": 8
                }
            ]
            return pd.DataFrame(demo_data)
        
        # Real database query would go here
        return pd.DataFrame()
    
    def search_threats(self, query: str, threat_type: str = "All") -> pd.DataFrame:
        """Search threats based on query and filters"""
        df = self.get_recent_threats(50)  # Get more data for searching
        
        if query:
            mask = df['title'].str.contains(query, case=False, na=False)
            df = df[mask]
        
        if threat_type != "All":
            df = df[df['threat_type'] == threat_type]
        
        return df
    
    def get_threat_trends(self) -> go.Figure:
        """Generate threat trends chart"""
        # Demo data for visualization
        dates = pd.date_range(start='2025-07-01', end='2025-07-12', freq='D')
        threat_counts = [15, 23, 18, 31, 27, 19, 34, 28, 25, 30, 22, 26]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=threat_counts,
            mode='lines+markers',
            name='Daily Threats',
            line=dict(color='#ff6b6b', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Threat Detection Trends (Last 12 Days)",
            xaxis_title="Date",
            yaxis_title="Number of Threats",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    def get_ioc_distribution(self) -> go.Figure:
        """Generate IOC type distribution chart"""
        # Demo data
        ioc_types = ['IP Address', 'Domain', 'URL', 'File Hash', 'Email']
        counts = [245, 189, 156, 123, 87]
        
        fig = px.pie(
            values=counts,
            names=ioc_types,
            title="IOC Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(height=400)
        return fig
    
    def analyze_text_with_ai(self, text: str) -> Dict:
        """Analyze text using AI service"""
        if not self.llm_service or not self.llm_service.is_available():
            return {
                "summary": "AI service not available",
                "threat_type": "unknown",
                "severity": "medium",
                "recommendations": ["Manual analysis required"]
            }
        
        result = self.llm_service.summarize_threat("User Input", text)
        return result


def create_dashboard():
    """Create and configure the Gradio dashboard"""
    
    dashboard = ThreatIntelDashboard()
    
    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px;
        margin: auto;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px;
    }
    .threat-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: #f9f9f9;
    }
    """
    
    with gr.Blocks(css=css, title="AI Threat Intel Aggregator") as demo:
        
        gr.Markdown("""
        # 🛡️ AI-Powered Threat Intelligence Aggregator
        
        Real-time monitoring and analysis of cybersecurity threats from multiple sources
        """)
        
        # Dashboard Stats Row
        with gr.Row():
            stats = dashboard.get_dashboard_stats()
            
            with gr.Column():
                gr.Markdown(f"""
                <div class="metric-box">
                    <h3>{stats['total_threats']}</h3>
                    <p>Total Threats</p>
                </div>
                """)
            
            with gr.Column():
                gr.Markdown(f"""
                <div class="metric-box">
                    <h3>{stats['total_iocs']}</h3>
                    <p>IOCs Extracted</p>
                </div>
                """)
            
            with gr.Column():
                gr.Markdown(f"""
                <div class="metric-box">
                    <h3>{stats['active_feeds']}</h3>
                    <p>Active Feeds</p>
                </div>
                """)
            
            with gr.Column():
                gr.Markdown(f"""
                <div class="metric-box">
                    <h3>{stats['critical_threats']}</h3>
                    <p>Critical Threats</p>
                </div>
                """)
        
        # Main Content Tabs
        with gr.Tab("📊 Dashboard"):
            with gr.Row():
                with gr.Column():
                    threat_trends = gr.Plot(dashboard.get_threat_trends())
                with gr.Column():
                    ioc_distribution = gr.Plot(dashboard.get_ioc_distribution())
            
            # Recent Threats Table
            gr.Markdown("## 🔥 Recent Threats")
            recent_threats_df = gr.DataFrame(
                dashboard.get_recent_threats(),
                headers=["Title", "Type", "Severity", "Date", "Source", "IOCs"],
                wrap=True
            )
        
        with gr.Tab("🔍 Threat Search"):
            gr.Markdown("## Search Threat Intelligence")
            
            with gr.Row():
                search_query = gr.Textbox(
                    label="Search Query",
                    placeholder="Enter keywords to search threats..."
                )
                threat_type_filter = gr.Dropdown(
                    choices=["All", "APT", "Malware", "Phishing", "Ransomware", "Vulnerability"],
                    value="All",
                    label="Threat Type"
                )
                search_btn = gr.Button("🔍 Search", variant="primary")
            
            search_results = gr.DataFrame(
                headers=["Title", "Type", "Severity", "Date", "Source", "IOCs"]
            )
            
            def perform_search(query, threat_type):
                return dashboard.search_threats(query, threat_type)
            
            search_btn.click(
                perform_search,
                inputs=[search_query, threat_type_filter],
                outputs=[search_results]
            )
        
        with gr.Tab("🤖 AI Analysis"):
            gr.Markdown("## AI-Powered Threat Analysis")
            gr.Markdown("Paste threat intelligence content below for AI analysis")
            
            with gr.Row():
                with gr.Column():
                    analysis_input = gr.Textbox(
                        label="Threat Content",
                        placeholder="Paste threat intelligence article, report, or IOCs here...",
                        lines=10
                    )
                    analyze_btn = gr.Button("🧠 Analyze with AI", variant="primary")
                
                with gr.Column():
                    analysis_output = gr.JSON(label="AI Analysis Results")
            
            def analyze_content(text):
                if not text.strip():
                    return {"error": "Please provide content to analyze"}
                return dashboard.analyze_text_with_ai(text)
            
            analyze_btn.click(
                analyze_content,
                inputs=[analysis_input],
                outputs=[analysis_output]
            )
        
        with gr.Tab("📡 Feed Management"):
            gr.Markdown("## RSS/Atom Feed Sources")
            
            # This would show feed management interface
            gr.Markdown("""
            **Active Feeds:**
            - 🟢 Krebs on Security (Last updated: 2 minutes ago)
            - 🟢 SANS ISC (Last updated: 5 minutes ago)
            - 🟢 Threat Post (Last updated: 8 minutes ago)
            - 🟡 Malware Traffic Analysis (Last updated: 15 minutes ago)
            - 🔴 Dark Web Monitor (Error: Connection timeout)
            """)
            
            with gr.Row():
                new_feed_url = gr.Textbox(label="Add New Feed URL")
                add_feed_btn = gr.Button("➕ Add Feed")
        
        with gr.Tab("📈 Analytics"):
            gr.Markdown("## Threat Intelligence Analytics")
            
            # Placeholder for advanced analytics
            gr.Markdown("""
            ### 📊 Weekly Threat Summary
            - **Total Threats Processed:** 1,247
            - **Most Common Threat Type:** Malware (34%)
            - **Top Targeted Industries:** Finance, Healthcare, Government
            - **Peak Activity Hours:** 14:00-16:00 UTC
            
            ### 🎯 IOC Statistics
            - **New IOCs This Week:** 3,456
            - **High Confidence IOCs:** 2,134 (62%)
            - **False Positives Identified:** 89 (2.6%)
            
            ### 🚨 Critical Alerts
            - 🔴 APT29 infrastructure changes detected
            - 🟡 New ransomware variant signatures available
            - 🟢 All feeds operational
            """)
    
    return demo


if __name__ == "__main__":
    # Initialize database if available
    if DATABASE_AVAILABLE:
        try:
            init_database()
        except Exception as e:
            print(f"Database initialization failed: {e}")
    
    # Create and launch dashboard
    demo = create_dashboard()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
