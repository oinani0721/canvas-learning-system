"""
Linear Session Spawner - Manage Claude CLI session lifecycle.

Spawns Claude Code sessions with the full Dev+QA+Git workflow prompt.
Based on qa_spawner.py architecture.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, IO
from datetime import datetime


class LinearSessionSpawner:
    """
    Spawns and manages Claude CLI sessions for linear development.

    Each session executes the complete Dev→QA→Git workflow for a single Story.
    """

    # Full Dev+QA+Git workflow prompt template (from parallel-develop-auto.ps1)
    PROMPT_TEMPLATE = '''Execute complete Dev→QA→Git workflow for Story {story_id}.
{ultrathink_section}

===============================================================================
STRICT WORKFLOW RULES - MUST FOLLOW EXACTLY
===============================================================================
1. ALWAYS read .ai-context.md first
2. HALT immediately if tests fail - do NOT proceed to QA
3. HALT immediately if QA Gate = FAIL - do NOT commit
4. If QA Gate = CONCERNS: attempt 1 fix cycle, re-run gate, then decide
5. ONLY commit if QA Gate = PASS or WAIVED
6. ALWAYS write .worktree-result.json at workflow end

===============================================================================
PHASE 1: DEVELOPMENT
===============================================================================
Step 1: Read .ai-context.md to understand Story context
Step 2: Activate Developer Agent: /dev
Step 3: Implement the Story: *develop-story {story_id}
Step 4: Run all tests: *run-tests

**DECISION POINT A - TEST RESULTS**:
- If ALL tests PASS:
  - Update .worktree-status.yaml: status="dev-complete", tests_passed=true
  - PROCEED to Phase 2
- If ANY test FAILS:
  - Update .worktree-status.yaml: status="dev-blocked", tests_passed=false
  - Write .worktree-result.json with outcome="DEV_BLOCKED"
  - HALT WORKFLOW HERE - Do not proceed to QA

===============================================================================
PHASE 2: QUALITY ASSURANCE (Full QA Sequence)
===============================================================================
Step 5: Activate QA Agent: /qa
Step 6: Trace requirements coverage: *trace {story_id}
Step 7: Assess non-functional requirements: *nfr-assess {story_id}
Step 8: Comprehensive code review: *review {story_id}
Step 9: Quality gate decision: *gate {story_id}

**DECISION POINT B - QA GATE RESULT**:
- If gate = PASS:
  - Update .worktree-status.yaml: status="ready-to-merge", qa_gate="PASS"
  - PROCEED to Phase 3
- If gate = WAIVED:
  - Update .worktree-status.yaml: status="ready-to-merge", qa_gate="WAIVED"
  - PROCEED to Phase 3
- If gate = CONCERNS:
  - Attempt to fix the identified issues
  - Re-run tests: *run-tests
  - Re-run gate: *gate {story_id}
  - If now PASS/WAIVED: PROCEED to Phase 3
  - If still CONCERNS or FAIL after 1 fix attempt:
    - Update status: qa_gate="CONCERNS"
    - Write .worktree-result.json with outcome="QA_CONCERNS_UNFIXED"
    - HALT WORKFLOW HERE
- If gate = FAIL:
  - Update .worktree-status.yaml: status="qa-blocked", qa_gate="FAIL"
  - Write .worktree-result.json with outcome="QA_BLOCKED"
  - HALT WORKFLOW HERE - Do not commit

===============================================================================
PHASE 3: GIT COMMIT (Only if QA Gate = PASS or WAIVED)
===============================================================================
Step 10: Stage all changes: git add -A
Step 11: Create commit with structured message:
         git commit -m "Story {story_id}: [Brief Description]

         QA Gate: [PASS/WAIVED]
         Tests: [PASS]

         Generated with [Claude Code](https://claude.com/claude-code)
         Co-Authored-By: Claude <noreply@anthropic.com>"

Step 12: Update .worktree-status.yaml: status="ready-to-merge"

**Note**: Pre-commit hooks will automatically validate:
- JSON Schema syntax
- OpenAPI spec validity
- Gherkin syntax
- SDD coverage
- Content consistency

If pre-commit fails, fix issues and re-commit.

===============================================================================
PHASE 4: RESULT OUTPUT (ALWAYS Execute)
===============================================================================
Step 13: Write .worktree-result.json with ENHANCED status (include dev_record and qa_record):

{{
  "story_id": "{story_id}",
  "story_title": "[Story title from Story file]",
  "outcome": "SUCCESS|DEV_BLOCKED|QA_BLOCKED|QA_CONCERNS_UNFIXED",
  "tests_passed": true|false,
  "test_count": [number],
  "test_coverage": [percentage, e.g. 94.0],
  "qa_gate": "PASS|CONCERNS|FAIL|WAIVED"|null,
  "commit_sha": "[sha from git log -1 --format=%H]"|null,
  "blocking_reason": "[reason if blocked]"|null,
  "fix_attempts": 0|1,
  "timestamp": "[ISO-8601 timestamp]",
  "duration_seconds": [total seconds from start],

  "dev_record": {{
    "agent_model": "Claude Code (claude-sonnet-4-5)",
    "duration_seconds": [seconds],
    "files_created": [
      {{"path": "path/to/file.py", "description": "What was created"}}
    ],
    "files_modified": [
      {{"path": "path/to/existing.py", "description": "What changed"}}
    ],
    "completion_notes": "[Brief summary of implementation]"
  }},

  "qa_record": {{
    "quality_score": [0-100],
    "ac_coverage": {{
      "AC1": {{"status": "PASS|FAIL", "evidence": "[test name or file]"}},
      "AC2": {{"status": "PASS|FAIL", "evidence": "[test name or file]"}}
    }},
    "issues_found": [
      {{"severity": "low|medium|high", "description": "[issue]"}}
    ],
    "recommendations": ["[recommendation 1]", "[recommendation 2]"]
  }}
}}

===============================================================================
PHASE 5: STORY FILE UPDATE (ALWAYS Execute After Phase 4)
===============================================================================
Step 14: Find and update Story file's "## Dev Agent Record" section:

    1. Locate Story file: docs/stories/{{story_id}}.story.md or story-{{story_id}}.md

    2. Replace "## Dev Agent Record" section content with:

       ### Agent Model Used
       Claude Code (claude-sonnet-4-5)

       ### Debug Log References
       - Session ID: [from progress file or auto-generated]
       - Process: Automated via `*linear` / `/parallel`

       ### Completion Notes List
       - [Summary of AC implementation]
       - Tests: PASS/FAIL ([test_count] tests, [coverage]% coverage)
       - QA Gate: [PASS/CONCERNS/FAIL/WAIVED]

       ### Commit Info
       - **Commit SHA**: `[sha]`
       - **Duration**: [seconds]s
       - **Completed At**: [ISO timestamp]
       - **Retry Count**: [0 or 1]

       ### File List
       **新创建:**
       - `path/file.py` - [description]
       **修改:**
       - `path/existing.py` - [what changed]

Step 15: Update Story file's "## QA Results" section:

    **验证方式**: `*linear` / `/parallel` 自动化验证流程
    **验证时间**: [YYYY-MM-DD]
    **验证状态**: ✅ PASSED / ⚠️ CONCERNS / ❌ FAILED

    ### Review Date: [YYYY-MM-DD]
    ### Reviewed By: Quinn (Test Architect) - Automated

    ### Gate Status
    **Gate: [PASS/CONCERNS/FAIL/WAIVED]**
    **Quality Score**: [score]/100

    ### AC Coverage
    | AC | Status | Evidence |
    |----|--------|----------|
    | AC1 | PASS/FAIL | [test or file reference] |

    ### Issues Found
    [list of issues or "无"]

    ### Gate File Reference
    `docs/qa/gates/{{story_id}}-[slug].yml`

    **验证流程**:
    - [x] 单元测试通过
    - [x] *trace - 需求覆盖追溯
    - [x] *nfr-assess - 非功能需求评估
    - [x] *review - 综合审查
    - [x] *gate - 质量门禁 ([GATE STATUS])

Step 16: Set story_file_updated in .worktree-result.json:
    - If Story file was successfully updated: "story_file_updated": true
    - If update failed or skipped: "story_file_updated": false

===============================================================================
IMPORTANT REMINDERS
===============================================================================
- Follow all coding standards in CLAUDE.md
- Run tests BEFORE QA review
- Document any issues in the QA assessment files
- Do NOT push from worktree - orchestrator handles merge
- Update .worktree-status.yaml at EVERY decision point
'''

    # Allowed tools for development workflow
    ALLOWED_TOOLS = "Bash,Read,Write,Edit,Grep,Glob,Task,TodoWrite"

    # UltraThink section template - enables extended deep thinking
    ULTRATHINK_SECTION = '''
===============================================================================
🧠 ULTRATHINK MODE ENABLED - EXTENDED DEEP THINKING
===============================================================================
This session uses UltraThink extended thinking mode for maximum code quality:

1. **Before EVERY Task**: Pause and deeply analyze dependencies, edge cases,
   and potential issues before writing any code.

2. **Technical Verification**: ALWAYS query @context7 or @langgraph for API
   documentation. Never guess or assume - verify from official sources.

3. **Zero Hallucination Protocol**: Every API call, function signature, and
   configuration MUST be verified from documentation and annotated with source.

4. **Deep Architecture Analysis**: Consider how each change affects the overall
   system. Think about error handling, edge cases, and future maintainability.

5. **Code Quality Standards**: Write production-ready code with proper error
   handling, logging, type hints, and documentation.

When implementing each Task:
- Read the full Story file first
- Identify all dependencies and affected files
- Query documentation for any uncertain APIs
- Plan the implementation approach
- Implement with proper error handling
- Add tests for edge cases
- Review your own code before moving on
'''

    def __init__(self, max_turns: int = 200, ultrathink: bool = False):
        """
        Initialize the session spawner.

        Args:
            max_turns: Maximum agentic turns per session (default: 200)
            ultrathink: Enable UltraThink extended thinking mode (default: False)
        """
        self.max_turns = max_turns
        self.ultrathink = ultrathink

    def spawn(
        self,
        story_id: str,
        worktree_path: Path,
        log_file: Optional[Path] = None,
    ) -> subprocess.Popen:
        """
        Spawn a Claude CLI session for a Story.

        Args:
            story_id: The Story ID to develop (e.g., "15.1")
            worktree_path: Path to the worktree directory
            log_file: Optional path to log file (default: {worktree}/dev-qa-output.log)

        Returns:
            subprocess.Popen handle to the running process
        """
        if log_file is None:
            log_file = worktree_path / "dev-qa-output.log"

        # Generate prompt with story ID and optional ultrathink section
        ultrathink_section = self.ULTRATHINK_SECTION if self.ultrathink else ""
        prompt = self.PROMPT_TEMPLATE.format(
            story_id=story_id,
            ultrathink_section=ultrathink_section
        )

        # Build Claude CLI command
        cmd = [
            'claude',
            '-p', prompt,
            '--dangerously-skip-permissions',
            '--allowedTools', self.ALLOWED_TOOLS,
            '--max-turns', str(self.max_turns),
        ]

        # Open log file for writing
        log_handle = open(log_file, 'w', encoding='utf-8')

        # Write header to log
        log_handle.write(f"{'=' * 70}\n")
        log_handle.write(f"Linear Development Daemon - Story {story_id}\n")
        log_handle.write(f"Started: {datetime.now().isoformat()}\n")
        log_handle.write(f"Worktree: {worktree_path}\n")
        log_handle.write(f"Max Turns: {self.max_turns}\n")
        log_handle.write(f"UltraThink: {self.ultrathink}\n")
        log_handle.write(f"{'=' * 70}\n\n")
        log_handle.flush()

        # Spawn process
        try:
            # Windows-specific: create new process group
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(
                cmd,
                cwd=str(worktree_path),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creation_flags,
            )

            print(f"[SessionSpawner] Started Claude session for Story {story_id}")
            print(f"[SessionSpawner]   PID: {process.pid}")
            print(f"[SessionSpawner]   Log: {log_file}")

            return process

        except Exception as e:
            log_handle.write(f"\n\nERROR: Failed to spawn Claude session: {e}\n")
            log_handle.close()
            raise

    def get_log_handle(self, worktree_path: Path) -> IO:
        """Get a handle to the log file for monitoring."""
        log_file = worktree_path / "dev-qa-output.log"
        return open(log_file, 'r', encoding='utf-8', errors='replace')

    def cleanup_result_file(self, worktree_path: Path):
        """Remove previous result file before starting new session."""
        result_file = worktree_path / ".worktree-result.json"
        if result_file.exists():
            try:
                result_file.unlink()
                print(f"[SessionSpawner] Removed old result file: {result_file}")
            except Exception as e:
                print(f"[SessionSpawner] Warning: Could not remove result file: {e}")


if __name__ == "__main__":
    # Quick test
    print("LinearSessionSpawner module loaded successfully")
    print(f"Max turns: 200 (default)")
    print(f"Allowed tools: {LinearSessionSpawner.ALLOWED_TOOLS}")
    print(f"Prompt template length: {len(LinearSessionSpawner.PROMPT_TEMPLATE)} chars")

    # Test prompt formatting
    test_prompt = LinearSessionSpawner.PROMPT_TEMPLATE.format(story_id="15.1")
    print(f"Formatted prompt (first 200 chars): {test_prompt[:200]}...")
