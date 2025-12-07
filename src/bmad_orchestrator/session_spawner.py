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

SM_PROMPT_TEMPLATE = '''Execute SM (Scrum Master) Agent for Story Draft Creation.
{ultrathink_section}

===============================================================================
MISSION: Create Story {story_id} from Epic {epic_id}
===============================================================================

**Your Role**: Bob (Scrum Master) - Create complete, self-contained Story draft

**STRICT RULES**:
1. Read core-config.yaml to get document paths
2. Load Epic file from prdShardedLocation
3. Load Architecture docs from architectureShardedLocation
4. Generate Story with COMPLETE Dev Notes (including SDD references)

===============================================================================
PHASE 1: CONTEXT LOADING
===============================================================================
Step 1: Read .bmad-core/core-config.yaml for paths
Step 2: Load Epic file: {epic_file}
Step 3: Load Architecture docs from configured paths
Step 4: Identify Story scope and requirements

===============================================================================
PHASE 2: STORY CREATION
===============================================================================
Step 5: Activate SM Agent: /sm
Step 6: Create Story draft: *draft
Step 7: Ensure Dev Notes include:
   - SDD规范引用 (OpenAPI endpoints, Schema definitions)
   - ADR关联 (Related architecture decisions)
   - 所有技术上下文 (Dev Agent only reads Story file)

===============================================================================
PHASE 3: STORY VALIDATION
===============================================================================
Step 8: Run Story checklist: *story-checklist
Step 9: Verify Section 6 (SDD/ADR) passes:
   - 6.1 SDD规范引用存在性
   - 6.2 ADR关联存在性
   - 6.3 反幻觉验证 (file paths, line numbers)

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 10: Write Story file to: docs/stories/{story_id}.story.md
Step 11: Write .sm-result.json:
{{
  "story_id": "{story_id}",
  "epic_id": "{epic_id}",
  "outcome": "SUCCESS|VALIDATION_FAILED|ERROR",
  "story_file": "docs/stories/{story_id}.story.md",
  "title": "[Story Title]",
  "sdd_references": ["specs/api/...", "specs/data/..."],
  "adr_references": ["docs/architecture/decisions/..."],
  "checklist_passed": true|false,
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT
===============================================================================
- Story must be SELF-CONTAINED (Dev Agent won't load PRD/Architecture)
- Include ALL technical context in Dev Notes
- Verify file paths exist before referencing
'''

PO_PROMPT_TEMPLATE = '''Execute PO (Product Owner) Agent for Story Validation.
{ultrathink_section}

===============================================================================
MISSION: Validate Story {story_id} with SoT Hierarchy
===============================================================================

**Your Role**: Sarah (Product Owner) - Validate Story against PRD and Specs

**STRICT RULES**:
1. Check Story aligns with PRD requirements
2. Verify SDD references are valid
3. Detect and auto-resolve SoT conflicts using hierarchy

**SoT Hierarchy** (highest to lowest):
1. PRD (Level 1) - WHAT
2. Architecture (Level 2) - HOW
3. JSON Schema (Level 3) - Data contracts
4. OpenAPI Spec (Level 4) - API contracts
5. Story (Level 5) - Implementation details
6. Code (Level 6) - Must comply with all above

===============================================================================
PHASE 1: STORY REVIEW
===============================================================================
Step 1: Read Story file: {story_file}
Step 2: Activate PO Agent: /po
Step 3: Validate Story: *validate-story-draft {story_id}

===============================================================================
PHASE 2: SoT CONFLICT DETECTION
===============================================================================
Step 4: Load PRD sections related to Story scope
Step 5: Load OpenAPI specs referenced in Story
Step 6: Load JSON Schemas referenced in Story
Step 7: Detect any conflicts between documents

===============================================================================
PHASE 3: AUTO-RESOLUTION (if conflicts found)
===============================================================================
Step 8: Apply SoT Hierarchy:
   - Higher level document wins
   - Auto-resolve Phase 4 conflicts (OpenAPI > Story)
   - Record all resolutions

Step 9: Update Story if needed (to match higher-level docs)

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 10: **MUST** use the Write tool to create `.po-result.json` file.

**IMPORTANT**: You MUST actually execute the Write tool to create the file.
Do NOT just output the JSON content - you must USE the Write tool.

Use Write tool with file_path=".po-result.json" and content:
{{
  "story_id": "{story_id}",
  "outcome": "APPROVED|REJECTED|AUTO_RESOLVED",
  "validation_passed": true|false,
  "sot_conflicts_found": 0,
  "sot_resolutions": [
    {{
      "conflict_type": "PRD_VS_OPENAPI|SCHEMA_VS_OPENAPI|...",
      "source_a": "docs/prd/section-2.md#L45",
      "source_b": "specs/api/canvas-api.openapi.yml#L156",
      "field_name": "response_format",
      "value_a": "JSON",
      "value_b": "MessagePack",
      "resolution": "JSON (PRD wins)",
      "sot_level_applied": "PRD"
    }}
  ],
  "rejection_reason": null|"[reason]",
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
DECISION LOGIC
===============================================================================
- APPROVED: Story aligns with PRD, SDD valid, no conflicts
- AUTO_RESOLVED: Conflicts found but auto-resolved via hierarchy
- REJECTED: Critical issues that cannot be auto-resolved
'''

