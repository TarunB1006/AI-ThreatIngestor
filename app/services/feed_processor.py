"""
Enhanced feed processing service for the AI-Powered Threat Intelligence Aggregator
"""

import feedparser
import requests
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from loguru import logger
import re
from urllib.parse import urljoin, urlparse

# Import your existing ThreatIngestor components
try:
    from threatingestor.sources.rss import Plugin as RSSPlugin
    from threatingestor.artifacts import Artifact
    THREATINGESTOR_AVAILABLE = True
except ImportError:
    THREATINGESTOR_AVAILABLE = False
    logger.warning("ThreatIngestor not available - using standalone mode")


class EnhancedFeedProcessor:
    """Enhanced feed processor with AI integration"""
    
    def __init__(self, llm_service=None, db_session=None):
        self.llm_service = llm_service
        self.db_session = db_session
        self.user_agent = "AI-ThreatIntel-Aggregator/1.0"
        
        # Enhanced IOC extraction patterns
        self.ioc_patterns = {
            'ip': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'  # IPv6
            ],
            'domain': [
                r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b'
            ],
            'url': [
                r'https?://[^\s<>"{}|\\^`\[\]]+',
                r'ftp://[^\s<>"{}|\\^`\[\]]+',
                r'hxxps?://[^\s<>"{}|\\^`\[\]]+'  # Defanged URLs
            ],
            'hash_md5': [
                r'\b[a-fA-F0-9]{32}\b'
            ],
            'hash_sha1': [
                r'\b[a-fA-F0-9]{40}\b'
            ],
            'hash_sha256': [
                r'\b[a-fA-F0-9]{64}\b'
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'cve': [
                r'CVE-\d{4}-\d{4,7}'
            ],
            'bitcoin': [
                r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',  # Bitcoin addresses
                r'\bbc1[a-z0-9]{39,59}\b'  # Bech32 addresses
            ]
        }
    
    def fetch_feed(self, feed_url: str, last_updated: Optional[datetime] = None) -> List[Dict]:
        """Fetch and parse RSS/Atom feed"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'
            }
            
            # Add conditional request headers if we have last updated time
            if last_updated:
                headers['If-Modified-Since'] = last_updated.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            logger.info(f"Fetching feed: {feed_url}")
            response = requests.get(feed_url, headers=headers, timeout=30)
            
            if response.status_code == 304:
                logger.info(f"Feed not modified: {feed_url}")
                return []
            
            if response.status_code != 200:
                logger.error(f"Feed fetch failed: {feed_url} - Status: {response.status_code}")
                return []
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries:
                processed_entry = self._process_feed_entry(entry, feed_url)
                if processed_entry:
                    entries.append(processed_entry)
            
            logger.info(f"Processed {len(entries)} entries from {feed_url}")
            return entries
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def _process_feed_entry(self, entry, feed_url: str) -> Optional[Dict]:
        """Process individual feed entry"""
        try:
            # Extract basic information
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '')
            description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
            author = getattr(entry, 'author', '')
            
            # Parse publication date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            
            # Get full content if available
            content = description
            if hasattr(entry, 'content') and entry.content:
                content = ' '.join([c.value for c in entry.content if hasattr(c, 'value')])
            elif hasattr(entry, 'summary_detail') and entry.summary_detail:
                content = entry.summary_detail.value
            
            # Clean up HTML tags from content
            content = self._clean_html(content)
            
            return {
                'title': title,
                'url': link,
                'description': description,
                'content': content,
                'author': author,
                'published_date': published_date,
                'source_feed': feed_url
            }
            
        except Exception as e:
            logger.error(f"Error processing feed entry: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        import html
        text = html.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_iocs(self, text: str) -> Dict[str, List[Dict]]:
        """Extract IOCs from text using enhanced patterns"""
        iocs = {}
        
        for ioc_type, patterns in self.ioc_patterns.items():
            iocs[ioc_type] = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    ioc_value = match.group()
                    
                    # Basic validation
                    if self._is_valid_ioc(ioc_value, ioc_type):
                        # Get context around the IOC
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].strip()
                        
                        ioc_data = {
                            'value': ioc_value,
                            'type': ioc_type,
                            'context': context,
                            'position': match.start(),
                            'confidence': self._calculate_ioc_confidence(ioc_value, ioc_type, context)
                        }
                        
                        # Avoid duplicates
                        if not any(existing['value'] == ioc_value for existing in iocs[ioc_type]):
                            iocs[ioc_type].append(ioc_data)
        
        return iocs
    
    def _is_valid_ioc(self, value: str, ioc_type: str) -> bool:
        """Validate IOC based on type"""
        if ioc_type == 'ip':
            try:
                import ipaddress
                ip = ipaddress.ip_address(value)
                # Filter out private/local IPs for threat intel
                return not (ip.is_private or ip.is_loopback or ip.is_link_local)
            except:
                return False
        
        elif ioc_type == 'domain':
            # Basic domain validation
            parts = value.split('.')
            if len(parts) < 2:
                return False
            # Check for common false positives
            false_positives = ['example.com', 'test.com', 'localhost', 'www.w3.org']
            return value.lower() not in false_positives
        
        elif ioc_type in ['hash_md5', 'hash_sha1', 'hash_sha256']:
            # Validate hash format
            expected_lengths = {'hash_md5': 32, 'hash_sha1': 40, 'hash_sha256': 64}
            return len(value) == expected_lengths[ioc_type] and value.isalnum()
        
        elif ioc_type == 'email':
            # Basic email validation
            return '@' in value and '.' in value.split('@')[1]
        
        return True
    
    def _calculate_ioc_confidence(self, value: str, ioc_type: str, context: str) -> float:
        """Calculate confidence score for IOC"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on context keywords
        threat_keywords = [
            'malware', 'malicious', 'threat', 'attack', 'compromise', 'exploit',
            'phishing', 'scam', 'fraud', 'suspicious', 'blacklist', 'c2', 'c&c'
        ]
        
        context_lower = context.lower()
        keyword_matches = sum(1 for keyword in threat_keywords if keyword in context_lower)
        confidence += min(0.3, keyword_matches * 0.1)
        
        # Adjust based on IOC type
        if ioc_type == 'hash_sha256':
            confidence += 0.1  # SHA256 hashes are more reliable
        elif ioc_type == 'cve':
            confidence += 0.2  # CVEs are highly reliable
        
        # Decrease confidence for common domains/IPs
        if ioc_type in ['domain', 'ip']:
            common_patterns = ['google', 'microsoft', 'amazon', 'cloudflare']
            if any(pattern in value.lower() for pattern in common_patterns):
                confidence -= 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def process_threat_with_ai(self, threat_data: Dict) -> Dict:
        """Process threat data with AI analysis"""
        if not self.llm_service:
            return threat_data
        
        try:
            # Generate AI analysis
            ai_analysis = self.llm_service.summarize_threat(
                threat_data['title'],
                threat_data['content']
            )
            
            # Merge AI analysis with threat data
            threat_data.update({
                'ai_summary': ai_analysis.get('summary', ''),
                'threat_type': ai_analysis.get('threat_type', 'unknown'),
                'severity': ai_analysis.get('severity', 'medium'),
                'key_points': ai_analysis.get('key_points', []),
                'recommendations': ai_analysis.get('recommendations', []),
                'ai_confidence': ai_analysis.get('confidence_score', 0.5)
            })
            
            logger.info(f"AI analysis completed for: {threat_data['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            threat_data.update({
                'ai_summary': 'AI analysis unavailable',
                'threat_type': 'unknown',
                'severity': 'medium'
            })
        
        return threat_data
    
    def process_single_feed(self, feed_url: str, feed_name: str = None) -> List[Dict]:
        """Process a single feed end-to-end"""
        logger.info(f"Processing feed: {feed_name or feed_url}")
        
        # Fetch feed entries
        entries = self.fetch_feed(feed_url)
        
        processed_threats = []
        for entry in entries:
            try:
                # Extract IOCs
                iocs = self.extract_iocs(entry['content'])
                entry['iocs'] = iocs
                entry['ioc_count'] = sum(len(ioc_list) for ioc_list in iocs.values())
                
                # Process with AI if available
                if self.llm_service and self.llm_service.is_available():
                    entry = self.process_threat_with_ai(entry)
                
                processed_threats.append(entry)
                
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
        
        logger.info(f"Processed {len(processed_threats)} threats from {feed_name or feed_url}")
        return processed_threats


