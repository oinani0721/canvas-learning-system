"""
BMad Orchestrator CLI Entry Point

Usage:
    python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 15.3
    python -m bmad_orchestrator epic-status epic-15
    python -m bmad_orchestrator epic-resume epic-15
    python -m bmad_orchestrator epic-stop epic-15

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