DEV_PROMPT_TEMPLATE = '''Execute Dev (Developer) Agent for Story Implementation.
{ultrathink_section}

===============================================================================
MISSION: Implement Story {story_id}
===============================================================================

**Your Role**: James (Developer) - Implement Story with tests

**STRICT RULES**:
1. ONLY read Story file - it contains ALL needed context
2. Follow devLoadAlwaysFiles for coding standards
3. Write tests BEFORE proceeding to QA
4. Update .worktree-status.yaml at each decision point

===============================================================================
PHASE 1: CONTEXT LOADING
===============================================================================
Step 1: Read Story file: {story_file}
Step 2: Read devLoadAlwaysFiles from core-config.yaml:
   - docs/architecture/coding-standards.md
   - specs/api/canvas-api.openapi.yml
   - specs/data/*.schema.json

===============================================================================
PHASE 2: IMPLEMENTATION
===============================================================================
Step 3: Activate Dev Agent: /dev
Step 4: Implement Story: *develop-story {story_id}
Step 5: Follow Dev Notes in Story for:
   - API endpoint implementation
   - Data model implementation
   - Integration points

===============================================================================
PHASE 3: TESTING
===============================================================================
Step 6: Run tests: *run-tests
Step 7: Ensure test coverage ≥ 80%

**DECISION POINT - TEST RESULTS**:
- If ALL tests PASS:
  - Update .worktree-status.yaml: status="dev-complete", tests_passed=true
  - PROCEED to output
- If ANY test FAILS:
  - Update .worktree-status.yaml: status="dev-blocked", tests_passed=false
  - Write .dev-result.json with outcome="DEV_BLOCKED"
  - HALT WORKFLOW HERE

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 8: Write .dev-result.json:
{{
  "story_id": "{story_id}",
  "outcome": "SUCCESS|DEV_BLOCKED|TIMEOUT|ERROR",
  "tests_passed": true|false,
  "test_count": [number],
  "test_coverage": [percentage],
  "files_created": ["path/to/new.py", ...],
  "files_modified": ["path/to/existing.py", ...],
  "duration_seconds": [seconds],
  "blocking_reason": null|"[reason]",
  "completion_notes": "[summary]",
  "agent_model": "claude-sonnet-4-5",
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT
===============================================================================
- Do NOT load PRD or Architecture (Story has all context)
- Follow SDD references in Dev Notes exactly
- Write production-ready code with proper error handling
'''

