# Canvas Learning System

<p align="center">
  <strong>AI-Powered Learning Platform for Obsidian Canvas</strong><br/>
  Transform passive learning into active understanding using the Feynman Technique
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Obsidian-Plugin-7C3AED" alt="Obsidian Plugin"/>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/TypeScript-4.x-3178C6" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
</p>

<p align="center">
  <a href="https://github.com/oinani0721/canvas-learning-system/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=oinani0721/canvas-learning-system" alt="Contributors"/>
  </a>
</p>

---

## Overview

Canvas Learning System transforms **passive learning** into an **active learning process**. With 12-14 specialized AI Agents collaborating, it guides you from confusion to mastery through the Feynman Learning Method.

### Problems We Solve

- **Passive Consumption** - Reading/watching without active engagement
- **Illusion of Competence** - Familiarity mistaken for true understanding
- **Lack of Personalization** - One-size-fits-all learning approaches
- **No Systematic Verification** - No objective way to measure understanding

### Our Solution

- **Visual Learning** - Color-coded knowledge nodes on Obsidian Canvas
- **Forced Output** - Dedicated explanation spaces (yellow nodes)
- **Personalized Guidance** - 14 specialized AI Agents
- **Systematic Verification** - 4-dimension scoring system
- **Knowledge Graph** - Visual map that grows with your understanding

---

## Features

### Color-Coded Learning System

| Color | Code | Meaning |
|-------|------|---------|
| Red | 1 | Unknown concept - needs learning |
| Yellow | 6 | User explanation space - your understanding |
| Purple | 3 | Partial understanding - needs deepening |
| Green | 2 | Fully mastered |
| Blue | 5 | AI-generated content |

### 14 Specialized AI Agents

**Decomposition Agents**
- `basic-decomposition` - Break complex topics into 3-7 guiding questions
- `deep-decomposition` - Create deep verification questions
- `question-decomposition` - Generate breakthrough questions

**Explanation Agents**
- `oral-explanation` - Professor-style 800-1200 word oral explanations
- `clarification-path` - 1500+ word systematic explanations
- `comparison-table` - Structured comparison tables for similar concepts
- `memory-anchor` - Vivid analogies and memory anchors
- `four-level-explanation` - Progressive 4-level explanations
- `example-teaching` - Complete problem tutorials with solutions

**Assessment Agents**
- `scoring-agent` - 4-dimension understanding assessment
- `verification-question` - Deep understanding verification questions

### Review System (FSRS)

- Intelligent review based on Ebbinghaus forgetting curve
- Auto-generated review Canvas
- Progress tracking dashboard

---

## Installation

### Prerequisites

