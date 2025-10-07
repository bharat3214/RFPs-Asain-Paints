# RFP AI - Multi-Agent System for B2B RFP Response Automation

This project implements a multi-agent AI system to automate the B2B RFP (Request for Proposal) response process for industrial manufacturers.

## Overview

The system consists of four main agents:
- **Sales Agent**: Scans URLs for RFPs, identifies those due within 3 months
- **Technical Agent**: Matches RFP requirements to product SKUs with spec matching
- **Pricing Agent**: Calculates material and service costs
- **Master Agent**: Orchestrates the entire process and consolidates responses

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the system:
```bash
python main.py
```

## Project Structure

```
rfp_ai/
├── main.py                 # Main application entry point
├── Agents/                 # Agent implementations
│   ├── master_agent.py     # Master orchestrator agent
│   ├── sales_agent.py      # Sales agent for RFP scanning
│   ├── technical_agent.py  # Technical agent for product matching
│   └── pricing_agent.py    # Pricing agent for cost calculation
├── data/                   # Data files and configurations
│   ├── rfps.json          # Sample RFP data
│   ├── products.json      # Product specifications database
│   ├── pricing.json       # Pricing tables
│   └── test_requirements.json  # Test and service requirements
├── models/                 # Data models and schemas
│   └── __init__.py
└── utils/                  # Utility functions
    └── __init__.py
```

## Features

- Automated RFP scanning and identification
- Intelligent product-to-requirement matching with similarity scores
- Automated pricing calculation including material and service costs
- Consolidated RFP response generation
- Terminal-based interface for easy monitoring

## Configuration

The system uses synthetic data for demonstration purposes. In a production environment, you would connect to:
- Real RFP scanning URLs
- Product database APIs
- Pricing systems
- OpenAI API for enhanced AI capabilities