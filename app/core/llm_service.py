"""
LLM Service for AI-powered threat analysis using Ollama
"""

import json
import time
import requests
from typing import Dict, List, Optional
from loguru import logger


class OllamaLLMService:
    """Service for interacting with Ollama local LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "tinyllama"):
        self.base_url = base_url
        self.model = model
        self.timeout = 60  # Increased timeout for better success rate
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate response from LLM"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None
    
    def summarize_threat(self, title: str, content: str) -> Dict:
        """Generate AI summary of a threat intelligence article"""
        
        prompt = f"""
Analyze this cybersecurity threat in 2-3 sentences:

Title: {title}
Content: {content[:1000]}

Respond ONLY with JSON:
{{
    "summary": "Brief 2-3 sentence summary",
    "threat_type": "malware",
    "severity": "high",
    "key_points": ["Point 1", "Point 2"],
    "recommendations": ["Action 1", "Action 2"]
}}
"""
        
        start_time = time.time()
        response = self.generate_response(prompt)
        processing_time = time.time() - start_time
        
        if not response:
            return self._get_fallback_analysis(title, content, processing_time)
        
        try:
            # Extract JSON from response (LLM might include extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                analysis = json.loads(json_str)
                analysis['processing_time'] = processing_time
                analysis['model_used'] = self.model
                return analysis
            else:
                logger.warning("Could not extract JSON from LLM response")
                return self._get_fallback_analysis(title, content, processing_time)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            return self._get_fallback_analysis(title, content, processing_time)
    
    def _get_fallback_analysis(self, title: str, content: str, processing_time: float) -> Dict:
        """Provide fallback analysis when LLM fails"""
        
        # Simple keyword-based classification
        content_lower = (title + " " + content).lower()
        
        threat_type = "other"
        severity = "medium"
        
        # Basic threat type detection
        if any(word in content_lower for word in ["malware", "virus", "trojan", "backdoor"]):
            threat_type = "malware"
            severity = "high"
        elif any(word in content_lower for word in ["phishing", "phish", "scam"]):
            threat_type = "phishing"
            severity = "medium"
        elif any(word in content_lower for word in ["vulnerability", "cve-", "exploit"]):
            threat_type = "vulnerability"
            severity = "high"
        elif any(word in content_lower for word in ["ransomware", "ransom"]):
            threat_type = "ransomware"
            severity = "critical"
        elif any(word in content_lower for word in ["breach", "leak", "exposed"]):
            threat_type = "data_breach"
            severity = "high"
        
        return {
            "summary": f"Threat intelligence report: {title[:100]}...",
            "threat_type": threat_type,
            "severity": severity,
            "key_points": ["Analysis unavailable - LLM service offline"],
            "threat_actors": [],
            "affected_systems": [],
            "iocs_mentioned": [],
            "recommendations": ["Review article manually", "Monitor for IOCs"],
            "urgency": "medium",
            "processing_time": processing_time,
            "model_used": "fallback_analysis",
            "confidence_score": 0.3
        }
    
    def classify_ioc(self, ioc_value: str, ioc_type: str, context: str = "") -> Dict:
        """Classify and analyze an IOC"""
        
        prompt = f"""
You are a cybersecurity analyst. Analyze the following Indicator of Compromise (IOC):

IOC Type: {ioc_type}
IOC Value: {ioc_value}
Context: {context[:500]}

Provide a JSON response with:
{{
    "is_malicious": true/false,
    "confidence": 0.0-1.0,
    "threat_category": "malware|phishing|c2|scanning|legitimate|unknown",
    "risk_level": "low|medium|high|critical",
    "notes": "Brief explanation of the assessment"
}}
"""
        
        response = self.generate_response(prompt)
        
        if not response:
            return {
                "is_malicious": True,  # Conservative default
                "confidence": 0.5,
                "threat_category": "unknown",
                "risk_level": "medium",
                "notes": "Analysis unavailable"
            }
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.error(f"Error parsing IOC classification: {e}")
        
        return {
            "is_malicious": True,
            "confidence": 0.5,
            "threat_category": "unknown",
            "risk_level": "medium",
            "notes": "Parse error"
        }


# Global LLM service instance
llm_service = OllamaLLMService()


def get_llm_service() -> OllamaLLMService:
    """Get the global LLM service instance"""
    return llm_service
