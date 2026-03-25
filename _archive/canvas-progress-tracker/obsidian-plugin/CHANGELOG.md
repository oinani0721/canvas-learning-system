# Changelog

All notable changes to the Canvas Review System plugin will be documented in this file.

## [1.0.1] - 2026-02-10

### Added
- Memory Query Service — 3-layer memory integration (local + Neo4j + Graphiti)
- FSRS State Query Service — backend-synced review scheduling
- Today Review List Service — daily review queue with caching
- Verification History Service — track verification attempts
- Node Color Change Watcher — real-time node status monitoring
- Canvas Edge sync to Neo4j knowledge graph (EPIC-36)
- Storage health check endpoint integration
- Deploy/verify scripts for vault sync automation

### Changed
- esbuild config now outputs directly to vault (auto-detected or via OBSIDIAN_VAULT env)
- Added hot-reload support with `.hotreload` marker file
- Improved API client retry strategy with exponential backoff

### Fixed
- Node-level concurrent request queue deadlock
- GroupPreviewModal performance with large canvas files

## [1.0.0] - 2026-01-01

### Initial Release
- Canvas-based review management
- Ebbinghaus/FSRS spaced repetition scheduling
- Four-level intelligent explanations
- Adaptive difficulty adjustment
- Cross-Canvas concept association
- Learning progress visualization with Chart.js
- Configurable backend API connection
- Multi-tab settings panel (Connection, Storage, Interface, Review, Advanced)
