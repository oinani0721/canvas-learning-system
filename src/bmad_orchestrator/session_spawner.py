"""
BMad Session Spawner - 异步 Claude CLI 会话管理

为全自动化 SM→PO→Dev→QA 工作流提供会话生成和生命周期管理。

✅ Verified from existing pattern: scripts/daemon/linear_session_spawner.py
- subprocess.Popen for process management
- --dangerously-skip-permissions flag
- Log file streaming
- Process group creation for Windows

核心功能:
- 4种 Agent Prompt Templates (SM, PO, Dev, QA)
- 异步子进程管理 (asyncio.subprocess)
- 会话状态追踪
- 结果文件解析
- 超时处理

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-30
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

# ============================================================================
# Session Health Monitoring (v1.1.0)
# ============================================================================

# Health status type
SessionHealthStatus = Literal["healthy", "stuck", "crashed", "completed"]


@dataclass
class SessionHealthMonitor:
    """
    会话健康监控器 - 检测卡住的 Claude 会话

    通过监控日志文件活动来检测会话是否卡住。
    如果日志文件在指定时间内没有更新，判定为 "stuck"。

    Attributes:
        log_file: 日志文件路径
        stuck_threshold_seconds: 卡住阈值（秒），默认 300 (5分钟)
        check_interval_seconds: 检查间隔（秒），默认 30
        last_size: 上次检测时的文件大小
        last_activity_time: 上次活动时间
    """
    log_file: Path
    stuck_threshold_seconds: int = 300  # 5 minutes (user confirmed)
    check_interval_seconds: int = 30
    last_size: int = field(default=0, init=False)
    last_activity_time: float = field(default_factory=time.time, init=False)

    def check_health(self, process: asyncio.subprocess.Process) -> SessionHealthStatus:
        """
        检查会话健康状态

        Returns:
            - "healthy": 日志文件有新输出
            - "stuck": 日志文件超过阈值时间未更新
            - "crashed": 进程已退出且返回码非零
            - "completed": 进程已正常退出
        """
        # 检查进程状态
        if process.returncode is not None:
            if process.returncode == 0:
                return "completed"
            return "crashed"

        # 检查日志文件活动
        try:
            current_size = self.log_file.stat().st_size if self.log_file.exists() else 0
        except OSError:
            current_size = 0

        current_time = time.time()

        if current_size > self.last_size:
            # 有新输出 - 更新状态
            self.last_size = current_size
            self.last_activity_time = current_time
            return "healthy"

        # 检查是否超过卡住阈值
        elapsed = current_time - self.last_activity_time
        if elapsed > self.stuck_threshold_seconds:
            return "stuck"

        return "healthy"

    def get_elapsed_since_activity(self) -> float:
        """获取距离上次活动的时间（秒）"""
        return time.time() - self.last_activity_time

    async def extract_partial_result(self) -> Optional[Dict[str, Any]]:
        """
        从卡住的会话中提取部分结果

        尝试解析日志文件中已完成的工作，以便工作流可以继续。

        Returns:
            部分结果字典，如果无法提取返回 None
        """
        if not self.log_file.exists():
            return None

        try:
            content = self.log_file.read_text(encoding='utf-8', errors='replace')

            # 提取已创建/修改的文件
            files_created = []
            files_modified = []

            for line in content.split('\n'):
                if 'Created:' in line or 'created file' in line.lower():
                    # 提取文件路径
                    parts = line.split()
                    for part in parts:
                        if part.endswith(('.py', '.ts', '.md', '.json', '.yaml', '.yml')):
                            files_created.append(part.strip())
                elif 'Modified:' in line or 'edited file' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if part.endswith(('.py', '.ts', '.md', '.json', '.yaml', '.yml')):
                            files_modified.append(part.strip())

            # 尝试查找结果 JSON
            result_json = None
            json_start = content.rfind('{')
            if json_start != -1:
                try:
                    # 尝试解析最后一个 JSON 对象
                    json_str = content[json_start:]
                    json_end = json_str.find('}') + 1
                    if json_end > 0:
                        result_json = json.loads(json_str[:json_end])
                except json.JSONDecodeError:
                    pass

            return {
                "partial": True,
                "files_created": files_created,
                "files_modified": files_modified,
                "result_json": result_json,
                "log_size": self.last_size,
                "extracted_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"[SessionHealthMonitor] Failed to extract partial result: {e}")
            return None


# ============================================================================
# Prompt Templates
# ============================================================================

SM_PROMPT_TEMPLATE = '''**IMPORTANT: IGNORE ALL AGENT DEFINITIONS. EXECUTE THIS TASK DIRECTLY.**

You are running in AUTOMATED BATCH MODE. Do NOT wait for user commands.
Do NOT show menus or ask "What would you like to do?".
IMMEDIATELY execute ALL steps below and create the required output files.

{ultrathink_section}

===============================================================================
MISSION: Create Story {story_id} from Epic {epic_id}
===============================================================================

**CRITICAL - AUTOMATED MODE RULES**:
1. This is a NON-INTERACTIVE session - NO user is present to respond
2. Do NOT wait for *draft or any other commands - execute directly NOW
3. Do NOT display menus or available commands
4. IMMEDIATELY start reading files and creating the Story draft

===============================================================================
PHASE 1: CONTEXT LOADING
===============================================================================
Step 1: Read .bmad-core/core-config.yaml for document paths
Step 2: Load Epic file: {epic_file}
Step 3: Load Architecture docs from configured paths (architectureShardedLocation)
Step 4: Identify Story {story_id} scope and acceptance criteria from Epic

===============================================================================
PHASE 2: STORY CREATION (Direct Execution - No /sm command needed)
===============================================================================
Step 5: Create Story document with ALL required sections:

**Story Structure**:
```markdown
# Story {story_id}: [Title from Epic]

## Status
- [ ] Draft
- [ ] Ready for Dev
- [ ] In Progress
- [ ] QA Review
- [ ] Done

## Story Overview
[Brief description]

## Acceptance Criteria
[From Epic, numbered AC1, AC2, etc.]

## Dev Notes (CRITICAL - Must be complete)
### Technical Context
[All info Dev Agent needs - they ONLY read this Story file]

### API Endpoints (if applicable)
[Reference specs/api/canvas-api.openapi.yml with line numbers]

### Data Models (if applicable)
[Reference specs/data/*.schema.json with line numbers]

### SDD References
- OpenAPI: specs/api/canvas-api.openapi.yml#L[line]
- Schema: specs/data/[name].schema.json#L[line]

### ADR References
- docs/architecture/decisions/[relevant ADRs]

### Implementation Guidelines
[Step-by-step implementation guide]

## Testing Requirements
[Test scenarios from AC]

## Dependencies
[Other stories, external dependencies]
```

===============================================================================
PHASE 3: STORY VALIDATION CHECKLIST
===============================================================================
Step 6: Self-validate Story against checklist:
   - [ ] 1.1 Story follows template structure
   - [ ] 1.2 Title is clear and descriptive
   - [ ] 2.1 AC are testable (Given-When-Then format preferred)
   - [ ] 2.2 AC numbered (AC1, AC2, etc.)
   - [ ] 5.1 Dev Notes contain ALL technical context
   - [ ] 5.2 Dev Notes reference specific line numbers
   - [ ] 6.1 SDD references exist and are valid
   - [ ] 6.2 ADR references exist (if architectural decisions involved)
   - [ ] 6.3 File paths verified to exist (anti-hallucination)

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 7: Use Write tool to create Story file:
   - File path: docs/stories/{story_id}.story.md

Step 8: Use Write tool to create result file:
   - File path: .sm-result.json
   - Content:
{{
  "story_id": "{story_id}",
  "epic_id": "{epic_id}",
  "outcome": "SUCCESS",
  "story_file": "docs/stories/{story_id}.story.md",
  "title": "[Story Title]",
  "sdd_references": ["specs/api/...", "specs/data/..."],
  "adr_references": ["docs/architecture/decisions/..."],
  "checklist_passed": true,
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT RULES
===============================================================================
- This is NON-INTERACTIVE - execute ALL steps without asking questions
- Story must be SELF-CONTAINED (Dev Agent won't load PRD/Architecture)
- Include ALL technical context in Dev Notes
- Verify file paths exist before referencing (use Glob/Grep)
- MUST create both .story.md and .sm-result.json files
'''

PO_PROMPT_TEMPLATE = '''You are Sarah, the Product Owner (PO) Agent. Your mission is to validate a Story.
{ultrathink_section}

===============================================================================
MISSION: Validate Story {story_id} with SoT Hierarchy
===============================================================================

**Your Role**: Sarah (Product Owner) - Validate Story against PRD and Specs

**CRITICAL**: This is a NON-INTERACTIVE session. Do NOT ask questions.
Execute ALL steps below and produce the required outputs.

**SoT Hierarchy** (highest to lowest):
1. PRD (Level 1) - WHAT: Functional requirements
2. Architecture (Level 2) - HOW: System design
3. JSON Schema (Level 3) - Data contracts
4. OpenAPI Spec (Level 4) - API contracts
5. Story (Level 5) - Implementation details
6. Code (Level 6) - Must comply with all above

===============================================================================
PHASE 1: STORY REVIEW (Direct Execution - No /po command needed)
===============================================================================
Step 1: Read Story file: {story_file}
Step 2: Extract SDD references from Story's Dev Notes section
Step 3: Load PRD sections related to Story scope

===============================================================================
PHASE 2: SoT CONFLICT DETECTION
===============================================================================
Step 4: Load OpenAPI specs referenced in Story (verify they exist)
Step 5: Load JSON Schemas referenced in Story (verify they exist)
Step 6: Compare Story requirements against:
   - PRD functional requirements
   - OpenAPI endpoint definitions
   - Schema data structures
Step 7: Document any conflicts found

===============================================================================
PHASE 3: AUTO-RESOLUTION (if conflicts found)
===============================================================================
Step 8: Apply SoT Hierarchy for conflict resolution:
   - Higher level document ALWAYS wins
   - PRD > Architecture > Schema > OpenAPI > Story > Code
   - Record all resolutions with justification

Step 9: Update Story if needed (to match higher-level docs)

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 10: Use Write tool to create result file:
   - File path: .po-result.json
   - Content:
{{
  "story_id": "{story_id}",
  "outcome": "APPROVED|REJECTED|AUTO_RESOLVED",
  "validation_passed": true|false,
  "sot_conflicts_found": 0,
  "sot_resolutions": [],
  "rejection_reason": null,
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
DECISION LOGIC
===============================================================================
- APPROVED: Story aligns with PRD, SDD valid, no conflicts
- AUTO_RESOLVED: Conflicts found but auto-resolved via hierarchy
- REJECTED: Critical issues that cannot be auto-resolved

===============================================================================
IMPORTANT RULES
===============================================================================
- This is NON-INTERACTIVE - execute ALL steps without asking questions
- MUST create .po-result.json file using Write tool
- Verify all file references exist before approving
'''

DEV_PROMPT_TEMPLATE = '''You are James, the Developer (Dev) Agent. Your mission is to implement a Story.
{ultrathink_section}

===============================================================================
MISSION: Implement Story {story_id}
===============================================================================

**Your Role**: James (Developer) - Implement Story with tests

**CRITICAL**: This is a NON-INTERACTIVE session. Do NOT ask questions.
Execute ALL steps below and produce the required outputs.

===============================================================================
PHASE 1: CONTEXT LOADING
===============================================================================
Step 1: Read Story file: {story_file}
   - Extract Acceptance Criteria (AC1, AC2, etc.)
   - Extract Dev Notes with technical context
   - Note SDD references (OpenAPI, Schema paths)

Step 2: Read coding standards from:
   - docs/architecture/coding-standards.md (if exists)
   - .bmad-core/core-config.yaml for devLoadAlwaysFiles

Step 3: Verify SDD references from Story:
   - specs/api/canvas-api.openapi.yml
   - specs/data/*.schema.json

===============================================================================
PHASE 2: IMPLEMENTATION (Direct Execution - No /dev command needed)
===============================================================================
Step 4: Implement Story requirements:
   - Follow Dev Notes in Story exactly
   - Create/modify files as specified
   - Follow existing code patterns in codebase

Step 5: Implementation checklist:
   - [ ] API endpoints match OpenAPI spec
   - [ ] Data models match JSON Schema
   - [ ] Error handling implemented
   - [ ] Logging added for key operations

===============================================================================
PHASE 3: TESTING
===============================================================================
Step 6: Write unit tests for new code
   - Test each Acceptance Criteria
   - Target coverage ≥ 80%

Step 7: Run tests using Bash tool:
   - Python: python -m pytest tests/ -v
   - TypeScript: npm test

**DECISION POINT - TEST RESULTS**:
- If ALL tests PASS: outcome="SUCCESS"
- If ANY test FAILS: outcome="DEV_BLOCKED", document failing tests

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 8: Use Write tool to create result file:
   - File path: .dev-result.json
   - Content:
{{
  "story_id": "{story_id}",
  "outcome": "SUCCESS|DEV_BLOCKED|ERROR",
  "tests_passed": true|false,
  "test_count": 0,
  "test_coverage": 0.0,
  "files_created": [],
  "files_modified": [],
  "duration_seconds": 0,
  "blocking_reason": null,
  "completion_notes": "[summary of implementation]",
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT RULES
===============================================================================
- This is NON-INTERACTIVE - execute ALL steps without asking questions
- Do NOT load PRD or Architecture (Story has all context)
- Follow SDD references in Dev Notes exactly
- MUST create .dev-result.json file using Write tool
- Write production-ready code with proper error handling
'''

QA_PROMPT_TEMPLATE = '''You are Quinn, the QA (Quality Assurance) Agent. Your mission is to review a Story implementation.
{ultrathink_section}

===============================================================================
MISSION: QA Review for Story {story_id}
===============================================================================

**Your Role**: Quinn (Test Architect) - Comprehensive QA review

**CRITICAL**: This is a NON-INTERACTIVE session. Do NOT ask questions.
Execute ALL steps below and produce the required outputs.

===============================================================================
PHASE 1: CONTEXT LOADING
===============================================================================
Step 1: Read Story file to understand requirements and AC
Step 2: Read .dev-result.json to see what was implemented
Step 3: List files created/modified during development

===============================================================================
PHASE 2: QA REVIEW (Direct Execution - No /qa command needed)
===============================================================================
Step 4: Requirements Traceability
   - For each AC (AC1, AC2, etc.), verify:
     - Implementation exists
     - Test coverage exists
     - Evidence documented

Step 5: Non-Functional Requirements (NFR) Assessment
   - Performance: No obvious bottlenecks
   - Security: No hardcoded secrets, SQL injection, XSS
   - Maintainability: Code is readable and documented
   - Error handling: Proper try/catch, logging

Step 6: Code Review
   - Code follows project coding standards
   - No obvious bugs or logic errors
   - Proper typing (Python type hints, TypeScript types)

===============================================================================
PHASE 3: QUALITY GATE DECISION
===============================================================================
Step 7: Determine quality gate result:

**DECISION LOGIC**:
- **PASS**: All AC covered, no critical issues, tests passing
- **CONCERNS**: Minor issues found, can be addressed later
- **FAIL**: Critical issues (security, missing tests, broken logic)
- **WAIVED**: Issues acknowledged but accepted (document reason)

**Auto-FAIL conditions**:
- Security vulnerabilities detected
- Missing tests for P0 functionality
- Implementation doesn't match AC

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 8: Use Write tool to create result file:
   - File path: .qa-result.json
   - Content:
{{
  "story_id": "{story_id}",
  "qa_gate": "PASS|CONCERNS|FAIL|WAIVED",
  "quality_score": 0,
  "ac_coverage": {{}},
  "issues_found": [],
  "recommendations": [],
  "adr_compliance": true,
  "fix_attempts": 0,
  "duration_seconds": 0,
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT RULES
===============================================================================
- This is NON-INTERACTIVE - execute ALL steps without asking questions
- Be rigorous but fair in assessment
- Document all issues with specific file:line locations
- Security issues = automatic FAIL
- Missing P0 tests = automatic FAIL
- MUST create .qa-result.json file using Write tool
'''

# UltraThink section template
ULTRATHINK_SECTION = '''
===============================================================================
[ULTRATHINK] MODE ENABLED - EXTENDED DEEP THINKING
===============================================================================
This session uses UltraThink extended thinking mode for maximum quality:

1. **Before EVERY Task**: Pause and deeply analyze dependencies, edge cases,
   and potential issues before taking action.

2. **Technical Verification**: ALWAYS query @context7 or @langgraph for API
   documentation. Never guess or assume - verify from official sources.

3. **Zero Hallucination Protocol**: Every API call, function signature, and
   configuration MUST be verified from documentation and annotated with source.

4. **Deep Analysis**: Consider how each action affects the overall workflow.
   Think about error handling, edge cases, and downstream impacts.
'''


# ============================================================================
# Session Result Data Classes
# ============================================================================

@dataclass
class SessionResult:
    """Generic session result structure."""
    story_id: str
    outcome: str
    timestamp: str
    duration_seconds: int = 0
    error_message: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SMResult(SessionResult):
    """SM Agent session result."""
    story_file: Optional[str] = None
    title: Optional[str] = None
    sdd_references: list = field(default_factory=list)
    adr_references: list = field(default_factory=list)
    checklist_passed: bool = False


@dataclass
class POResult(SessionResult):
    """PO Agent session result."""
    validation_passed: bool = False
    sot_conflicts_found: int = 0
    sot_resolutions: list = field(default_factory=list)
    rejection_reason: Optional[str] = None


@dataclass
class DevResult(SessionResult):
    """Dev Agent session result."""
    tests_passed: bool = False
    test_count: int = 0
    test_coverage: float = 0.0
    files_created: list = field(default_factory=list)
    files_modified: list = field(default_factory=list)
    blocking_reason: Optional[str] = None
    completion_notes: Optional[str] = None


@dataclass
class QAResult(SessionResult):
    """QA Agent session result."""
    qa_gate: Optional[str] = None
    quality_score: int = 0
    ac_coverage: Dict[str, Dict[str, str]] = field(default_factory=dict)
    issues_found: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    adr_compliance: bool = True
    fix_attempts: int = 0


# ============================================================================
# Session Spawner Class
# ============================================================================

class BmadSessionSpawner:
    """
    异步 Claude CLI 会话生成器

    ✅ Verified from LangGraph Skill (Pattern: Async subprocess management)

    为 BMad 编排器提供:
    - 4种 Agent Prompt Templates
    - 异步子进程管理
    - 会话状态追踪
    - 结果文件解析
    - 超时处理
    """

    # Default allowed tools for each agent type
    ALLOWED_TOOLS = {
        "SM": "Read,Write,Edit,Glob,Grep,Task,TodoWrite",
        "PO": "Read,Write,Edit,Glob,Grep,Task,TodoWrite",
        "DEV": "Bash,Read,Write,Edit,Glob,Grep,Task,TodoWrite",
        "QA": "Read,Write,Edit,Glob,Grep,Task,TodoWrite",
    }

    # Result file names for each phase
    RESULT_FILES = {
        "SM": ".sm-result.json",
        "PO": ".po-result.json",
        "DEV": ".dev-result.json",
        "QA": ".qa-result.json",
    }

    def __init__(
        self,
        max_turns: int = 200,
        ultrathink: bool = True,
        timeout_seconds: int = 3600,  # 1 hour default
    ):
        """
        初始化会话生成器

        Args:
            max_turns: 每个 Claude 会话的最大轮数
            ultrathink: 启用 UltraThink 扩展思考模式
            timeout_seconds: 会话超时时间（秒）
        """
        self.max_turns = max_turns
        self.ultrathink = ultrathink
        self.timeout_seconds = timeout_seconds
        self._active_sessions: Dict[str, asyncio.subprocess.Process] = {}
        self._output_tasks: Dict[str, asyncio.Task] = {}  # Track output streaming tasks

    async def _stream_output_to_file(
        self,
        process: asyncio.subprocess.Process,
        log_file: Path,
        session_id: str,
    ) -> None:
        """
        异步读取进程输出并写入日志文件 (Windows 专用)

        避免 PIPE 缓冲区死锁：持续读取 stdout，写入文件
        """
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                while True:
                    # Read line by line from stdout
                    if process.stdout is None:
                        break
                    line = await process.stdout.readline()
                    if not line:
                        # EOF - process finished
                        break
                    # Decode and write to file
                    text = line.decode('utf-8', errors='replace')
                    f.write(text)
                    f.flush()  # Ensure immediate write
        except Exception as e:
            print(f"[BmadSessionSpawner] Output streaming error for {session_id}: {e}")

    def _get_prompt(
        self,
        phase: Literal["SM", "PO", "DEV", "QA"],
        story_id: str,
        epic_id: str = "",
        epic_file: str = "",
        story_file: str = "",
    ) -> str:
        """
        生成指定阶段的 Prompt

        Args:
            phase: 工作流阶段
            story_id: Story ID
            epic_id: Epic ID (SM phase)
            epic_file: Epic 文件路径 (SM phase)
            story_file: Story 文件路径 (PO/DEV/QA phases)

        Returns:
            格式化的 Prompt 字符串
        """
        ultrathink_section = ULTRATHINK_SECTION if self.ultrathink else ""

        if phase == "SM":
            return SM_PROMPT_TEMPLATE.format(
                story_id=story_id,
                epic_id=epic_id,
                epic_file=epic_file,
                ultrathink_section=ultrathink_section,
            )
        elif phase == "PO":
            return PO_PROMPT_TEMPLATE.format(
                story_id=story_id,
                story_file=story_file,
                ultrathink_section=ultrathink_section,
            )
        elif phase == "DEV":
            return DEV_PROMPT_TEMPLATE.format(
                story_id=story_id,
                story_file=story_file,
                ultrathink_section=ultrathink_section,
            )
        elif phase == "QA":
            return QA_PROMPT_TEMPLATE.format(
                story_id=story_id,
                ultrathink_section=ultrathink_section,
            )
        else:
            raise ValueError(f"Unknown phase: {phase}")

    async def spawn_session(
        self,
        phase: Literal["SM", "PO", "DEV", "QA"],
        story_id: str,
        worktree_path: Path,
        epic_id: str = "",
        epic_file: str = "",
        story_file: str = "",
        log_file: Optional[Path] = None,
    ) -> str:
        """
        异步生成 Claude CLI 会话

        Args:
            phase: 工作流阶段 (SM, PO, DEV, QA)
            story_id: Story ID
            worktree_path: Worktree 目录路径
            epic_id: Epic ID (SM phase only)
            epic_file: Epic 文件路径 (SM phase only)
            story_file: Story 文件路径 (PO/DEV/QA phases)
            log_file: 日志文件路径

        Returns:
            会话 ID (用于追踪)
        """
        session_id = f"{phase}-{story_id}-{uuid.uuid4().hex[:8]}"

        if log_file is None:
            log_file = worktree_path / f"{phase.lower()}-output.log"

        # Generate prompt
        prompt = self._get_prompt(
            phase=phase,
            story_id=story_id,
            epic_id=epic_id,
            epic_file=epic_file,
            story_file=story_file,
        )

        # Clean up previous result file
        result_file = worktree_path / self.RESULT_FILES[phase]
        if result_file.exists():
            result_file.unlink()

        # ✅ FIX v14: Disable BMad agents to prevent Claude from loading interactive definitions
        # Claude Code loads .bmad-core/agents/*.md which override our automated prompt
        # Solution: Temporarily rename the agents directory before starting the session
        bmad_agents_dir = worktree_path / '.bmad-core' / 'agents'
        bmad_agents_disabled = worktree_path / '.bmad-core' / 'agents.disabled'
        if bmad_agents_dir.exists() and not bmad_agents_disabled.exists():
            try:
                bmad_agents_dir.rename(bmad_agents_disabled)
                print(f"[Session] Disabled BMad agents for automated session: {bmad_agents_dir}")
            except Exception as e:
                print(f"[Session] Warning: Could not disable BMad agents: {e}")

        # Build Claude CLI command
        # ✅ FIX v5: Do NOT pass prompt as command-line argument
        # Windows has issues with long/complex prompts as CLI args (causes hanging)
        # Instead, pass prompt via stdin (verified working with echo "..." | claude -p ...)
        # ✅ FIX v13: Add --verbose --output-format text for Windows subprocess.PIPE compatibility
        # Root cause: Claude CLI on Windows doesn't output to stdout when run from subprocess
        # unless --verbose flag is used with -p mode.
        # Solution: Use -p --verbose --output-format text with subprocess.PIPE and threaded readers
        cmd = [
            'claude',
            '-p',  # Print mode (non-interactive output)
            '--verbose',  # ✅ FIX v13: Required for subprocess.PIPE output on Windows
            '--output-format', 'text',  # ✅ FIX v13: Human-readable output format
            '--dangerously-skip-permissions',
            '--allowedTools', self.ALLOWED_TOOLS[phase],
            '--max-turns', str(self.max_turns),
            # prompt removed - will be passed via stdin
        ]

        # Write log header
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"{'=' * 70}\n")
            f.write(f"BMad Orchestrator - {phase} Session for Story {story_id}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write(f"Worktree: {worktree_path}\n")
            f.write(f"Max Turns: {self.max_turns}\n")
            f.write(f"UltraThink: {self.ultrathink}\n")
            f.write(f"Timeout: {self.timeout_seconds}s\n")
            f.write(f"{'=' * 70}\n\n")

        # ✅ FIX v13: Windows - Use subprocess.PIPE with threaded readers
        # Previous fixes v5-v12 with file piping/redirection didn't produce output.
        # Root cause: Claude CLI on Windows doesn't output to stdout when redirected to file,
        # but DOES output when using subprocess.PIPE with --verbose flag.
        # Solution: Use -p --verbose --output-format text with PIPE and threaded log writers.

        if sys.platform == 'win32':
            import subprocess as sp
            import threading

            # Write prompt to file for debugging and for passing to Claude
            # ✅ FIX v15: Use file-based prompt passing to avoid Windows command line issues
            # Windows has command line length limit (~8191 chars) and special char issues
            prompt_file = worktree_path / '.bmad-prompt.txt'
            try:
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt)
                print(f"[Session] Wrote prompt to file: {prompt_file} ({len(prompt)} chars)")
            except Exception as e:
                print(f"[Session] ERROR: Failed to write prompt file: {e}")
                raise

            # ✅ FIX v15: Use subprocess with stdin PIPE to pass prompt
            # This avoids command line length limits and special character issues
            # Claude CLI reads prompt from stdin when -p is used without a prompt argument

            # Set UTF-8 environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # Open log file for writing output from reader threads
            log_handle = open(str(log_file), 'a', encoding='utf-8', buffering=1)

            # Start process with PIPE for stdin/stdout/stderr
            # ✅ FIX v15: Use list instead of shell=True for better handling
            popen_process = sp.Popen(
                cmd,  # Use cmd list directly, prompt will be passed via stdin
                shell=False,  # ✅ FIX v15: Don't use shell
                cwd=str(worktree_path),
                stdin=sp.PIPE,  # ✅ FIX v15: Use PIPE for stdin to pass prompt
                stdout=sp.PIPE,
                stderr=sp.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env,
            )

            # ✅ FIX v15: Write prompt to stdin
            try:
                popen_process.stdin.write(prompt.encode('utf-8'))
                popen_process.stdin.close()
                print(f"[Session] Sent prompt via stdin ({len(prompt)} chars)")
            except Exception as e:
                print(f"[Session] ERROR: Failed to send prompt via stdin: {e}")

            # Threaded reader function that writes to log file
            def pipe_reader(pipe, log_handle, name):
                try:
                    for line in iter(pipe.readline, b''):
                        decoded = line.decode('utf-8', errors='replace')
                        log_handle.write(decoded)
                        log_handle.flush()
                except Exception:
                    pass
                finally:
                    pipe.close()

            # Start reader threads
            stdout_thread = threading.Thread(
                target=pipe_reader,
                args=(popen_process.stdout, log_handle, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=pipe_reader,
                args=(popen_process.stderr, log_handle, 'stderr'),
                daemon=True
            )
            stdout_thread.start()
            stderr_thread.start()

            # Wrap in an object that has .pid and can be awaited
            class PopenWrapper:
                def __init__(self, popen, log_handle, stdout_thread, stderr_thread):
                    self.popen = popen
                    self.pid = popen.pid
                    self.log_handle = log_handle
                    self.stdout_thread = stdout_thread
                    self.stderr_thread = stderr_thread
                    self.returncode = None

                async def wait(self):
                    # Poll in async manner
                    while self.popen.poll() is None:
                        await asyncio.sleep(1)
                    self.returncode = self.popen.returncode
                    # Wait for reader threads to finish
                    self.stdout_thread.join(timeout=5)
                    self.stderr_thread.join(timeout=5)
                    # Close log handle after process ends
                    try:
                        self.log_handle.close()
                    except Exception:
                        pass
                    return self.returncode

            process = PopenWrapper(popen_process, log_handle, stdout_thread, stderr_thread)
        else:
            # Unix: File descriptor approach works fine
            log_handle = open(str(log_file), 'a', encoding='utf-8')
            log_fd = log_handle.fileno()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(worktree_path),
                stdout=log_fd,
                stderr=asyncio.subprocess.STDOUT,
            )

            # Store log handle for cleanup (only needed for Unix)
            if not hasattr(self, '_log_handles'):
                self._log_handles = {}
            self._log_handles[session_id] = log_handle

        self._active_sessions[session_id] = process

        print(f"[BmadSessionSpawner] Started {phase} session for Story {story_id}")
        print(f"[BmadSessionSpawner]   Session ID: {session_id}")
        print(f"[BmadSessionSpawner]   PID: {process.pid}")
        print(f"[BmadSessionSpawner]   Log: {log_file}")

        return session_id

    async def wait_for_session(
        self,
        session_id: str,
        timeout: Optional[int] = None,
        log_file: Optional[Path] = None,
        stuck_threshold_seconds: int = 300,  # 5 minutes (user confirmed)
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        等待会话完成 - 支持卡住检测 (v1.1.0)

        Args:
            session_id: 会话 ID
            timeout: 超时时间（秒），None 使用默认值
            log_file: 日志文件路径（用于卡住检测）
            stuck_threshold_seconds: 卡住阈值（秒），默认 300 (5分钟)

        Returns:
            Tuple[int, Optional[Dict]]:
                - 进程退出码 (-1 表示卡住被终止)
                - 部分结果字典（如果卡住被终止），否则 None

        Raises:
            asyncio.TimeoutError: 超时
            KeyError: 会话不存在
        """
        if session_id not in self._active_sessions:
            raise KeyError(f"Session not found: {session_id}")

        process = self._active_sessions[session_id]
        timeout = timeout or self.timeout_seconds

        # 如果提供了 log_file，启用卡住检测
        if log_file is not None:
            monitor = SessionHealthMonitor(
                log_file=log_file,
                stuck_threshold_seconds=stuck_threshold_seconds,
            )
            start_time = time.time()

            while True:
                # 检查总超时
                elapsed_total = time.time() - start_time
                if elapsed_total > timeout:
                    print(f"[BmadSessionSpawner] Session {session_id} timed out after {timeout}s")
                    process.terminate()
                    await process.wait()
                    raise asyncio.TimeoutError(f"Session {session_id} timed out")

                # 检查进程是否完成
                if hasattr(process, 'popen'):
                    # Windows PopenWrapper
                    if process.popen.poll() is not None:
                        process.returncode = process.popen.returncode
                        return (process.returncode, None)
                else:
                    # Unix asyncio subprocess
                    if process.returncode is not None:
                        return (process.returncode, None)

                # 检查健康状态
                health_status = monitor.check_health(process)

                if health_status == "completed":
                    return (0, None)
                elif health_status == "crashed":
                    return (process.returncode or 1, None)
                elif health_status == "stuck":
                    elapsed_inactive = monitor.get_elapsed_since_activity()
                    print(f"[BmadSessionSpawner] Session {session_id} detected as STUCK")
                    print(f"[BmadSessionSpawner]   No log activity for {elapsed_inactive:.1f}s")
                    print("[BmadSessionSpawner]   Extracting partial results...")

                    # 提取部分结果
                    partial_result = await monitor.extract_partial_result()

                    # 优雅终止
                    print("[BmadSessionSpawner]   Terminating stuck session...")
                    if hasattr(process, 'popen'):
                        process.popen.terminate()
                        await asyncio.sleep(2)
                        if process.popen.poll() is None:
                            process.popen.kill()
                    else:
                        process.terminate()
                        await asyncio.sleep(2)
                        try:
                            process.kill()
                        except ProcessLookupError:
                            pass

                    return (-1, partial_result)

                # 等待检查间隔
                await asyncio.sleep(monitor.check_interval_seconds)

        # 无卡住检测的原始行为
        try:
            returncode = await asyncio.wait_for(process.wait(), timeout=timeout)
            return (returncode, None)
        except asyncio.TimeoutError:
            print(f"[BmadSessionSpawner] Session {session_id} timed out after {timeout}s")
            process.terminate()
            await process.wait()
            raise

    async def get_session_result(
        self,
        phase: Literal["SM", "PO", "DEV", "QA"],
        worktree_path: Path,
    ) -> Optional[SessionResult]:
        """
        获取会话结果

        Args:
            phase: 工作流阶段
            worktree_path: Worktree 目录路径

        Returns:
            解析后的结果对象，如果文件不存在返回 None
        """
        result_file = worktree_path / self.RESULT_FILES[phase]

        if not result_file.exists():
            return None

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse based on phase
            if phase == "SM":
                return SMResult(
                    story_id=data.get("story_id", ""),
                    outcome=data.get("outcome", "ERROR"),
                    timestamp=data.get("timestamp", ""),
                    story_file=data.get("story_file"),
                    title=data.get("title"),
                    sdd_references=data.get("sdd_references", []),
                    adr_references=data.get("adr_references", []),
                    checklist_passed=data.get("checklist_passed", False),
                    raw_data=data,
                )
            elif phase == "PO":
                return POResult(
                    story_id=data.get("story_id", ""),
                    outcome=data.get("outcome", "ERROR"),
                    timestamp=data.get("timestamp", ""),
                    validation_passed=data.get("validation_passed", False),
                    sot_conflicts_found=data.get("sot_conflicts_found", 0),
                    sot_resolutions=data.get("sot_resolutions", []),
                    rejection_reason=data.get("rejection_reason"),
                    raw_data=data,
                )
            elif phase == "DEV":
                # Map 'status' to 'outcome' if Claude used wrong field name
                outcome = data.get("outcome")
                if outcome is None:
                    status = data.get("status", "")
                    # Map common status values to expected outcome values
                    status_to_outcome = {
                        "completed": "SUCCESS",
                        "success": "SUCCESS",
                        "passed": "SUCCESS",
                        "failed": "ERROR",
                        "error": "ERROR",
                        "blocked": "DEV_BLOCKED",
                    }
                    outcome = status_to_outcome.get(status.lower(), "ERROR") if status else "ERROR"

                # Extract test_results if nested (Claude sometimes nests these)
                test_results = data.get("test_results", {})
                tests_passed = data.get("tests_passed", test_results.get("passed", 0) > 0 if test_results else False)
                test_count = data.get("test_count", test_results.get("total", 0))
                test_coverage = data.get("test_coverage", 0.0)

                return DevResult(
                    story_id=data.get("story_id", ""),
                    outcome=outcome,
                    timestamp=data.get("timestamp", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    tests_passed=tests_passed,
                    test_count=test_count,
                    test_coverage=test_coverage,
                    files_created=data.get("files_created", []),
                    files_modified=data.get("files_modified", []),
                    blocking_reason=data.get("blocking_reason"),
                    completion_notes=data.get("completion_notes"),
                    raw_data=data,
                )
            elif phase == "QA":
                # Map 'status' to 'outcome' if Claude used wrong field name
                outcome = data.get("outcome")
                if outcome is None:
                    status = data.get("status", "")
                    status_to_outcome = {
                        "passed": "PASS",
                        "pass": "PASS",
                        "approved": "PASS",
                        "concerns": "CONCERNS",
                        "failed": "FAIL",
                        "fail": "FAIL",
                        "rejected": "FAIL",
                    }
                    outcome = status_to_outcome.get(status.lower(), "ERROR") if status else "ERROR"

                # Handle qa_gate being in different places
                qa_gate = data.get("qa_gate") or data.get("gate") or data.get("decision") or outcome

                return QAResult(
                    story_id=data.get("story_id", ""),
                    outcome=outcome,
                    timestamp=data.get("timestamp", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    qa_gate=qa_gate,
                    quality_score=data.get("quality_score", 0),
                    ac_coverage=data.get("ac_coverage", {}),
                    issues_found=data.get("issues_found", []),
                    recommendations=data.get("recommendations", []),
                    adr_compliance=data.get("adr_compliance", True),
                    fix_attempts=data.get("fix_attempts", 0),
                    raw_data=data,
                )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[BmadSessionSpawner] Error parsing result file: {e}")
            return SessionResult(
                story_id="",
                outcome="PARSE_ERROR",
                timestamp=datetime.now().isoformat(),
                error_message=str(e),
            )

        return None

    def is_session_active(self, session_id: str) -> bool:
        """检查会话是否活跃"""
        if session_id not in self._active_sessions:
            return False
        return self._active_sessions[session_id].returncode is None

    async def kill_session(self, session_id: str) -> bool:
        """
        终止会话

        Args:
            session_id: 会话 ID

        Returns:
            True 如果成功终止，False 如果会话不存在
        """
        if session_id not in self._active_sessions:
            return False

        process = self._active_sessions[session_id]
        if process.returncode is None:
            process.terminate()
            await process.wait()
            print(f"[BmadSessionSpawner] Killed session: {session_id}")

        # Close log file handle if exists
        if hasattr(self, '_log_handles') and session_id in self._log_handles:
            try:
                self._log_handles[session_id].close()
                print(f"[BmadSessionSpawner] Closed log handle for: {session_id}")
            except Exception as e:
                print(f"[BmadSessionSpawner] Error closing log handle: {e}")
            del self._log_handles[session_id]

        del self._active_sessions[session_id]
        return True

    async def cleanup_all(self):
        """终止所有活跃会话并关闭所有日志句柄"""
        for session_id in list(self._active_sessions.keys()):
            await self.kill_session(session_id)

        # Close any remaining log handles
        if hasattr(self, '_log_handles'):
            for _session_id, handle in list(self._log_handles.items()):
                try:
                    handle.close()
                except Exception:
                    pass
            self._log_handles.clear()

    def get_active_session_ids(self) -> list:
        """获取所有活跃会话 ID"""
        return [
            sid for sid, proc in self._active_sessions.items()
            if proc.returncode is None
        ]


# ============================================================================
# Convenience Functions
# ============================================================================

async def run_single_session(
    phase: Literal["SM", "PO", "DEV", "QA"],
    story_id: str,
    worktree_path: Path,
    epic_id: str = "",
    epic_file: str = "",
    story_file: str = "",
    max_turns: int = 200,
    ultrathink: bool = True,
    timeout_seconds: int = 3600,
) -> Optional[SessionResult]:
    """
    运行单个会话并等待结果

    便捷函数，用于简单场景。

    Args:
        phase: 工作流阶段
        story_id: Story ID
        worktree_path: Worktree 目录路径
        epic_id: Epic ID (SM phase)
        epic_file: Epic 文件路径 (SM phase)
        story_file: Story 文件路径 (PO/DEV/QA phases)
        max_turns: 最大轮数
        ultrathink: 启用 UltraThink
        timeout_seconds: 超时时间

    Returns:
        会话结果，超时或错误返回 None
    """
    spawner = BmadSessionSpawner(
        max_turns=max_turns,
        ultrathink=ultrathink,
        timeout_seconds=timeout_seconds,
    )

    try:
        session_id = await spawner.spawn_session(
            phase=phase,
            story_id=story_id,
            worktree_path=worktree_path,
            epic_id=epic_id,
            epic_file=epic_file,
            story_file=story_file,
        )

        # 启用卡住检测
        log_file = worktree_path / f"{phase.lower()}-output.log"
        returncode, partial = await spawner.wait_for_session(
            session_id, log_file=log_file
        )
        return await spawner.get_session_result(phase, worktree_path)

    except asyncio.TimeoutError:
        return SessionResult(
            story_id=story_id,
            outcome="TIMEOUT",
            timestamp=datetime.now().isoformat(),
            error_message=f"Session timed out after {timeout_seconds}s",
        )
    except Exception as e:
        return SessionResult(
            story_id=story_id,
            outcome="ERROR",
            timestamp=datetime.now().isoformat(),
            error_message=str(e),
        )
    finally:
        await spawner.cleanup_all()


if __name__ == "__main__":
    print("BmadSessionSpawner module loaded successfully")
    print("Max turns: 200 (default)")
    print("Timeout: 3600s (default)")
    print("Phases: SM, PO, DEV, QA")
    print(f"Result files: {BmadSessionSpawner.RESULT_FILES}")
