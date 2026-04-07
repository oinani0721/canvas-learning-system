# verification-service Specification

## Purpose
TBD - created by archiving change fix-fr-kg-04-schema-drift-and-sync-hardening. Update Purpose after archive.
## Requirements
### Requirement: Fail-Closed Degraded Scoring

The `VerificationService._mock_evaluate_answer` helper SHALL return a neutral fail-closed result `(quality="unknown", score=0.0)` in ALL invocation paths. It SHALL NOT derive a quality rating or numeric score from the length, pattern, or content of `user_answer`. When the caller propagates the result via `process_answer`, mastery counters (`green_count` / `yellow_count` / `red_count` / `purple_count`) MUST NOT be updated for degraded evaluations, while `completed_concepts` MAY still advance to avoid blocking the user's learning flow.

This requirement exists because length-based or pattern-based heuristic scoring is trivially bypassed by adversarial input (a 101-character noise string scored 90 while a 19-character correct answer scored 20), and because degraded evaluations polluted long-term mastery state across every fallback path (mock mode, agent timeout, agent exception, agent unavailable). Fail-closed is the only safe behavior because the system cannot distinguish good input from adversarial input while the scoring agent is unavailable.

#### Scenario: Short input returns unknown in degraded mode

- **GIVEN** `VerificationService` with an unavailable scoring agent (or `USE_MOCK_VERIFICATION=true`)
- **WHEN** `_mock_evaluate_answer("F=ma")` is called
- **THEN** the return value is `("unknown", 0.0)`
- **AND** no downstream mastery counter is incremented

#### Scenario: Long noise input does NOT outscore short correct input

- **GIVEN** the same degraded state
- **WHEN** `_mock_evaluate_answer("x" * 101)` and `_mock_evaluate_answer("正确答案是F等于ma")` are both called
- **THEN** both return `("unknown", 0.0)`
- **AND** neither result produces a higher mastery signal than the other

#### Scenario: Empty input returns unknown in degraded mode

- **GIVEN** the same degraded state
- **WHEN** `_mock_evaluate_answer("")` is called
- **THEN** the return value is `("unknown", 0.0)`

#### Scenario: Degraded mode does not update mastery counts

- **GIVEN** an active verification session with `green_count=0, yellow_count=0, red_count=0, purple_count=0`
- **AND** the scoring agent is unavailable (degraded=True will be returned)
- **WHEN** the user submits an answer via `process_answer`
- **THEN** the response includes `degraded=true`, `score=0.0`, `quality="unknown"`
- **AND** all four color counters remain at 0
- **AND** `completed_concepts` increments by 1 (user still advances)

#### Scenario: Degraded mode still advances to next concept

- **GIVEN** an active verification session mid-way through a concept queue
- **WHEN** an answer is submitted while the scoring agent is unavailable
- **THEN** the response `action` is `"next"` or `"complete"` (never stuck on `"hint"` loop)
- **AND** `current_concept_idx` advances

#### Scenario: Degraded warning text is user-facing

- **GIVEN** a degraded evaluation response
- **WHEN** the API returns the result to the frontend
- **THEN** the `degraded_warning` field reads "评分服务暂时不可用，本次回答不计分也不更新掌握度。您可以继续下一题。"
- **AND** the `degraded_reason` field is one of: `"mock_mode_enabled"`, `"agent_timeout"`, `"agent_exception"`, `"agent_unavailable"`

#### Scenario: Logger messages do not claim content-based scoring

- **GIVEN** any degraded scoring path (mock mode / timeout / exception / unavailable)
- **WHEN** the `[DEGRADED SCORING]` warning log is emitted
- **THEN** the log message contains the phrase `"mastery state will NOT be updated"`
- **AND** the log message does NOT contain the phrase `"not based on content quality"` (legacy text that implied a numerical score was still assigned)

---

### Requirement: Canvas File Access Defense-in-Depth

