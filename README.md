<div align="center">

# 🛡️ AI-ThreatIngestor

**AI-Powered Threat Intelligence Feed Aggregator**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Transform raw threat data into actionable intelligence using Large Language Models

</div>

---

## Overview

**AI-ThreatIngestor** is a comprehensive threat intelligence platform that aggregates, analyzes, and visualizes cybersecurity threats using advanced AI capabilities. Built with modern LLM integration, it transforms raw threat feeds into actionable intelligence through automated analysis, IOC extraction, and intelligent summarization.

### Key Capabilities

- **AI-Powered Analysis** - Leverages Ollama LLMs for intelligent threat summarization
- **Real-Time Processing** - Continuous threat feed monitoring with instant updates  
- **Smart IOC Extraction** - Automatically identifies IPs, domains, hashes, CVEs, and more
- **Interactive Dashboard** - Modern Gradio-based interface for threat visualization
- **Docker Ready** - One-command deployment with full environment isolation
- **Integration Friendly** - STIX/TAXII support, MISP integration, and RESTful APIs

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Ollama AI service
- 8GB+ RAM (for LLM processing)
- 50GB+ storage (for threat data)

### Installation

**1. Clone the Repository**

```bash
git clone https://github.com/TarunB1006/AI-ThreatIngestor.git
cd AI-ThreatIngestor
```

**2. Set Up Python Environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**3. Install Ollama**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

**4. Start Ollama and Pull a Model**

```bash
ollama serve &
ollama pull tinyllama   # Or: ollama pull llama2
```

**5. Initialize the Database**

> **Important:** This step creates the required database schema and tables.

```bash
python populate_db.py
```

**6. Launch the Dashboard**

```bash
python simple_dashboard.py
```

Visit **http://localhost:7862** in your browser

---

## Docker Setup

Docker provides a reproducible, isolated environment with all dependencies pre-configured.

### Production Deployment

```bash
docker-compose up -d threatingestor-prod
```

Dashboard: http://localhost:7862

### Development Mode

```bash
docker-compose --profile dev up -d threatingestor-dev
```

Dashboard: http://localhost:7863

**Note:** The Docker container automatically initializes the database and configures Ollama.

---

## Technical Stack

**Backend**
- Python 3.8+
- SQLite/PostgreSQL for data storage
- Ollama for LLM integration
- FastAPI (optional, for API endpoints)

**Frontend**
- Gradio for rapid prototyping and dashboard
- Custom CSS for professional styling
- Chart.js/Plotly for visualizations

**AI/ML**
- Ollama (LLaMA 2, Mistral, CodeLlama, TinyLlama)
- Custom prompt engineering
- Threat classification models

---

## Project Structure

```
AI-ThreatIngestor/
│
├── app/
│   ├── core/
│   │   ├── database.py          # Database management
│   │   ├── llm_service.py       # AI/LLM integration
│   │   └── config.py            # Configuration
│   │
│   ├── models/
│   │   ├── threat.py            # Threat data models
│   │   ├── ioc.py               # IOC models
│   │   └── summary.py           # Summary models
│   │
│   ├── services/
│   │   ├── feed_processor.py    # Feed aggregation
│   │   ├── ioc_extractor.py     # IOC extraction
│   │   ├── summarizer.py        # AI summarization
│   │   └── analyzer.py          # Threat analysis
│   │
│   ├── api/
│   │   ├── endpoints/           # REST API endpoints
│   │   └── dependencies.py      # API dependencies
│   │
│   └── ui/
│       ├── dashboard.py         # Main dashboard
│       ├── components/          # UI components
│       └── static/              # Static assets
│
├── threatingestor/              # Original ThreatIngestor code
├── data/                        # Data storage
├── configs/                     # Configuration files
├── tests/                       # Test suites
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker configuration
└── README.md                    # This file
```

---

## Features

### AI Capabilities
- Intelligent threat summarization
- Automated severity scoring
- TTP extraction and classification
- Threat actor identification
- Actionable recommendations

### Security Intelligence
- Aggregation from 20+ threat feed sources
- Multi-format IOC extraction (IPs, domains, hashes, CVEs)
- CVE vulnerability tracking
- Real-time alert system
- Historical trend analysis

### Dashboard
- Real-time threat monitoring
- Advanced search and filtering
- Export functionality (CSV, JSON, STIX)
- Custom visualizations
- Feed management interface

### Integrations
- MISP threat sharing platform
- STIX/TAXII format support
- RESTful API endpoints
- Webhook notifications
- GitHub threat repositories

---

## Performance Metrics

### Functional Requirements
- Aggregate 20+ threat intel sources
- Extract and classify 1000+ IOCs daily
- Generate AI summaries for all threat reports
- Provide sub-second search across historical data
- Support real-time dashboard updates

### Performance Requirements
- Process feeds every 10 seconds
- Generate summaries within 30 seconds
- Support 10+ concurrent users
- 99% uptime for dashboard

---

## System Requirements

**Development Tools**
- Python 3.8+
- Ollama installation
- SQLite/PostgreSQL
- Git for version control

**External Services**
- GitHub API token (optional)
- RSS feed endpoints
- MISP instance (optional)

**Hardware Requirements**
- 8GB+ RAM for LLM processing
- 50GB+ storage for threat data
- Multi-core CPU recommended

---

## Future Work

- Advanced trend analysis and prediction models
- Custom LLM fine-tuning for threat intelligence
- Multi-language threat feed support
- Enhanced visualization dashboards
- Mobile-responsive interface
- Cloud deployment templates (AWS, Azure, GCP)
- Kubernetes orchestration support
- Advanced alerting with integrations (Slack, PagerDuty)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built using [Ollama](https://ollama.ai/)
- Dashboard powered by [Gradio](https://gradio.app/)
- Inspired by the cybersecurity community
