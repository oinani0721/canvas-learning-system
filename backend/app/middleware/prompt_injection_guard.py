"""
Prompt Injection Guard Middleware (Story 7.1, Tasks 2 and 3)

Implements OWASP LLM Top 10 2025 three-layer defense against prompt injection:

Layer 1 - Structural Isolation: PromptTemplate builder enforces system/user
          message separation. User input never enters system messages.

Layer 2 - Input Detection: Heuristic rule engine detects known injection
          patterns (role override, encoding bypass, delimiter manipulation,
          multilingual variants). Risk scoring with configurable threshold.

Layer 3 - Output Safety Check: Detects system prompt leakage, role override
          instructions, and malicious code execution directives in LLM output.

References:
- OWASP LLM Top 10 2025: LLM01 Prompt Injection (number 1 risk)
  https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP Prompt Injection Prevention Cheat Sheet
  https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
"""

import base64
import codecs
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import List

import structlog

logger = logging.getLogger(__name__)
struct_logger = structlog.get_logger("prompt_injection_guard")

INJECTION_THRESHOLD = float(os.getenv("INJECTION_THRESHOLD", "0.7"))
INJECTION_GUARD_ENABLED = os.getenv("INJECTION_GUARD_ENABLED", "true").lower() == "true"
SYSTEM_BOUNDARY_MARKER = "<!-- SYSTEM_BOUNDARY_f7a9c2e1 -->"

# Story 3.13 AC-2: Safety degradation response messages
SAFETY_BLOCK_INPUT_MESSAGE = (
    "\u68c0\u6d4b\u5230\u5f02\u5e38\u8f93\u5165\u6a21\u5f0f"
    "\uff0c\u8bf7\u91cd\u65b0\u8868\u8ff0\u60a8\u7684\u95ee\u9898\u3002"
    "\u5982\u679c\u8fd9\u662f\u6b63\u5e38\u5b66\u4e60\u5185\u5bb9"
    "\uff0c\u8bf7\u5c1d\u8bd5\u7528\u4e0d\u540c\u7684\u65b9\u5f0f\u63d0\u95ee\u3002"
)
SAFETY_BLOCK_OUTPUT_PREFIX = (
    "[\u5b89\u5168\u63d0\u793a] AI \u8f93\u51fa\u4e2d\u68c0\u6d4b\u5230"
    "\u6f5c\u5728\u4e0d\u5b89\u5168\u5185\u5bb9\uff0c\u5df2\u8fc7\u6ee4\u5904\u7406\u3002"
)


@dataclass
class InjectionCheckResult:
    """Result of input injection detection check."""

    risk_score: float
    is_blocked: bool
    matched_patterns: List[str] = field(default_factory=list)
    details: str = ""


@dataclass
class OutputCheckResult:
    """Result of output safety check."""

    is_safe: bool
    violations: List[str] = field(default_factory=list)
    sanitized_output: str = ""
    details: str = ""


class PromptTemplate:
    """Enforces structural isolation between system and user messages."""

    @staticmethod
    def build(system_prompt, user_input, context="", assistant_prefix=""):
        messages = [
            {
                "role": "system",
                "content": f"{system_prompt}\n\n{SYSTEM_BOUNDARY_MARKER}",
            }
        ]
        if context:
            messages.append(
                {"role": "user", "content": f"Reference context:\n---\n{context}\n---"}
            )
        messages.append({"role": "user", "content": user_input})
        if assistant_prefix:
            messages.append({"role": "assistant", "content": assistant_prefix})
        return messages

    @staticmethod
    def validate_messages(messages):
        if not messages:
            return False
        if messages[0].get("role") != "system":
            return False
        if SYSTEM_BOUNDARY_MARKER not in messages[0].get("content", ""):
            return False
        return True


DIRECT_INJECTION_PATTERNS = [
    (
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        0.95,
        "role_override:ignore_previous",
    ),
    (
        re.compile(r"forget\s+(everything|all)\s+(above|before)", re.IGNORECASE),
        0.95,
        "role_override:forget_above",
    ),
    (
        re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
        0.85,
        "role_override:you_are_now",
    ),
    (
        re.compile(r"act\s+as\s+(DAN|a\s+new|an?\s+unrestricted)", re.IGNORECASE),
        0.90,
        "role_override:act_as_dan",
    ),
    (
        re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
        0.85,
        "role_override:new_instructions",
    ),
    (
        re.compile(
            r"(system|assistant)\s*:\s*(you\s+must|new\s+task|override)", re.IGNORECASE
        ),
        0.90,
        "role_override:system_prefix",
    ),
    (
        re.compile(r"---\s*SYSTEM\s*---", re.IGNORECASE),
        0.95,
        "delimiter:spoofed_system_block",
    ),
    (
        re.compile(
            r"(repeat|print|output|reveal|show)\s+(the\s+)?(above\s+)?(system\s+)?(message|prompt|instructions?)",
            re.IGNORECASE,
        ),
        0.85,
        "output_manipulation:reveal_prompt",
    ),
    (
        re.compile(r"what\s+are\s+your\s+instructions", re.IGNORECASE),
        0.80,
        "output_manipulation:ask_instructions",
    ),
    (
        re.compile(
            r"(list|display|tell\s+me)\s+(your|the)\s+(initial\s+)?(prompt|instructions|rules)",
            re.IGNORECASE,
        ),
        0.80,
        "output_manipulation:list_prompt",
    ),
    (
        re.compile(r"print\s+your\s+initial\s+prompt", re.IGNORECASE),
        0.90,
        "output_manipulation:print_initial_prompt",
    ),
]

