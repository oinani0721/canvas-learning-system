"""
Story Harness - Anthropic-style long-running agent harness for BMad workflow.

Based on Anthropic's official harness pattern:
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Components:
- harness_progress.py: Progress persistence and crash recovery
- story_harness.py: Main 24/7 loop with CommitGate integration
"""

from .harness_progress import HarnessProgress, StoryProgress, GateResult
from .story_harness import StoryHarness

__all__ = [
    'HarnessProgress',
    'StoryProgress',
    'GateResult',
    'StoryHarness',
]