QA_PROMPT_TEMPLATE = '''Execute QA (Quality Assurance) Agent for Story Review.
{ultrathink_section}

===============================================================================
MISSION: QA Review for Story {story_id}
===============================================================================

**Your Role**: Quinn (Test Architect) - Comprehensive QA review

**STRICT RULES**:
1. Run full QA sequence: trace → nfr-assess → review → gate
2. Generate quality gate decision
3. Only PASS/WAIVED allows proceeding to commit

===============================================================================
PHASE 1: QA REVIEW
===============================================================================
Step 1: Activate QA Agent: /qa
Step 2: Trace requirements: *trace {story_id}
Step 3: NFR assessment: *nfr-assess {story_id}
Step 4: Code review: *review {story_id}

===============================================================================
PHASE 2: QUALITY GATE
===============================================================================
Step 5: Gate decision: *gate {story_id}

**DECISION LOGIC**:
- **PASS**: All critical requirements met, proceed to commit
- **CONCERNS**: Non-critical issues, attempt 1 fix cycle
- **FAIL**: Critical issues (security, P0 tests missing), HALT
- **WAIVED**: Issues acknowledged but accepted, proceed

===============================================================================
PHASE 3: FIX CYCLE (if CONCERNS)
===============================================================================
If gate = CONCERNS:
  Step 6: Document issues to fix
  Step 7: Re-run gate: *gate {story_id}
  Step 8: If still CONCERNS after 1 attempt, record and HALT

===============================================================================
PHASE 4: OUTPUT (CRITICAL - MUST USE Write TOOL)
===============================================================================
Step 9: Write .qa-result.json:
{{
  "story_id": "{story_id}",
  "qa_gate": "PASS|CONCERNS|FAIL|WAIVED",
  "quality_score": [0-100],
  "ac_coverage": {{
    "AC1": {{"status": "PASS|FAIL", "evidence": "[test or file]"}},
    "AC2": {{"status": "PASS|FAIL", "evidence": "[test or file]"}}
  }},
  "issues_found": [
    {{"severity": "low|medium|high", "description": "[issue]", "location": "[file:line]"}}
  ],
  "recommendations": ["[recommendation 1]", "[recommendation 2]"],
  "adr_compliance": true|false,
  "fix_attempts": 0|1,
  "duration_seconds": [seconds],
  "reviewer_model": "claude-sonnet-4-5",
  "timestamp": "[ISO timestamp]"
}}

===============================================================================
IMPORTANT
===============================================================================
- Be rigorous but fair in assessment
- Document all issues with specific locations
- Security issues = automatic FAIL
- Missing P0 tests = automatic FAIL
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

            # Write prompt to worktree for debugging
            debug_prompt_file = worktree_path / '.bmad-prompt.txt'
            try:
                with open(debug_prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt)
            except Exception:
                pass  # Ignore errors writing debug file

            # Build command with prompt as the last argument
            # -p mode accepts prompt as positional argument
            full_cmd = cmd + [prompt]
            cmd_str = ' '.join(f'"{arg}"' if ' ' in arg or '\n' in arg else arg for arg in full_cmd)

            # Set UTF-8 environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # Open log file for writing output from reader threads
            log_handle = open(str(log_file), 'a', encoding='utf-8', buffering=1)

            # Start process with PIPE for stdout/stderr
            popen_process = sp.Popen(
                cmd_str,
                shell=True,
                cwd=str(worktree_path),
                stdin=sp.DEVNULL,
                stdout=sp.PIPE,  # ✅ FIX v13: Use PIPE instead of file redirect
                stderr=sp.PIPE,  # ✅ FIX v13: Separate stderr for debugging
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env,
            )

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
                    except:
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
                return DevResult(
                    story_id=data.get("story_id", ""),
                    outcome=data.get("outcome", "ERROR"),
                    timestamp=data.get("timestamp", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    tests_passed=data.get("tests_passed", False),
                    test_count=data.get("test_count", 0),
                    test_coverage=data.get("test_coverage", 0.0),
                    files_created=data.get("files_created", []),
                    files_modified=data.get("files_modified", []),
                    blocking_reason=data.get("blocking_reason"),
                    completion_notes=data.get("completion_notes"),
                    raw_data=data,
                )
            elif phase == "QA":
                return QAResult(
                    story_id=data.get("story_id", ""),
                    outcome=data.get("outcome", "ERROR"),
                    timestamp=data.get("timestamp", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    qa_gate=data.get("qa_gate"),
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
            for session_id, handle in list(self._log_handles.items()):
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