The `VerificationService._do_extract_concepts` method SHALL enforce two independent validation layers when reading Canvas files. Method 1 (preferred) SHALL delegate to `CanvasService.read_canvas(canvas_name)` using a logical canvas name, which triggers `CanvasService._validate_canvas_name` to reject traversal patterns. Method 2 (fallback) SHALL NOT use a bare `open()` call; instead it MUST pre-validate the resolved path via `_resolve_safe_canvas_path`, which enforces strict base-directory containment using `pathlib.resolve()` + `Path.relative_to(base)`. If either layer rejects the input, the method SHALL return the fallback concepts `["默认概念"]` rather than attempting an unsafe read.

This requirement exists because the previous fallback path deliberately bypassed `CanvasService._validate_canvas_name` by reading an already-constructed absolute path via `_read_canvas_file_sync`, producing an attack chain where `canvas_name="../../etc/passwd"` could reach the filesystem via: `review.py` string concatenation → `CanvasService.read_canvas` raises `ValidationError` → except clause falls back to `_read_canvas_file_sync(file_path)` → bare `open()` reads the traversal target. CanvasService's validation alone is insufficient because any caller can bypass it; defense-in-depth ensures the second layer is independently effective.

#### Scenario: Dot-dot traversal is rejected

- **GIVEN** `VerificationService` with `_canvas_base_path="/vault"`
- **WHEN** `_resolve_safe_canvas_path("../../etc/passwd", None)` is called
- **THEN** the return value is `None`
- **AND** a WARNING log is emitted identifying the rejected pattern

#### Scenario: Absolute path in canvas_name is rejected

- **GIVEN** the same service
- **WHEN** `_resolve_safe_canvas_path("/etc/passwd", None)` is called
- **THEN** the return value is `None`

#### Scenario: Null byte in canvas_name is rejected

- **GIVEN** the same service
- **WHEN** `_resolve_safe_canvas_path("test\0.canvas", None)` is called
- **THEN** the return value is `None`

#### Scenario: canvas_path that resolves outside base is rejected

- **GIVEN** `_canvas_base_path="/vault/sub"` and a `canvas_path="/vault/other/legitimate.canvas"` that legitimately points outside the configured base
- **WHEN** `_resolve_safe_canvas_path("test", canvas_path)` is called
- **THEN** the return value is `None` because `canvas_path.resolve().relative_to(base)` raises `ValueError`

#### Scenario: Non-canvas suffix is rejected

- **GIVEN** a `canvas_path` pointing to a file inside the base directory but with suffix `.sh` or `.py`
- **WHEN** `_resolve_safe_canvas_path("evil", canvas_path)` is called
- **THEN** the return value is `None` because `resolved.suffix != ".canvas"`

#### Scenario: Valid nested relative canvas_name resolves successfully

- **GIVEN** `_canvas_base_path="/vault"` and a file at `/vault/Math/Lecture5.canvas`
- **WHEN** `_resolve_safe_canvas_path("Math/Lecture5", None)` is called
- **THEN** the return value is the absolute path `/vault/Math/Lecture5.canvas`
- **AND** the path is confirmed to be inside the base directory

#### Scenario: Double .canvas suffix is normalized

- **GIVEN** a canvas_name already containing the `.canvas` suffix
- **WHEN** `_resolve_safe_canvas_path("test.canvas", None)` is called
- **THEN** the resolved path ends with a single `test.canvas`
- **AND** does NOT end with `test.canvas.canvas`

#### Scenario: End-to-end traversal attempt returns fallback concepts

- **GIVEN** an active verification session whose `start_session` receives `canvas_name="../../etc/passwd"`
- **WHEN** `_do_extract_concepts` runs on this canvas_name
- **THEN** `CanvasService.read_canvas` raises `ValidationError` (Method 1 rejects)
- **AND** `_resolve_safe_canvas_path` also returns `None` (Method 2 rejects)
- **AND** the method returns `["默认概念"]`
- **AND** no file outside `_canvas_base_path` is opened

#### Scenario: _read_canvas_file_sync trusts caller validation

- **GIVEN** `_read_canvas_file_sync` is called with a file_path
- **THEN** the method docstring explicitly states that callers MUST pre-validate via `_resolve_safe_canvas_path`
- **AND** the method does NOT re-implement path validation (avoiding drift between two validators)
- **AND** the single reachable caller (`_do_extract_concepts` Method 2) always performs pre-validation before invoking this helper