def demo_feed_processing():
    """Demo function to test feed processing"""
    processor = EnhancedFeedProcessor()
    
    # Test feeds
    test_feeds = [
        ("https://krebsonsecurity.com/feed/", "Krebs on Security"),
        ("https://www.schneier.com/feed/", "Schneier on Security"),
        ("https://isc.sans.edu/rssfeed.xml", "SANS ISC")
    ]
    
    for feed_url, feed_name in test_feeds:
        print(f"\n{'='*60}")
        print(f"Processing: {feed_name}")
        print(f"URL: {feed_url}")
        print('='*60)
        
        threats = processor.process_single_feed(feed_url, feed_name)
        
        for i, threat in enumerate(threats[:3]):  # Show first 3
            print(f"\n--- Threat {i+1} ---")
            print(f"Title: {threat['title']}")
            print(f"URL: {threat['url']}")
            print(f"IOC Count: {threat['ioc_count']}")
            
            if threat['iocs']:
                for ioc_type, ioc_list in threat['iocs'].items():
                    if ioc_list:
                        print(f"{ioc_type.upper()}: {len(ioc_list)} found")
                        for ioc in ioc_list[:2]:  # Show first 2 of each type
                            print(f"  - {ioc['value']} (confidence: {ioc['confidence']:.2f})")


if __name__ == "__main__":
    demo_feed_processing()
