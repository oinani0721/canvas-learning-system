# Canvas Review System

AI-powered learning progress tracker for Obsidian, featuring FSRS-based spaced repetition scheduling and Canvas-based knowledge visualization.

## Features

- **FSRS Spaced Repetition** — Scientifically optimized review scheduling based on the Free Spaced Repetition Scheduler algorithm
- **Canvas Knowledge Graph** — Visualize learning progress directly on Obsidian Canvas with color-coded nodes
- **AI-Enhanced Learning** — Four-level explanations, adaptive difficulty, and intelligent hint generation
- **Cross-Canvas Association** — Automatically link related concepts across different Canvas files
- **Multimodal Support** — Attach images, audio, and video to learning nodes
- **Progress Analytics** — Track mastery over time with charts and statistics

## Requirements

This plugin connects to a **self-hosted Canvas Learning System backend** (FastAPI) for AI features and data persistence.

- **Obsidian** v0.15.0 or later
- **Backend API** — A running instance of the Canvas Learning System FastAPI server

> Without the backend, the plugin works in offline mode with limited functionality (local Canvas editing only).

## Installation

### From Community Plugins (Recommended)

1. Open **Settings** → **Community Plugins** → **Browse**
2. Search for "Canvas Review System"
3. Click **Install**, then **Enable**

### Manual Installation

1. Download `main.js`, `manifest.json`, and `styles.css` from the [latest release](https://github.com/canvas-learning-system/canvas-progress-tracker/releases)
2. Create folder: `<your-vault>/.obsidian/plugins/canvas-review-system/`
3. Copy the three files into this folder
4. Enable the plugin in **Settings** → **Community Plugins**

## Setup

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Configure the Plugin

1. Open **Settings** → **Canvas Review System**
2. Go to the **Connection** tab
3. Set the **API Server URL** (default: `http://localhost:8000`)
4. Click **Test Connection** to verify

### 3. Start Learning

1. Open or create a Canvas file
2. Right-click on a node → **Start Review**
3. The system will schedule reviews automatically based on your performance

## Settings

| Tab | Options |
|-----|---------|
| **Connection** | API URL, API Key, AI provider/model selection |
| **Storage** | Canvas base path, backup settings |
| **Interface** | Language, theme, notification preferences |
| **Review** | Daily review limit, minimum interval, difficulty weights |
| **Advanced** | Debug logging, cache size, timeout settings |

## Data & Privacy

- All data is sent to **your configured backend server** — no third-party services involved
- The plugin stores settings locally in your Obsidian vault
- Learning progress and review history are stored on your backend
- No data leaves your network unless you configure an external server

## Development

### Prerequisites

- Node.js 18+
- npm

### Local Development

```bash
# Clone and install
cd canvas-progress-tracker/obsidian-plugin
npm install

# Development mode (auto-compile + hot-reload)
npm run dev

# Production build
npm run build

# Deploy to vault + verify
npm run deploy

# Check vault freshness
npm run verify
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSIDIAN_VAULT` | Path to your test vault | Auto-detected from `../../笔记库/` |

### Project Structure

```
obsidian-plugin/
├── main.ts              — Plugin entry point
├── src/
│   ├── api/             — Backend API client
│   ├── settings/        — Settings tab UI
│   ├── views/           — Canvas info panels
│   ├── modals/          — Dialog components
│   ├── managers/        — State management
│   └── types/           — TypeScript type definitions
├── scripts/
│   ├── sync-vault.mjs   — Sync assets to vault
│   └── verify-vault.mjs — Verify vault freshness
└── esbuild.config.mjs   — Build configuration
```

## Support

- [Report Issues](https://github.com/canvas-learning-system/canvas-progress-tracker/issues)
- [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE)