CHINESE_INJECTION_PATTERNS = [
    (
        re.compile(r"(请|你)?忽略(之前|以前|上面)(的)?(所有)?指令", re.IGNORECASE),
        0.95,
        "role_override:chinese_ignore_previous",
    ),
    (
        re.compile(r"你现在是一个(没有|不受)(任何)?限制", re.IGNORECASE),
        0.90,
        "role_override:chinese_no_restrictions",
    ),
    (
        re.compile(r"输出(你的)?系统(提示词|指令|消息)", re.IGNORECASE),
        0.85,
        "output_manipulation:chinese_reveal_prompt",
    ),
    (
        re.compile(r"(忘记|无视)(之前|以前|上面)(的)?(一切|所有|全部)", re.IGNORECASE),
        0.90,
        "role_override:chinese_forget_above",
    ),
]

DELIMITER_PATTERNS = [
    (re.compile(r"<\|system\|>", re.IGNORECASE), 0.95, "delimiter:chatml_system_tag"),
    (re.compile(r"<\|user\|>", re.IGNORECASE), 0.85, "delimiter:chatml_user_tag"),
    (
        re.compile(r"<\|assistant\|>", re.IGNORECASE),
        0.85,
        "delimiter:chatml_assistant_tag",
    ),
    (
        re.compile(r"#{3,}\s*(SYSTEM|OVERRIDE|INSTRUCTION)", re.IGNORECASE),
        0.80,
        "delimiter:markdown_header_injection",
    ),
    (
        re.compile(r"<!--\s*(AI\s+INSTRUCTION|SYSTEM\s+OVERRIDE)", re.IGNORECASE),
        0.90,
        "delimiter:html_comment_injection",
    ),
    (
        re.compile(r"\[SYSTEM\s+OVERRIDE\]", re.IGNORECASE),
        0.90,
        "delimiter:bracket_system_override",
    ),
]

INDIRECT_INJECTION_PATTERNS = [
    (
        re.compile(
            r"(when\s+summarizing|when\s+answering|when\s+processing).*?(also|instead)\s+(reveal|output|show)",
            re.IGNORECASE,
        ),
        0.85,
        "indirect:conditional_reveal",
    ),
    (
        re.compile(
            r"(this\s+)?(node|content|note).*?should\s+be\s+treated\s+as\s+(system\s+)?instructions?",
            re.IGNORECASE,
        ),
        0.90,
        "indirect:content_as_instruction",
    ),
    (
        re.compile(r"new\s+task\s*:\s*disregard", re.IGNORECASE),
        0.90,
        "indirect:new_task_disregard",
    ),
]

OUTPUT_LEAK_PATTERNS = [
    (
        re.compile(re.escape(SYSTEM_BOUNDARY_MARKER)),
        "system_prompt_leak:boundary_marker",
    ),
    (
        re.compile(
            r"(my|the)\s+(system\s+)?(prompt|instructions?)\s+(is|are|says?)\s*:",
            re.IGNORECASE,
        ),
        "system_prompt_leak:self_disclosure",
    ),
    (
        re.compile(r"(I\s+was|I\s+am)\s+instructed\s+to", re.IGNORECASE),
        "system_prompt_leak:instruction_disclosure",
    ),
]

OUTPUT_ROLE_OVERRIDE_PATTERNS = [
    (
        re.compile(r"(execute|run|eval)\s*\(\s*['\"].*['\"]\s*\)", re.IGNORECASE),
        "dangerous_output:code_execution",
    ),
    (
        re.compile(
            r"(os\.system|subprocess\.(run|call|Popen)|exec\(|eval\()", re.IGNORECASE
        ),
        "dangerous_output:system_command",
    ),
    (
        re.compile(
            r"(curl|wget|fetch)\s+https?://.*\|\s*(bash|sh|python)", re.IGNORECASE
        ),
        "dangerous_output:remote_code_execution",
    ),
    (
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        "dangerous_output:xss_script",
    ),
]


def _try_decode_base64(text):
    b64_pattern = re.compile(r"[A-Za-z0-9+/=]{20,}")
    matches = b64_pattern.findall(text)
    for match in matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            if decoded.isprintable() and len(decoded) > 5:
                return decoded
        except (ValueError, UnicodeDecodeError):
            continue
    return None