- [Obsidian](https://obsidian.md/) v1.0+
- Python 3.9+ (for backend)
- Node.js 18+ (for development)

### Obsidian Plugin Installation

**Method 1: From Release (Recommended)**

1. Download the latest [Release](https://github.com/oinani0721/canvas-learning-system/releases)
2. Extract `main.js` and `manifest.json`
3. Create folder `.obsidian/plugins/canvas-review-system/` in your Vault
4. Copy the files to that folder
5. Enable the plugin in Obsidian Settings > Community Plugins

**Method 2: Manual Build**

```bash
cd canvas-progress-tracker/obsidian-plugin
npm install
npm run build
# Copy main.js and manifest.json to your Vault's plugins folder
```

### Backend Service Installation

```bash
# Clone repository
git clone https://github.com/oinani0721/canvas-learning-system.git
cd canvas-learning-system/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment (Neo4j + Memory System)

#### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Ports available: `7475` (Neo4j HTTP), `7688` (Neo4j Bolt), `8000` (Backend API)
- Memory: ≥1GB available for Neo4j container

#### Step 1: Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` with the following critical settings:

```env
# IMPORTANT: Use port 7688, NOT the default 7687
NEO4J_URI=bolt://localhost:7688
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
```

> **Warning**: The password in `.env` and `docker-compose.yml` must match exactly. Mismatched passwords cause silent authentication failures.

#### Step 2: Start Services

```bash
# Start Neo4j container
docker-compose up -d neo4j

# Wait for Neo4j to initialize (~10 seconds)
# Then start the backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use the one-click startup script (Windows):
```bash
./start-canvas-services.bat
```

#### Step 3: Verify Deployment

```bash
# Neo4j Browser (note: port 7475, not 7474)
curl http://localhost:7475

# Backend health check
curl http://localhost:8000/api/v1/health

# Neo4j connection check
curl http://localhost:8000/api/v1/health/neo4j

# Storage health check
curl http://localhost:8000/api/v1/health/storage
```

#### Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Connection timeout | Wrong port in NEO4J_URI (7687 vs 7688) | Set `NEO4J_URI=bolt://localhost:7688` |
| Auth failure with no error | Password mismatch between .env and docker-compose | Ensure both passwords match |
| Queries return empty results | Silent fallback to JSON mode | Check logs for "JSON_FALLBACK" |
| Neo4j Browser won't open | Port mapping is 7475, not 7474 | Visit `http://localhost:7475` |
| Backend process orphaned | Obsidian didn't kill backend on exit | Fixed: uses execSync + taskkill |
| LanceDB path error | Incorrect relative path when running from backend/ | Fixed: normalized to project-relative paths |

---

## Quick Start

1. **Create a new Canvas** - Create a `.canvas` file in Obsidian
2. **Add red nodes** - Write concepts you don't understand
3. **Right-click to invoke Agent** - Select appropriate Agent for decomposition/explanation
4. **Explain in yellow nodes** - Use your own words to explain the concept
5. **Use scoring Agent** - Get 4-dimension understanding assessment
6. **Watch colors change** - Red > Purple > Green

---

## Project Structure

```
canvas-learning-system/
├── canvas-progress-tracker/
│   └── obsidian-plugin/          # Obsidian Plugin (TypeScript)
│       ├── src/                  # Source code
│       ├── main.js               # Build output
│       └── manifest.json         # Plugin manifest
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # REST API endpoints
│   │   ├── services/             # Business logic
│   │   └── models/               # Data models
│   └── requirements.txt
├── src/agentic_rag/              # LangGraph RAG system
├── docs/                         # Documentation
│   ├── prd/                      # Product requirements
│   └── architecture/             # Architecture design
└── specs/                        # OpenAPI specifications
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | TypeScript, Obsidian Plugin API |
| Backend | Python 3.9+, FastAPI |
| AI | Claude API (Anthropic) |
| Memory System | Graphiti + Neo4j |
| Vector Store | LanceDB |
| Deployment | Docker, Docker Compose |

---

## Recent Updates

### Memory System Health Checks
- `/api/v1/health/neo4j` - Neo4j connection status with async driver support
- `/api/v1/health/storage` - Unified storage health (LanceDB + Neo4j)
- Automatic retry with configurable timeouts for slow first connections

### Canvas Metadata Management (Story 38.1)
- Backend metadata API for canvas subject mapping
- Configurable subject resolver with YAML-based mapping
- Canvas info view in Obsidian plugin settings

### Bug Fixes
- **LanceDB data isolation**: Fixed path calculation that caused index/query to use different databases
- **Backend process cleanup**: Fixed orphaned uvicorn processes on Obsidian exit (execSync + taskkill)
- **Graphiti client**: Unified connection architecture with proper error handling

---

## API Documentation

After starting the backend service:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Development

```bash
# Plugin development
cd canvas-progress-tracker/obsidian-plugin
npm run dev

# Backend development
cd backend
uvicorn app.main:app --reload

# Run tests
cd backend && pytest
cd canvas-progress-tracker/obsidian-plugin && npm test
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Obsidian](https://obsidian.md/) - Powerful knowledge management tool
- Feynman Learning Method researchers

---

*"If you can't explain it simply, you don't understand it well enough." - Richard Feynman*
