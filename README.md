# Sentix Engine: Advanced Multi-Tier Hospitality Sentiment Analytics Platform

Sentix Engine is a high-performance, enterprise-grade Natural Language Processing (NLP) dashboard designed for hotel administration and hospitality governance. It transitions traditional sentiment analysis from simple lexicon lookups into a multi-dimensional analytics ecosystem, allowing stakeholders to track operational performance, evaluate aspect-specific valence shifts, and mitigate linguistic ironies in real-time.

### 🌐 Live Production Deployment
The application is fully compiled, containerized, and deployed in a production-ready cloud environment.
* **Live Dashboard URL:** [https://sentix-engine.onrender.com](https://sentix-engine.onrender.com)

---

## 🚀 Key Core Architectural Features

1. **Aspect-Specific Valence Scoring (Fine-Grained Sentiment)**
   * Utilizes NLTK clause tokenization to break apart multi-clause feedback loops.
   * Maps independent sentiment scores directly onto distinct operational layers (*Staff & Service, Cleanliness & Room, Food & Dining, Value & Price*) instead of relying on a flawed global average score.

2. **Linguistic Sarcasm Detection & Override Matrix**
   * Employs a custom rule-based heuristics matrix to analyze syntactic contrast shifts (e.g., immediate transitions from high positive sentiment tokens to destructive negative exclamations).
   * Automatically penalizes manipulated lexicon outputs to ensure strict compliance with high-confidence negative scoring models.

3. **Interactive Frontend Analytics Filters (Client-Side Telemetry)**
   * Built on a glassmorphic Single Page Application (SPA) design framework.
   * Features instant client-side rendering filters that let administrators segment data on the fly (*Operational Negatives, Specific Operational Aspects*) without initiating expensive server-side database reloads.

4. **Data Portability Engine & Automated CRM Pipeline**
   * Offers single-click dynamic database joins with a live `.csv` executive report exporter.
   * Features a context-aware automated CRM response generation module that auto-drafts targeted escalation emails based on the operational nodes flagged by the engine.

5. **Security Isolation Framework**
   * Features a custom, styled Tailwind CSS modal overlay replacing default browser alert layers.
   * Includes a dynamic, state-controlled data management interface that safely handles connection isolation pools and prevents database write-race conditions (`sqlite3.OperationalError: database is locked`).

---

## 📂 System Directory Structure

```text
guest-sentiment-analysis-dashboard/
│
├── app.py                  # Main Flask Controller, Endpoint Routing & Session Handlers
├── database.py             # SQLite3 Relational Data Persistence Layer & Context Pools
├── analyzer.py             # Hybrid NLP Ingestion Pipeline & Sarcasm Mitigation Rules
├── sentiment_analytics.db   # Relational Database Storage Ledger (Auto-generated)
│
├── requirements.txt        # Production System Dependency Manifest
│
└── templates/
    └── index.html          # SPA Glassmorphic User Interface & Chart.js Engine Integrations