def _try_decode_hex(text):
    hex_pattern = re.compile(r"[0-9a-fA-F]{20,}")
    matches = hex_pattern.findall(text)
    for match in matches:
        try:
            if len(match) % 2 != 0:
                continue
            decoded = bytes.fromhex(match).decode("utf-8", errors="ignore")
            if decoded.isprintable() and len(decoded) > 5:
                return decoded
        except (ValueError, UnicodeDecodeError):
            continue
    return None


def _try_decode_rot13(text):
    return codecs.decode(text, "rot_13")


def check_input(text):
    """Layer 2: Check user input for prompt injection patterns."""
    if not INJECTION_GUARD_ENABLED:
        return InjectionCheckResult(
            risk_score=0.0, is_blocked=False, details="Guard disabled"
        )
    if not text or not text.strip():
        return InjectionCheckResult(
            risk_score=0.0, is_blocked=False, details="Empty input"
        )

    start_time = time.perf_counter()
    max_score = 0.0
    matched = list()

    all_patterns = (
        DIRECT_INJECTION_PATTERNS
        + CHINESE_INJECTION_PATTERNS
        + DELIMITER_PATTERNS
        + INDIRECT_INJECTION_PATTERNS
    )
    for pattern, score, label in all_patterns:
        if pattern.search(text):
            matched.append(label)
            max_score = max(max_score, score)

    decoded_b64 = _try_decode_base64(text)
    if decoded_b64:
        for pattern, score, label in DIRECT_INJECTION_PATTERNS:
            if pattern.search(decoded_b64):
                matched.append(f"encoding_bypass:base64:{label}")
                max_score = max(max_score, score)

    decoded_hex = _try_decode_hex(text)
    if decoded_hex:
        for pattern, score, label in DIRECT_INJECTION_PATTERNS:
            if pattern.search(decoded_hex):
                matched.append(f"encoding_bypass:hex:{label}")
                max_score = max(max_score, score)

    rot13_text = _try_decode_rot13(text)
    for pattern, score, label in DIRECT_INJECTION_PATTERNS:
        if pattern.search(rot13_text):
            rot13_label = f"encoding_bypass:rot13:{label}"
            if rot13_label not in matched and label not in matched:
                matched.append(rot13_label)
                max_score = max(max_score, score)

    is_blocked = max_score >= INJECTION_THRESHOLD
    latency_ms = (time.perf_counter() - start_time) * 1000
    result = InjectionCheckResult(
        risk_score=max_score,
        is_blocked=is_blocked,
        matched_patterns=matched,
        details=f"Checked {len(text)} chars in {latency_ms:.1f}ms",
    )
    if matched:
        _log_injection_detection(result, text, latency_ms)
    return result


def check_output(output, system_prompt=""):
    """Layer 3: Check LLM output for safety violations."""
    if not output or not output.strip():
        return OutputCheckResult(is_safe=True, sanitized_output=output)

    violations = list()
    sanitized = output

    for pattern, label in OUTPUT_LEAK_PATTERNS:
        if pattern.search(output):
            violations.append(label)

    if system_prompt and len(system_prompt) > 20:
        window_size = min(50, len(system_prompt) // 3)
        if window_size > 10:
            for i in range(0, len(system_prompt) - window_size, 10):
                chunk = system_prompt[i : i + window_size]
                if chunk in output:
                    violations.append("system_prompt_leak:verbatim_content")
                    break

    for pattern, label in OUTPUT_ROLE_OVERRIDE_PATTERNS:
        if pattern.search(output):
            violations.append(label)

    if violations:
        sanitized = _sanitize_output(output, violations)

    is_safe = len(violations) == 0
    return OutputCheckResult(
        is_safe=is_safe,
        violations=violations,
        sanitized_output=sanitized,
        details=f"Found {len(violations)} violation(s)" if violations else "Clean",
    )


def _sanitize_output(output, violations):
    sanitized = output
    sanitized = sanitized.replace(SYSTEM_BOUNDARY_MARKER, "")
    has_dangerous = any(v.startswith("dangerous_output:") for v in violations)
    if has_dangerous:
        sanitized = (
            "[Safety Notice: Potentially unsafe content has been filtered.]\n\n"
            + sanitized
        )
        sanitized = re.sub(
            r"<script[^>]*>.*?</script>",
            "[removed: script content]",
            sanitized,
            flags=re.IGNORECASE | re.DOTALL,
        )
    return sanitized


def _log_injection_detection(result, input_text, latency_ms):
    try:
        struct_logger.warning(
            "injection_detection",
            check_type="prompt_injection",
            risk_score=result.risk_score,
            is_blocked=result.is_blocked,
            matched_patterns=result.matched_patterns,
            input_length=len(input_text),
            input_preview=input_text[:100] + "..."
            if len(input_text) > 100
            else input_text,
            latency_ms=round(latency_ms, 2),
        )
    except (ValueError, TypeError, RuntimeError, OSError) as e:
        logger.error(f"[prompt_injection_guard] Failed to emit structured log: {e}")
