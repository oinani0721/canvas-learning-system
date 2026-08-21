#!/usr/bin/env python3
"""Fail-closed GOV-01 static toolchain acquisition executor (Python 3.9 stdlib).

This draft intentionally never invokes Node, npm, npx, JavaScript, OpenSpec, or
installed package code.  Public stdout is a small JSON projection; private
locators and detailed manifests are written only to an owner-only state root.
"""

import argparse
import base64
import binascii
import copy
import ctypes
import datetime as _datetime
import errno
import hashlib
import hmac
import json
import os
import platform
import posixpath
import re
import stat
import subprocess
import sys
import sysconfig
import types
import unicodedata
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit


class Exit(IntEnum):
    OK = 0
    USAGE = 10
    CONTRACT = 11
    RECEIPT = 12
    EXPIRED = 13
    REPLAY = 14
    PRIVATE_STATE = 15
    CHECKER_DRIFT = 16
    PREFLIGHT_DRIFT = 20
    UNSAFE_PATH = 21
    RUNTIME = 22
    CACHE_LOCK = 23
    ARCHIVE = 24
    TRACE = 25
    EXTRACT = 30
    BIN_LINK = 31
    SEAL = 32
    PRE_WORKTREE_CAS = 40
    PROMOTE = 41
    POST_INSTALL = 50
    GIT_CONTAINMENT = 51
    PRIVACY = 55
    ROLLBACK = 60
    EVIDENCE = 61
    INTERNAL = 70


class ContractError(Exception):
    def __init__(
        self,
        code: Exit,
        public_code: str,
        public_payload: Optional[Mapping[str, Any]] = None,
    ):
        super().__init__(public_code)
        self.code = code
        self.public_code = public_code
        # Preserve AuthorityBoundPublicResult's non-serialized checker input
        # across command_* -> ContractError -> main -> emit.
        self.public_payload = copy.deepcopy(public_payload) if public_payload is not None else None


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse normally echoes user-controlled values (including paths) to stderr.
        del message
        fail(Exit.USAGE, "USAGE")


SCRIPT_VERSION = "gov01-static-acquisition-executor-draft-v2"
VAULT_PREFIX = "canvas-vault"
EXPECTED_PLATFORM = "darwin"
EXPECTED_ARCH = "arm64"
EXPECTED_SELECTED_PACKAGES = 167
EXPECTED_BIN_LINKS = 12
EXPECTED_TREE_SHA256 = "777dc62b5a2094903c2047cb30bc63eccf34543c3d4466be30b6ae4789d391a2"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_GIT_OUTPUT = 32 * 1024 * 1024
MAX_CACHE_OBJECT_BYTES = 512 * 1024 * 1024
CHALLENGE_RE = re.compile(r"\AGOV01-SA-[0-9]{8}-[0-9a-f]{32,64}\Z")
SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
PACKAGE_COMPONENT_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._~-]*\Z")
RECEIPT_DOMAINS = {
    "gov-01-toolchain-acquisition-envelope-v1": b"CLS/GOV01-TOOLCHAIN-ACQUISITION-RECEIPT/v1",
    "gov-01-toolchain-static-acquisition-envelope-v2": b"CLS/GOV01-TOOLCHAIN-STATIC-ACQUISITION-RECEIPT/v2",
}
PRIVATE_EVIDENCE_DOMAIN = b"CLS/GOV01/PRIVATE-PREAPPROVAL/v2"
PRIVATE_CONTROL_IDENTITY_DOMAIN = b"CLS/GOV01/PRIVATE-CONTROL-IDENTITY/v2"
PRIVATE_LOCATOR_DOMAIN = b"CLS/GOV01/PRIVATE-LOCATOR/v2"
HMAC_KEY_ID_DOMAIN = b"CLS/GOV01/HMAC-KEY-ID/v2"
GIT_SNAPSHOT_DOMAIN = b"CLS/GOV01/GIT-SNAPSHOT/v2"
GIT_DIRTY_MANIFEST_DOMAIN = b"CLS/GOV01/GIT-DIRTY-CONTENT/v2"
PUBLIC_ARTIFACT_SET_DOMAIN = b"CLS/GOV01/PUBLIC-ARTIFACT-SET/v2"
TOOLCHAIN_SET_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-TOOLCHAIN-SET/v2"
TOOL_TREE_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-TOOL-TREE-MERKLE/v2\x00"
DYNAMIC_TOOLCHAIN_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-DYNAMIC-CLOSURE/v2"
LEDGER_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-LEDGER/v2"
LEDGER_CHECKER_INTERFACE = "gov01-ledger-semantic-checker-v2"
GATE_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-GATE/v2"
GATE_SET_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-GATE-SET/v2"
PUBLIC_RESULT_SCHEMA_VERSION = "gov-01-toolchain-static-acquisition-public-result-v2"
PUBLIC_RESULT_ARTIFACT_TYPE = "gov-01-toolchain-static-acquisition-public-result"
MARKER_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-INCOMPLETE/v2"
VERIFIER_RELATIVE = "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py"
EXECUTOR_RELATIVE = "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py"
INCOMPLETE_MARKER = ".gov01-incomplete"
TARGET_NAME = "node_modules"
MAX_COMPRESSED_CLOSURE = 14_000_000
MAX_PAYLOAD_CLOSURE = 64_000_000
RENAME_EXCL = 0x00000004
SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-pending-envelope:v2:draft"
PRIVATE_SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-private-evidence:v2:draft"
PUBLIC_SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-public-attestation:v2:draft"
CONTROL_PREFIX = "_bmad-output/审查/phase0a-annotation-truth/"
PROTECTED_CONTROL_PATHS = ("package.json", "package-lock.json", ".gitignore")
ABSENT_CONTROL_PATHS = (".npmrc", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb")
TOOLCHAIN_ROLES = (
    "static-executor",
    "static-verifier",
    "python-interpreter",
    "python-stdlib-tree",
    "xcode-select-resolver",
    "xcrun-resolver",
    "git-read-only-evidence",
    "pgrep-read-only-evidence",
    "lsof-read-only-evidence",
)
GATE_SCOPES = (
    ("G00", "schema-and-public-projection"),
    ("G01", "single-use-authorization-ledger"),
    ("G02", "private-public-boundary"),
    ("G03", "content-addressed-toolchain"),
    ("G04", "authorized-child-process-static-structural-ceiling"),
    ("G05", "source-content-receipt"),
    ("G06", "ustar-member-receipt"),
    ("G07", "ustar-format-header"),
    ("G08", "member-path-type"),
    ("G09", "resource-limits"),
    ("G10", "control-root-before"),
    ("G11", "target-preimage"),
    ("G12", "process-census-before"),
    ("G13", "stage-scope-device"),
    ("G14", "expected-closure"),
    ("G15", "resolution-receipt"),
    ("G16", "stage-tree-merkle"),
    ("G17", "payload-and-lifecycle-static-structural-ceiling"),
    ("G18", "rename-excl-publication"),
    ("G19", "control-root-after"),
    ("G20", "outside-scope-postimage"),
    ("G21", "final-tree-merkle"),
    ("G22", "process-census-after"),
    ("G23", "ledger-terminal"),
    ("G24", "privacy-redaction"),
)
GATE_SCOPE_BY_ID = dict(GATE_SCOPES)
GATE_PHASE_BY_ID = dict(GATE_SCOPES)
GATE_PHASE_BY_ID["G00"] = "schema-contract"
TOOLCHAIN_ROLE_PROFILE = {
    "static-executor": ("regular-file", "raw-file-sha256", "read-as-python-source-by-bound-interpreter"),
    "static-verifier": ("regular-file", "raw-file-sha256", "read-as-python-source-by-bound-interpreter"),
    "python-interpreter": ("regular-file", "raw-file-sha256", "execute-as-bound-interpreter"),
    "python-stdlib-tree": (
        "directory-tree",
        "CLS/GOV01/STATIC-ACQUISITION-TOOL-TREE-MERKLE/v2",
        "read-only-tree-never-directly-executed",
    ),
    "xcode-select-resolver": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
    "xcrun-resolver": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
    "git-read-only-evidence": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
    "pgrep-read-only-evidence": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
    "lsof-read-only-evidence": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
}
FIXED_TOOL_PATHS = {
    "xcode-select-resolver": "/usr/bin/xcode-select",
    "xcrun-resolver": "/usr/bin/xcrun",
    "pgrep-read-only-evidence": "/usr/bin/pgrep",
    "lsof-read-only-evidence": "/usr/sbin/lsof",
}
_AUTHORIZED_EXECUTABLE_HASHES: Dict[str, str] = {}
_ACL_FUNCTIONS: Optional[Tuple[Any, Any, Any]] = None
ALLOWED_CHILD_ENV_NAMES = frozenset(
    {
        "PATH", "HOME", "LC_ALL", "LANG", "GIT_OPTIONAL_LOCKS", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_TERMINAL_PROMPT", "GIT_NO_REPLACE_OBJECTS",
        "GIT_PROTOCOL_FROM_USER", "GIT_ALLOW_PROTOCOL",
        "GIT_ATTR_NOSYSTEM", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
)
TOP_LEVEL_FIELDS = frozenset(
    "schema_version artifact_type artifact_id plan_id state approval_challenge_id single_use census_at_utc "
    "not_after_utc path_base encoding_profile receipt_digest_profile approval_receipt_contract predecessor "
    "artifacts artifact_path_uniqueness_policy authorization_preimage frozen_toolchain schema_binding "
    "static_acquisition_contract lock_closure execution_plan mutation_scope failure_contract success_contract "
    "private_state_authorization privacy".split()
)
AUTHORIZATION_PREIMAGE_FIELDS = frozenset(
    "head_commit_oid head_tree_oid git_object_format git_snapshot_commitment git_snapshot_commitment_profile "
    "private_preapproval_commitment private_preapproval_commitment_profile public_repo_artifact_set_receipt_sha256 "
    "private_preimage_capture worktree_state preexisting_dirty_policy target_preimage acquisition_control_root_state "
    "protected_existing_control_paths protected_existing_control_state absent_control_paths absent_control_state "
    "node_modules_state target_worktree_claude_sessions forbidden_process_match_count "
    "node_modules_parent_or_sibling_reuse_allowed private_vault_census_allowed".split()
)
SCHEMA_BINDING_FIELDS = frozenset(
    "schema_id schema_artifact_path schema_raw_file_sha256 schema_artifact_role external_validator_profile "
    "preapproval_external_validation_required runtime_json_schema_execution_allowed runtime_schema_hash_binding_required "
    "runtime_manual_critical_field_checks_required runtime_checkpoint schema_digest_must_equal_artifact_entry "
    "validation_failure_action".split()
)
STATIC_CONTRACT_FIELDS = frozenset(
    "verifier_profile_version verifier_artifact_path verifier_sha256 executor_artifact_path executor_sha256 "
    "stage_repo_relative target_repo_relative compressed_blobs_memory_resident_before_write "
    "payload_bytes_memory_resident_before_write hidden_package_lock_generation_allowed expected "
    "node_execution_allowed npm_execution_allowed openspec_execution_allowed openspec_scaffold_allowed "
    "lifecycle_execution_allowed network_allowed protected_control_paths protected_control_pre_post_hash_check_required "
    "absent_control_paths absent_control_pre_post_lstat_check_required".split()
)
STATIC_EXPECTED_FIELDS = frozenset(
    "profile_version package_json_sha256 package_lock_sha256 lockfile_version lock_package_count selected_package_count "
    "excluded_platform_package_count compressed_bytes tar_stream_bytes payload_bytes raw_member_count raw_regular_count "
    "raw_directory_count bin_link_count lifecycle_field_count content_receipt_body_bytes content_receipt_sha256 "
    "ustar_closure_body_bytes ustar_closure_sha256 resolution tree".split()
)
LOCK_CLOSURE_FIELDS = frozenset(
    "source_kind host_selected_package_count host_selected_cache_bytes host_bin_link_count expected_archive_member_count "
    "expected_resolved_tree_entry_count content_receipt_profile content_receipt_sha256 ustar_closure_receipt_profile "
    "ustar_closure_sha256 resolution_receipt_profile resolution_receipt_sha256 expected_tree_receipt_profile "
    "expected_tree_sha256 resource_limits archive_member_types generated_symlink_policy source_locator_policy "
    "direct_sri_policy network_fetch_allowed".split()
)
LOCK_OBSERVATION_FIELDS = frozenset(
    "host_selected_package_count host_selected_cache_bytes host_bin_link_count "
    "expected_archive_member_count expected_resolved_tree_entry_count content_receipt_sha256 "
    "ustar_closure_sha256 resolution_receipt_sha256 expected_tree_sha256".split()
)
EXECUTION_PLAN_FIELDS = frozenset(
    "attempt_policy phase_order runner executor_interface_state executor_interface_version executor_argv_template "
    "executor_argv_template_sha256 verifier_profile_version verifier_census_argv_template "
    "verifier_installed_argv_template evidence_command_templates evidence_command_templates_sha256 expiry_checkpoints "
    "environment_mode environment_name_allowlist ustar_parser compression_policy ustar_safety_policy member_type_policy "
    "duplicate_collision_policy launcher_executable_role allowed_subprocess_executable_roles forbidden_executable_names "
    "shell_allowed subprocess_from_executor_allowed archive_or_payload_execution_allowed network_allowed "
    "stop_after_static_attestation".split()
)
PRIVATE_PREAPPROVAL_FIELDS = (
    "schema_version",
    "approval_challenge_id",
    "census_at_utc",
    "hmac_key_id",
    "authorized_locator_commitments",
    "private_control_identity_commitment",
    "public_repo_artifact_set_receipt_sha256",
    "git_snapshot_commitment",
    "toolchain_set_receipt_sha256",
    "package_lock_raw_sha256",
    "host_platform",
    "host_architecture",
    "target_worktree_claude_sessions",
    "forbidden_process_match_count",
    "host_selected_package_count",
    "host_selected_cache_bytes",
    "host_bin_link_count",
    "content_receipt_sha256",
    "ustar_closure_sha256",
    "resolution_receipt_sha256",
    "expected_tree_sha256",
)


def fail(code: Exit, public_code: str) -> None:
    raise ContractError(code, public_code)


def is_nfc(value: str) -> bool:
    return unicodedata.normalize("NFC", value) == value


def reject_float(_: str) -> None:
    fail(Exit.CONTRACT, "JSON_NUMBER_PROFILE")


def reject_constant(_: str) -> None:
    fail(Exit.CONTRACT, "JSON_NUMBER_PROFILE")


def object_pairs_no_duplicates(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(Exit.CONTRACT, "JSON_DUPLICATE_KEY")
        if not is_nfc(key):
            fail(Exit.CONTRACT, "JSON_NON_NFC")
        result[key] = value
    return result


def validate_json_values(value: Any) -> None:
    if isinstance(value, str):
        if not is_nfc(value):
            fail(Exit.CONTRACT, "JSON_NON_NFC")
    elif isinstance(value, list):
        for child in value:
            validate_json_values(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or not is_nfc(key):
                fail(Exit.CONTRACT, "JSON_NON_NFC")
            validate_json_values(child)
    elif value is None or isinstance(value, (bool, int)):
        return
    else:
        fail(Exit.CONTRACT, "JSON_TYPE_PROFILE")


def parse_json_bytes(raw: bytes, label: str) -> Any:
    if not raw or len(raw) > MAX_JSON_BYTES:
        fail(Exit.CONTRACT, label + "_SIZE")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        fail(Exit.CONTRACT, label + "_ENCODING")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.CONTRACT, label + "_UTF8")
    if not is_nfc(text):
        fail(Exit.CONTRACT, label + "_NFC")
    try:
        value = json.loads(
            text,
            object_pairs_hook=object_pairs_no_duplicates,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except ContractError:
        raise
    except (ValueError, TypeError):
        fail(Exit.CONTRACT, label + "_JSON")
    validate_json_values(value)
    return value


def canonical_json(value: Any) -> bytes:
    validate_json_values(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
    except (ValueError, TypeError, UnicodeError):
        fail(Exit.EVIDENCE, "CANONICAL_JSON")
    raise AssertionError("unreachable")


def hmac_frame(key: bytes, domain: bytes, body: bytes) -> str:
    framed = domain + b"\x00" + len(body).to_bytes(8, "big") + body
    return hmac.new(key, framed, hashlib.sha256).hexdigest()


def public_json(payload: Mapping[str, Any]) -> None:
    safe = dict(payload)
    encoded = canonical_json(safe).decode("utf-8", "strict")
    sys.stdout.write(encoded)
    sys.stdout.flush()


def has_forbidden_public_value(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        path_components = tuple(
            unicodedata.normalize("NFC", component).casefold()
            for component in value.split("/")
            if component
        )
        return (
            any(unicodedata.category(character) == "Cc" for character in value)
            or value.startswith("/")
            or value.startswith("~")
            or "\\" in value
            or re.match(r"\A[A-Za-z]:[/\\]", value) is not None
            or value == ".."
            or value.startswith("../")
            or "/../" in value
            or "file://" in lowered
            or "/users/" in lowered
            or VAULT_PREFIX in lowered
            or ".obsidian" in path_components
            or "traceback" in lowered
        )
    if isinstance(value, list):
        return any(has_forbidden_public_value(child) for child in value)
    if isinstance(value, dict):
        return any(has_forbidden_public_value(k) or has_forbidden_public_value(v) for k, v in value.items())
    return False


def privacy_rejection_result() -> Dict[str, Any]:
    return {
        "schema_version": PUBLIC_RESULT_SCHEMA_VERSION,
        "artifact_type": PUBLIC_RESULT_ARTIFACT_TYPE,
        "ok": False,
        "mode": "unknown",
        "phase": "public-projection",
        "state": "failed",
        "terminal_state": {
            "challenge_state": "unknown-fail-closed",
            "claim_state": "unknown-fail-closed",
            "stage_state": "unknown-fail-closed",
            "publication_state": "unknown-fail-closed",
            "ledger_terminal_state": "unknown-fail-closed",
            "target_disposition": "unknown-user-decision-required",
        },
        "runtime_assurance": {
            "toolchain_assurance": "runtime-self-attested-not-pre-exec",
            "pre_exec_launcher_attested": False,
            "python_isolation_flags_required": ["-I", "-S", "-B"],
        },
        "gate_results": {
            "profile": "gov01-static-acquisition-gate-set-v2",
            "complete": False,
            "reached_gate_count": 0,
            "reached_gates": [],
            "unreached_gate_ids": [gate_id for gate_id, _ in GATE_SCOPES],
            "gate_set_receipt_sha256": None,
        },
        "authority": {
            "retry_authorized": False,
            "public_success_attestation_allowed": False,
            "automatic_cleanup_authorized": False,
            "openspec_execution_allowed": False,
            "openspec_scaffold_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "next_required_authority": "new explicit user approval after private-state inspection",
        },
        "error": {
            "code": "PRIVACY_FAIL_CLOSED",
            "detail_code": "PUBLIC_PROJECTION_REJECTED",
            "exit": int(Exit.PRIVACY),
        },
        "retention": {
            "stage_deleted_or_moved_on_failure": False,
            "automatic_rollback_performed": False,
            "private_state_inspection_required": True,
        },
    }


class AuthorityBoundPublicResult(dict):
    """In-process public projection plus a non-serialized trusted checker input."""

    def __init__(self, payload: Mapping[str, Any], authority_binding: Optional[Mapping[str, Any]]) -> None:
        super().__init__(payload)
        self.authority_binding = None if authority_binding is None else copy.deepcopy(dict(authority_binding))


def emit(payload: Mapping[str, Any]) -> int:
    """Serialize one checked public projection and return its exact process exit.

    The serialized record, rather than the caller's superseded control-flow
    error, is the exit-code authority.  This keeps a checker/privacy fallback
    from being printed with exit 55 while the process incorrectly returns 0 or
    an unrelated primary error.
    """
    actual_payload: Mapping[str, Any] = payload
    if has_forbidden_public_value(actual_payload):
        actual_payload = privacy_rejection_result()
    try:
        validate_public_result_projection(actual_payload)
    except BaseException:
        # Never let a secondary projection-checker defect expose a Python
        # traceback or replace a fail-closed public record with silence.
        actual_payload = privacy_rejection_result()
    public_json(actual_payload)
    if actual_payload.get("ok") is True:
        return int(Exit.OK)
    error = actual_payload.get("error")
    if isinstance(error, Mapping):
        exit_code = error.get("exit")
        if type(exit_code) is int and exit_code in {int(item) for item in Exit}:
            return exit_code
    # The fixed privacy projection above makes this unreachable for every
    # production result; retain a deterministic fail-closed value nonetheless.
    return int(Exit.PRIVACY)


def assert_absolute(path: str, label: str) -> str:
    if (
        not isinstance(path, str)
        or not path
        or not is_nfc(path)
        or "\x00" in path
        or any(unicodedata.category(character) == "Cc" for character in path)
        or not os.path.isabs(path)
    ):
        fail(Exit.UNSAFE_PATH, label + "_ABSOLUTE")
    normalized = os.path.normpath(path)
    if normalized != path:
        fail(Exit.UNSAFE_PATH, label + "_NORMALIZED")
    return path


def is_same_or_within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def has_forbidden_vault_component(path: str) -> bool:
    for component in [item for item in path.split(os.sep) if item]:
        folded = unicodedata.normalize("NFC", component).casefold()
        if VAULT_PREFIX in folded or folded == ".obsidian":
            return True
    return False


def paths_overlap(left: str, right: str) -> bool:
    return is_same_or_within(left, right) or is_same_or_within(right, left)


def validate_locator_boundaries(args: argparse.Namespace) -> None:
    locators = (
        (args.repo_root, "REPO_ROOT"),
        (args.cache_root, "CACHE_ROOT"),
        (args.state_root, "STATE_ROOT"),
        (args.key_file, "HMAC_KEY"),
        (args.envelope, "ENVELOPE"),
    )
    for value, label in locators:
        assert_absolute(value, label)
        if has_forbidden_vault_component(value):
            fail(Exit.PRIVACY, label + "_VAULT_LOCATOR")
    separated = (
        (args.repo_root, args.cache_root, "REPO_CACHE_OVERLAP"),
        (args.repo_root, args.state_root, "REPO_STATE_OVERLAP"),
        (args.repo_root, args.key_file, "REPO_KEY_OVERLAP"),
        (args.cache_root, args.state_root, "CACHE_STATE_OVERLAP"),
        (args.cache_root, args.key_file, "CACHE_KEY_OVERLAP"),
        (args.state_root, args.key_file, "STATE_KEY_OVERLAP"),
        (args.cache_root, args.envelope, "CACHE_ENVELOPE_OVERLAP"),
        (args.state_root, args.envelope, "STATE_ENVELOPE_OVERLAP"),
        (args.key_file, args.envelope, "KEY_ENVELOPE_OVERLAP"),
    )
    for left, right, label in separated:
        if paths_overlap(left, right):
            fail(Exit.PRIVATE_STATE, label)
    if not is_same_or_within(args.envelope, args.repo_root):
        fail(Exit.CONTRACT, "ENVELOPE_OUTSIDE_REPO")
    envelope_relative = os.path.relpath(args.envelope, args.repo_root).replace(os.sep, "/")
    validate_relative(envelope_relative, "ENVELOPE_CONTROL_PATH")
    if not envelope_relative.startswith(CONTROL_PREFIX):
        fail(Exit.CONTRACT, "ENVELOPE_OUTSIDE_CONTROL_PREFIX")


def assert_no_symlink_components(path: str, label: str) -> os.stat_result:
    assert_absolute(path, label)
    current = os.sep
    parts = [part for part in path.split(os.sep) if part]
    if not parts:
        return os.lstat(os.sep)
    for part in parts:
        current = os.path.join(current, part)
        try:
            metadata = os.lstat(current)
        except OSError:
            fail(Exit.UNSAFE_PATH, label + "_MISSING")
        if stat.S_ISLNK(metadata.st_mode):
            fail(Exit.UNSAFE_PATH, label + "_SYMLINK")
    return metadata


def assert_no_extended_acl_fd(fd: int, label: str) -> None:
    if sys.platform != "darwin":
        fail(Exit.RUNTIME, label + "_ACL_PLATFORM")
    global _ACL_FUNCTIONS
    if _ACL_FUNCTIONS is None:
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            get_fd = libc.acl_get_fd_np
            get_fd.argtypes = [ctypes.c_int, ctypes.c_int]
            get_fd.restype = ctypes.c_void_p
            get_entry = libc.acl_get_entry
            get_entry.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
            get_entry.restype = ctypes.c_int
            free_acl = libc.acl_free
            free_acl.argtypes = [ctypes.c_void_p]
            free_acl.restype = ctypes.c_int
        except (OSError, AttributeError):
            fail(Exit.RUNTIME, label + "_ACL_API")
        _ACL_FUNCTIONS = (get_fd, get_entry, free_acl)
    get_fd, get_entry, free_acl = _ACL_FUNCTIONS
    ctypes.set_errno(0)
    acl = get_fd(fd, 0x00000100)
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return
        fail(Exit.UNSAFE_PATH, label + "_ACL_GET")
    try:
        entry = ctypes.c_void_p()
        ctypes.set_errno(0)
        result = get_entry(acl, 0, ctypes.byref(entry))
        if result == 0:
            fail(Exit.UNSAFE_PATH, label + "_EXTENDED_ACL")
        if result != -1 or ctypes.get_errno() not in (0, errno.ENOENT):
            fail(Exit.UNSAFE_PATH, label + "_ACL_ENTRY")
    finally:
        if free_acl(acl) != 0:
            fail(Exit.UNSAFE_PATH, label + "_ACL_FREE")


def require_owned_directory(path: str, label: str, exact_mode: Optional[int] = None) -> os.stat_result:
    metadata = assert_no_symlink_components(path, label)
    if not stat.S_ISDIR(metadata.st_mode):
        fail(Exit.UNSAFE_PATH, label + "_NOT_DIRECTORY")
    if metadata.st_uid != os.getuid():
        fail(Exit.UNSAFE_PATH, label + "_OWNER")
    if exact_mode is not None and stat.S_IMODE(metadata.st_mode) != exact_mode:
        fail(Exit.PRIVATE_STATE, label + "_MODE")
    if exact_mode is None and stat.S_IMODE(metadata.st_mode) & 0o022:
        fail(Exit.UNSAFE_PATH, label + "_WRITABLE_BY_OTHERS")
    return metadata


def open_directory(path: str, label: str) -> int:
    require_owned_directory(path, label)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        try:
            assert_no_extended_acl_fd(fd, label)
        except BaseException as error:
            os.close(fd)
            raise
        return fd
    except OSError:
        fail(Exit.UNSAFE_PATH, label + "_OPEN")
    raise AssertionError("unreachable")


def validate_relative(path: str, label: str, forbid_vault: bool = True) -> List[str]:
    if not isinstance(path, str) or not path or not is_nfc(path):
        fail(Exit.UNSAFE_PATH, label + "_FORMAT")
    if path.startswith("/") or "\\" in path or "\x00" in path:
        fail(Exit.UNSAFE_PATH, label + "_FORMAT")
    components = path.split("/")
    if any(not part or part in (".", "..") for part in components):
        fail(Exit.UNSAFE_PATH, label + "_TRAVERSAL")
    if any(any(unicodedata.category(ch) == "Cc" for ch in part) for part in components):
        fail(Exit.UNSAFE_PATH, label + "_CONTROL")
    if components[0] == ".git":
        fail(Exit.UNSAFE_PATH, label + "_GIT")
    if forbid_vault:
        for component in components:
            folded = unicodedata.normalize("NFC", component).casefold()
            if VAULT_PREFIX in folded or folded == ".obsidian":
                fail(Exit.UNSAFE_PATH, label + "_VAULT")
    return components


def open_relative_regular(root_fd: int, path: str, label: str, max_bytes: int) -> Tuple[int, os.stat_result]:
    components = validate_relative(path, label)
    current = os.dup(root_fd)
    try:
        for component in components[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            os.close(current)
            current = next_fd
        file_fd = os.open(components[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=current)
        try:
            assert_no_extended_acl_fd(file_fd, label)
        except BaseException as error:
            os.close(file_fd)
            raise
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink < 1 or metadata.st_size > max_bytes:
            os.close(file_fd)
            fail(Exit.UNSAFE_PATH, label + "_NOT_REGULAR")
        return file_fd, metadata
    except ContractError:
        raise
    except OSError:
        fail(Exit.UNSAFE_PATH, label + "_OPEN")
    finally:
        os.close(current)
    raise AssertionError("unreachable")


def read_fd(fd: int, max_bytes: int, label: str) -> bytes:
    pieces: List[bytes] = []
    total = 0
    while True:
        try:
            chunk = os.read(fd, min(1024 * 1024, max_bytes + 1 - total))
        except OSError:
            fail(Exit.UNSAFE_PATH, label + "_READ")
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            fail(Exit.UNSAFE_PATH, label + "_SIZE")
        pieces.append(chunk)
    return b"".join(pieces)


def hash_fd(fd: int, algorithm: str, max_bytes: int, label: str) -> Tuple[str, int]:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
    except OSError:
        fail(Exit.UNSAFE_PATH, label + "_SEEK")
    digest = hashlib.new(algorithm)
    total = 0
    while True:
        try:
            chunk = os.read(fd, 1024 * 1024)
        except OSError:
            fail(Exit.UNSAFE_PATH, label + "_READ")
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            fail(Exit.UNSAFE_PATH, label + "_SIZE")
        digest.update(chunk)
    return digest.hexdigest(), total


def read_json_relative(root_fd: int, path: str, label: str) -> Tuple[Any, bytes, os.stat_result]:
    fd, metadata = open_relative_regular(root_fd, path, label, MAX_JSON_BYTES)
    try:
        raw = read_fd(fd, MAX_JSON_BYTES, label)
    finally:
        os.close(fd)
    return parse_json_bytes(raw, label), raw, metadata


def read_absolute_regular(path: str, label: str, max_bytes: int) -> Tuple[bytes, os.stat_result]:
    metadata = assert_no_symlink_components(path, label)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        fail(Exit.UNSAFE_PATH, label + "_NOT_REGULAR")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        fail(Exit.UNSAFE_PATH, label + "_OPEN")
    try:
        opened = os.fstat(fd)
        assert_no_extended_acl_fd(fd, label)
        before = (
            metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid, metadata.st_gid,
            metadata.st_nlink, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns,
            getattr(metadata, "st_flags", 0),
        )
        opened_tuple = (
            opened.st_dev, opened.st_ino, opened.st_mode, opened.st_uid, opened.st_gid,
            opened.st_nlink, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns,
            getattr(opened, "st_flags", 0),
        )
        if opened_tuple != before:
            fail(Exit.UNSAFE_PATH, label + "_RACE")
        raw = read_fd(fd, max_bytes, label)
        final = os.fstat(fd)
        final_tuple = (
            final.st_dev, final.st_ino, final.st_mode, final.st_uid, final.st_gid,
            final.st_nlink, final.st_size, final.st_mtime_ns, final.st_ctime_ns,
            getattr(final, "st_flags", 0),
        )
        if final_tuple != opened_tuple or len(raw) != opened.st_size:
            fail(Exit.UNSAFE_PATH, label + "_READ_RACE")
    finally:
        os.close(fd)
    return raw, metadata


def load_hmac_key(
    path: str,
    expected_uid: Optional[int] = None,
    expected_gid: Optional[int] = None,
) -> bytes:
    raw, metadata = read_absolute_regular(path, "HMAC_KEY", 64)
    if (
        metadata.st_uid != (os.getuid() if expected_uid is None else expected_uid)
        or (expected_gid is not None and metadata.st_gid != expected_gid)
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_nlink != 1
        or len(raw) != 32
    ):
        fail(Exit.PRIVATE_STATE, "HMAC_KEY_POLICY")
    return raw


def locator_commitment(key: bytes, label: str, path: str) -> str:
    body = canonical_json({"label": label, "locator": path})
    return hmac_frame(key, PRIVATE_LOCATOR_DOMAIN, body)


def hmac_key_id(key: bytes) -> str:
    return hmac_frame(key, HMAC_KEY_ID_DOMAIN, b"")


def locator_commitments(args: argparse.Namespace, key: bytes) -> Dict[str, Dict[str, str]]:
    return {
        "repo_root": {
            "label": "repo-root",
            "commitment": locator_commitment(key, "repo-root", args.repo_root),
        },
        "cache_root": {
            "label": "npm-cache",
            "commitment": locator_commitment(key, "npm-cache", args.cache_root),
        },
        "state_root": {
            "label": "state-root",
            "commitment": locator_commitment(key, "state-root", args.state_root),
        },
        "key_file": {
            "label": "hmac-key",
            "commitment": locator_commitment(key, "hmac-key", args.key_file),
        },
        "envelope": {
            "label": "envelope",
            "commitment": locator_commitment(key, "envelope", args.envelope),
        },
    }


def compare_private_authorization(
    envelope: Mapping[str, Any],
    key: bytes,
    actual_locators: Mapping[str, Any],
) -> None:
    authority = envelope.get("private_state_authorization")
    if not isinstance(authority, dict):
        fail(Exit.CONTRACT, "PRIVATE_AUTHORIZATION_SCHEMA")
    expected_key_id = authority.get("hmac_key_id")
    if not isinstance(expected_key_id, str) or not hmac.compare_digest(expected_key_id, hmac_key_id(key)):
        fail(Exit.RECEIPT, "HMAC_KEY_ID_MISMATCH")
    expected_locators = authority.get("authorized_locator_commitments")
    if not isinstance(expected_locators, dict):
        fail(Exit.CONTRACT, "LOCATOR_COMMITMENTS_SCHEMA")
    if set(expected_locators) != set(actual_locators):
        fail(Exit.CONTRACT, "LOCATOR_COMMITMENTS_KEYS")
    for name in sorted(actual_locators):
        expected_entry = expected_locators.get(name)
        actual_entry = actual_locators.get(name)
        if not isinstance(expected_entry, dict) or not isinstance(actual_entry, dict):
            fail(Exit.CONTRACT, "LOCATOR_COMMITMENT_SCHEMA")
        if expected_entry.get("label") != actual_entry.get("label"):
            fail(Exit.RECEIPT, "LOCATOR_LABEL_MISMATCH")
        expected_commitment = expected_entry.get("commitment")
        actual_commitment = actual_entry.get("commitment")
        if (
            not isinstance(expected_commitment, str)
            or not isinstance(actual_commitment, str)
            or not hmac.compare_digest(expected_commitment, actual_commitment)
        ):
            fail(Exit.RECEIPT, "LOCATOR_COMMITMENT_MISMATCH")


def parse_utc(value: Any, label: str) -> _datetime.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        fail(Exit.CONTRACT, label + "_FORMAT")
    try:
        parsed = _datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        fail(Exit.CONTRACT, label + "_FORMAT")
    return parsed.replace(tzinfo=_datetime.timezone.utc)


def utc_now() -> _datetime.datetime:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class GateRecorder:
    """Content-addressed, locator-free receipts for gates actually reached."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}
        self._active_gate: Optional[str] = None
        self._phase = "entry"
        self._terminal_failure = False
        # This is a non-serialized, monotonically growing authority snapshot.
        # It prevents a caller from coherently rewriting a reached public gate
        # and its receipt after the gate was observed.  Only commitments and
        # public schema metadata are retained here; never private locators.
        self._authority_binding: Dict[str, Any] = {}

    def _merge_authority(self, fragment: Mapping[str, Any]) -> None:
        if not isinstance(fragment, Mapping) or not fragment:
            fail(Exit.EVIDENCE, "GATE_AUTHORITY_FRAGMENT")
        copied = copy.deepcopy(dict(fragment))
        for name, candidate in copied.items():
            if name in self._authority_binding and self._authority_binding[name] != candidate:
                fail(Exit.EVIDENCE, "GATE_AUTHORITY_REBIND")
        self._authority_binding.update(copied)

    def bind_run_authority(self, challenge: Any, receipt_digest: Any) -> None:
        if not isinstance(challenge, str) or CHALLENGE_RE.fullmatch(challenge) is None:
            fail(Exit.EVIDENCE, "GATE_RUN_AUTHORITY_CHALLENGE")
        require_sha256(receipt_digest, "GATE_RUN_AUTHORITY_RECEIPT")
        self._merge_authority(
            {"approval_challenge_id": challenge, "receipt_digest": receipt_digest}
        )

    def bind_schema_authority(self, observation: Mapping[str, Any]) -> None:
        observed = require_exact_object(
            observation,
            ("path", "sha256", "bytes", "schema_count", "schema_bundle_receipt_sha256"),
            "GATE_SCHEMA_AUTHORITY",
        )
        validate_relative(observed.get("path"), "GATE_SCHEMA_AUTHORITY_PATH")
        require_sha256(observed.get("sha256"), "GATE_SCHEMA_AUTHORITY_SHA")
        require_sha256(
            observed.get("schema_bundle_receipt_sha256"),
            "GATE_SCHEMA_AUTHORITY_BUNDLE",
        )
        if type(observed.get("bytes")) is not int or not 1 <= observed["bytes"] <= MAX_JSON_BYTES:
            fail(Exit.EVIDENCE, "GATE_SCHEMA_AUTHORITY_BYTES")
        if type(observed.get("schema_count")) is not int or observed["schema_count"] != 3:
            fail(Exit.EVIDENCE, "GATE_SCHEMA_AUTHORITY_COUNT")
        self._merge_authority({"schema_binding_observation": observed})

    def bind_private_authority(
        self,
        private_control_identity_commitment: Any,
        hmac_identifier: Any,
        locators: Mapping[str, Any],
    ) -> None:
        require_sha256(
            private_control_identity_commitment,
            "GATE_PRIVATE_AUTHORITY_CONTROL",
        )
        require_sha256(hmac_identifier, "GATE_PRIVATE_AUTHORITY_KEY")
        expected_labels = {
            "repo_root": "repo-root",
            "cache_root": "npm-cache",
            "state_root": "state-root",
            "key_file": "hmac-key",
            "envelope": "envelope",
        }
        if not isinstance(locators, Mapping) or set(locators) != set(expected_labels):
            fail(Exit.EVIDENCE, "GATE_PRIVATE_AUTHORITY_LOCATORS")
        checked_locators: Dict[str, Dict[str, str]] = {}
        for name, expected_label in expected_labels.items():
            entry = locators.get(name)
            if not isinstance(entry, Mapping) or set(entry) != {"label", "commitment"}:
                fail(Exit.EVIDENCE, "GATE_PRIVATE_AUTHORITY_LOCATOR_ENTRY")
            if entry.get("label") != expected_label:
                fail(Exit.EVIDENCE, "GATE_PRIVATE_AUTHORITY_LOCATOR_LABEL")
            require_sha256(entry.get("commitment"), "GATE_PRIVATE_AUTHORITY_LOCATOR_COMMITMENT")
            checked_locators[name] = {
                "label": expected_label,
                "commitment": entry["commitment"],
            }
        self._merge_authority(
            {
                "private_control_identity_commitment": private_control_identity_commitment,
                "hmac_key_id": hmac_identifier,
                "authorized_locator_commitments": checked_locators,
            }
        )

    def bind_toolchain_authority(self, toolchain: Mapping[str, Any]) -> None:
        binding = {
            "toolchain_set_receipt_sha256": toolchain.get("toolchain_set_receipt_sha256"),
            "dynamic_closure_receipt_sha256": toolchain.get("dynamic_closure_receipt_sha256"),
        }
        for label, digest_value in binding.items():
            require_sha256(digest_value, "GATE_TOOLCHAIN_AUTHORITY_" + label.upper())
        self._merge_authority(binding)

    def toolchain_authority_binding(self) -> Optional[Dict[str, str]]:
        names = ("toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256")
        if not all(name in self._authority_binding for name in names):
            return None
        return {name: self._authority_binding[name] for name in names}

    def authority_binding(self) -> Optional[Dict[str, Any]]:
        return None if not self._authority_binding else copy.deepcopy(self._authority_binding)

    def begin(self, gate_id: str, phase: str) -> None:
        if (
            gate_id not in GATE_SCOPE_BY_ID
            or gate_id in self._records
            or self._active_gate is not None
            or self._terminal_failure
        ):
            fail(Exit.INTERNAL, "GATE_BEGIN_STATE")
        if not isinstance(phase, str) or phase != GATE_PHASE_BY_ID[gate_id]:
            fail(Exit.INTERNAL, "GATE_PHASE")
        self._active_gate = gate_id
        self._phase = phase

    def _record(self, gate_id: str, status: str, evidence: Mapping[str, Any]) -> Dict[str, Any]:
        if gate_id not in GATE_SCOPE_BY_ID or gate_id in self._records:
            fail(Exit.INTERNAL, "GATE_RECORD_STATE")
        if status not in ("PASS", "FAIL") or not isinstance(evidence, Mapping):
            fail(Exit.INTERNAL, "GATE_RECORD_SCHEMA")
        evidence_value = dict(evidence)
        if has_forbidden_public_value(evidence_value):
            fail(Exit.PRIVACY, "GATE_PRIVATE_VALUE")
        validate_gate_evidence(gate_id, status, evidence_value)
        body = {
            "schema_version": "gov01-static-acquisition-gate-evidence-v2",
            "gate_id": gate_id,
            "scope": GATE_SCOPE_BY_ID[gate_id],
            "phase": self._phase,
            "status": status,
            "checker_role": "frozen-static-executor",
            "assurance": "runtime-self-attested-not-pre-exec",
            "evidence": evidence_value,
        }
        record = dict(body)
        record["receipt_sha256"] = sha256(GATE_DOMAIN + b"\x00" + canonical_json(body))
        self._records[gate_id] = record
        self._active_gate = None
        return record

    def passed(self, gate_id: str, evidence: Mapping[str, Any]) -> Dict[str, Any]:
        if self._active_gate != gate_id:
            fail(Exit.INTERNAL, "GATE_PASS_STATE")
        return self._record(gate_id, "PASS", evidence)

    def passed_with_authority(
        self,
        gate_id: str,
        evidence: Mapping[str, Any],
        authority_kind: str,
        authority_value: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Atomically bind trusted sidecar authority and record a PASS gate."""
        expected_kind = {"G00": "schema", "G02": "private", "G03": "toolchain"}.get(gate_id)
        if authority_kind != expected_kind or not isinstance(authority_value, Mapping):
            fail(Exit.EVIDENCE, "GATE_PASS_AUTHORITY_KIND")
        records_before = dict(self._records)
        active_before = self._active_gate
        terminal_before = self._terminal_failure
        authority_before = copy.deepcopy(self._authority_binding)
        try:
            if authority_kind == "schema":
                self.bind_schema_authority(authority_value)
            elif authority_kind == "private":
                required = {
                    "private_control_identity_commitment",
                    "hmac_key_id",
                    "authorized_locator_commitments",
                }
                if set(authority_value) != required:
                    fail(Exit.EVIDENCE, "GATE_PRIVATE_PASS_AUTHORITY_FIELDS")
                self.bind_private_authority(
                    authority_value["private_control_identity_commitment"],
                    authority_value["hmac_key_id"],
                    authority_value["authorized_locator_commitments"],
                )
            else:
                self.bind_toolchain_authority(authority_value)
            return self.passed(gate_id, evidence)
        except BaseException:
            # Restore an active gate so the outer failure path can emit a
            # truthful FAIL receipt.  A PASS and its sidecar snapshot are
            # therefore never observable separately, even under interruption.
            self._records = records_before
            self._active_gate = active_before
            self._terminal_failure = terminal_before
            self._authority_binding = authority_before
            raise

    def failed(self, public_code: str, public_exit: int) -> None:
        gate_id = self._active_gate
        if gate_id is None or gate_id in self._records:
            self._active_gate = None
            return
        safe_code = public_code if isinstance(public_code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", public_code) else "INTERNAL_FAIL_CLOSED"
        exit_value = int(public_exit) if type(public_exit) is int else int(Exit.INTERNAL)
        self._record(
            gate_id,
            "FAIL",
            {
                "public_code": public_exit_category(exit_value),
                "detail_code": safe_code,
                "public_exit": exit_value,
            },
        )
        self._terminal_failure = True

    def _ordered_records(self) -> List[Dict[str, Any]]:
        return [self._records[gate_id] for gate_id, _ in GATE_SCOPES if gate_id in self._records]

    def partial_projection(self) -> Dict[str, Any]:
        reached = self._ordered_records()
        return {
            "profile": "gov01-static-acquisition-gate-set-v2",
            "complete": False,
            "reached_gate_count": len(reached),
            "reached_gates": reached,
            "unreached_gate_ids": [gate_id for gate_id, _ in GATE_SCOPES if gate_id not in self._records],
            "gate_set_receipt_sha256": None,
        }

    def complete_projection(self) -> Dict[str, Any]:
        ordered = self._ordered_records()
        if len(ordered) != len(GATE_SCOPES) or any(record.get("status") != "PASS" for record in ordered):
            fail(Exit.EVIDENCE, "GATE_SET_INCOMPLETE")
        receipt_body = {
            "schema_version": "gov01-static-acquisition-gate-set-v2",
            "gate_receipts": [
                {"gate_id": record["gate_id"], "receipt_sha256": record["receipt_sha256"]}
                for record in ordered
            ],
        }
        return {
            "profile": "gov01-static-acquisition-gate-set-v2",
            "complete": True,
            "reached_gate_count": len(ordered),
            "reached_gates": ordered,
            "unreached_gate_ids": [],
            "gate_set_receipt_sha256": sha256(GATE_SET_DOMAIN + b"\x00" + canonical_json(receipt_body)),
        }


def completed_public_authority_binding(
    recorder: GateRecorder,
    additions: Mapping[str, Any],
) -> Dict[str, Any]:
    """Extend the monotonic reached-gate snapshot with non-gate authorities."""

    trusted = require_exact_object(
        recorder.authority_binding(),
        (
            "approval_challenge_id",
            "receipt_digest",
            "schema_binding_observation",
            "private_control_identity_commitment",
            "hmac_key_id",
            "authorized_locator_commitments",
            "toolchain_set_receipt_sha256",
            "dynamic_closure_receipt_sha256",
        ),
        "COMPLETED_GATE_AUTHORITY",
    )
    extra = require_exact_object(
        additions,
        (
            "toolchain_hashes",
            "public_repo_artifact_set_receipt_sha256",
            "git_snapshot_commitment",
            "private_preapproval_commitment",
            "package_lock_raw_sha256",
        ),
        "COMPLETED_PUBLIC_AUTHORITY",
    )
    if set(trusted).intersection(extra):
        fail(Exit.EVIDENCE, "COMPLETED_PUBLIC_AUTHORITY_REBIND")
    result = copy.deepcopy(dict(trusted))
    result.update(copy.deepcopy(dict(extra)))
    return result


def validate_gate_projection(value: Mapping[str, Any]) -> Dict[str, Any]:
    projection = require_exact_object(
        value,
        (
            "profile", "complete", "reached_gate_count", "reached_gates",
            "unreached_gate_ids", "gate_set_receipt_sha256",
        ),
        "GATE_PROJECTION",
    )
    if projection.get("profile") != "gov01-static-acquisition-gate-set-v2":
        fail(Exit.EVIDENCE, "GATE_PROFILE")
    complete = projection.get("complete")
    reached = projection.get("reached_gates")
    unreached = projection.get("unreached_gate_ids")
    if not isinstance(complete, bool) or not isinstance(reached, list) or not isinstance(unreached, list):
        fail(Exit.EVIDENCE, "GATE_PROJECTION_TYPES")
    reached_gate_count = projection.get("reached_gate_count")
    if type(reached_gate_count) is not int or reached_gate_count != len(reached):
        fail(Exit.EVIDENCE, "GATE_REACHED_COUNT")
    order = {gate_id: index for index, (gate_id, _) in enumerate(GATE_SCOPES)}
    observed_ids: List[str] = []
    previous_index = -1
    for raw_record in reached:
        record = require_exact_object(
            raw_record,
            (
                "schema_version", "gate_id", "scope", "phase", "status",
                "checker_role", "assurance", "evidence", "receipt_sha256",
            ),
            "GATE_RECORD",
        )
        gate_id = record.get("gate_id")
        if not isinstance(gate_id, str) or gate_id not in order or gate_id in observed_ids:
            fail(Exit.EVIDENCE, "GATE_ID")
        current_index = order[gate_id]
        if current_index <= previous_index:
            fail(Exit.EVIDENCE, "GATE_ORDER")
        previous_index = current_index
        observed_ids.append(gate_id)
        if (
            record.get("schema_version") != "gov01-static-acquisition-gate-evidence-v2"
            or record.get("scope") != GATE_SCOPE_BY_ID[gate_id]
            or record.get("phase") != GATE_PHASE_BY_ID[gate_id]
            or record.get("status") not in ("PASS", "FAIL")
            or record.get("checker_role") != "frozen-static-executor"
            or record.get("assurance") != "runtime-self-attested-not-pre-exec"
            or not isinstance(record.get("evidence"), dict)
            or has_forbidden_public_value(record["evidence"])
        ):
            fail(Exit.EVIDENCE, "GATE_RECORD_CONTRACT")
        validate_gate_evidence(gate_id, record["status"], record["evidence"])
        body = dict(record)
        actual_receipt = body.pop("receipt_sha256", None)
        require_sha256(actual_receipt, "GATE_RECEIPT")
        expected_receipt = sha256(GATE_DOMAIN + b"\x00" + canonical_json(body))
        if not hmac.compare_digest(actual_receipt, expected_receipt):
            fail(Exit.EVIDENCE, "GATE_RECEIPT_MISMATCH")
    expected_unreached = [gate_id for gate_id, _ in GATE_SCOPES if gate_id not in observed_ids]
    if unreached != expected_unreached:
        fail(Exit.EVIDENCE, "GATE_UNREACHED_PARTITION")
    all_pass = len(reached) == len(GATE_SCOPES) and all(record.get("status") == "PASS" for record in reached)
    gate_set_receipt = projection.get("gate_set_receipt_sha256")
    if complete:
        if not all_pass or unreached:
            fail(Exit.EVIDENCE, "GATE_COMPLETE_STATE")
        require_sha256(gate_set_receipt, "GATE_SET_RECEIPT")
        body = {
            "schema_version": "gov01-static-acquisition-gate-set-v2",
            "gate_receipts": [
                {"gate_id": record["gate_id"], "receipt_sha256": record["receipt_sha256"]}
                for record in reached
            ],
        }
        expected_set_receipt = sha256(GATE_SET_DOMAIN + b"\x00" + canonical_json(body))
        if not hmac.compare_digest(gate_set_receipt, expected_set_receipt):
            fail(Exit.EVIDENCE, "GATE_SET_RECEIPT_MISMATCH")
    elif gate_set_receipt is not None or all_pass:
        fail(Exit.EVIDENCE, "GATE_PARTIAL_STATE")
    return dict(projection)


def validate_public_result_projection(
    value: Mapping[str, Any],
    authority_binding: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Content-addressed cross-field checker for every public stdout result."""
    if authority_binding is None and isinstance(value, AuthorityBoundPublicResult):
        authority_binding = value.authority_binding
    if not isinstance(value, Mapping) or has_forbidden_public_value(value):
        fail(Exit.PRIVACY, "PUBLIC_RESULT_PRIVATE_VALUE")
    result = dict(value)
    if result.get("schema_version") != PUBLIC_RESULT_SCHEMA_VERSION or result.get("artifact_type") != PUBLIC_RESULT_ARTIFACT_TYPE:
        fail(Exit.EVIDENCE, "PUBLIC_RESULT_PROFILE")
    gate_projection = result.get("gate_results")
    if not isinstance(gate_projection, Mapping):
        fail(Exit.EVIDENCE, "PUBLIC_RESULT_GATES")
    validated_gates = validate_gate_projection(gate_projection)
    gate_records = validated_gates.get("reached_gates")
    if not isinstance(gate_records, list):
        fail(Exit.EVIDENCE, "PUBLIC_RESULT_GATE_RECORDS")
    gates = {record["gate_id"]: record for record in gate_records}

    def cross(condition: bool, label: str) -> None:
        if not condition:
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + label)

    def typed_subset(parent: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
        for name, frozen in expected.items():
            actual = parent.get(name)
            cross(type(actual) is type(frozen) and actual == frozen, label)

    def mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
        child = parent.get(name)
        if not isinstance(child, Mapping):
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + name.upper())
        return child

    def gate_evidence(gate_id: str) -> Mapping[str, Any]:
        record = gates.get(gate_id)
        if not isinstance(record, Mapping) or record.get("status") != "PASS":
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + gate_id + "_PASS")
        evidence = record.get("evidence")
        if not isinstance(evidence, Mapping):
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + gate_id + "_EVIDENCE")
        return evidence

    def checked_public_ledger() -> Mapping[str, Any]:
        ledger_value = mapping(result, "ledger_evidence")
        require_exact_object(
            ledger_value,
            ("checker_interface", "record_count", "terminal_kind", "head_hmac_sha256", "raw_sha256", "raw_bytes"),
            "PUBLIC_RESULT_LEDGER_EVIDENCE",
        )
        cross(ledger_value.get("checker_interface") == LEDGER_CHECKER_INTERFACE, "LEDGER_INTERFACE")
        count = ledger_value.get("record_count")
        raw_bytes = ledger_value.get("raw_bytes")
        cross(type(count) is int and 2 <= count <= 6, "LEDGER_COUNT")
        cross(type(raw_bytes) is int and 1 <= raw_bytes <= MAX_JSON_BYTES, "LEDGER_BYTES")
        cross(ledger_value.get("terminal_kind") in ("success", "failure"), "LEDGER_KIND")
        require_sha256(ledger_value.get("head_hmac_sha256"), "PUBLIC_RESULT_LEDGER_HEAD")
        require_sha256(ledger_value.get("raw_sha256"), "PUBLIC_RESULT_LEDGER_RAW")
        return ledger_value

    def checked_schema_observation(parent: Mapping[str, Any]) -> Mapping[str, Any]:
        schema_value = mapping(parent, "schema_binding_observation")
        require_exact_object(
            schema_value,
            ("path", "sha256", "bytes", "schema_count", "schema_bundle_receipt_sha256"),
            "PUBLIC_RESULT_SCHEMA_OBSERVATION",
        )
        schema_path = schema_value.get("path")
        cross(isinstance(schema_path, str), "SCHEMA_OBSERVATION_PATH_TYPE")
        validate_relative(schema_path, "PUBLIC_SCHEMA_OBSERVATION_PATH")
        schema_bytes = schema_value.get("bytes")
        schema_count = schema_value.get("schema_count")
        cross(
            type(schema_bytes) is int and 1 <= schema_bytes <= MAX_JSON_BYTES,
            "SCHEMA_OBSERVATION_BYTES",
        )
        cross(type(schema_count) is int and schema_count == 3, "SCHEMA_OBSERVATION_COUNT")
        require_sha256(schema_value.get("sha256"), "PUBLIC_RESULT_SCHEMA_OBSERVATION_SHA")
        require_sha256(
            schema_value.get("schema_bundle_receipt_sha256"),
            "PUBLIC_RESULT_SCHEMA_BUNDLE_RECEIPT",
        )
        return schema_value

    def checked_locator_commitments(value: Any) -> Mapping[str, Any]:
        expected_labels = {
            "repo_root": "repo-root",
            "cache_root": "npm-cache",
            "state_root": "state-root",
            "key_file": "hmac-key",
            "envelope": "envelope",
        }
        cross(isinstance(value, Mapping) and set(value) == set(expected_labels), "LOCATOR_COMMITMENTS")
        for name, expected_label in expected_labels.items():
            entry = value.get(name)
            cross(
                isinstance(entry, Mapping) and set(entry) == {"label", "commitment"},
                "LOCATOR_COMMITMENT_ENTRY",
            )
            cross(entry.get("label") == expected_label, "LOCATOR_COMMITMENT_LABEL")
            require_sha256(entry.get("commitment"), "PUBLIC_RESULT_LOCATOR_COMMITMENT")
        return value

    def execution_prefix_length(order: Sequence[str], label: str) -> int:
        observed = frozenset(gates)
        for length in range(len(order) + 1):
            if observed == frozenset(order[:length]):
                failures = [record for record in gate_records if record.get("status") == "FAIL"]
                if failures and (length == 0 or failures[0].get("gate_id") != order[length - 1]):
                    fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + label + "_FAIL_POSITION")
                return length
        fail(Exit.EVIDENCE, "PUBLIC_RESULT_" + label + "_PREFIX")
        raise AssertionError("unreachable")

    ok = result.get("ok")
    mode = result.get("mode")
    terminal = mapping(result, "terminal_state")
    runtime = mapping(result, "runtime_assurance")
    authority = mapping(result, "authority")
    require_exact_object(
        terminal,
        (
            "challenge_state", "claim_state", "stage_state", "publication_state",
            "ledger_terminal_state", "target_disposition",
        ),
        "PUBLIC_RESULT_TERMINAL",
    )
    terminal_enums = {
        "challenge_state": {
            "not-consumed-read-only", "preclaim-pending", "preclaim-rejected-new-envelope-required",
            "claimed-consumed", "completed-consumed", "unknown-fail-closed",
        },
        "claim_state": {"not-created", "created-0700", "unknown-fail-closed"},
        "stage_state": {
            "not-created", "retained-marker-not-yet-created", "retained-marker-present",
            "retained-marker-removed", "renamed-to-target", "retained-marker-state-unknown",
            "retained-marker-unexpected-type", "unexpected-stage-type-fail-closed", "unknown-fail-closed",
        },
        "publication_state": {
            "not-attempted", "rename-succeeded-attestation-incomplete", "static-attested",
            "static-ledger-success-public-result-failed", "target-observed-unattributed-fail-closed",
            "promoted-target-missing-fail-closed", "attributed-target-and-stage-both-observed-fail-closed",
            "unexpected-target-type-fail-closed", "unknown-fail-closed",
        },
        "ledger_terminal_state": {
            "not-created", "receipt-consumed-recorded", "terminal-failure-recorded",
            "absent-partial-or-semantic-invalid", "terminal-success-recorded", "unknown-fail-closed",
        },
        "target_disposition": {
            "target-absent", "target-absent-stage-retained-user-decision-required",
            "retain-unattributed-target-user-decision-required",
            "retain-unauthorized-target-user-decision-required", "static-attested-target-retained",
            "retain-target-user-decision-required", "unknown-user-decision-required",
        },
    }
    for terminal_field, allowed_values in terminal_enums.items():
        terminal_value = terminal.get(terminal_field)
        cross(
            isinstance(terminal_value, str) and terminal_value in allowed_values,
            "TERMINAL_" + terminal_field.upper(),
        )
    runtime_fields = frozenset(runtime)
    runtime_base_fields = frozenset(
        ("toolchain_assurance", "pre_exec_launcher_attested", "python_isolation_flags_required")
    )
    cross(
        runtime_fields
        in (
            runtime_base_fields,
            runtime_base_fields | {"toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256"},
        ),
        "RUNTIME_FIELDS",
    )
    require_exact_object(
        authority,
        (
            "retry_authorized", "public_success_attestation_allowed", "automatic_cleanup_authorized",
            "openspec_execution_allowed", "openspec_scaffold_allowed", "commit_allowed", "push_allowed",
            "next_required_authority",
        ),
        "PUBLIC_RESULT_AUTHORITY",
    )
    common_fields = frozenset(
        (
            "schema_version", "artifact_type", "ok", "mode", "phase", "state",
            "terminal_state", "runtime_assurance", "gate_results", "authority",
        )
    )
    cross(runtime.get("toolchain_assurance") == "runtime-self-attested-not-pre-exec", "RUNTIME_ASSURANCE")
    cross(runtime.get("pre_exec_launcher_attested") is False, "PRE_EXEC_ASSURANCE")
    cross(runtime.get("python_isolation_flags_required") == ["-I", "-S", "-B"], "PYTHON_FLAGS")
    for denied in (
        "automatic_cleanup_authorized", "openspec_execution_allowed", "openspec_scaffold_allowed",
        "commit_allowed", "push_allowed",
    ):
        cross(authority.get(denied) is False, "AUTHORITY_DENY")

    if ok is True and mode in ("census", "verify"):
        cross(
            frozenset(result) == common_fields | {"approval_challenge_id", "receipt_digest", "observation"},
            "READ_ONLY_FIELDS",
        )
        challenge = result.get("approval_challenge_id")
        receipt = result.get("receipt_digest")
        cross(isinstance(challenge, str) and CHALLENGE_RE.fullmatch(challenge) is not None, "READ_ONLY_CHALLENGE")
        require_sha256(receipt, "PUBLIC_RESULT_READ_ONLY_RECEIPT")
        observation = mapping(result, "observation")
        require_exact_object(
            observation,
            (
                "selected_packages", "selected_cache_bytes", "bin_links", "claude_sessions",
                "hmac_key_id", "authorized_locator_commitments", "private_control_identity_commitment",
                "schema_binding_observation", "public_repo_artifact_set_receipt_sha256",
                "git_snapshot_commitment", "toolchain_set_receipt_sha256",
                "dynamic_closure_receipt_sha256", "toolchain_hashes", "package_lock_raw_sha256",
                "lock_closure_observed", "static_expected", "private_preapproval_commitment",
            ),
            "PUBLIC_RESULT_READ_ONLY_OBSERVATION",
        )
        cross(validated_gates.get("complete") is False, "READ_ONLY_COMPLETE")
        cross(terminal == read_only_terminal_state(), "READ_ONLY_TERMINAL")
        cross(authority.get("retry_authorized") is True and authority.get("public_success_attestation_allowed") is False, "READ_ONLY_AUTHORITY")
        expected_read_only_gates = frozenset(
            ("G00", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12", "G14", "G15")
        )
        cross(frozenset(gates) == expected_read_only_gates, "READ_ONLY_GATE_SET")
        cross(all(record.get("status") == "PASS" for record in gate_records), "READ_ONLY_GATE_STATUS")
        expected_state = "read-only-preapproval-census" if mode == "census" else "preconditions-reverified-read-only"
        cross(result.get("state") == expected_state and result.get("phase") == expected_state + "-complete", "READ_ONLY_STATE")
        cross(
            authority.get("next_required_authority")
            == "exact user-approved acquisition receipt and challenge required before any mutation",
            "READ_ONLY_NEXT_AUTHORITY",
        )
        g00 = gate_evidence("G00")
        g02 = gate_evidence("G02")
        g03 = gate_evidence("G03")
        g05 = gate_evidence("G05")
        g06 = gate_evidence("G06")
        g12 = gate_evidence("G12")
        g14 = gate_evidence("G14")
        g15 = gate_evidence("G15")
        schema_observation = checked_schema_observation(observation)
        for digest_field in (
            "public_repo_artifact_set_receipt_sha256",
            "git_snapshot_commitment",
            "private_preapproval_commitment",
            "private_control_identity_commitment",
            "hmac_key_id",
        ):
            require_sha256(
                observation.get(digest_field),
                "PUBLIC_RESULT_READ_ONLY_" + digest_field.upper(),
            )
        checked_locator_commitments(observation.get("authorized_locator_commitments"))
        static_expected = mapping(observation, "static_expected")
        validate_static_expected_shape(static_expected)
        static_tree = mapping(static_expected, "tree")
        static_resolution = mapping(static_expected, "resolution")
        lock_closure = mapping(observation, "lock_closure_observed")
        require_exact_object(
            lock_closure,
            LOCK_OBSERVATION_FIELDS,
            "PUBLIC_RESULT_READ_ONLY_LOCK_CLOSURE",
        )
        typed_subset(
            observation,
            {"selected_packages": 167, "selected_cache_bytes": 13_916_529, "bin_links": 12, "claude_sessions": 0},
            "READ_ONLY_OBSERVATION_COUNTS",
        )
        typed_subset(
            lock_closure,
            {
                "host_selected_package_count": 167,
                "host_selected_cache_bytes": 13_916_529,
                "host_bin_link_count": 12,
                "expected_archive_member_count": 4117,
                "expected_resolved_tree_entry_count": 4665,
                "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
                "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
                "resolution_receipt_sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
                "expected_tree_sha256": EXPECTED_TREE_SHA256,
            },
            "READ_ONLY_LOCK_CLOSURE",
        )
        cross(
            g00.get("schema_sha256") == schema_observation.get("sha256")
            and g00.get("schema_bytes") == schema_observation.get("bytes")
            and g00.get("schema_count") == schema_observation.get("schema_count")
            and g00.get("schema_bundle_receipt_sha256") == schema_observation.get("schema_bundle_receipt_sha256"),
            "READ_ONLY_SCHEMA_BINDING",
        )
        cross(g02.get("private_control_identity_commitment") == observation.get("private_control_identity_commitment"), "READ_ONLY_PRIVATE_CONTROL")
        cross(
            runtime.get("toolchain_set_receipt_sha256") == observation.get("toolchain_set_receipt_sha256") == g03.get("toolchain_set_receipt_sha256")
            and runtime.get("dynamic_closure_receipt_sha256") == observation.get("dynamic_closure_receipt_sha256") == g03.get("dynamic_closure_receipt_sha256"),
            "READ_ONLY_TOOLCHAIN",
        )
        cross(g05.get("content_receipt_sha256") == static_expected.get("content_receipt_sha256") == lock_closure.get("content_receipt_sha256"), "READ_ONLY_CONTENT")
        cross(g06.get("ustar_closure_sha256") == static_expected.get("ustar_closure_sha256") == lock_closure.get("ustar_closure_sha256"), "READ_ONLY_USTAR")
        cross(g14.get("expected_tree_sha256") == static_tree.get("sha256") == lock_closure.get("expected_tree_sha256"), "READ_ONLY_TREE")
        cross(g15.get("resolution_receipt_sha256") == static_resolution.get("sha256") == lock_closure.get("resolution_receipt_sha256"), "READ_ONLY_RESOLUTION")
        cross(g12.get("target_worktree_claude_sessions") == observation.get("claude_sessions") == 0, "READ_ONLY_SESSIONS")
        tool_hashes = observation.get("toolchain_hashes")
        cross(isinstance(tool_hashes, Mapping) and frozenset(tool_hashes) == frozenset(TOOLCHAIN_ROLES), "READ_ONLY_TOOL_HASH_ROLES")
        for digest_value in tool_hashes.values():
            require_sha256(digest_value, "PUBLIC_RESULT_TOOL_HASH")
        binding = require_exact_object(
            authority_binding,
            (
                "approval_challenge_id", "receipt_digest", "schema_binding_observation", "toolchain_hashes",
                "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment",
                "private_preapproval_commitment", "private_control_identity_commitment",
                "hmac_key_id", "authorized_locator_commitments", "package_lock_raw_sha256",
                "toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256",
            ),
            "PUBLIC_RESULT_AUTHORITY_BINDING",
        )
        require_sha256(binding.get("hmac_key_id"), "PUBLIC_RESULT_READ_ONLY_AUTHORITY_KEY")
        checked_locator_commitments(binding.get("authorized_locator_commitments"))
        cross(binding.get("approval_challenge_id") == challenge, "READ_ONLY_AUTHORITY_CHALLENGE")
        cross(binding.get("receipt_digest") == receipt, "READ_ONLY_AUTHORITY_RECEIPT")
        cross(binding.get("schema_binding_observation") == schema_observation, "READ_ONLY_AUTHORITY_SCHEMA")
        cross(binding.get("toolchain_hashes") == tool_hashes, "READ_ONLY_AUTHORITY_TOOLCHAIN")
        for field in (
            "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment",
            "private_preapproval_commitment", "private_control_identity_commitment",
            "hmac_key_id", "authorized_locator_commitments", "package_lock_raw_sha256",
            "toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256",
        ):
            cross(binding.get(field) == observation.get(field), "READ_ONLY_AUTHORITY_" + field.upper())
        cross(
            observation.get("package_lock_raw_sha256")
            == static_expected.get("package_lock_sha256")
            == "c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea",
            "READ_ONLY_PACKAGE_LOCK",
        )
        return result

    if ok is True and mode == "acquire":
        cross(
            frozenset(result) == common_fields | {"approval_challenge_id", "receipt_digest", "attestation"},
            "SUCCESS_FIELDS",
        )
        cross(validated_gates.get("complete") is True, "SUCCESS_GATE_SET")
        cross(authority.get("retry_authorized") is False and authority.get("public_success_attestation_allowed") is True, "SUCCESS_AUTHORITY")
        attestation = mapping(result, "attestation")
        require_exact_object(
            attestation,
            (
                "schema_version", "approval_challenge_id", "receipt_digest",
                "schema_binding_observation", "public_repo_artifact_set_receipt_sha256",
                "git_snapshot_commitment", "private_preapproval_commitment",
                "private_control_identity_commitment", "toolchain", "source_and_receipts",
                "publication", "containment", "execution_counters", "next_required_authorization",
            ),
            "PUBLIC_RESULT_SUCCESS_ATTESTATION",
        )
        cross(attestation.get("schema_version") == "gov01-static-acquisition-success-attestation-v2", "SUCCESS_ATTESTATION_VERSION")
        cross(
            attestation.get("next_required_authorization")
            == "new runtime-use envelope binding this final tree and a fresh single-use challenge",
            "SUCCESS_NEXT_AUTHORIZATION",
        )
        challenge = result.get("approval_challenge_id")
        cross(isinstance(challenge, str) and CHALLENGE_RE.fullmatch(challenge) is not None, "SUCCESS_CHALLENGE")
        cross(result.get("approval_challenge_id") == attestation.get("approval_challenge_id"), "SUCCESS_CHALLENGE_BINDING")
        cross(result.get("receipt_digest") == attestation.get("receipt_digest"), "SUCCESS_RECEIPT_BINDING")
        require_sha256(result.get("receipt_digest"), "PUBLIC_RESULT_RECEIPT")
        cross(
            result.get("state") == "static-attested-unexecuted"
            and result.get("phase") == "static-attestation-complete"
            and terminal
            == {
                "challenge_state": "completed-consumed",
                "claim_state": "created-0700",
                "stage_state": "renamed-to-target",
                "publication_state": "static-attested",
                "ledger_terminal_state": "terminal-success-recorded",
                "target_disposition": "static-attested-target-retained",
            },
            "SUCCESS_STATE",
        )
        cross(
            authority.get("next_required_authority")
            == "new runtime-use envelope binding this final tree and a fresh single-use challenge",
            "SUCCESS_NEXT_AUTHORITY",
        )
        toolchain = mapping(attestation, "toolchain")
        require_exact_object(
            toolchain,
            (
                "assurance", "pre_exec_launcher_attested", "toolchain_set_receipt_sha256",
                "dynamic_closure_receipt_sha256", "hashes",
            ),
            "PUBLIC_RESULT_SUCCESS_TOOLCHAIN",
        )
        cross(
            toolchain.get("assurance") == "runtime-self-attested-not-pre-exec"
            and toolchain.get("pre_exec_launcher_attested") is False,
            "SUCCESS_TOOLCHAIN_ASSURANCE",
        )
        source = mapping(attestation, "source_and_receipts")
        require_exact_object(
            source,
            ("lock_closure_observed", "static_expected"),
            "PUBLIC_RESULT_SUCCESS_SOURCE",
        )
        static_expected = mapping(source, "static_expected")
        validate_static_expected_shape(static_expected)
        static_tree = mapping(static_expected, "tree")
        static_resolution = mapping(static_expected, "resolution")
        lock_closure = mapping(source, "lock_closure_observed")
        require_exact_object(
            lock_closure,
            LOCK_OBSERVATION_FIELDS,
            "PUBLIC_RESULT_SUCCESS_LOCK_CLOSURE",
        )
        typed_subset(
            lock_closure,
            {
                "host_selected_package_count": 167,
                "host_selected_cache_bytes": 13_916_529,
                "host_bin_link_count": 12,
                "expected_archive_member_count": 4117,
                "expected_resolved_tree_entry_count": 4665,
                "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
                "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
                "resolution_receipt_sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
                "expected_tree_sha256": EXPECTED_TREE_SHA256,
            },
            "SUCCESS_LOCK_CLOSURE",
        )
        publication = mapping(attestation, "publication")
        require_exact_object(
            publication,
            ("publish_syscall", "publish_flag", "tree_sha256", "private_ledger_head_hmac_sha256", "target_state"),
            "PUBLIC_RESULT_SUCCESS_PUBLICATION",
        )
        cross(publication.get("target_state") == "static-attested-unexecuted", "SUCCESS_PUBLICATION_STATE")
        containment = mapping(attestation, "containment")
        counters = mapping(attestation, "execution_counters")
        require_exact_object(
            containment,
            (
                "protected_controls_unchanged", "absent_alternate_controls",
                "public_artifacts_unchanged", "toolchain_unchanged", "git_snapshot_unchanged",
                "cache_closure_unchanged", "outside_scope_mutation_count",
                "target_worktree_claude_sessions",
            ),
            "PUBLIC_RESULT_SUCCESS_CONTAINMENT",
        )
        require_exact_object(
            counters,
            (
                "network_attempt_count", "lifecycle_execution_count", "installed_code_execution_count",
                "node_npm_npx_execution_count", "counter_scope", "runtime_syscall_observation_available",
            ),
            "PUBLIC_RESULT_SUCCESS_COUNTERS",
        )
        schema_observation = checked_schema_observation(attestation)
        for digest_field in (
            "public_repo_artifact_set_receipt_sha256",
            "git_snapshot_commitment",
            "private_preapproval_commitment",
            "private_control_identity_commitment",
        ):
            require_sha256(
                attestation.get(digest_field),
                "PUBLIC_RESULT_SUCCESS_" + digest_field.upper(),
            )
        g00 = gate_evidence("G00")
        g02 = gate_evidence("G02")
        g03 = gate_evidence("G03")
        g04 = gate_evidence("G04")
        g05 = gate_evidence("G05")
        g06 = gate_evidence("G06")
        g14 = gate_evidence("G14")
        g15 = gate_evidence("G15")
        g16 = gate_evidence("G16")
        g17 = gate_evidence("G17")
        g18 = gate_evidence("G18")
        g20 = gate_evidence("G20")
        g21 = gate_evidence("G21")
        g22 = gate_evidence("G22")
        g23 = gate_evidence("G23")
        gate_evidence("G24")
        typed_subset(
            containment,
            {
                "protected_controls_unchanged": True,
                "absent_alternate_controls": True,
                "public_artifacts_unchanged": True,
                "toolchain_unchanged": True,
                "git_snapshot_unchanged": True,
                "cache_closure_unchanged": True,
                "outside_scope_mutation_count": 0,
                "target_worktree_claude_sessions": 0,
            },
            "SUCCESS_CONTAINMENT_SHAPE",
        )
        typed_subset(
            counters,
            {
                "network_attempt_count": 0,
                "lifecycle_execution_count": 0,
                "installed_code_execution_count": 0,
                "node_npm_npx_execution_count": 0,
                "counter_scope": "executor-authorized-call-sites-only",
                "runtime_syscall_observation_available": False,
            },
            "SUCCESS_COUNTER_SHAPE",
        )
        cross(
            g00.get("schema_sha256") == schema_observation.get("sha256")
            and g00.get("schema_bytes") == schema_observation.get("bytes")
            and g00.get("schema_count") == schema_observation.get("schema_count")
            and g00.get("schema_bundle_receipt_sha256") == schema_observation.get("schema_bundle_receipt_sha256"),
            "SUCCESS_SCHEMA_BINDING",
        )
        cross(g02.get("private_control_identity_commitment") == attestation.get("private_control_identity_commitment"), "SUCCESS_PRIVATE_CONTROL")
        cross(
            runtime.get("toolchain_set_receipt_sha256") == toolchain.get("toolchain_set_receipt_sha256") == g03.get("toolchain_set_receipt_sha256")
            and runtime.get("dynamic_closure_receipt_sha256") == toolchain.get("dynamic_closure_receipt_sha256") == g03.get("dynamic_closure_receipt_sha256"),
            "SUCCESS_TOOLCHAIN",
        )
        tool_hashes = toolchain.get("hashes")
        cross(isinstance(tool_hashes, Mapping) and frozenset(tool_hashes) == frozenset(TOOLCHAIN_ROLES), "SUCCESS_TOOL_HASH_ROLES")
        for digest_value in tool_hashes.values():
            require_sha256(digest_value, "PUBLIC_RESULT_TOOL_HASH")
        binding = require_exact_object(
            authority_binding,
            (
                "approval_challenge_id", "receipt_digest", "schema_binding_observation", "toolchain_hashes",
                "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment",
                "private_preapproval_commitment", "private_control_identity_commitment",
                "hmac_key_id", "authorized_locator_commitments", "package_lock_raw_sha256",
                "toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256",
            ),
            "PUBLIC_RESULT_AUTHORITY_BINDING",
        )
        require_sha256(binding.get("hmac_key_id"), "PUBLIC_RESULT_SUCCESS_AUTHORITY_KEY")
        checked_locator_commitments(binding.get("authorized_locator_commitments"))
        cross(binding.get("approval_challenge_id") == challenge, "SUCCESS_AUTHORITY_CHALLENGE")
        cross(binding.get("receipt_digest") == result.get("receipt_digest"), "SUCCESS_AUTHORITY_RECEIPT")
        cross(binding.get("schema_binding_observation") == schema_observation, "SUCCESS_AUTHORITY_SCHEMA")
        cross(binding.get("toolchain_hashes") == tool_hashes, "SUCCESS_AUTHORITY_TOOLCHAIN")
        for field in (
            "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment",
            "private_preapproval_commitment", "private_control_identity_commitment",
        ):
            cross(binding.get(field) == attestation.get(field), "SUCCESS_AUTHORITY_" + field.upper())
        cross(
            binding.get("package_lock_raw_sha256") == static_expected.get("package_lock_sha256"),
            "SUCCESS_AUTHORITY_PACKAGE_LOCK",
        )
        cross(
            binding.get("toolchain_set_receipt_sha256") == toolchain.get("toolchain_set_receipt_sha256")
            and binding.get("dynamic_closure_receipt_sha256") == toolchain.get("dynamic_closure_receipt_sha256"),
            "SUCCESS_AUTHORITY_TOOLCHAIN_RECEIPTS",
        )
        cross(g05.get("content_receipt_sha256") == static_expected.get("content_receipt_sha256") == lock_closure.get("content_receipt_sha256"), "SUCCESS_CONTENT")
        cross(g06.get("ustar_closure_sha256") == static_expected.get("ustar_closure_sha256") == lock_closure.get("ustar_closure_sha256"), "SUCCESS_USTAR")
        cross(g14.get("expected_tree_sha256") == static_tree.get("sha256") == lock_closure.get("expected_tree_sha256"), "SUCCESS_TREE")
        cross(g15.get("resolution_receipt_sha256") == static_resolution.get("sha256") == lock_closure.get("resolution_receipt_sha256"), "SUCCESS_RESOLUTION")
        cross(
            g16.get("tree_sha256") == g21.get("tree_sha256") == publication.get("tree_sha256") == static_tree.get("sha256"),
            "SUCCESS_FINAL_TREE",
        )
        cross(g18.get("publish_syscall") == publication.get("publish_syscall") and g18.get("publish_flag") == publication.get("publish_flag"), "SUCCESS_PUBLICATION")
        cross(g23.get("ledger_head_hmac_sha256") == publication.get("private_ledger_head_hmac_sha256"), "SUCCESS_LEDGER_HEAD")
        cross(g04.get("authorized_network_call_site_invocation_count") == counters.get("network_attempt_count") == 0, "SUCCESS_NETWORK_COUNTER")
        cross(
            g17.get("authorized_lifecycle_execution_call_site_invocation_count") == counters.get("lifecycle_execution_count") == 0
            and g17.get("authorized_installed_code_call_site_invocation_count") == counters.get("installed_code_execution_count") == 0
            and g17.get("authorized_node_npm_npx_call_site_invocation_count") == counters.get("node_npm_npx_execution_count") == 0,
            "SUCCESS_EXECUTION_COUNTERS",
        )
        cross(g20.get("outside_scope_mutation_count") == containment.get("outside_scope_mutation_count") == 0, "SUCCESS_CONTAINMENT")
        cross(g22.get("target_worktree_claude_sessions") == containment.get("target_worktree_claude_sessions") == 0, "SUCCESS_SESSIONS")
        return result

    if ok is False:
        allowed_failure_fields = common_fields | {
            "approval_challenge_id", "receipt_digest", "error", "retention", "ledger_evidence",
        }
        cross(frozenset(result).issubset(allowed_failure_fields), "FAILURE_FIELDS")
        cross("error" in result and "retention" in result, "FAILURE_REQUIRED_FIELDS")
        cross(
            ("approval_challenge_id" in result) == ("receipt_digest" in result),
            "FAILURE_AUTHORITY_PAIR",
        )
        if "approval_challenge_id" in result:
            challenge = result.get("approval_challenge_id")
            cross(isinstance(challenge, str) and CHALLENGE_RE.fullmatch(challenge) is not None, "FAILURE_CHALLENGE")
        if "receipt_digest" in result:
            require_sha256(result.get("receipt_digest"), "PUBLIC_RESULT_FAILURE_RECEIPT")
        cross(result.get("state") == "failed", "FAILURE_STATE")
        cross(authority.get("retry_authorized") is False and authority.get("public_success_attestation_allowed") is False, "FAILURE_AUTHORITY")
        error = mapping(result, "error")
        require_exact_object(error, ("code", "detail_code", "exit"), "PUBLIC_RESULT_ERROR")
        error_exit = error.get("exit")
        error_code = error.get("code")
        error_detail = error.get("detail_code")
        cross(type(error_exit) is int and error_exit in {int(item) for item in Exit if item is not Exit.OK}, "FAILURE_ERROR_EXIT")
        cross(error_code == public_exit_category(error_exit), "FAILURE_ERROR_CATEGORY")
        cross(
            isinstance(error_detail, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", error_detail) is not None,
            "FAILURE_ERROR_DETAIL",
        )
        retention = mapping(result, "retention")
        require_exact_object(
            retention,
            (
                "stage_deleted_or_moved_on_failure", "automatic_rollback_performed",
                "private_state_inspection_required",
            ),
            "PUBLIC_RESULT_RETENTION",
        )
        cross(retention.get("stage_deleted_or_moved_on_failure") is False and retention.get("automatic_rollback_performed") is False, "FAILURE_RETENTION")
        failed_gate_records = [record for record in gate_records if record.get("status") == "FAIL"]
        cross(len(failed_gate_records) <= 1, "FAILURE_GATE_COUNT")
        if failed_gate_records:
            failed_evidence = failed_gate_records[0].get("evidence")
            cross(
                isinstance(failed_evidence, Mapping)
                and failed_evidence.get("public_code") == error_code
                and failed_evidence.get("detail_code") == error_detail
                and failed_evidence.get("public_exit") == error_exit,
                "FAILURE_GATE_CODE",
            )
        passed_gate_ids = {
            record.get("gate_id")
            for record in gate_records
            if isinstance(record, Mapping) and record.get("status") == "PASS"
        }
        failure_authority_fields: List[str] = []
        if "approval_challenge_id" in result:
            failure_authority_fields.extend(("approval_challenge_id", "receipt_digest"))
        if "G00" in passed_gate_ids:
            failure_authority_fields.append("schema_binding_observation")
        if "G02" in passed_gate_ids:
            failure_authority_fields.extend(
                (
                    "private_control_identity_commitment",
                    "hmac_key_id",
                    "authorized_locator_commitments",
                )
            )
        if "G03" in passed_gate_ids:
            failure_authority_fields.extend(
                ("toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256")
            )
        if "ledger_evidence" in result:
            failure_authority_fields.append("ledger_evidence")
        failure_authority: Optional[Mapping[str, Any]] = None
        if failure_authority_fields:
            failure_authority = require_exact_object(
                authority_binding,
                failure_authority_fields,
                "PUBLIC_RESULT_FAILURE_AUTHORITY_BINDING",
            )
        else:
            cross(authority_binding is None or authority_binding == {}, "FAILURE_AUTHORITY_BINDING_ABSENT")
        if "approval_challenge_id" in result:
            cross(
                failure_authority is not None
                and failure_authority.get("approval_challenge_id") == result.get("approval_challenge_id")
                and failure_authority.get("receipt_digest") == result.get("receipt_digest"),
                "FAILURE_RUN_AUTHORITY",
            )
        if "G00" in passed_gate_ids:
            g00 = gate_evidence("G00")
            schema_authority = checked_schema_observation(
                {"schema_binding_observation": failure_authority.get("schema_binding_observation")}
            )
            cross(
                g00.get("schema_sha256") == schema_authority.get("sha256")
                and g00.get("schema_bytes") == schema_authority.get("bytes")
                and g00.get("schema_count") == schema_authority.get("schema_count")
                and g00.get("schema_bundle_receipt_sha256")
                == schema_authority.get("schema_bundle_receipt_sha256"),
                "FAILURE_SCHEMA_AUTHORITY",
            )
        if "G02" in passed_gate_ids:
            g02 = gate_evidence("G02")
            private_control = failure_authority.get("private_control_identity_commitment")
            require_sha256(private_control, "PUBLIC_RESULT_FAILURE_PRIVATE_CONTROL")
            require_sha256(failure_authority.get("hmac_key_id"), "PUBLIC_RESULT_FAILURE_HMAC_KEY")
            failure_locators = checked_locator_commitments(
                failure_authority.get("authorized_locator_commitments")
            )
            cross(
                private_control == g02.get("private_control_identity_commitment")
                and len(failure_locators) == g02.get("authorized_locator_commitment_count") == 5,
                "FAILURE_PRIVATE_AUTHORITY",
            )
        if "G03" in passed_gate_ids:
            g03 = gate_evidence("G03")
            cross(
                runtime.get("toolchain_set_receipt_sha256") == g03.get("toolchain_set_receipt_sha256")
                == failure_authority.get("toolchain_set_receipt_sha256")
                and runtime.get("dynamic_closure_receipt_sha256") == g03.get("dynamic_closure_receipt_sha256")
                == failure_authority.get("dynamic_closure_receipt_sha256"),
                "FAILURE_TOOLCHAIN_RECEIPTS",
            )
        else:
            cross(runtime_fields == runtime_base_fields, "FAILURE_TOOLCHAIN_RECEIPTS_ABSENT")
        read_only_execution_order = (
            "G00", "G02", "G10", "G03", "G11", "G12", "G04",
            "G05", "G06", "G07", "G08", "G09", "G14", "G15",
        )
        acquire_execution_order = (
            "G00", "G02", "G10", "G03", "G12", "G04", "G11",
            "G05", "G06", "G07", "G08", "G09", "G14", "G15",
            "G01", "G13", "G16", "G17", "G18", "G21", "G19", "G20",
            "G22", "G23", "G24",
        )
        if mode in ("census", "verify"):
            cross(
                "approval_challenge_id" not in result and "receipt_digest" not in result,
                "READ_ONLY_FAILURE_AUTHORITY_ABSENT",
            )
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after fail-closed evidence review",
                "READ_ONLY_FAILURE_NEXT_AUTHORITY",
            )
            cross(result.get("phase") in ("entry-fail-closed", "read-only-fail-closed"), "READ_ONLY_FAILURE_PHASE")
            cross(terminal == read_only_terminal_state(), "READ_ONLY_FAILURE_TERMINAL")
            cross(retention.get("private_state_inspection_required") is False, "READ_ONLY_FAILURE_RETENTION")
            if result.get("phase") == "entry-fail-closed":
                cross(not gates, "READ_ONLY_ENTRY_GATES")
            else:
                execution_prefix_length(read_only_execution_order, "READ_ONLY_FAILURE_GATE")
        elif mode == "unknown" and result.get("phase") == "public-projection":
            cross(
                "approval_challenge_id" not in result and "receipt_digest" not in result,
                "PRIVACY_FAILURE_AUTHORITY_ABSENT",
            )
            cross(not gates, "PRIVACY_FAILURE_GATES")
            cross(
                terminal
                == {
                    "challenge_state": "unknown-fail-closed",
                    "claim_state": "unknown-fail-closed",
                    "stage_state": "unknown-fail-closed",
                    "publication_state": "unknown-fail-closed",
                    "ledger_terminal_state": "unknown-fail-closed",
                    "target_disposition": "unknown-user-decision-required",
                },
                "PRIVACY_FAILURE_TERMINAL",
            )
            typed_subset(
                error,
                {
                    "code": "PRIVACY_FAIL_CLOSED",
                    "detail_code": "PUBLIC_PROJECTION_REJECTED",
                    "exit": int(Exit.PRIVACY),
                },
                "PRIVACY_FAILURE_ERROR",
            )
            cross(retention.get("private_state_inspection_required") is True, "PRIVACY_FAILURE_RETENTION")
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after private-state inspection",
                "PRIVACY_FAILURE_NEXT_AUTHORITY",
            )
        elif mode == "unknown":
            cross(
                "approval_challenge_id" not in result and "receipt_digest" not in result,
                "UNKNOWN_FAILURE_AUTHORITY_ABSENT",
            )
            cross(result.get("phase") == "entry-fail-closed" and not gates, "UNKNOWN_FAILURE_ENTRY")
            cross(terminal == read_only_terminal_state(), "UNKNOWN_FAILURE_TERMINAL")
            cross(retention.get("private_state_inspection_required") is False, "UNKNOWN_FAILURE_RETENTION")
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after fail-closed evidence review",
                "UNKNOWN_FAILURE_NEXT_AUTHORITY",
            )
        elif mode == "acquire" and result.get("phase") == "entry-fail-closed":
            cross(
                "approval_challenge_id" not in result and "receipt_digest" not in result,
                "ACQUIRE_ENTRY_AUTHORITY_ABSENT",
            )
            cross(not gates, "ACQUIRE_ENTRY_GATES")
            expected_entry_terminal = read_only_terminal_state()
            expected_entry_terminal["challenge_state"] = "preclaim-rejected-new-envelope-required"
            cross(terminal == expected_entry_terminal, "ACQUIRE_ENTRY_TERMINAL")
            cross(retention.get("private_state_inspection_required") is True, "ACQUIRE_ENTRY_RETENTION")
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after fail-closed evidence review",
                "ACQUIRE_ENTRY_NEXT_AUTHORITY",
            )
        elif mode == "acquire" and validated_gates.get("complete") is False:
            cross(
                "approval_challenge_id" in result and "receipt_digest" in result,
                "ACQUIRE_FAILURE_AUTHORITY_REQUIRED",
            )
            prefix_length = execution_prefix_length(acquire_execution_order, "ACQUIRE_FAILURE_GATE")
            phase = result.get("phase")
            last_status = (
                None
                if prefix_length == 0
                else gates[acquire_execution_order[prefix_length - 1]].get("status")
            )
            pass_or_fail = frozenset(("PASS", "FAIL"))
            phase_trace_matrix = {
                "schema-contract": {0: {None}, 1: pass_or_fail},
                "private-public-boundary": {1: {"PASS"}, 2: pass_or_fail},
                "control-root-before": {2: {"PASS"}, 3: pass_or_fail},
                "content-addressed-toolchain": {3: {"PASS"}, 4: pass_or_fail},
                "git-preimage": {4: {"PASS"}},
                "process-census-before": {4: {"PASS"}, 5: pass_or_fail, 6: pass_or_fail},
                "target-preimage": {6: {"PASS"}, 7: pass_or_fail},
                "cache-and-expected-closure": {
                    7: {"PASS"},
                    **{length: pass_or_fail for length in range(8, 15)},
                },
                "persistent-claim": {14: {"PASS"}, 15: pass_or_fail},
                "stage-materialization": {15: {"PASS"}, 16: pass_or_fail},
                "stage-tree-attestation": {16: {"PASS"}, 17: pass_or_fail, 18: pass_or_fail},
                "pre-promotion-cas": {18: {"PASS"}},
                "sealed-marker-removed": {18: {"PASS"}, 19: {"FAIL"}},
                "rename-succeeded-attestation-incomplete": {19: pass_or_fail, 20: pass_or_fail},
                "post-promotion-containment": {
                    20: {"PASS"}, 21: pass_or_fail, 22: pass_or_fail, 23: pass_or_fail,
                },
                "ledger-terminal-success": {23: {"PASS"}, 24: {"FAIL"}},
                "static-attestation-complete": {24: pass_or_fail, 25: {"FAIL"}},
            }
            cross(isinstance(phase, str) and phase in phase_trace_matrix, "ACQUIRE_FAILURE_PHASE")
            allowed_status_by_prefix = phase_trace_matrix[phase]
            cross(
                prefix_length in allowed_status_by_prefix
                and last_status in allowed_status_by_prefix[prefix_length],
                "ACQUIRE_FAILURE_PHASE_GATE",
            )
            g18_record = gates.get("G18")
            g18_status = g18_record.get("status") if isinstance(g18_record, Mapping) else None
            g21_record = gates.get("G21")
            g21_status = g21_record.get("status") if isinstance(g21_record, Mapping) else None
            g23_record = gates.get("G23")
            g23_status = g23_record.get("status") if isinstance(g23_record, Mapping) else None
            if phase == "post-promotion-containment":
                cross(g18_status == "PASS" and g21_status == "PASS", "ACQUIRE_POST_PHASE_GATES")
            claim_state = terminal.get("claim_state")
            ledger_state = terminal.get("ledger_terminal_state")
            challenge_state = terminal.get("challenge_state")
            publication_state = terminal.get("publication_state")
            cross(claim_state in ("not-created", "created-0700"), "ACQUIRE_FAILURE_CLAIM")
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after retained-state inspection; never retry automatically",
                "ACQUIRE_FAILURE_NEXT_AUTHORITY",
            )
            if prefix_length < 15:
                cross(claim_state == "not-created", "ACQUIRE_PRE_G01_CLAIM")
            elif prefix_length > 15:
                cross(claim_state == "created-0700", "ACQUIRE_POST_G01_CLAIM")
            elif gates.get("G01", {}).get("status") == "PASS":
                cross(claim_state == "created-0700", "ACQUIRE_G01_PASS_CLAIM")
            if prefix_length < 19:
                cross(terminal.get("stage_state") != "renamed-to-target", "ACQUIRE_PRE_G18_STAGE")
                cross(
                    publication_state
                    not in (
                        "rename-succeeded-attestation-incomplete",
                        "attributed-target-and-stage-both-observed-fail-closed",
                        "promoted-target-missing-fail-closed",
                    ),
                    "ACQUIRE_PRE_G18_PUBLICATION",
                )
            cross(
                terminal.get("target_disposition") != "static-attested-target-retained",
                "ACQUIRE_FAILURE_STATIC_TARGET",
            )
            cross(ledger_state != "receipt-consumed-recorded", "ACQUIRE_FAILURE_NONTERMINAL_LEDGER")
            stage_state = terminal.get("stage_state")
            target_disposition = terminal.get("target_disposition")
            stage_class_by_state = {
                "not-created": "N",
                "retained-marker-not-yet-created": "R",
                "retained-marker-present": "R",
                "retained-marker-removed": "R",
                "retained-marker-state-unknown": "R",
                "retained-marker-unexpected-type": "R",
                "renamed-to-target": "M",
                "unexpected-stage-type-fail-closed": "H",
                "unknown-fail-closed": "H",
            }
            stage_class = stage_class_by_state[stage_state]
            publication_stage_disposition = {
                "not-attempted": {
                    "N": "target-absent",
                    "R": "target-absent-stage-retained-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "target-observed-unattributed-fail-closed": {
                    "N": "retain-unattributed-target-user-decision-required",
                    "R": "retain-unattributed-target-user-decision-required",
                    "M": "retain-unattributed-target-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "unexpected-target-type-fail-closed": {
                    "N": "retain-unauthorized-target-user-decision-required",
                    "R": "retain-unauthorized-target-user-decision-required",
                    "M": "retain-unauthorized-target-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "rename-succeeded-attestation-incomplete": {
                    "M": "retain-unauthorized-target-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "attributed-target-and-stage-both-observed-fail-closed": {
                    "R": "retain-unauthorized-target-user-decision-required",
                },
                "promoted-target-missing-fail-closed": {
                    "R": "unknown-user-decision-required",
                    "M": "unknown-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "unknown-fail-closed": {
                    "N": "unknown-user-decision-required",
                    "R": "unknown-user-decision-required",
                    "M": "unknown-user-decision-required",
                    "H": "unknown-user-decision-required",
                },
                "static-ledger-success-public-result-failed": {
                    "M": "retain-target-user-decision-required",
                },
                "static-attested": {
                    "M": "static-attested-target-retained",
                },
            }
            allowed_dispositions = publication_stage_disposition[publication_state]
            cross(stage_class in allowed_dispositions, "ACQUIRE_PUBLICATION_STAGE_REACHABILITY")
            cross(
                target_disposition == allowed_dispositions[stage_class],
                "ACQUIRE_PUBLICATION_DISPOSITION_REACHABILITY",
            )
            if isinstance(g18_record, Mapping) and g18_record.get("status") == "PASS":
                cross(publication_state != "not-attempted", "ACQUIRE_G18_PASS_PUBLICATION")
            if phase == "sealed-marker-removed":
                cross(stage_state != "not-created", "ACQUIRE_SEALED_PHASE_STAGE")
            if phase in (
                "stage-tree-attestation", "pre-promotion-cas", "sealed-marker-removed",
                "rename-succeeded-attestation-incomplete", "post-promotion-containment",
                "ledger-terminal-success", "static-attestation-complete",
            ):
                cross(stage_state != "not-created", "ACQUIRE_POST_MATERIALIZATION_PHASE_STAGE")
            g13_record = gates.get("G13")
            if isinstance(g13_record, Mapping) and g13_record.get("status") == "PASS":
                cross(stage_state != "not-created", "ACQUIRE_G13_PASS_STAGE")
            if phase == "rename-succeeded-attestation-incomplete":
                cross(publication_state != "not-attempted", "ACQUIRE_RENAME_PHASE_PUBLICATION")
            if phase in (
                "post-promotion-containment", "ledger-terminal-success", "static-attestation-complete",
            ):
                cross(publication_state != "not-attempted", "ACQUIRE_POST_RENAME_PHASE_PUBLICATION")
            if claim_state == "not-created":
                cross(challenge_state == "preclaim-rejected-new-envelope-required", "ACQUIRE_PRECLAIM_CHALLENGE")
                cross(ledger_state == "not-created", "ACQUIRE_PRECLAIM_LEDGER")
            elif claim_state == "created-0700":
                cross(challenge_state in ("claimed-consumed", "completed-consumed"), "ACQUIRE_CLAIM_CHALLENGE")
                cross(retention.get("private_state_inspection_required") is True, "ACQUIRE_CLAIM_RETENTION")
                cross(
                    ledger_state
                    in (
                        "absent-partial-or-semantic-invalid",
                        "terminal-failure-recorded",
                        "terminal-success-recorded",
                    ),
                    "ACQUIRE_CREATED_CLAIM_LEDGER",
                )
            if ledger_state == "terminal-success-recorded":
                cross(prefix_length >= 24, "ACQUIRE_SUCCESS_LEDGER_GATE_PREFIX")
                cross(challenge_state == "completed-consumed", "ACQUIRE_SUCCESS_LEDGER_CHALLENGE")
                cross(claim_state == "created-0700", "ACQUIRE_SUCCESS_LEDGER_CLAIM")
                cross(stage_state != "not-created", "ACQUIRE_SUCCESS_LEDGER_STAGE")
                cross(
                    publication_state
                    in (
                        "static-ledger-success-public-result-failed",
                        "rename-succeeded-attestation-incomplete",
                        "target-observed-unattributed-fail-closed",
                        "promoted-target-missing-fail-closed",
                        "attributed-target-and-stage-both-observed-fail-closed",
                        "unexpected-target-type-fail-closed",
                        "unknown-fail-closed",
                    ),
                    "ACQUIRE_SUCCESS_LEDGER_PUBLICATION",
                )
                if publication_state == "rename-succeeded-attestation-incomplete":
                    cross(
                        stage_class == "H"
                        and target_disposition == "unknown-user-decision-required",
                        "ACQUIRE_SUCCESS_LEDGER_RENAME_RECOVERY",
                    )
            else:
                cross(challenge_state != "completed-consumed", "ACQUIRE_INCOMPLETE_CHALLENGE")
                cross(publication_state not in ("static-attested", "static-ledger-success-public-result-failed"), "ACQUIRE_INCOMPLETE_PUBLICATION")
            if phase == "static-attestation-complete":
                cross(ledger_state == "terminal-success-recorded", "ACQUIRE_STATIC_PHASE_LEDGER")
            cross(
                retention.get("private_state_inspection_required") is (claim_state != "not-created"),
                "ACQUIRE_FAILURE_RETENTION",
            )
            if "ledger_evidence" in result:
                phase_ledger_counts = {
                    "persistent-claim": {2, 3},
                    "stage-materialization": {3, 4},
                    "stage-tree-attestation": {4},
                    "pre-promotion-cas": {4, 5},
                    "sealed-marker-removed": {5},
                    "rename-succeeded-attestation-incomplete": {5, 6},
                    "post-promotion-containment": {6},
                    "ledger-terminal-success": {6},
                    "static-attestation-complete": {6},
                }
                phase_ledger = checked_public_ledger()
                failed_gate_id = (
                    failed_gate_records[0].get("gate_id") if failed_gate_records else None
                )
                failed_gate_ledger_count = {"G01": 2, "G13": 3, "G18": 5}
                if (
                    phase_ledger.get("terminal_kind") == "failure"
                    and failed_gate_id in failed_gate_ledger_count
                ):
                    cross(
                        phase_ledger.get("record_count")
                        == failed_gate_ledger_count[failed_gate_id],
                        "ACQUIRE_FAILED_GATE_LEDGER_PROVENANCE",
                    )
                cross(
                    phase in phase_ledger_counts
                    and phase_ledger.get("record_count") in phase_ledger_counts[phase],
                    "ACQUIRE_LEDGER_PHASE_PROVENANCE",
                )
        elif mode != "acquire":
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_FAILURE_MODE")
        ledger_state = terminal.get("ledger_terminal_state")
        ledger_evidence_present = "ledger_evidence" in result
        if ledger_state in ("terminal-success-recorded", "terminal-failure-recorded"):
            cross(ledger_evidence_present, "FAILURE_TERMINAL_LEDGER_EVIDENCE")
        elif ledger_evidence_present:
            fail(Exit.EVIDENCE, "PUBLIC_RESULT_FAILURE_LEDGER_STATE_WITH_EVIDENCE")
        g23_record = gates.get("G23")
        if isinstance(g23_record, Mapping) and g23_record.get("status") == "PASS":
            ledger = checked_public_ledger()
            g23 = gate_evidence("G23")
            cross(
                terminal.get("challenge_state") == "completed-consumed"
                and terminal.get("claim_state") == "created-0700"
                and terminal.get("stage_state") != "not-created"
                and terminal.get("publication_state")
                in (
                    "static-ledger-success-public-result-failed",
                    "rename-succeeded-attestation-incomplete",
                    "target-observed-unattributed-fail-closed",
                    "promoted-target-missing-fail-closed",
                    "attributed-target-and-stage-both-observed-fail-closed",
                    "unexpected-target-type-fail-closed",
                    "unknown-fail-closed",
                )
                and terminal.get("ledger_terminal_state") == "terminal-success-recorded",
                "G23_SUCCESS_TERMINAL",
            )
            cross(
                ledger.get("checker_interface") == g23.get("checker_interface") == LEDGER_CHECKER_INTERFACE
                and ledger.get("record_count") == g23.get("record_count") == 6
                and ledger.get("terminal_kind") == g23.get("terminal_kind") == "success"
                and ledger.get("head_hmac_sha256") == g23.get("ledger_head_hmac_sha256"),
                "G23_SUCCESS_LEDGER",
            )
        if ledger_evidence_present:
            cross(
                failure_authority is not None
                and failure_authority.get("ledger_evidence") == result.get("ledger_evidence"),
                "FAILURE_LEDGER_AUTHORITY",
            )
        if validated_gates.get("complete") is True:
            cross(
                "approval_challenge_id" in result and "receipt_digest" in result,
                "FINALIZATION_AUTHORITY_REQUIRED",
            )
            ledger = checked_public_ledger()
            g23 = gate_evidence("G23")
            cross(mode == "acquire" and result.get("phase") == "resource-finalization", "FINALIZATION_PHASE")
            cross(
                error_code == "EVIDENCE_FAIL_CLOSED"
                and error_detail == "RESOURCE_FINALIZATION_CLOSE"
                and error_exit == int(Exit.EVIDENCE),
                "FINALIZATION_ERROR",
            )
            cross(terminal.get("publication_state") == "static-ledger-success-public-result-failed", "FINALIZATION_PUBLICATION")
            cross(
                retention.get("private_state_inspection_required") is True,
                "FINALIZATION_RETENTION",
            )
            cross(
                authority.get("next_required_authority")
                == "new explicit user approval after retained-state inspection; never retry automatically",
                "FINALIZATION_NEXT_AUTHORITY",
            )
            cross(
                terminal
                == {
                    "challenge_state": "completed-consumed",
                    "claim_state": "created-0700",
                    "stage_state": "renamed-to-target",
                    "publication_state": "static-ledger-success-public-result-failed",
                    "ledger_terminal_state": "terminal-success-recorded",
                    "target_disposition": "retain-target-user-decision-required",
                },
                "FINALIZATION_TERMINAL",
            )
            cross(
                ledger.get("checker_interface") == LEDGER_CHECKER_INTERFACE
                and ledger.get("terminal_kind") == "success"
                and ledger.get("record_count") == 6,
                "FINALIZATION_LEDGER",
            )
            cross(
                ledger.get("head_hmac_sha256") == g23.get("ledger_head_hmac_sha256")
                and ledger.get("checker_interface") == g23.get("checker_interface")
                and ledger.get("record_count") == g23.get("record_count")
                and ledger.get("terminal_kind") == g23.get("terminal_kind"),
                "FINALIZATION_LEDGER_HEAD",
            )
        elif "ledger_evidence" in result:
            ledger = checked_public_ledger()
            if ledger.get("terminal_kind") == "success":
                cross(terminal.get("ledger_terminal_state") == "terminal-success-recorded", "FAILURE_SUCCESS_LEDGER_STATE")
            else:
                cross(ledger.get("terminal_kind") == "failure", "FAILURE_LEDGER_KIND")
                cross(terminal.get("ledger_terminal_state") == "terminal-failure-recorded", "FAILURE_LEDGER_STATE")
        return result

    fail(Exit.EVIDENCE, "PUBLIC_RESULT_BRANCH")
    raise AssertionError("unreachable")


class AttemptState:
    """Public, locator-free recovery state for one acquire invocation."""

    def __init__(self) -> None:
        self.phase = "entry"
        self.challenge_state = "preclaim-pending"
        self.claim_state = "not-created"
        self.stage_state = "not-created"
        self.publication_state = "not-attempted"
        self.ledger_terminal_state = "not-created"
        self.target_disposition = "target-absent"

    def set_phase(self, phase: str) -> None:
        if not isinstance(phase, str) or not re.fullmatch(r"[a-z0-9-]{3,96}", phase):
            fail(Exit.INTERNAL, "ATTEMPT_PHASE")
        self.phase = phase

    def claim_created(self) -> None:
        self.challenge_state = "claimed-consumed"
        self.claim_state = "created-0700"
        self.ledger_terminal_state = "receipt-consumed-recorded"

    def claim_directory_created(self) -> None:
        self.challenge_state = "claimed-consumed"
        self.claim_state = "created-0700"
        self.ledger_terminal_state = "absent-partial-or-semantic-invalid"

    def stage_directory_created(self) -> None:
        self.stage_state = "retained-marker-not-yet-created"
        if self.publication_state == "not-attempted":
            self.target_disposition = "target-absent-stage-retained-user-decision-required"

    def stage_marker_created(self) -> None:
        self.stage_state = "retained-marker-present"
        if self.publication_state == "not-attempted":
            self.target_disposition = "target-absent-stage-retained-user-decision-required"

    def stage_created(self) -> None:
        self.stage_marker_created()

    def stage_marker_removed(self) -> None:
        self.stage_state = "retained-marker-removed"
        if self.publication_state == "not-attempted":
            self.target_disposition = "target-absent-stage-retained-user-decision-required"

    def target_promoted(self) -> None:
        self.stage_state = "renamed-to-target"
        self.publication_state = "rename-succeeded-attestation-incomplete"
        self.target_disposition = "retain-unauthorized-target-user-decision-required"

    def terminal_failure_recorded(self) -> None:
        self.ledger_terminal_state = "terminal-failure-recorded"

    def ledger_invalid(self) -> None:
        self.ledger_terminal_state = "absent-partial-or-semantic-invalid"

    def terminal_success_publication_failed(self) -> None:
        self.challenge_state = "completed-consumed"
        self.ledger_terminal_state = "terminal-success-recorded"
        if (
            self.stage_state == "renamed-to-target"
            and self.publication_state in ("rename-succeeded-attestation-incomplete", "static-attested")
        ):
            self.publication_state = "static-ledger-success-public-result-failed"
            self.target_disposition = "retain-target-user-decision-required"

    def terminal_success_recorded(self) -> None:
        self.challenge_state = "completed-consumed"
        self.ledger_terminal_state = "terminal-success-recorded"
        self.publication_state = "static-attested"
        self.target_disposition = "static-attested-target-retained"

    def projection(self) -> Dict[str, Any]:
        return {
            "challenge_state": self.challenge_state,
            "claim_state": self.claim_state,
            "stage_state": self.stage_state,
            "publication_state": self.publication_state,
            "ledger_terminal_state": self.ledger_terminal_state,
            "target_disposition": self.target_disposition,
        }

    def failure_projection(self) -> Dict[str, Any]:
        result = self.projection()
        if self.claim_state == "not-created":
            result["challenge_state"] = "preclaim-rejected-new-envelope-required"
        return result


def runtime_assurance_projection(toolchain: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "toolchain_assurance": "runtime-self-attested-not-pre-exec",
        "pre_exec_launcher_attested": False,
        "python_isolation_flags_required": ["-I", "-S", "-B"],
    }
    if toolchain is not None:
        result["toolchain_set_receipt_sha256"] = toolchain.get("toolchain_set_receipt_sha256")
        result["dynamic_closure_receipt_sha256"] = toolchain.get("dynamic_closure_receipt_sha256")
    return result


def base_public_result(
    ok: bool,
    mode: str,
    phase: str,
    state: str,
    terminal_state: Mapping[str, Any],
    gates: Mapping[str, Any],
    toolchain: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": PUBLIC_RESULT_SCHEMA_VERSION,
        "artifact_type": PUBLIC_RESULT_ARTIFACT_TYPE,
        "ok": ok,
        "mode": mode,
        "phase": phase,
        "state": state,
        "terminal_state": dict(terminal_state),
        "runtime_assurance": runtime_assurance_projection(toolchain),
        "gate_results": dict(gates),
    }


def _ledger_expected_data(event: str) -> Tuple[str, ...]:
    fields = {
        "receipt-consumed": ("authority",),
        "preflight-frozen": (
            "envelope_raw_sha256", "artifact_manifest_commitment", "git_commitment",
            "cache_manifest_commitment", "selected_package_count", "compressed_bytes",
            "payload_bytes", "tree_sha256", "network_attempt_count",
            "lifecycle_execution_count", "installed_code_execution_count",
        ),
        "stage-materialized": (
            "file_count", "directory_count", "symlink_count", "tree_sha256",
            "incomplete_marker_present",
        ),
        "pre-promotion-cas-pass": (
            "artifact_manifest_unchanged", "git_unchanged", "cache_unchanged",
            "claude_sessions", "target_absent", "incomplete_marker_present",
        ),
        "stage-promoted": ("tree_sha256", "incomplete_marker_present", "root_mode", "rename_profile"),
        "static-attestation-complete": (
            "state", "tree_sha256", "selected_package_count", "network_attempt_count",
            "lifecycle_execution_count", "installed_code_execution_count",
            "openspec_execution_allowed", "openspec_scaffold_allowed",
        ),
        "attempt-failed": (
            "public_code", "promoted", "stage_deleted_or_moved_on_failure",
            "automatic_rollback_performed",
        ),
    }
    if event not in fields:
        fail(Exit.EVIDENCE, "LEDGER_EVENT_UNKNOWN")
    return fields[event]


def _validate_ledger_event_data(event: str, sequence: int, data: Mapping[str, Any]) -> None:
    require_exact_object(data, _ledger_expected_data(event), "LEDGER_DATA")
    tree = "777dc62b5a2094903c2047cb30bc63eccf34543c3d4466be30b6ae4789d391a2"
    if event == "receipt-consumed":
        if data.get("authority") != "single-use-consumed-before-stage-write":
            fail(Exit.EVIDENCE, "LEDGER_RECEIPT_DATA")
    elif event == "preflight-frozen":
        for key in ("envelope_raw_sha256", "artifact_manifest_commitment", "git_commitment", "cache_manifest_commitment"):
            require_sha256(data.get(key), "LEDGER_PREFLIGHT")
        if (
            data.get("selected_package_count") != 167
            or data.get("compressed_bytes") != 13_916_529
            or data.get("payload_bytes") != 55_954_126
            or data.get("tree_sha256") != tree
        ):
            fail(Exit.EVIDENCE, "LEDGER_PREFLIGHT_CLOSURE")
        for key in ("network_attempt_count", "lifecycle_execution_count", "installed_code_execution_count"):
            require_zero(data.get(key), "LEDGER_PREFLIGHT_ZERO")
    elif event == "stage-materialized":
        if data != {
            "file_count": 4099,
            "directory_count": 554,
            "symlink_count": 12,
            "tree_sha256": tree,
            "incomplete_marker_present": True,
        }:
            fail(Exit.EVIDENCE, "LEDGER_STAGE_DATA")
    elif event == "pre-promotion-cas-pass":
        if data != {
            "artifact_manifest_unchanged": True,
            "git_unchanged": True,
            "cache_unchanged": True,
            "claude_sessions": 0,
            "target_absent": True,
            "incomplete_marker_present": True,
        }:
            fail(Exit.EVIDENCE, "LEDGER_CAS_DATA")
    elif event == "stage-promoted":
        if data != {
            "tree_sha256": tree,
            "incomplete_marker_present": False,
            "root_mode": "0755",
            "rename_profile": "renameatx_np-RENAME_EXCL",
        }:
            fail(Exit.EVIDENCE, "LEDGER_PROMOTED_DATA")
    elif event == "static-attestation-complete":
        if data != {
            "state": "static-attested-unexecuted",
            "tree_sha256": tree,
            "selected_package_count": 167,
            "network_attempt_count": 0,
            "lifecycle_execution_count": 0,
            "installed_code_execution_count": 0,
            "openspec_execution_allowed": False,
            "openspec_scaffold_allowed": False,
        }:
            fail(Exit.EVIDENCE, "LEDGER_COMPLETE_DATA")
    else:
        public_code = data.get("public_code")
        if not isinstance(public_code, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", public_code):
            fail(Exit.EVIDENCE, "LEDGER_FAILURE_CODE")
        promoted = data.get("promoted")
        if not isinstance(promoted, bool):
            fail(Exit.EVIDENCE, "LEDGER_FAILURE_PROMOTED")
        if sequence in (1, 2, 3) and promoted:
            fail(Exit.EVIDENCE, "LEDGER_FAILURE_PROMOTED_EARLY")
        if sequence == 5 and not promoted:
            fail(Exit.EVIDENCE, "LEDGER_FAILURE_PROMOTED_LATE")
        if data.get("stage_deleted_or_moved_on_failure") is not False or data.get("automatic_rollback_performed") is not False:
            fail(Exit.EVIDENCE, "LEDGER_FAILURE_RETENTION")


def validate_ledger_jsonl(
    raw: bytes,
    key: bytes,
    expected_challenge: str,
    expected_receipt: str,
    expected_head: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate exact executor JSONL bytes, event state machine and keyed chain."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_JSON_BYTES:
        fail(Exit.EVIDENCE, "LEDGER_RAW_SIZE")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n") or b"\n\n" in raw:
        fail(Exit.EVIDENCE, "LEDGER_RAW_PROFILE")
    if not isinstance(key, bytes) or len(key) != 32:
        fail(Exit.EVIDENCE, "LEDGER_KEY_PROFILE")
    if not isinstance(expected_challenge, str) or not CHALLENGE_RE.fullmatch(expected_challenge):
        fail(Exit.EVIDENCE, "LEDGER_CHALLENGE_PROFILE")
    require_sha256(expected_receipt, "LEDGER_RECEIPT")
    records: List[Dict[str, Any]] = []
    previous = "0" * 64
    previous_time: Optional[_datetime.datetime] = None
    for index, line in enumerate(raw.splitlines(keepends=True)):
        if not line.endswith(b"\n") or line == b"\n":
            fail(Exit.EVIDENCE, "LEDGER_LINE_PROFILE")
        value = parse_json_bytes(line, "LEDGER_LINE")
        if not isinstance(value, dict) or canonical_json(value) != line:
            fail(Exit.EVIDENCE, "LEDGER_LINE_NONCANONICAL")
        record = require_exact_object(
            value,
            "schema_version sequence at_utc challenge receipt_digest event previous_hmac_sha256 data hmac_sha256".split(),
            "LEDGER_RECORD",
        )
        if record.get("schema_version") != "gov01-static-acquisition-ledger-event-v2" or record.get("sequence") != index:
            fail(Exit.EVIDENCE, "LEDGER_SEQUENCE")
        if record.get("challenge") != expected_challenge or record.get("receipt_digest") != expected_receipt:
            fail(Exit.EVIDENCE, "LEDGER_AUTHORITY_DRIFT")
        at_utc = parse_utc(record.get("at_utc"), "LEDGER_TIME")
        if previous_time is not None and at_utc < previous_time:
            fail(Exit.EVIDENCE, "LEDGER_TIME_REVERSED")
        previous_time = at_utc
        if record.get("previous_hmac_sha256") != previous:
            fail(Exit.EVIDENCE, "LEDGER_CHAIN")
        event = record.get("event")
        data = record.get("data")
        if not isinstance(event, str) or not isinstance(data, dict):
            fail(Exit.EVIDENCE, "LEDGER_EVENT_SCHEMA")
        _validate_ledger_event_data(event, index, data)
        base = dict(record)
        actual_hmac = base.pop("hmac_sha256", None)
        require_sha256(actual_hmac, "LEDGER_HMAC")
        calculated = hmac_frame(key, LEDGER_DOMAIN, canonical_json(base))
        if not hmac.compare_digest(actual_hmac, calculated):
            fail(Exit.EVIDENCE, "LEDGER_HMAC_MISMATCH")
        previous = actual_hmac
        records.append(record)
    if len(records) < 2 or len(records) > 6:
        fail(Exit.EVIDENCE, "LEDGER_RECORD_COUNT")
    events = [record["event"] for record in records]
    success = [
        "receipt-consumed", "preflight-frozen", "stage-materialized",
        "pre-promotion-cas-pass", "stage-promoted", "static-attestation-complete",
    ]
    failure_prefixes = [success[:length] + ["attempt-failed"] for length in range(1, 6)]
    if events != success and events not in failure_prefixes:
        fail(Exit.EVIDENCE, "LEDGER_EVENT_SEQUENCE")
    if expected_head is not None:
        require_sha256(expected_head, "LEDGER_EXPECTED_HEAD")
        if not hmac.compare_digest(previous, expected_head):
            fail(Exit.EVIDENCE, "LEDGER_HEAD_MISMATCH")
    terminal_kind = "success" if events == success else "failure"
    return {
        "checker_interface": LEDGER_CHECKER_INTERFACE,
        "record_count": len(records),
        "terminal_kind": terminal_kind,
        "head_hmac_sha256": previous,
        "raw_sha256": sha256(raw),
        "raw_bytes": len(raw),
        "records": records,
    }


def build_private_ledger_projection(
    checker_report: Mapping[str, Any],
    checker_raw_sha256: str,
    checker_byte_length: int,
) -> Dict[str, Any]:
    """Project a successfully checked JSONL ledger into the private schema ABI."""
    report = require_exact_object(
        checker_report,
        "checker_interface record_count terminal_kind head_hmac_sha256 raw_sha256 raw_bytes records".split(),
        "PRIVATE_LEDGER_CHECKER_REPORT",
    )
    if report.get("checker_interface") != LEDGER_CHECKER_INTERFACE:
        fail(Exit.EVIDENCE, "PRIVATE_LEDGER_CHECKER_INTERFACE")
    require_sha256(checker_raw_sha256, "PRIVATE_LEDGER_CHECKER_ARTIFACT")
    if not isinstance(checker_byte_length, int) or isinstance(checker_byte_length, bool) or checker_byte_length <= 0:
        fail(Exit.EVIDENCE, "PRIVATE_LEDGER_CHECKER_BYTES")
    require_sha256(report.get("head_hmac_sha256"), "PRIVATE_LEDGER_HEAD")
    require_sha256(report.get("raw_sha256"), "PRIVATE_LEDGER_RAW")
    if report.get("terminal_kind") not in ("success", "failure"):
        fail(Exit.EVIDENCE, "PRIVATE_LEDGER_TERMINAL_KIND")
    if not isinstance(report.get("records"), list) or report.get("record_count") != len(report["records"]):
        fail(Exit.EVIDENCE, "PRIVATE_LEDGER_RECORDS")
    return {
        "schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2",
        "artifact_type": "gov-01-toolchain-static-acquisition-private-evidence",
        "classification": "PRIVATE-LOCAL-DO-NOT-COMMIT",
        "projection_kind": "read-only-complete-ledger-jsonl-projection; not a separately authorized persisted artifact",
        "ledger_parse_state": "complete-canonical-jsonl",
        "canonical_record_profile": (
            "each raw line is exactly UTF-8 NFC sorted-key compact JSON plus one LF; no BOM, CR, duplicate key, "
            "float, NaN, Infinity, blank line or trailing bytes"
        ),
        "semantic_checker_profile": (
            "require all records share challenge and receipt_digest; sequence is zero-based contiguous; at_utc is "
            "nondecreasing; first previous_hmac_sha256 is 64 zeroes; every later previous_hmac_sha256 equals prior "
            "hmac_sha256; recompute each HMAC-SHA-256 over ASCII(CLS/GOV01/STATIC-ACQUISITION-LEDGER/v2) || NUL || "
            "uint64be(canonical-base-byte-length) || canonical base JSON excluding hmac_sha256; "
            "ledger_head_hmac_sha256 equals final record hmac_sha256; every repeated tree_sha256 is identical"
        ),
        "semantic_checker_binding": {
            "checker_interface": LEDGER_CHECKER_INTERFACE,
            "artifact_role": "static-executor",
            "repo_relative_path": EXECUTOR_RELATIVE,
            "raw_file_sha256": checker_raw_sha256,
            "byte_length": checker_byte_length,
            "hmac_domain": "CLS/GOV01/STATIC-ACQUISITION-LEDGER/v2",
            "assurance": "content-addressed-runtime-self-attested-not-pre-exec",
        },
        "semantic_validation": {
            "status": "PASS",
            "canonical_raw_bytes": True,
            "same_challenge_and_receipt": True,
            "contiguous_sequence": True,
            "nondecreasing_timestamps": True,
            "previous_hmac_chain": True,
            "every_record_hmac": True,
            "terminal_head_match": True,
            "event_state_machine": "S-or-F1-through-F5",
            "closure_constants": True,
        },
        "record_count": report["record_count"],
        "terminal_kind": report["terminal_kind"],
        "raw_sha256": report["raw_sha256"],
        "raw_bytes": report["raw_bytes"],
        "records": report["records"],
        "ledger_head_hmac_sha256": report["head_hmac_sha256"],
        "failure_retention_contract": {
            "automatic_cleanup_allowed": False,
            "pre_marker_stage": (
                "retain hidden 0700 stage without marker when failure occurs before incomplete marker creation"
            ),
            "marker_present_stage": "retain hidden 0700 stage and exact 0600 incomplete marker",
            "marker_removed_stage": (
                "retain hidden 0755 sealed stage without marker when failure occurs after finalize_stage_marker and "
                "before rename"
            ),
            "published_target": (
                "retain unauthorized published target and require user decision when rename succeeded but final "
                "attestation failed"
            ),
            "unrepresentable_ledger_states": [
                "claim-created-ledger-absent",
                "ledger-partial-or-noncanonical-line",
                "terminal-failure-append-failed",
            ],
        },
    }


def load_envelope(path: str, expected_receipt: Optional[str]) -> Tuple[Dict[str, Any], bytes, str]:
    raw, metadata = read_absolute_regular(path, "ENVELOPE", MAX_JSON_BYTES)
    if metadata.st_uid != os.getuid():
        fail(Exit.CONTRACT, "ENVELOPE_OWNER")
    value = parse_json_bytes(raw, "ENVELOPE")
    if not isinstance(value, dict):
        fail(Exit.CONTRACT, "ENVELOPE_ROOT")
    version = value.get("schema_version")
    domain = RECEIPT_DOMAINS.get(version)
    if domain is None:
        fail(Exit.CONTRACT, "ENVELOPE_VERSION")
    if value.get("artifact_type") != "gov-01-toolchain-acquisition-envelope":
        fail(Exit.CONTRACT, "ENVELOPE_TYPE")
    challenge = value.get("approval_challenge_id")
    if not isinstance(challenge, str) or not CHALLENGE_RE.fullmatch(challenge):
        fail(Exit.CONTRACT, "CHALLENGE_FORMAT")
    if value.get("single_use") is not True:
        fail(Exit.CONTRACT, "SINGLE_USE_REQUIRED")
    expiry = parse_utc(value.get("not_after_utc"), "EXPIRY")
    if utc_now() >= expiry:
        fail(Exit.EXPIRED, "ENVELOPE_EXPIRED")
    digest = hashlib.sha256(domain + b"\x00" + raw).hexdigest()
    if expected_receipt is not None:
        if not isinstance(expected_receipt, str) or not SHA256_RE.fullmatch(expected_receipt):
            fail(Exit.RECEIPT, "RECEIPT_FORMAT")
        if not hmac.compare_digest(digest, expected_receipt):
            fail(Exit.RECEIPT, "RECEIPT_MISMATCH")
    return value, raw, digest


def require_exact_object(value: Any, fields: Iterable[str], label: str) -> Dict[str, Any]:
    expected = frozenset(fields)
    if not isinstance(value, dict) or frozenset(value) != expected:
        fail(Exit.CONTRACT, label + "_FIELDS")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        fail(Exit.CONTRACT, label + "_SHA256")
    return value


def require_zero(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != 0:
        fail(Exit.CONTRACT, label + "_ZERO")


GATE_PASS_EVIDENCE_FIELDS: Dict[str, Tuple[str, ...]] = {
    "G00": (
        "schema_sha256", "schema_bytes", "schema_count", "schema_bundle_receipt_sha256",
        "manual_critical_contract_passed",
    ),
    "G01": ("challenge_claim_created", "ledger_receipt_consumed_recorded", "first_authorized_write_contract"),
    "G02": (
        "authorized_locator_commitment_count", "private_control_identity_commitment",
        "private_locator_public_count", "private_vault_read_count",
    ),
    "G03": (
        "toolchain_role_count", "toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256",
        "assurance", "pre_exec_launcher_attested",
    ),
    "G04": (
        "authorized_subprocess_role_count", "shell_allowed", "network_capable_child_authorized",
        "authorized_network_call_site_invocation_count", "runtime_network_syscall_observation_available",
        "assurance",
    ),
    "G05": ("selected_package_count", "compressed_bytes", "content_receipt_sha256"),
    "G06": ("raw_member_count", "ustar_closure_sha256"),
    "G07": ("parser", "gzip_stream_count", "required_zero_eoa_blocks"),
    "G08": (
        "accepted_member_types", "raw_regular_count", "raw_directory_count", "generated_symlink_count",
        "bundled_node_modules_allowed",
    ),
    "G09": ("compressed_bytes", "payload_bytes", "tar_stream_bytes", "limits_enforced_by_frozen_verifier"),
    "G10": ("protected_control_count", "absent_alternate_control_count"),
    "G11": ("target_absent", "stage_absent"),
    "G12": ("candidate_count", "target_worktree_claude_sessions", "pgrep_sha256", "candidate_lsof_sha256"),
    "G13": ("same_filesystem", "stage_root_mode", "incomplete_marker_present", "stage_entry_write_scope_exact"),
    "G14": ("entry_count", "file_count", "directory_count", "symlink_count", "expected_tree_sha256"),
    "G15": ("profile", "row_count", "required_missing", "allowed_missing", "resolution_receipt_sha256"),
    "G16": ("tree_sha256", "entry_count", "incomplete_marker_excluded_from_tree", "double_stable_fingerprint_required_before_publication"),
    "G17": (
        "authorized_payload_execution_call_site_invocation_count",
        "authorized_lifecycle_execution_call_site_invocation_count",
        "authorized_installed_code_call_site_invocation_count",
        "authorized_node_npm_npx_call_site_invocation_count",
        "runtime_exec_syscall_observation_available", "assurance",
    ),
    "G18": ("publish_syscall", "publish_flag", "publish_attempt_count", "target_parent_fsynced", "overwrite_allowed"),
    "G19": ("protected_control_count", "protected_controls_unchanged", "absent_alternate_control_count"),
    "G20": (
        "public_artifacts_unchanged", "toolchain_unchanged", "git_snapshot_unchanged",
        "cache_closure_unchanged", "protected_controls_unchanged", "stage_path_absent_after_publication",
        "outside_scope_mutation_count", "assurance",
    ),
    "G21": ("tree_sha256", "entry_count", "file_count", "directory_count", "symlink_count", "double_stable_fingerprint_passed"),
    "G22": ("candidate_count", "target_worktree_claude_sessions", "pgrep_sha256", "candidate_lsof_sha256"),
    "G23": (
        "checker_interface", "record_count", "terminal_kind", "ledger_head_hmac_sha256",
        "canonical_jsonl_and_hmac_chain_valid", "private_projection_schema_version",
    ),
    "G24": ("private_locator_public_count", "private_vault_read_count", "raw_command_output_public_count", "projection_preflight_passed"),
}


def validate_gate_evidence(gate_id: str, status: str, evidence: Mapping[str, Any]) -> None:
    """Validate the semantic ABI behind every public gate receipt."""
    if gate_id not in GATE_PASS_EVIDENCE_FIELDS or status not in ("PASS", "FAIL"):
        fail(Exit.EVIDENCE, "GATE_EVIDENCE_GATE")
    if status == "FAIL":
        failed = require_exact_object(
            evidence,
            ("public_code", "detail_code", "public_exit"),
            "GATE_FAILURE_EVIDENCE",
        )
        public_code = failed.get("public_code")
        detail_code = failed.get("detail_code")
        public_exit = failed.get("public_exit")
        if (
            not isinstance(public_code, str)
            or type(public_exit) is not int
            or public_code != public_exit_category(public_exit)
            or not isinstance(detail_code, str)
            or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", detail_code)
        ):
            fail(Exit.EVIDENCE, "GATE_FAILURE_CODE")
        return
    value = require_exact_object(evidence, GATE_PASS_EVIDENCE_FIELDS[gate_id], "GATE_" + gate_id + "_EVIDENCE")

    def exact(expected: Mapping[str, Any]) -> None:
        for name, frozen in expected.items():
            actual = value.get(name)
            if type(actual) is not type(frozen) or actual != frozen:
                fail(Exit.EVIDENCE, "GATE_" + gate_id + "_CONSTANT")

    def digest(name: str) -> None:
        require_sha256(value.get(name), "GATE_" + gate_id + "_" + name.upper())

    def nonnegative(name: str, maximum: int = 2 ** 31 - 1) -> None:
        observed = value.get(name)
        if not isinstance(observed, int) or isinstance(observed, bool) or observed < 0 or observed > maximum:
            fail(Exit.EVIDENCE, "GATE_" + gate_id + "_INTEGER")

    if gate_id == "G00":
        digest("schema_sha256")
        digest("schema_bundle_receipt_sha256")
        nonnegative("schema_bytes", MAX_JSON_BYTES)
        if value.get("schema_bytes", 0) < 1:
            fail(Exit.EVIDENCE, "GATE_G00_SCHEMA_BYTES")
        exact({"schema_count": 3, "manual_critical_contract_passed": True})
    elif gate_id == "G01":
        exact({
            "challenge_claim_created": True,
            "ledger_receipt_consumed_recorded": True,
            "first_authorized_write_contract": "exclusive-0700-challenge-mkdir",
        })
    elif gate_id == "G02":
        digest("private_control_identity_commitment")
        exact({
            "authorized_locator_commitment_count": 5,
            "private_locator_public_count": 0,
            "private_vault_read_count": 0,
        })
    elif gate_id == "G03":
        digest("toolchain_set_receipt_sha256")
        digest("dynamic_closure_receipt_sha256")
        exact({
            "toolchain_role_count": len(TOOLCHAIN_ROLES),
            "assurance": "runtime-self-attested-not-pre-exec",
            "pre_exec_launcher_attested": False,
        })
    elif gate_id == "G04":
        exact({
            "authorized_subprocess_role_count": len(TOOLCHAIN_ROLES[4:]),
            "shell_allowed": False,
            "network_capable_child_authorized": False,
            "authorized_network_call_site_invocation_count": 0,
            "runtime_network_syscall_observation_available": False,
            "assurance": "static-structural-self-attestation-not-syscall-observation",
        })
    elif gate_id == "G05":
        exact({
            "selected_package_count": 167,
            "compressed_bytes": 13_916_529,
            "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
        })
    elif gate_id == "G06":
        exact({
            "raw_member_count": 4117,
            "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
        })
    elif gate_id == "G07":
        exact({"parser": "custom-fixed-512-byte-ustar", "gzip_stream_count": 1, "required_zero_eoa_blocks": 2})
    elif gate_id == "G08":
        exact({
            "accepted_member_types": ["regular-file", "directory"],
            "raw_regular_count": 4099,
            "raw_directory_count": 18,
            "generated_symlink_count": 12,
            "bundled_node_modules_allowed": False,
        })
    elif gate_id == "G09":
        exact({
            "compressed_bytes": 13_916_529,
            "payload_bytes": 55_954_126,
            "tar_stream_bytes": 59_361_280,
            "limits_enforced_by_frozen_verifier": True,
        })
    elif gate_id == "G10":
        exact({"protected_control_count": len(PROTECTED_CONTROL_PATHS), "absent_alternate_control_count": len(ABSENT_CONTROL_PATHS)})
    elif gate_id == "G11":
        exact({"target_absent": True, "stage_absent": True})
    elif gate_id in ("G12", "G22"):
        nonnegative("candidate_count", 1024)
        exact({"target_worktree_claude_sessions": 0})
        digest("pgrep_sha256")
        digest("candidate_lsof_sha256")
    elif gate_id == "G13":
        exact({"same_filesystem": True, "stage_root_mode": "0700", "incomplete_marker_present": True, "stage_entry_write_scope_exact": True})
    elif gate_id == "G14":
        exact({"entry_count": 4665, "file_count": 4099, "directory_count": 554, "symlink_count": 12, "expected_tree_sha256": EXPECTED_TREE_SHA256})
    elif gate_id == "G15":
        exact({
            "profile": "package-lock-path-closure-not-semver-proof",
            "row_count": 256,
            "required_missing": 0,
            "allowed_missing": 10,
            "resolution_receipt_sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
        })
    elif gate_id == "G16":
        exact({"tree_sha256": EXPECTED_TREE_SHA256, "entry_count": 4665, "incomplete_marker_excluded_from_tree": True, "double_stable_fingerprint_required_before_publication": True})
    elif gate_id == "G17":
        exact({
            "authorized_payload_execution_call_site_invocation_count": 0,
            "authorized_lifecycle_execution_call_site_invocation_count": 0,
            "authorized_installed_code_call_site_invocation_count": 0,
            "authorized_node_npm_npx_call_site_invocation_count": 0,
            "runtime_exec_syscall_observation_available": False,
            "assurance": "static-structural-self-attestation-not-syscall-observation",
        })
    elif gate_id == "G18":
        exact({"publish_syscall": "renameatx_np", "publish_flag": "RENAME_EXCL", "publish_attempt_count": 1, "target_parent_fsynced": True, "overwrite_allowed": False})
    elif gate_id == "G19":
        exact({"protected_control_count": len(PROTECTED_CONTROL_PATHS), "protected_controls_unchanged": True, "absent_alternate_control_count": len(ABSENT_CONTROL_PATHS)})
    elif gate_id == "G20":
        exact({
            "public_artifacts_unchanged": True,
            "toolchain_unchanged": True,
            "git_snapshot_unchanged": True,
            "cache_closure_unchanged": True,
            "protected_controls_unchanged": True,
            "stage_path_absent_after_publication": True,
            "outside_scope_mutation_count": 0,
            "assurance": "targeted-content-and-metadata-CAS-not-machine-wide-audit",
        })
    elif gate_id == "G21":
        exact({"tree_sha256": EXPECTED_TREE_SHA256, "entry_count": 4665, "file_count": 4099, "directory_count": 554, "symlink_count": 12, "double_stable_fingerprint_passed": True})
    elif gate_id == "G23":
        digest("ledger_head_hmac_sha256")
        exact({
            "checker_interface": LEDGER_CHECKER_INTERFACE,
            "record_count": 6,
            "terminal_kind": "success",
            "canonical_jsonl_and_hmac_chain_valid": True,
            "private_projection_schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2",
        })
    elif gate_id == "G24":
        exact({"private_locator_public_count": 0, "private_vault_read_count": 0, "raw_command_output_public_count": 0, "projection_preflight_passed": True})


def require_exact_sequence(value: Any, expected: Sequence[Any], label: str) -> None:
    if not isinstance(value, list) or value != list(expected):
        fail(Exit.CONTRACT, label + "_SEQUENCE")


def validate_static_expected_shape(value: Any) -> Dict[str, Any]:
    expected = require_exact_object(value, STATIC_EXPECTED_FIELDS, "STATIC_EXPECTED")
    frozen_scalars = {
        "profile_version": "gov-01-toolchain-static-verifier-v2",
        "package_json_sha256": "bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe",
        "package_lock_sha256": "c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea",
        "lockfile_version": 3,
        "lock_package_count": 176,
        "selected_package_count": 167,
        "excluded_platform_package_count": 9,
        "compressed_bytes": 13_916_529,
        "tar_stream_bytes": 59_361_280,
        "payload_bytes": 55_954_126,
        "raw_member_count": 4117,
        "raw_regular_count": 4099,
        "raw_directory_count": 18,
        "bin_link_count": 12,
        "lifecycle_field_count": 11,
        "content_receipt_body_bytes": 49_665,
        "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
        "ustar_closure_body_bytes": 41_470,
        "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
    }
    for key, frozen in frozen_scalars.items():
        actual = expected.get(key)
        if type(actual) is not type(frozen) or actual != frozen:
            fail(Exit.CONTRACT, "STATIC_EXPECTED_" + key.upper())
    resolution = require_exact_object(
        expected.get("resolution"),
        "row_count body_bytes sha256 required_missing allowed_missing".split(),
        "STATIC_RESOLUTION",
    )
    frozen_resolution = {
        "row_count": 256,
        "body_bytes": 26_629,
        "sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
        "required_missing": 0,
        "allowed_missing": 10,
    }
    for key, frozen in frozen_resolution.items():
        actual = resolution.get(key)
        if type(actual) is not type(frozen) or actual != frozen:
            fail(Exit.CONTRACT, "STATIC_RESOLUTION_" + key.upper())
    tree = require_exact_object(
        expected.get("tree"),
        "entry_count file_count directory_count symlink_count body_bytes sha256".split(),
        "STATIC_TREE",
    )
    frozen_tree = {
        "entry_count": 4665,
        "file_count": 4099,
        "directory_count": 554,
        "symlink_count": 12,
        "body_bytes": 539_842,
        "sha256": EXPECTED_TREE_SHA256,
    }
    for key, frozen in frozen_tree.items():
        actual = tree.get(key)
        if type(actual) is not type(frozen) or actual != frozen:
            fail(Exit.CONTRACT, "STATIC_TREE_" + key.upper())
    return expected


def verify_bound_schema_artifact(repo_fd: int, envelope: Mapping[str, Any]) -> Dict[str, Any]:
    binding = require_exact_object(envelope.get("schema_binding"), SCHEMA_BINDING_FIELDS, "SCHEMA_BINDING")
    if binding.get("schema_id") != SCHEMA_ID or binding.get("schema_artifact_role") != "pending-envelope-schema":
        fail(Exit.CONTRACT, "SCHEMA_BINDING_IDENTITY")
    if (
        binding.get("preapproval_external_validation_required") is not True
        or binding.get("runtime_json_schema_execution_allowed") is not False
        or binding.get("runtime_schema_hash_binding_required") is not True
        or binding.get("runtime_manual_critical_field_checks_required") is not True
        or binding.get("schema_digest_must_equal_artifact_entry") is not True
    ):
        fail(Exit.CONTRACT, "SCHEMA_BINDING_AUTHORITY")
    path = binding.get("schema_artifact_path")
    digest = require_sha256(binding.get("schema_raw_file_sha256"), "SCHEMA_BINDING")
    if not isinstance(path, str):
        fail(Exit.CONTRACT, "SCHEMA_BINDING_PATH")
    validate_relative(path, "SCHEMA_BINDING_PATH")
    if not path.startswith(CONTROL_PREFIX) or not path.endswith(".schema.json"):
        fail(Exit.CONTRACT, "SCHEMA_BINDING_CONTROL_PATH")
    artifacts = envelope.get("artifacts")
    if not isinstance(artifacts, list):
        fail(Exit.CONTRACT, "SCHEMA_ARTIFACTS")
    matches = []
    for entry in artifacts:
        if not isinstance(entry, dict):
            fail(Exit.CONTRACT, "SCHEMA_ARTIFACT_ENTRY")
        if entry.get("path") == path:
            matches.append(entry)
    if len(matches) != 1:
        fail(Exit.CONTRACT, "SCHEMA_ARTIFACT_UNIQUE")
    artifact = matches[0]
    if (
        artifact.get("role") != "pending-envelope-schema"
        or artifact.get("file_kind") != "regular"
        or artifact.get("raw_file_sha256") != digest
    ):
        fail(Exit.CONTRACT, "SCHEMA_ARTIFACT_BINDING")
    length = artifact.get("byte_length")
    if not isinstance(length, int) or isinstance(length, bool) or length <= 0 or length > MAX_JSON_BYTES:
        fail(Exit.CONTRACT, "SCHEMA_ARTIFACT_LENGTH")
    fd, _ = open_relative_regular(repo_fd, path, "BOUND_SCHEMA", length)
    try:
        raw = read_fd(fd, length, "BOUND_SCHEMA")
    finally:
        os.close(fd)
    if len(raw) != length or not hmac.compare_digest(sha256(raw), digest):
        fail(Exit.CHECKER_DRIFT, "BOUND_SCHEMA_DRIFT")
    schema = parse_json_bytes(raw, "BOUND_SCHEMA")
    if not isinstance(schema, dict):
        fail(Exit.CONTRACT, "BOUND_SCHEMA_ROOT")
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("$id") != SCHEMA_ID
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
    ):
        fail(Exit.CONTRACT, "BOUND_SCHEMA_PROFILE")
    if frozenset(schema.get("required") or []) != TOP_LEVEL_FIELDS:
        fail(Exit.CONTRACT, "BOUND_SCHEMA_REQUIRED")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or frozenset(properties) != TOP_LEVEL_FIELDS:
        fail(Exit.CONTRACT, "BOUND_SCHEMA_PROPERTIES")
    return {"path": path, "sha256": digest, "bytes": length}


def verify_projection_schema_bundle(
    repo_fd: int,
    artifacts: Sequence[Mapping[str, Any]],
    pending_observation: Mapping[str, Any],
) -> Dict[str, Any]:
    profiles = {
        "private-evidence-schema": (
            PRIVATE_SCHEMA_ID,
            frozenset(
                "schema_version artifact_type classification projection_kind ledger_parse_state "
                "canonical_record_profile semantic_checker_profile semantic_checker_binding semantic_validation "
                "record_count terminal_kind raw_sha256 raw_bytes records ledger_head_hmac_sha256 "
                "failure_retention_contract".split()
            ),
        ),
        "public-attestation-schema": (
            PUBLIC_SCHEMA_ID,
            frozenset(
                "schema_version artifact_type ok mode phase state terminal_state runtime_assurance gate_results "
                "authority".split()
            ),
        ),
    }
    rows = [
        {
            "role": "pending-envelope-schema",
            "sha256": pending_observation.get("sha256"),
            "bytes": pending_observation.get("bytes"),
        }
    ]
    for role, (expected_id, expected_required) in profiles.items():
        matches = [entry for entry in artifacts if entry.get("role") == role]
        if len(matches) != 1:
            fail(Exit.CONTRACT, "PROJECTION_SCHEMA_ROLE")
        artifact = matches[0]
        path = artifact.get("path")
        digest = artifact.get("sha256")
        length = artifact.get("bytes")
        if not isinstance(path, str) or not path.startswith(CONTROL_PREFIX) or not path.endswith(".schema.json"):
            fail(Exit.CONTRACT, "PROJECTION_SCHEMA_PATH")
        require_sha256(digest, "PROJECTION_SCHEMA")
        if not isinstance(length, int) or isinstance(length, bool) or length <= 0 or length > MAX_JSON_BYTES:
            fail(Exit.CONTRACT, "PROJECTION_SCHEMA_BYTES")
        fd, _ = open_relative_regular(repo_fd, path, "PROJECTION_SCHEMA", length)
        try:
            raw = read_fd(fd, length, "PROJECTION_SCHEMA")
        finally:
            os.close(fd)
        if len(raw) != length or not hmac.compare_digest(sha256(raw), digest):
            fail(Exit.CHECKER_DRIFT, "PROJECTION_SCHEMA_REOPEN_DRIFT")
        schema = parse_json_bytes(raw, "PROJECTION_SCHEMA")
        if (
            not isinstance(schema, dict)
            or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("$id") != expected_id
            or schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
            or frozenset(schema.get("required") or []) != expected_required
        ):
            fail(Exit.CONTRACT, "PROJECTION_SCHEMA_PROFILE")
        rows.append({"role": role, "sha256": digest, "bytes": length})
    body = canonical_json(sorted(rows, key=lambda row: row["role"]))
    return {
        "schema_count": 3,
        "schema_bundle_receipt_sha256": sha256(b"CLS/GOV01/SCHEMA-BUNDLE/v2\x00" + body),
    }


def validate_manual_envelope_contract(envelope: Mapping[str, Any]) -> None:
    require_exact_object(envelope, TOP_LEVEL_FIELDS, "ENVELOPE")
    if envelope.get("schema_version") != "gov-01-toolchain-static-acquisition-envelope-v2":
        fail(Exit.CONTRACT, "MANUAL_SCHEMA_VERSION")
    if envelope.get("artifact_type") != "gov-01-toolchain-acquisition-envelope":
        fail(Exit.CONTRACT, "MANUAL_ARTIFACT_TYPE")
    if envelope.get("plan_id") != "PLAN-CLS-PRODUCTIVITY-2026-08-20":
        fail(Exit.CONTRACT, "MANUAL_PLAN_ID")
    if envelope.get("state") != "pending-user-confirmation" or envelope.get("single_use") is not True:
        fail(Exit.CONTRACT, "MANUAL_STATE")
    if not isinstance(envelope.get("artifact_id"), str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}", envelope["artifact_id"]
    ):
        fail(Exit.CONTRACT, "MANUAL_ARTIFACT_ID")
    challenge = envelope.get("approval_challenge_id")
    if not isinstance(challenge, str) or not CHALLENGE_RE.fullmatch(challenge):
        fail(Exit.CONTRACT, "MANUAL_CHALLENGE")
    census_at = parse_utc(envelope.get("census_at_utc"), "CENSUS_AT")
    expiry = parse_utc(envelope.get("not_after_utc"), "EXPIRY")
    if census_at > expiry:
        fail(Exit.CONTRACT, "CENSUS_AFTER_EXPIRY")
    approval = require_exact_object(
        envelope.get("approval_receipt_contract"),
        "required_user_reference receipt_must_match_raw_envelope_bytes challenge_must_match "
        "receipt_before_any_authorized_write first_authorized_write authority_is_exact authority_expansion_allowed".split(),
        "APPROVAL_RECEIPT_CONTRACT",
    )
    for key in (
        "receipt_must_match_raw_envelope_bytes",
        "challenge_must_match",
        "receipt_before_any_authorized_write",
        "authority_is_exact",
    ):
        if approval.get(key) is not True:
            fail(Exit.CONTRACT, "APPROVAL_RECEIPT_AUTHORITY")
    if approval.get("authority_expansion_allowed") is not False:
        fail(Exit.CONTRACT, "APPROVAL_EXPANSION")
    predecessor = require_exact_object(
        envelope.get("predecessor"),
        "first_approval_envelope_raw_sha256 first_receipt_domain_sha256 bootstrap_patch_raw_sha256 "
        "bootstrap_target_receipt_sha256 bootstrap_containment_state predecessor_chain_receipt_sha256".split(),
        "PREDECESSOR",
    )
    for key, value in predecessor.items():
        if key.endswith("sha256"):
            require_sha256(value, "PREDECESSOR_" + key.upper())
    if predecessor.get("bootstrap_containment_state") != "independently-verified-pass":
        fail(Exit.CONTRACT, "PREDECESSOR_STATE")
    artifacts = envelope.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) < 10 or len(artifacts) > 64:
        fail(Exit.CONTRACT, "MANUAL_ARTIFACT_COUNT")
    seen_paths = set()
    role_counts: Dict[str, int] = {}
    allowed_roles = {
        "goal", "governance-decision", "approval-predecessor", "bootstrap-patch", "static-executor",
        "static-verifier", "pending-envelope-schema", "private-evidence-schema", "public-attestation-schema",
        "package-manifest", "package-lock", "gitignore", "receipt-profile", "other-public-governance-artifact",
    }
    for entry in artifacts:
        artifact = require_exact_object(entry, "path role file_kind byte_length raw_file_sha256".split(), "ARTIFACT")
        path = artifact.get("path")
        if not isinstance(path, str):
            fail(Exit.CONTRACT, "ARTIFACT_PATH")
        validate_relative(path, "ARTIFACT_PATH")
        if path in seen_paths:
            fail(Exit.CONTRACT, "ARTIFACT_DUPLICATE_PATH")
        seen_paths.add(path)
        role = artifact.get("role")
        if role not in allowed_roles or artifact.get("file_kind") != "regular":
            fail(Exit.CONTRACT, "ARTIFACT_PROFILE")
        size = artifact.get("byte_length")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            fail(Exit.CONTRACT, "ARTIFACT_SIZE")
        require_sha256(artifact.get("raw_file_sha256"), "ARTIFACT")
        role_counts[role] = role_counts.get(role, 0) + 1
    for role in (
        "goal", "governance-decision", "static-executor", "static-verifier", "pending-envelope-schema",
        "private-evidence-schema", "public-attestation-schema", "package-manifest", "package-lock", "gitignore",
    ):
        if role_counts.get(role) != 1:
            fail(Exit.CONTRACT, "ARTIFACT_REQUIRED_ROLE")
    exact_role_paths = {
        "static-executor": EXECUTOR_RELATIVE,
        "static-verifier": VERIFIER_RELATIVE,
        "package-manifest": "package.json",
        "package-lock": "package-lock.json",
        "gitignore": ".gitignore",
    }
    for role, expected_path in exact_role_paths.items():
        matching_paths = [entry.get("path") for entry in artifacts if entry.get("role") == role]
        if matching_paths != [expected_path]:
            fail(Exit.CONTRACT, "ARTIFACT_ROLE_PATH_BINDING")
    preimage = require_exact_object(
        envelope.get("authorization_preimage"), AUTHORIZATION_PREIMAGE_FIELDS, "AUTHORIZATION_PREIMAGE"
    )
    object_format = preimage.get("git_object_format")
    if object_format not in ("sha1", "sha256"):
        fail(Exit.CONTRACT, "PREIMAGE_OBJECT_FORMAT")
    oid_length = 40 if object_format == "sha1" else 64
    for key in ("head_commit_oid", "head_tree_oid"):
        value = preimage.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{%d}" % oid_length, value):
            fail(Exit.CONTRACT, "PREIMAGE_OID")
    for key in (
        "git_snapshot_commitment",
        "private_preapproval_commitment",
        "public_repo_artifact_set_receipt_sha256",
    ):
        require_sha256(preimage.get(key), "PREIMAGE_" + key.upper())
    require_exact_sequence(preimage.get("protected_existing_control_paths"), PROTECTED_CONTROL_PATHS, "PROTECTED")
    require_exact_sequence(preimage.get("absent_control_paths"), ABSENT_CONTROL_PATHS, "ABSENT")
    if preimage.get("target_preimage") != "ABSENT" or preimage.get("node_modules_state") != "ABSENT":
        fail(Exit.CONTRACT, "PREIMAGE_TARGET")
    for key in ("target_worktree_claude_sessions", "forbidden_process_match_count"):
        require_zero(preimage.get(key), "PREIMAGE_" + key.upper())
    for key in ("node_modules_parent_or_sibling_reuse_allowed", "private_vault_census_allowed"):
        if preimage.get(key) is not False:
            fail(Exit.CONTRACT, "PREIMAGE_AUTHORITY")
    frozen = require_exact_object(
        envelope.get("frozen_toolchain"),
        "platform architecture entries dynamic_closure_receipt_sha256 toolchain_set_receipt_profile "
        "toolchain_set_receipt_sha256 private_locator_policy recompute_before_first_non_ledger_acquisition_write "
        "drift_action".split(),
        "FROZEN_TOOLCHAIN",
    )
    if frozen.get("platform") != EXPECTED_PLATFORM or frozen.get("architecture") != EXPECTED_ARCH:
        fail(Exit.CONTRACT, "FROZEN_TOOLCHAIN_HOST")
    entries = frozen.get("entries")
    if not isinstance(entries, list) or len(entries) != len(TOOLCHAIN_ROLES):
        fail(Exit.CONTRACT, "FROZEN_TOOLCHAIN_ENTRIES")
    for index, role in enumerate(TOOLCHAIN_ROLES):
        entry = require_exact_object(
            entries[index],
            "role logical_id artifact_kind version digest_profile raw_digest_sha256 private_locator_omitted "
            "execution_authority".split(),
            "FROZEN_TOOL",
        )
        if entry.get("role") != role or entry.get("private_locator_omitted") is not True:
            fail(Exit.CONTRACT, "FROZEN_TOOL_ROLE")
        expected_kind, expected_digest_profile, expected_authority = TOOLCHAIN_ROLE_PROFILE[role]
        if (
            entry.get("artifact_kind") != expected_kind
            or entry.get("digest_profile") != expected_digest_profile
            or entry.get("execution_authority") != expected_authority
        ):
            fail(Exit.CONTRACT, "FROZEN_TOOL_PROFILE")
        for key in ("logical_id", "version"):
            value = entry.get(key)
            if (
                not isinstance(value, str)
                or not value
                or len(value) > 128
                or any(unicodedata.category(character) == "Cc" for character in value)
            ):
                fail(Exit.CONTRACT, "FROZEN_TOOL_IDENTITY")
        require_sha256(entry.get("raw_digest_sha256"), "FROZEN_TOOL")
    require_sha256(frozen.get("dynamic_closure_receipt_sha256"), "DYNAMIC_CLOSURE")
    require_sha256(frozen.get("toolchain_set_receipt_sha256"), "TOOLCHAIN_SET")
    if frozen.get("recompute_before_first_non_ledger_acquisition_write") is not True:
        fail(Exit.CONTRACT, "TOOLCHAIN_RECOMPUTE")
    binding = require_exact_object(envelope.get("schema_binding"), SCHEMA_BINDING_FIELDS, "SCHEMA_BINDING")
    if binding.get("schema_id") != SCHEMA_ID:
        fail(Exit.CONTRACT, "SCHEMA_BINDING_ID")
    static_contract = require_exact_object(
        envelope.get("static_acquisition_contract"), STATIC_CONTRACT_FIELDS, "STATIC_CONTRACT"
    )
    validate_static_expected_shape(static_contract.get("expected"))
    require_exact_sequence(static_contract.get("protected_control_paths"), PROTECTED_CONTROL_PATHS, "STATIC_PROTECTED")
    require_exact_sequence(static_contract.get("absent_control_paths"), ABSENT_CONTROL_PATHS, "STATIC_ABSENT")
    for key in (
        "compressed_blobs_memory_resident_before_write",
        "payload_bytes_memory_resident_before_write",
        "protected_control_pre_post_hash_check_required",
        "absent_control_pre_post_lstat_check_required",
    ):
        if static_contract.get(key) is not True:
            fail(Exit.CONTRACT, "STATIC_REQUIRED_GATE")
    for key in (
        "hidden_package_lock_generation_allowed", "node_execution_allowed", "npm_execution_allowed",
        "openspec_execution_allowed", "openspec_scaffold_allowed", "lifecycle_execution_allowed", "network_allowed",
    ):
        if static_contract.get(key) is not False:
            fail(Exit.CONTRACT, "STATIC_FORBIDDEN_AUTHORITY")
    lock_closure = require_exact_object(envelope.get("lock_closure"), LOCK_CLOSURE_FIELDS, "LOCK_CLOSURE")
    if lock_closure.get("host_selected_package_count") != EXPECTED_SELECTED_PACKAGES:
        fail(Exit.CONTRACT, "LOCK_PACKAGE_COUNT")
    if lock_closure.get("host_bin_link_count") != EXPECTED_BIN_LINKS or lock_closure.get("network_fetch_allowed") is not False:
        fail(Exit.CONTRACT, "LOCK_AUTHORITY")
    for key in (
        "content_receipt_sha256", "ustar_closure_sha256", "resolution_receipt_sha256", "expected_tree_sha256"
    ):
        require_sha256(lock_closure.get(key), "LOCK_" + key.upper())
    resource_limits = require_exact_object(
        lock_closure.get("resource_limits"),
        "selected_archive_count compressed_closure_bytes_max tar_stream_bytes_per_archive_max "
        "member_count_per_archive_max final_path_utf8_bytes_max single_file_bytes_max "
        "payload_closure_bytes_max required_raw_regular_count required_bin_link_count".split(),
        "LOCK_RESOURCE_LIMITS",
    )
    required_limits = {
        "selected_archive_count": EXPECTED_SELECTED_PACKAGES,
        "compressed_closure_bytes_max": MAX_COMPRESSED_CLOSURE,
        "tar_stream_bytes_per_archive_max": 24_000_000,
        "member_count_per_archive_max": 5_000,
        "final_path_utf8_bytes_max": 128,
        "single_file_bytes_max": 15_000_000,
        "payload_closure_bytes_max": MAX_PAYLOAD_CLOSURE,
        "required_raw_regular_count": 4099,
        "required_bin_link_count": EXPECTED_BIN_LINKS,
    }
    if resource_limits != required_limits:
        fail(Exit.CONTRACT, "LOCK_RESOURCE_LIMIT_VALUES")
    execution = require_exact_object(envelope.get("execution_plan"), EXECUTION_PLAN_FIELDS, "EXECUTION_PLAN")
    if execution.get("executor_interface_version") != SCRIPT_VERSION:
        fail(Exit.CONTRACT, "EXECUTOR_INTERFACE_VERSION")
    if execution.get("launcher_executable_role") != "python-interpreter":
        fail(Exit.CONTRACT, "LAUNCHER_ROLE")
    if execution.get("allowed_subprocess_executable_roles") != list(TOOLCHAIN_ROLES[4:]):
        fail(Exit.CONTRACT, "SUBPROCESS_ROLES")
    executor_template = execution.get("executor_argv_template")
    verifier_census_template = execution.get("verifier_census_argv_template")
    verifier_installed_template = execution.get("verifier_installed_argv_template")
    for template in (executor_template, verifier_census_template, verifier_installed_template):
        if not isinstance(template, list) or template[:4] != ["{BOUND_PYTHON_PRIVATE}", "-I", "-S", "-B"]:
            fail(Exit.CONTRACT, "PYTHON_LAUNCH_FLAGS")
    if (
        len(executor_template) < 6
        or executor_template[4] != "{REPO_ROOT_PRIVATE}/" + EXECUTOR_RELATIVE
        or executor_template[5] != "acquire"
    ):
        fail(Exit.CONTRACT, "EXECUTOR_ARGV_TEMPLATE")
    if (
        execution.get("shell_allowed") is not False
        or execution.get("subprocess_from_executor_allowed") is not True
        or execution.get("archive_or_payload_execution_allowed") is not False
        or execution.get("network_allowed") is not False
        or execution.get("stop_after_static_attestation") is not True
    ):
        fail(Exit.CONTRACT, "EXECUTION_AUTHORITY")
    mutation = require_exact_object(
        envelope.get("mutation_scope"),
        "allowed_persistent_mutations allowed_ephemeral_mutations target_preimage publish_syscall publish_flag "
        "publish_attempt_ceiling overwrite_allowed forbidden_mutations".split(),
        "MUTATION_SCOPE",
    )
    if (
        mutation.get("target_preimage") != "ABSENT"
        or mutation.get("publish_syscall") != "renameatx_np"
        or mutation.get("publish_flag") != "RENAME_EXCL"
        or mutation.get("publish_attempt_ceiling") != 1
        or mutation.get("overwrite_allowed") is not False
    ):
        fail(Exit.CONTRACT, "MUTATION_CEILING")
    failure = require_exact_object(
        envelope.get("failure_contract"),
        "failure_action challenge_state retry_allowed public_success_attestation_allowed existing_target_action "
        "failed_stage_action evidence_action new_authority_required".split(),
        "FAILURE_CONTRACT",
    )
    if failure.get("retry_allowed") is not False or failure.get("public_success_attestation_allowed") is not False:
        fail(Exit.CONTRACT, "FAILURE_AUTHORITY")
    success = require_exact_object(
        envelope.get("success_contract"),
        "host_package_count maximum_state target_created_count target_tree_must_equal_expected_merkle "
        "missing_expected_entries unexpected_entries content_mismatches forbidden_control_paths_present "
        "protected_control_paths_changed outside_scope_mutation_count network_attempt_count "
        "npm_node_npx_execution_count javascript_execution_count lifecycle_execution_count "
        "archive_member_execution_count sandbox_exec_execution_count payload_execution_allowed_after_success "
        "governance_apply_allowed commit_allowed push_allowed next_required_authorization".split(),
        "SUCCESS_CONTRACT",
    )
    if success.get("host_package_count") != EXPECTED_SELECTED_PACKAGES or success.get("target_created_count") != 1:
        fail(Exit.CONTRACT, "SUCCESS_COUNT")
    for key in (
        "missing_expected_entries", "unexpected_entries", "content_mismatches", "forbidden_control_paths_present",
        "protected_control_paths_changed", "outside_scope_mutation_count", "network_attempt_count",
        "npm_node_npx_execution_count", "javascript_execution_count", "lifecycle_execution_count",
        "archive_member_execution_count", "sandbox_exec_execution_count",
    ):
        require_zero(success.get(key), "SUCCESS_" + key.upper())
    for key in (
        "payload_execution_allowed_after_success", "governance_apply_allowed", "commit_allowed", "push_allowed"
    ):
        if success.get(key) is not False:
            fail(Exit.CONTRACT, "SUCCESS_AUTHORITY")
    private = require_exact_object(
        envelope.get("private_state_authorization"),
        "private_read_authority private_write_authority locator_commitment_profile hmac_key_id_profile hmac_key_id "
        "authorized_locator_commitments private_control_identity_commitment_profile "
        "private_control_identity_commitment all_cli_locators_compared_before_any_write claims_container_preimage "
        "challenge_claim_preimage first_authorized_write persistent_single_use_ledger_required "
        "private_evidence_schema_required private_file_modes private_preimage_checks public_serialization_forbidden "
        "private_vault_authorized retention destruction_authorized".split(),
        "PRIVATE_STATE_AUTHORIZATION",
    )
    require_sha256(private.get("hmac_key_id"), "HMAC_KEY_ID")
    require_sha256(private.get("private_control_identity_commitment"), "PRIVATE_CONTROL_IDENTITY")
    if private.get("private_control_identity_commitment_profile") != (
        "HMAC-SHA-256 with the authorized 32-byte private key over "
        "ASCII(CLS/GOV01/PRIVATE-CONTROL-IDENTITY/v2) || NUL || uint64be(canonical-body-byte-length) || "
        "UTF-8-NFC-LF canonical JSON binding the receipt-approved owner UID, inherited control GID, exact "
        "state-root/claims/key modes and expected claim/ledger modes without serializing private locators"
    ):
        fail(Exit.CONTRACT, "PRIVATE_CONTROL_IDENTITY_PROFILE")
    locator_values = require_exact_object(
        private.get("authorized_locator_commitments"),
        "repo_root cache_root state_root key_file envelope".split(),
        "AUTHORIZED_LOCATORS",
    )
    locator_labels = {
        "repo_root": "repo-root", "cache_root": "npm-cache", "state_root": "state-root",
        "key_file": "hmac-key", "envelope": "envelope",
    }
    for key, label in locator_labels.items():
        entry = require_exact_object(locator_values.get(key), "label commitment".split(), "AUTHORIZED_LOCATOR")
        if entry.get("label") != label:
            fail(Exit.CONTRACT, "AUTHORIZED_LOCATOR_LABEL")
        require_sha256(entry.get("commitment"), "AUTHORIZED_LOCATOR")
    if (
        private.get("all_cli_locators_compared_before_any_write") is not True
        or private.get("persistent_single_use_ledger_required") is not True
        or private.get("private_vault_authorized") is not False
        or private.get("destruction_authorized") is not False
        or private.get("private_file_modes") != {"directory": "0700", "file": "0600", "umask": "0077"}
    ):
        fail(Exit.CONTRACT, "PRIVATE_AUTHORITY")
    if (
        private.get("claims_container_preimage")
        != "state-root/claims already exists as a receipt-bound-owner-and-group real 0700 directory and is not created by this attempt"
        or private.get("challenge_claim_preimage")
        != "exact state-root/claims/<approval_challenge_id> direct child ABSENT"
        or private.get("first_authorized_write")
        != "mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700; EEXIST is terminal replay; no earlier mkdir, claim, ledger, stage, target or other write"
    ):
        fail(Exit.CONTRACT, "PRIVATE_FIRST_WRITE_CONTRACT")
    privacy = require_exact_object(
        envelope.get("privacy"),
        "public_raw_sha256_allowed_for private_raw_sha256_only_for private_locator_public_count "
        "private_vault_read_count graphiti_call_count network_call_count".split(),
        "PRIVACY",
    )
    for key in ("private_locator_public_count", "private_vault_read_count", "graphiti_call_count", "network_call_count"):
        require_zero(privacy.get(key), "PRIVACY_" + key.upper())


def verify_artifacts(repo_fd: int, envelope: Mapping[str, Any]) -> List[Dict[str, Any]]:
    artifacts = envelope.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        fail(Exit.CONTRACT, "ARTIFACTS_SCHEMA")
    seen = set()
    result: List[Dict[str, Any]] = []
    for entry in artifacts:
        if not isinstance(entry, dict):
            fail(Exit.CONTRACT, "ARTIFACT_SCHEMA")
        path = entry.get("path")
        expected_hash = entry.get("raw_file_sha256")
        expected_size = entry.get("byte_length")
        if not isinstance(path, str) or path in seen:
            fail(Exit.CONTRACT, "ARTIFACT_PATH")
        seen.add(path)
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            fail(Exit.CONTRACT, "ARTIFACT_HASH")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            fail(Exit.CONTRACT, "ARTIFACT_SIZE")
        fd, metadata = open_relative_regular(repo_fd, path, "ARTIFACT", max(MAX_JSON_BYTES, expected_size))
        try:
            actual_hash, actual_size = hash_fd(fd, "sha256", max(MAX_JSON_BYTES, expected_size), "ARTIFACT")
        finally:
            os.close(fd)
        if actual_size != expected_size or not hmac.compare_digest(actual_hash, expected_hash):
            fail(Exit.PREFLIGHT_DRIFT, "ARTIFACT_DRIFT")
        result.append(
            {
                "path": path,
                "role": entry.get("role"),
                "sha256": actual_hash,
                "bytes": actual_size,
                "device": metadata.st_dev,
                "inode": metadata.st_ino,
            }
        )
    return result


def load_bound_verifier(repo_fd: int, artifacts: Sequence[Mapping[str, Any]]) -> types.ModuleType:
    matches = [entry for entry in artifacts if entry.get("path") == VERIFIER_RELATIVE]
    if len(matches) != 1:
        fail(Exit.CONTRACT, "VERIFIER_ARTIFACT_BINDING")
    frozen = matches[0]
    if frozen.get("role") not in ("static-verifier", "acquisition-verifier"):
        fail(Exit.CONTRACT, "VERIFIER_ARTIFACT_ROLE")
    expected_size = frozen.get("bytes")
    expected_hash = frozen.get("sha256")
    if not isinstance(expected_size, int) or not isinstance(expected_hash, str):
        fail(Exit.CONTRACT, "VERIFIER_ARTIFACT_SCHEMA")
    fd, _ = open_relative_regular(repo_fd, VERIFIER_RELATIVE, "BOUND_VERIFIER", expected_size)
    try:
        raw = read_fd(fd, expected_size, "BOUND_VERIFIER")
    finally:
        os.close(fd)
    if len(raw) != expected_size or not hmac.compare_digest(sha256(raw), expected_hash):
        fail(Exit.CHECKER_DRIFT, "VERIFIER_REOPEN_DRIFT")
    namespace = types.ModuleType("_gov01_content_addressed_static_verifier_v2")
    namespace.__file__ = "<gov01-content-addressed-verifier-v2>"
    namespace.__package__ = None
    try:
        code = compile(raw, namespace.__file__, "exec", dont_inherit=True, optimize=0)
        exec(code, namespace.__dict__)
    except Exception:
        fail(Exit.CHECKER_DRIFT, "VERIFIER_LOAD")
    if getattr(namespace, "PROFILE_VERSION", None) != "gov-01-toolchain-static-verifier-v2":
        fail(Exit.CHECKER_DRIFT, "VERIFIER_PROFILE")
    if getattr(namespace, "FINGERPRINT_TREE_FD_ABI", None) != "returns-layout-and-volatile-xattr-count-v2":
        fail(Exit.CHECKER_DRIFT, "VERIFIER_FINGERPRINT_ABI")
    for name in ("build_expected", "fingerprint_tree_fd", "layout_manifest", "public_summary"):
        if not callable(getattr(namespace, name, None)):
            fail(Exit.CHECKER_DRIFT, "VERIFIER_API")
    return namespace


def validate_static_contract(
    envelope: Mapping[str, Any],
    verifier: types.ModuleType,
    expected: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
    strict_expected: bool = True,
) -> str:
    if envelope.get("schema_version") != "gov-01-toolchain-static-acquisition-envelope-v2":
        fail(Exit.CONTRACT, "STATIC_ENVELOPE_VERSION")
    contract = envelope.get("static_acquisition_contract")
    if not isinstance(contract, dict):
        fail(Exit.CONTRACT, "STATIC_CONTRACT_SCHEMA")
    challenge = envelope.get("approval_challenge_id")
    exact_stage = ".gov01-toolchain-stage-" + str(challenge)
    validate_relative(exact_stage, "STATIC_STAGE")
    if "/" in exact_stage or not exact_stage.startswith("."):
        fail(Exit.CONTRACT, "STATIC_STAGE_SHAPE")
    verifier_entries = [entry for entry in artifacts if entry.get("path") == VERIFIER_RELATIVE]
    executor_entries = [entry for entry in artifacts if entry.get("path") == EXECUTOR_RELATIVE]
    if len(verifier_entries) != 1:
        fail(Exit.CONTRACT, "VERIFIER_ARTIFACT_BINDING")
    if len(executor_entries) != 1 or executor_entries[0].get("role") not in ("static-executor", "acquisition-executor"):
        fail(Exit.CONTRACT, "EXECUTOR_ARTIFACT_BINDING")
    expected_public = verifier.public_summary(expected)
    required = {
        "verifier_profile_version": "gov-01-toolchain-static-verifier-v2",
        "verifier_artifact_path": VERIFIER_RELATIVE,
        "verifier_sha256": verifier_entries[0].get("sha256"),
        "executor_artifact_path": EXECUTOR_RELATIVE,
        "executor_sha256": executor_entries[0].get("sha256"),
        "stage_repo_relative": exact_stage,
        "target_repo_relative": TARGET_NAME,
        "compressed_blobs_memory_resident_before_write": True,
        "payload_bytes_memory_resident_before_write": True,
        "hidden_package_lock_generation_allowed": False,
        "expected": expected_public,
    }
    for key, value in required.items():
        if key == "expected" and not strict_expected:
            continue
        if contract.get(key) != value:
            fail(Exit.RECEIPT, "STATIC_CONTRACT_MISMATCH")
    if expected_public.get("selected_package_count") != EXPECTED_SELECTED_PACKAGES:
        fail(Exit.CACHE_LOCK, "STATIC_PACKAGE_COUNT")
    if expected_public.get("bin_link_count") != EXPECTED_BIN_LINKS:
        fail(Exit.CACHE_LOCK, "STATIC_BIN_COUNT")
    if expected_public.get("raw_regular_count") != 4099:
        fail(Exit.ARCHIVE, "STATIC_FILE_COUNT")
    if expected_public.get("payload_bytes", 0) > MAX_PAYLOAD_CLOSURE:
        fail(Exit.ARCHIVE, "STATIC_PAYLOAD_BOUND")
    if expected_public.get("compressed_bytes", 0) > MAX_COMPRESSED_CLOSURE:
        fail(Exit.CACHE_LOCK, "STATIC_COMPRESSED_BOUND")
    top_execution_plan = envelope.get("execution_plan")
    if not isinstance(top_execution_plan, dict):
        fail(Exit.CONTRACT, "EXECUTION_PLAN_SCHEMA")
    # The v2 envelope must bind these directly in the static contract regardless
    # of where a human-readable policy projection is placed.
    for flag in (
        "node_execution_allowed",
        "npm_execution_allowed",
        "openspec_execution_allowed",
        "openspec_scaffold_allowed",
        "lifecycle_execution_allowed",
        "network_allowed",
    ):
        if contract.get(flag) is not False:
            fail(Exit.CONTRACT, "STATIC_EXECUTION_AUTHORITY")
    return exact_stage


def run_process(
    argv: Sequence[str],
    env: Mapping[str, str],
    max_output: int,
    label: str,
    allowed_returncodes: Sequence[int] = (0,),
) -> bytes:
    if not argv or not isinstance(argv[0], str) or not os.path.isabs(argv[0]):
        fail(Exit.TRACE, "PROCESS_EXECUTABLE")
    executable = os.path.normpath(argv[0])
    expected_executable_hash = _AUTHORIZED_EXECUTABLE_HASHES.get(executable)
    if expected_executable_hash is None:
        fail(Exit.TRACE, "PROCESS_NOT_AUTHORIZED")
    actual_executable_hash = hash_regular_absolute(executable, "PROCESS_EXECUTABLE", MAX_CACHE_OBJECT_BYTES)["sha256"]
    if not hmac.compare_digest(actual_executable_hash, expected_executable_hash):
        fail(Exit.TRACE, "PROCESS_EXECUTABLE_DRIFT")
    if not set(env).issubset(ALLOWED_CHILD_ENV_NAMES):
        fail(Exit.TRACE, "PROCESS_ENVIRONMENT")
    try:
        completed = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=dict(env),
            close_fds=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        fail(Exit.PREFLIGHT_DRIFT, label + "_EXEC")
    if completed.returncode not in allowed_returncodes or len(completed.stdout) > max_output:
        fail(Exit.PREFLIGHT_DRIFT, label + "_RESULT")
    return completed.stdout


def git_env() -> Dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": "/var/empty",
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_ALLOW_PROTOCOL": "",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM": "0",
    }


def resolve_clt_git(expected_git_hash: Optional[str]) -> Tuple[str, str]:
    environment = git_env()
    developer_raw = run_process(["/usr/bin/xcode-select", "-p"], environment, 4096, "XCODE_SELECT")
    binary_raw = run_process(["/usr/bin/xcrun", "--find", "git"], environment, 4096, "XCRUN_GIT")
    try:
        developer = developer_raw.rstrip(b"\n").decode("utf-8", "strict")
        binary = binary_raw.rstrip(b"\n").decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_ENCODING")
    if developer_raw.count(b"\n") != 1 or binary_raw.count(b"\n") != 1:
        fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_FORMAT")
    assert_absolute(developer, "CLT_DEVELOPER")
    assert_absolute(binary, "CLT_GIT")
    try:
        if os.path.commonpath([developer, binary]) != developer:
            fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_OUTSIDE_DEVELOPER")
    except ValueError:
        fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_OUTSIDE_DEVELOPER")
    metadata = assert_no_symlink_components(binary, "CLT_GIT")
    if not stat.S_ISREG(metadata.st_mode) or not (metadata.st_mode & stat.S_IXUSR):
        fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_TYPE")
    actual_hash = hash_regular_absolute(binary, "CLT_GIT", MAX_CACHE_OBJECT_BYTES)["sha256"]
    if expected_git_hash is not None and not hmac.compare_digest(actual_hash, expected_git_hash):
        fail(Exit.PREFLIGHT_DRIFT, "CLT_GIT_HASH")
    _AUTHORIZED_EXECUTABLE_HASHES[binary] = actual_hash
    return binary, actual_hash


def run_git(
    git_binary: str,
    repo_root: str,
    arguments: Sequence[str],
    label: str,
    enumerates_worktree: bool = False,
    authorized_excludes: Sequence[str] = (),
    allowed_returncodes: Sequence[int] = (0,),
) -> bytes:
    args = list(arguments)
    if enumerates_worktree:
        args.extend(["--", ".", ":(exclude)canvas-vault", ":(exclude)canvas-vault/**"])
        for excluded in authorized_excludes:
            validate_relative(excluded, "GIT_AUTHORIZED_EXCLUDE")
            args.extend([":(exclude)" + excluded, ":(exclude)" + excluded + "/**"])
    hardened = [
        "-c", "core.fsmonitor=false",
        "-c", "core.untrackedCache=false",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.worktree=" + repo_root,
        "-c", "core.bare=false",
        "-c", "core.excludesFile=/dev/null",
        "-c", "core.attributesFile=/dev/null",
        "-c", "submodule.recurse=false",
        "-c", "protocol.allow=never",
    ]
    argv = [git_binary] + hardened + ["-C", repo_root, "--no-pager"] + args
    return run_process(argv, git_env(), MAX_GIT_OUTPUT, label, allowed_returncodes=allowed_returncodes)


def safe_git_scalar(git_binary: str, repo_root: str, arguments: Sequence[str], label: str) -> str:
    raw = run_git(git_binary, repo_root, arguments, label)
    if b"\x00" in raw or b"\r" in raw or raw.count(b"\n") != 1:
        fail(Exit.PREFLIGHT_DRIFT, label + "_FORMAT")
    try:
        value = raw[:-1].decode("ascii", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_FORMAT")
    if not value:
        fail(Exit.PREFLIGHT_DRIFT, label + "_EMPTY")
    return value


def hash_regular_absolute(path: str, label: str, max_bytes: int = MAX_GIT_OUTPUT) -> Dict[str, Any]:
    metadata = assert_no_symlink_components(path, label)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        fail(Exit.PREFLIGHT_DRIFT, label + "_TYPE")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            fail(Exit.PREFLIGHT_DRIFT, label + "_RACE")
        digest, length = hash_fd(fd, "sha256", max_bytes, label)
    finally:
        os.close(fd)
    return {"sha256": digest, "bytes": length, "device": metadata.st_dev, "inode": metadata.st_ino}


def hash_directory_tree_absolute(path: str, label: str) -> Dict[str, Any]:
    metadata = assert_no_symlink_components(path, label)
    if not stat.S_ISDIR(metadata.st_mode):
        fail(Exit.PREFLIGHT_DRIFT, label + "_TYPE")
    root_fd = open_directory(path, label)
    rows: List[str] = []
    total_bytes = 0

    def walk(directory_fd: int, relative: str) -> None:
        nonlocal total_bytes
        try:
            entries = list(os.scandir(directory_fd))
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_SCAN")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            name = entry.name
            if not isinstance(name, str) or not is_nfc(name) or "\t" in name or "\n" in name:
                fail(Exit.PREFLIGHT_DRIFT, label + "_NAME")
            child_relative = name if not relative else relative + "/" + name
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISDIR(info.st_mode):
                rows.append("D\t%s\t%04o\t0\t-" % (child_relative, mode))
                child_fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    walk(child_fd, child_relative)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(info.st_mode):
                file_fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                try:
                    digest, length = hash_fd(file_fd, "sha256", MAX_GIT_OUTPUT, label)
                finally:
                    os.close(file_fd)
                total_bytes += length
                if total_bytes > MAX_GIT_OUTPUT:
                    fail(Exit.PREFLIGHT_DRIFT, label + "_SIZE")
                rows.append("F\t%s\t%04o\t%d\t%s" % (child_relative, mode, length, digest))
            elif stat.S_ISLNK(info.st_mode):
                link_text = os.readlink(name, dir_fd=directory_fd)
                if not isinstance(link_text, str) or "\t" in link_text or "\n" in link_text:
                    fail(Exit.PREFLIGHT_DRIFT, label + "_LINK")
                rows.append("L\t%s\t%04o\t%d\t%s" % (child_relative, mode, len(link_text.encode("utf-8")), link_text))
            else:
                fail(Exit.PREFLIGHT_DRIFT, label + "_SPECIAL")

    try:
        walk(root_fd, "")
    finally:
        os.close(root_fd)
    body = ("\n".join(rows) + "\n").encode("utf-8")
    return {"sha256": sha256(body), "entries": len(rows), "bytes": total_bytes}


def hash_tool_tree_absolute(path: str, label: str) -> Dict[str, Any]:
    root_path = os.path.realpath(path)
    assert_absolute(root_path, label)
    root_meta = assert_no_symlink_components(root_path, label)
    if (
        not stat.S_ISDIR(root_meta.st_mode)
        or root_meta.st_uid not in (0, os.getuid())
        or stat.S_IMODE(root_meta.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT_DRIFT, label + "_ROOT_POLICY")
    try:
        root_fd = os.open(
            root_path,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_ROOT_OPEN")
    rows = ["D\t.\t%04o\t0\t-" % stat.S_IMODE(root_meta.st_mode)]
    total_bytes = 0
    entry_count = 1

    def walk(directory_fd: int, relative: str) -> None:
        nonlocal total_bytes, entry_count
        initial = os.fstat(directory_fd)
        try:
            entries = list(os.scandir(directory_fd))
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_SCAN")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            name = entry.name
            if not isinstance(name, str) or not is_nfc(name) or any(character in name for character in ("\t", "\n", "\r")):
                fail(Exit.PREFLIGHT_DRIFT, label + "_NAME")
            child_relative = name if not relative else relative + "/" + name
            child_info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            mode = stat.S_IMODE(child_info.st_mode)
            if child_info.st_uid not in (0, os.getuid()) or (
                not stat.S_ISLNK(child_info.st_mode) and mode & 0o022
            ):
                fail(Exit.PREFLIGHT_DRIFT, label + "_ENTRY_POLICY")
            entry_count += 1
            if entry_count > 200_000:
                fail(Exit.PREFLIGHT_DRIFT, label + "_ENTRY_BOUND")
            if stat.S_ISDIR(child_info.st_mode):
                rows.append("D\t%s\t%04o\t0\t-" % (child_relative, mode))
                child_fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino, opened.st_mode) != (
                        child_info.st_dev,
                        child_info.st_ino,
                        child_info.st_mode,
                    ):
                        fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_RACE")
                    walk(child_fd, child_relative)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(child_info.st_mode):
                file_fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                try:
                    opened = os.fstat(file_fd)
                    if (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_size) != (
                        child_info.st_dev,
                        child_info.st_ino,
                        child_info.st_mode,
                        child_info.st_size,
                    ):
                        fail(Exit.PREFLIGHT_DRIFT, label + "_FILE_RACE")
                    digest, length = hash_fd(file_fd, "sha256", MAX_CACHE_OBJECT_BYTES, label)
                    final = os.fstat(file_fd)
                    if (opened.st_mtime_ns, opened.st_ctime_ns, opened.st_size) != (
                        final.st_mtime_ns,
                        final.st_ctime_ns,
                        final.st_size,
                    ):
                        fail(Exit.PREFLIGHT_DRIFT, label + "_FILE_READ_RACE")
                finally:
                    os.close(file_fd)
                total_bytes += length
                if total_bytes > 2 * 1024 * 1024 * 1024:
                    fail(Exit.PREFLIGHT_DRIFT, label + "_TOTAL_BOUND")
                rows.append("F\t%s\t%04o\t%d\t%s" % (child_relative, mode, length, digest))
            elif stat.S_ISLNK(child_info.st_mode):
                link_text = os.readlink(name, dir_fd=directory_fd)
                if not isinstance(link_text, str) or any(character in link_text for character in ("\t", "\n", "\r")):
                    fail(Exit.PREFLIGHT_DRIFT, label + "_LINK")
                rows.append(
                    "L\t%s\t%04o\t%d\t%s"
                    % (child_relative, mode, len(link_text.encode("utf-8")), link_text)
                )
            else:
                fail(Exit.PREFLIGHT_DRIFT, label + "_SPECIAL")
        final = os.fstat(directory_fd)
        if (initial.st_dev, initial.st_ino, initial.st_mtime_ns, initial.st_ctime_ns) != (
            final.st_dev,
            final.st_ino,
            final.st_mtime_ns,
            final.st_ctime_ns,
        ):
            fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_READ_RACE")

    try:
        walk(root_fd, "")
    finally:
        os.close(root_fd)
    body = ("\n".join(sorted(rows, key=lambda row: row.encode("utf-8"))) + "\n").encode("utf-8")
    return {"sha256": sha256(TOOL_TREE_DOMAIN + body), "entries": entry_count, "bytes": total_bytes}


def toolchain_set_receipt(entries: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            "\t".join(
                [
                    str(entry.get("role")),
                    str(entry.get("logical_id")),
                    str(entry.get("artifact_kind")),
                    str(entry.get("version")),
                    str(entry.get("digest_profile")),
                    str(entry.get("raw_digest_sha256")),
                ]
            )
        )
    body = ("\n".join(sorted(rows, key=lambda row: row.encode("utf-8"))) + "\n").encode("utf-8")
    return sha256(TOOLCHAIN_SET_DOMAIN + b"\x00" + body)


def dynamic_toolchain_receipt(entries: Sequence[Mapping[str, Any]]) -> str:
    body = canonical_json(
        {
            "schema_version": "gov01-static-acquisition-dynamic-toolchain-v2",
            "python_flags": ["-I", "-S", "-B"],
            "python_version": "%d.%d.%d" % sys.version_info[:3],
            "implementation": platform.python_implementation(),
            "toolchain_entries": list(entries),
        }
    )
    return sha256(DYNAMIC_TOOLCHAIN_DOMAIN + b"\x00" + body)


def public_artifact_set_receipt(artifacts: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for artifact in artifacts:
        rows.append(
            "\t".join(
                [
                    str(artifact.get("role")),
                    str(artifact.get("path")),
                    str(artifact.get("bytes")),
                    str(artifact.get("sha256")),
                ]
            )
        )
    body = ("\n".join(sorted(rows, key=lambda row: row.encode("utf-8"))) + "\n").encode("utf-8")
    return sha256(PUBLIC_ARTIFACT_SET_DOMAIN + b"\x00" + body)


def build_private_preapproval_body(
    envelope: Mapping[str, Any],
    key: bytes,
    locators: Mapping[str, Any],
    control_identity_commitment: str,
    artifact_receipt: str,
    git_state: Mapping[str, Any],
    toolchain: Mapping[str, Any],
    lock_raw: bytes,
    processes: Mapping[str, Any],
    selected_count: int,
    selected_cache_bytes: int,
    bin_count: int,
    expected: Mapping[str, Any],
) -> Dict[str, Any]:
    resolution = expected.get("resolution")
    tree = expected.get("tree")
    if not isinstance(resolution, dict) or not isinstance(tree, dict):
        fail(Exit.CHECKER_DRIFT, "PREAPPROVAL_EXPECTED_SCHEMA")
    body = {
        "schema_version": "gov01-private-preapproval-census-v2",
        "approval_challenge_id": envelope.get("approval_challenge_id"),
        "census_at_utc": envelope.get("census_at_utc"),
        "hmac_key_id": hmac_key_id(key),
        "authorized_locator_commitments": dict(locators),
        "private_control_identity_commitment": control_identity_commitment,
        "public_repo_artifact_set_receipt_sha256": artifact_receipt,
        "git_snapshot_commitment": git_state.get("commitment"),
        "toolchain_set_receipt_sha256": toolchain.get("toolchain_set_receipt_sha256"),
        "package_lock_raw_sha256": sha256(lock_raw),
        "host_platform": EXPECTED_PLATFORM,
        "host_architecture": EXPECTED_ARCH,
        "target_worktree_claude_sessions": processes.get("claude_session_count"),
        "forbidden_process_match_count": 0,
        "host_selected_package_count": selected_count,
        "host_selected_cache_bytes": selected_cache_bytes,
        "host_bin_link_count": bin_count,
        "content_receipt_sha256": expected.get("content_receipt_sha256"),
        "ustar_closure_sha256": expected.get("ustar_closure_sha256"),
        "resolution_receipt_sha256": resolution.get("sha256"),
        "expected_tree_sha256": tree.get("sha256"),
    }
    if tuple(body) != PRIVATE_PREAPPROVAL_FIELDS:
        fail(Exit.INTERNAL, "PREAPPROVAL_BODY_FIELDS")
    for key_name in (
        "private_control_identity_commitment",
        "public_repo_artifact_set_receipt_sha256",
        "git_snapshot_commitment",
        "toolchain_set_receipt_sha256",
        "package_lock_raw_sha256",
        "content_receipt_sha256",
        "ustar_closure_sha256",
        "resolution_receipt_sha256",
        "expected_tree_sha256",
    ):
        require_sha256(body.get(key_name), "PREAPPROVAL_" + key_name.upper())
    return body


def private_preapproval_commitment(key: bytes, body: Mapping[str, Any]) -> str:
    require_exact_object(body, PRIVATE_PREAPPROVAL_FIELDS, "PREAPPROVAL_BODY")
    return hmac_frame(key, PRIVATE_EVIDENCE_DOMAIN, canonical_json(body))


def compare_private_preapproval(envelope: Mapping[str, Any], actual: str) -> None:
    preimage = envelope.get("authorization_preimage")
    if not isinstance(preimage, dict):
        fail(Exit.CONTRACT, "PREAPPROVAL_ENVELOPE_SCHEMA")
    expected = preimage.get("private_preapproval_commitment")
    if not isinstance(expected, str) or not hmac.compare_digest(expected, actual):
        fail(Exit.PREFLIGHT_DRIFT, "PRIVATE_PREAPPROVAL_COMMITMENT_DRIFT")


def require_python_isolation() -> None:
    if not (
        sys.flags.isolated
        and sys.flags.ignore_environment
        and sys.flags.no_site
        and sys.flags.no_user_site
        and sys.flags.dont_write_bytecode
        and sys.flags.optimize == 0
        and sys.flags.debug == 0
        and not sys.flags.dev_mode
    ):
        fail(Exit.RUNTIME, "PYTHON_ISOLATION_FLAGS")


def verify_runtime_toolchain(
    repo_root: str,
    envelope: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
    strict: bool,
) -> Dict[str, Any]:
    require_python_isolation()
    frozen = envelope.get("frozen_toolchain")
    if not isinstance(frozen, dict) or not isinstance(frozen.get("entries"), list):
        fail(Exit.CONTRACT, "TOOLCHAIN_SCHEMA")
    frozen_entries = frozen["entries"]
    by_role = {entry.get("role"): entry for entry in frozen_entries if isinstance(entry, dict)}
    if set(by_role) != set(TOOLCHAIN_ROLES):
        fail(Exit.CONTRACT, "TOOLCHAIN_ROLES")
    artifact_by_role = {entry.get("role"): entry for entry in artifacts}
    executor_path = os.path.realpath(__file__)
    expected_executor_path = os.path.realpath(os.path.join(repo_root, EXECUTOR_RELATIVE))
    if executor_path != expected_executor_path:
        fail(Exit.CHECKER_DRIFT, "EXECUTOR_LAUNCH_PATH")
    python_binary = os.path.realpath(sys.executable)
    stdlib_root = os.path.realpath(sysconfig.get_path("stdlib"))
    actual_hashes = {
        "static-executor": hash_regular_absolute(executor_path, "EXECUTOR_TOOL", MAX_CACHE_OBJECT_BYTES)["sha256"],
        "static-verifier": artifact_by_role.get("static-verifier", {}).get("sha256"),
        "python-interpreter": hash_regular_absolute(python_binary, "PYTHON_TOOL", MAX_CACHE_OBJECT_BYTES)["sha256"],
        "python-stdlib-tree": hash_tool_tree_absolute(stdlib_root, "PYTHON_STDLIB")["sha256"],
    }
    for role, path in FIXED_TOOL_PATHS.items():
        actual_hashes[role] = hash_regular_absolute(path, role.upper(), MAX_CACHE_OBJECT_BYTES)["sha256"]
    observed_entries = []
    for role in TOOLCHAIN_ROLES:
        entry = dict(by_role[role])
        if role == "git-read-only-evidence":
            observed_entries.append(entry)
            continue
        actual = actual_hashes.get(role)
        if not isinstance(actual, str):
            fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_HASH")
        if strict and not hmac.compare_digest(str(entry.get("raw_digest_sha256")), actual):
            fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_DRIFT")
        entry["raw_digest_sha256"] = actual
        observed_entries.append(entry)
    for role in ("xcode-select-resolver", "xcrun-resolver"):
        path = FIXED_TOOL_PATHS[role]
        _AUTHORIZED_EXECUTABLE_HASHES[path] = actual_hashes[role]
    expected_git_hash = by_role["git-read-only-evidence"].get("raw_digest_sha256") if strict else None
    git_binary, git_hash = resolve_clt_git(expected_git_hash if isinstance(expected_git_hash, str) else None)
    actual_hashes["git-read-only-evidence"] = git_hash
    for index, entry in enumerate(observed_entries):
        if entry.get("role") == "git-read-only-evidence":
            entry = dict(entry)
            entry["raw_digest_sha256"] = git_hash
            observed_entries[index] = entry
            break
    for role in ("pgrep-read-only-evidence", "lsof-read-only-evidence"):
        path = FIXED_TOOL_PATHS[role]
        _AUTHORIZED_EXECUTABLE_HASHES[path] = actual_hashes[role]
    receipt = toolchain_set_receipt(observed_entries)
    if strict and not hmac.compare_digest(str(frozen.get("toolchain_set_receipt_sha256")), receipt):
        fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_SET_RECEIPT")
    dynamic_receipt = dynamic_toolchain_receipt(observed_entries)
    if strict and not hmac.compare_digest(str(frozen.get("dynamic_closure_receipt_sha256")), dynamic_receipt):
        fail(Exit.PREFLIGHT_DRIFT, "DYNAMIC_TOOLCHAIN_RECEIPT")
    return {
        "git_binary": git_binary,
        "pgrep_binary": FIXED_TOOL_PATHS["pgrep-read-only-evidence"],
        "lsof_binary": FIXED_TOOL_PATHS["lsof-read-only-evidence"],
        "entries": observed_entries,
        "toolchain_set_receipt_sha256": receipt,
        "dynamic_closure_receipt_sha256": dynamic_receipt,
        "assurance": "runtime-self-attested-not-pre-exec",
    }


def porcelain_v2_paths(status: bytes) -> List[bytes]:
    records = status.split(b"\x00")
    paths: List[bytes] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if record.startswith(b"1 "):
            fields = record.split(b" ", 8)
            if len(fields) != 9:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_STATUS_ORDINARY_FORMAT")
            paths.append(fields[8])
        elif record.startswith(b"2 "):
            fields = record.split(b" ", 9)
            if len(fields) != 10 or index >= len(records) or not records[index]:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_STATUS_RENAME_FORMAT")
            paths.append(fields[9])
            paths.append(records[index])
            index += 1
        elif record.startswith(b"u "):
            fields = record.split(b" ", 10)
            if len(fields) != 11:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_STATUS_UNMERGED_FORMAT")
            paths.append(fields[10])
        elif record.startswith(b"? "):
            paths.append(record[2:])
        else:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_STATUS_RECORD_FORMAT")
    return sorted(set(paths))


def dirty_path_manifest_commitment(repo_root: str, status: bytes, key: bytes) -> str:
    repo_fd = open_directory(repo_root, "DIRTY_REPO")
    rows = []
    try:
        for path_bytes in porcelain_v2_paths(status):
            if (
                not path_bytes
                or path_bytes.startswith(b"/")
                or b"\\" in path_bytes
                or b"\x00" in path_bytes
                or any(part in (b"", b".", b"..") for part in path_bytes.split(b"/"))
            ):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_PATH")
            lowered_components = [part.lower() for part in path_bytes.split(b"/")]
            if any(VAULT_PREFIX.encode("ascii") in part or part == b".obsidian" for part in lowered_components):
                fail(Exit.PRIVACY, "GIT_DIRTY_VAULT_PATH")
            path_id = hmac_frame(key, b"CLS/GOV01/GIT-DIRTY-PATH/v2", path_bytes)
            try:
                info = os.stat(path_bytes, dir_fd=repo_fd, follow_symlinks=False)
            except FileNotFoundError:
                rows.append({"path_hmac": path_id, "kind": "A"})
                continue
            except OSError:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_LSTAT")
            base = {
                "path_hmac": path_id,
                "dev": info.st_dev,
                "ino": info.st_ino,
                "mode": info.st_mode,
                "uid": info.st_uid,
                "gid": info.st_gid,
                "nlink": info.st_nlink,
                "size": info.st_size,
                "mtime_ns": info.st_mtime_ns,
                "ctime_ns": info.st_ctime_ns,
                "flags": getattr(info, "st_flags", 0),
            }
            if stat.S_ISREG(info.st_mode):
                fd = os.open(path_bytes, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=repo_fd)
                try:
                    opened = os.fstat(fd)
                    if (
                        opened.st_dev,
                        opened.st_ino,
                        opened.st_mode,
                        opened.st_size,
                        opened.st_mtime_ns,
                        opened.st_ctime_ns,
                    ) != (
                        info.st_dev,
                        info.st_ino,
                        info.st_mode,
                        info.st_size,
                        info.st_mtime_ns,
                        info.st_ctime_ns,
                    ):
                        fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_OPEN_RACE")
                    digest, length = hash_fd(fd, "sha256", MAX_CACHE_OBJECT_BYTES, "GIT_DIRTY_FILE")
                    final = os.fstat(fd)
                    if (
                        opened.st_dev,
                        opened.st_ino,
                        opened.st_mode,
                        opened.st_size,
                        opened.st_mtime_ns,
                        opened.st_ctime_ns,
                    ) != (
                        final.st_dev,
                        final.st_ino,
                        final.st_mode,
                        final.st_size,
                        final.st_mtime_ns,
                        final.st_ctime_ns,
                    ):
                        fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_READ_RACE")
                finally:
                    os.close(fd)
                post_path = os.stat(path_bytes, dir_fd=repo_fd, follow_symlinks=False)
                if (
                    post_path.st_dev,
                    post_path.st_ino,
                    post_path.st_mode,
                    post_path.st_uid,
                    post_path.st_gid,
                    post_path.st_nlink,
                    post_path.st_size,
                    post_path.st_mtime_ns,
                    post_path.st_ctime_ns,
                    getattr(post_path, "st_flags", 0),
                ) != (
                    info.st_dev,
                    info.st_ino,
                    info.st_mode,
                    info.st_uid,
                    info.st_gid,
                    info.st_nlink,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                    getattr(info, "st_flags", 0),
                ):
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_PATH_RACE")
                base.update({"kind": "F", "bytes": length, "content_sha256": digest})
            elif stat.S_ISLNK(info.st_mode):
                try:
                    link = os.readlink(path_bytes, dir_fd=repo_fd)
                except OSError:
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_READLINK")
                link_bytes = link if isinstance(link, bytes) else os.fsencode(link)
                final = os.stat(path_bytes, dir_fd=repo_fd, follow_symlinks=False)
                if (info.st_dev, info.st_ino, info.st_mode, info.st_mtime_ns, info.st_ctime_ns) != (
                    final.st_dev,
                    final.st_ino,
                    final.st_mode,
                    final.st_mtime_ns,
                    final.st_ctime_ns,
                ):
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_LINK_RACE")
                base.update({"kind": "L", "link_sha256": sha256(link_bytes)})
            elif stat.S_ISDIR(info.st_mode):
                final = os.stat(path_bytes, dir_fd=repo_fd, follow_symlinks=False)
                if (
                    final.st_dev,
                    final.st_ino,
                    final.st_mode,
                    final.st_uid,
                    final.st_gid,
                    final.st_nlink,
                    final.st_size,
                    final.st_mtime_ns,
                    final.st_ctime_ns,
                    getattr(final, "st_flags", 0),
                ) != (
                    info.st_dev,
                    info.st_ino,
                    info.st_mode,
                    info.st_uid,
                    info.st_gid,
                    info.st_nlink,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                    getattr(info, "st_flags", 0),
                ):
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_DIRECTORY_RACE")
                base.update({"kind": "D"})
            else:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_DIRTY_SPECIAL")
            rows.append(base)
    finally:
        os.close(repo_fd)
    return hmac_frame(key, GIT_DIRTY_MANIFEST_DOMAIN, canonical_json(rows))


def resolve_git_control_directory(repo_root: str, key: bytes) -> Tuple[str, str, Dict[str, Any]]:
    marker_path = os.path.join(repo_root, ".git")
    marker_meta = assert_no_symlink_components(marker_path, "GIT_CONTROL_MARKER")
    marker_observation: Dict[str, Any]
    if stat.S_ISDIR(marker_meta.st_mode):
        git_dir = marker_path
        marker_observation = {"kind": "directory"}
    elif stat.S_ISREG(marker_meta.st_mode):
        raw, metadata = read_absolute_regular(marker_path, "GIT_CONTROL_MARKER", 4096)
        if metadata.st_uid != os.getuid() or raw.count(b"\n") != 1 or not raw.startswith(b"gitdir: "):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_MARKER_PROFILE")
        try:
            locator = raw[8:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_MARKER_ENCODING")
        if not is_nfc(locator) or "\x00" in locator or "\\" in locator:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_MARKER_LOCATOR")
        git_dir = os.path.normpath(locator if os.path.isabs(locator) else os.path.join(repo_root, locator))
        marker_observation = {
            "kind": "gitfile",
            "raw_sha256": sha256(raw),
            "bytes": len(raw),
        }
    else:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_MARKER_TYPE")
    assert_absolute(git_dir, "GIT_CONTROL_DIRECTORY")
    if has_forbidden_vault_component(git_dir):
        fail(Exit.PRIVACY, "GIT_CONTROL_VAULT_LOCATOR")
    require_owned_directory(git_dir, "GIT_CONTROL_DIRECTORY")

    commondir_path = os.path.join(git_dir, "commondir")
    try:
        commondir_meta = os.lstat(commondir_path)
    except FileNotFoundError:
        common_dir = git_dir
        commondir_observation: Dict[str, Any] = {"state": "ABSENT"}
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_LSTAT")
    else:
        if not stat.S_ISREG(commondir_meta.st_mode) or stat.S_ISLNK(commondir_meta.st_mode):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_TYPE")
        raw, _ = read_absolute_regular(commondir_path, "GIT_COMMONDIR_FILE", 4096)
        if raw.count(b"\n") != 1:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_FORMAT")
        try:
            locator = raw[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_ENCODING")
        if not locator or not is_nfc(locator) or "\x00" in locator or "\\" in locator:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_LOCATOR")
        common_dir = os.path.normpath(locator if os.path.isabs(locator) else os.path.join(git_dir, locator))
        commondir_observation = {"state": "PRESENT", "raw_sha256": sha256(raw), "bytes": len(raw)}
    assert_absolute(common_dir, "GIT_COMMON_CONTROL_DIRECTORY")
    if has_forbidden_vault_component(common_dir):
        fail(Exit.PRIVACY, "GIT_COMMON_CONTROL_VAULT_LOCATOR")
    require_owned_directory(common_dir, "GIT_COMMON_CONTROL_DIRECTORY")
    observation = {
        "marker": marker_observation,
        "commondir": commondir_observation,
        "git_dir_locator_commitment": locator_commitment(key, "git-control-directory", git_dir),
        "common_dir_locator_commitment": locator_commitment(key, "git-common-control-directory", common_dir),
    }
    return git_dir, common_dir, observation


def git_control_preflight(repo_root: str, key: bytes) -> Dict[str, Any]:
    git_dir, common_dir, observation = resolve_git_control_directory(repo_root, key)

    def config_observation(path: str, label: str, required: bool) -> Dict[str, Any]:
        try:
            metadata = os.lstat(path)
        except FileNotFoundError:
            if required:
                fail(Exit.PREFLIGHT_DRIFT, label + "_MISSING")
            return {"state": "ABSENT"}
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_LSTAT")
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) or metadata.st_uid != os.getuid():
            fail(Exit.PREFLIGHT_DRIFT, label + "_TYPE")
        raw, _ = read_absolute_regular(path, label, MAX_JSON_BYTES)
        for line in raw.splitlines():
            stripped = line.lstrip()
            if stripped.startswith((b"#", b";")):
                continue
            lowered_line = stripped.lower()
            if lowered_line.startswith(b"[include"):
                fail(Exit.PRIVACY, "GIT_CONFIG_INCLUDE_PROHIBITED")
            if lowered_line.startswith((b"[filter", b"[diff", b"[merge")):
                fail(Exit.TRACE, "GIT_PROCESS_CAPABLE_CONFIG_PROHIBITED")
            if b"promisor" in lowered_line or b"partialclone" in lowered_line:
                fail(Exit.TRACE, "GIT_LAZY_FETCH_CONFIG_PROHIBITED")
        lowered = raw.lower()
        if b"canvas-vault" in lowered or b".obsidian" in lowered:
            fail(Exit.PRIVACY, "GIT_CONFIG_VAULT_LOCATOR")
        return {"state": "PRESENT", "raw_sha256": sha256(raw), "bytes": len(raw)}

    observation["common_config"] = config_observation(
        os.path.join(common_dir, "config"),
        "GIT_COMMON_CONFIG",
        required=True,
    )
    observation["worktree_config"] = config_observation(
        os.path.join(git_dir, "config.worktree"),
        "GIT_WORKTREE_CONFIG",
        required=False,
    )
    for relative in (
        "objects/info/alternates",
        "objects/info/http-alternates",
        "info/grafts",
    ):
        candidate = os.path.join(common_dir, *relative.split("/"))
        try:
            os.lstat(candidate)
        except FileNotFoundError:
            continue
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ALTERNATE_CONTROL_LSTAT")
        fail(Exit.PRIVACY, "GIT_ALTERNATE_CONTROL_PROHIBITED")
    observation["alternate_controls"] = "ABSENT"
    return observation


def git_snapshot(
    repo_root: str,
    key: bytes,
    git_binary: str,
    authorized_excludes: Sequence[str] = (),
) -> Dict[str, Any]:
    # Resolve and inspect local Git controls directly before Git has an
    # opportunity to follow an include or object-alternate private locator.
    git_control = git_control_preflight(repo_root, key)
    head = safe_git_scalar(git_binary, repo_root, ["rev-parse", "--verify", "HEAD"], "GIT_HEAD")
    tree = safe_git_scalar(git_binary, repo_root, ["rev-parse", "--verify", "HEAD^{tree}"], "GIT_TREE")
    object_format = safe_git_scalar(git_binary, repo_root, ["rev-parse", "--show-object-format"], "GIT_OBJECT_FORMAT")
    if object_format not in ("sha1", "sha256"):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_FORMAT")
    expected_oid_length = 40 if object_format == "sha1" else 64
    if not re.fullmatch(r"[0-9a-f]{%d}" % expected_oid_length, head):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_HEAD_FORMAT")
    if not re.fullmatch(r"[0-9a-f]{%d}" % expected_oid_length, tree):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_FORMAT")
    # This is the only command that enumerates worktree paths; exclusions are mandatory.
    status = run_git(
        git_binary,
        repo_root,
        ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
        "GIT_STATUS",
        enumerates_worktree=True,
        authorized_excludes=authorized_excludes,
    )
    if VAULT_PREFIX.encode("ascii") in status.lower():
        fail(Exit.PRIVACY, "GIT_STATUS_VAULT_LEAK")
    dirty_manifest = dirty_path_manifest_commitment(repo_root, status, key)
    # The v1 envelope freezes the exact byte stream produced by `git show-ref`.
    refs = run_git(git_binary, repo_root, ["show-ref"], "GIT_REFS")
    index_locator_raw = run_git(git_binary, repo_root, ["rev-parse", "--git-path", "index"], "GIT_INDEX_LOCATOR")
    try:
        index_locator_text = index_locator_raw.rstrip(b"\n").decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_INDEX_LOCATOR_FORMAT")
    index_path = index_locator_text if os.path.isabs(index_locator_text) else os.path.join(repo_root, index_locator_text)
    index_path = os.path.normpath(index_path)
    index_info = hash_regular_absolute(index_path, "GIT_INDEX")
    hooks_override = run_git(
        git_binary,
        repo_root,
        ["config", "--local", "--get", "core.hooksPath"],
        "GIT_HOOKS_OVERRIDE",
        allowed_returncodes=(0, 1),
    )
    if hooks_override:
        if hooks_override.count(b"\n") != 1:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_HOOKS_OVERRIDE_FORMAT")
        try:
            hooks_locator_text = hooks_override[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_HOOKS_OVERRIDE_FORMAT")
        hooks_path = os.path.normpath(
            hooks_locator_text if os.path.isabs(hooks_locator_text) else os.path.join(repo_root, hooks_locator_text)
        )
        common_raw = run_git(
            git_binary,
            repo_root,
            ["rev-parse", "--path-format=absolute", "--git-common-dir"],
            "GIT_COMMON_DIR",
        )
        try:
            common_path = os.path.normpath(common_raw.rstrip(b"\n").decode("utf-8", "strict"))
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMON_DIR_FORMAT")
        if hooks_path == "/dev/null":
            hooks_info = hash_regular_absolute(hooks_path, "GIT_HOOKS_DISABLED", 4096)
            hooks_state = "configured-dev-null"
        elif is_same_or_within(hooks_path, common_path) or is_same_or_within(hooks_path, repo_root):
            hooks_info = hash_directory_tree_absolute(hooks_path, "GIT_HOOKS")
            hooks_state = "configured-git-contained"
        else:
            # Never dereference an external/private configured hooks locator.
            fail(Exit.PREFLIGHT_DRIFT, "EXTERNAL_HOOKS_PATH")
    else:
        hooks_path_raw = run_git(git_binary, repo_root, ["rev-parse", "--git-path", "hooks"], "GIT_HOOKS_LOCATOR")
        try:
            hooks_locator_text = hooks_path_raw.rstrip(b"\n").decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_HOOKS_LOCATOR_FORMAT")
        hooks_path = hooks_locator_text if os.path.isabs(hooks_locator_text) else os.path.join(repo_root, hooks_locator_text)
        hooks_path = os.path.normpath(hooks_path)
        hooks_info = hash_directory_tree_absolute(hooks_path, "GIT_HOOKS")
        hooks_state = "default-git-path"
    config_path_raw = run_git(git_binary, repo_root, ["rev-parse", "--git-path", "config"], "GIT_CONFIG_LOCATOR")
    try:
        config_locator_text = config_path_raw.rstrip(b"\n").decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONFIG_LOCATOR_FORMAT")
    config_path = config_locator_text if os.path.isabs(config_locator_text) else os.path.join(repo_root, config_locator_text)
    config_info = hash_regular_absolute(os.path.normpath(config_path), "GIT_CONFIG")
    private_body = {
        "git_control": git_control,
        "head": head,
        "tree": tree,
        "object_format": object_format,
        "status_sha256": sha256(status),
        "status_bytes": len(status),
        "dirty_manifest_commitment": dirty_manifest,
        "refs_sha256": sha256(refs),
        "refs_bytes": len(refs),
        "index": index_info,
        "config": config_info,
        "hooks": hooks_info,
        "index_locator_commitment": locator_commitment(key, "git-index", index_path),
        "config_locator_commitment": locator_commitment(key, "git-config", config_path),
        "hooks_locator_commitment": locator_commitment(key, "git-hooks", hooks_path),
        "hooks_config_state": hooks_state,
        "git_binary_sha256": hash_regular_absolute(git_binary, "CLT_GIT")["sha256"],
    }
    body = canonical_json(private_body)
    private_body["commitment"] = hmac_frame(key, GIT_SNAPSHOT_DOMAIN, body)
    return private_body


def require_node_modules_absent(repo_root: str) -> None:
    target = os.path.join(repo_root, "node_modules")
    try:
        os.lstat(target)
    except FileNotFoundError:
        return
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "NODE_MODULES_LSTAT")
    fail(Exit.PREFLIGHT_DRIFT, "NODE_MODULES_NOT_ABSENT")


def selector_allows(values: Any, positive: str, label: str) -> bool:
    if values is None:
        return True
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        fail(Exit.CACHE_LOCK, label + "_SCHEMA")
    if ("!" + positive) in values:
        return False
    positives = [item for item in values if not item.startswith("!")]
    return not positives or positive in positives


def validate_package_key(key: str) -> None:
    components = validate_relative(key, "LOCK_PACKAGE_KEY")
    cursor = 0
    while cursor < len(components):
        if components[cursor] != "node_modules":
            fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_KEY_SHAPE")
        cursor += 1
        if cursor >= len(components):
            fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_KEY_SHAPE")
        if components[cursor].startswith("@"):
            if not PACKAGE_COMPONENT_RE.fullmatch(components[cursor][1:]):
                fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_SCOPE")
            cursor += 1
            if cursor >= len(components):
                fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_KEY_SHAPE")
        if not PACKAGE_COMPONENT_RE.fullmatch(components[cursor]):
            fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_NAME")
        cursor += 1


def parse_sha512_integrity(value: Any) -> Tuple[str, bytes]:
    if not isinstance(value, str):
        fail(Exit.CACHE_LOCK, "INTEGRITY_SCHEMA")
    candidates = []
    for token in value.split():
        if token.startswith("sha512-") and "?" not in token:
            candidates.append(token[7:])
    if len(candidates) != 1:
        fail(Exit.CACHE_LOCK, "INTEGRITY_PROFILE")
    try:
        raw = base64.b64decode(candidates[0], validate=True)
    except (binascii.Error, ValueError):
        fail(Exit.CACHE_LOCK, "INTEGRITY_BASE64")
    if len(raw) != 64:
        fail(Exit.CACHE_LOCK, "INTEGRITY_LENGTH")
    return candidates[0], raw


def validate_registry_url(value: Any) -> str:
    if not isinstance(value, str) or not is_nfc(value):
        fail(Exit.CACHE_LOCK, "RESOLVED_SCHEMA")
    if any(unicodedata.category(character) == "Cc" for character in value):
        fail(Exit.CACHE_LOCK, "RESOLVED_CONTROL_CHARACTER")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "registry.npmjs.org"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
    ):
        fail(Exit.CACHE_LOCK, "RESOLVED_ORIGIN")
    return value


def selected_lock_entries(lock: Mapping[str, Any]) -> List[Tuple[str, Mapping[str, Any]]]:
    if lock.get("lockfileVersion") != 3:
        fail(Exit.CACHE_LOCK, "LOCKFILE_VERSION")
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        fail(Exit.CACHE_LOCK, "LOCK_PACKAGES_SCHEMA")
    selected: List[Tuple[str, Mapping[str, Any]]] = []
    for key in sorted(packages.keys(), key=lambda item: item.encode("utf-8") if isinstance(item, str) else b""):
        if key == "":
            continue
        entry = packages[key]
        if not isinstance(key, str) or not isinstance(entry, dict):
            fail(Exit.CACHE_LOCK, "LOCK_ENTRY_SCHEMA")
        validate_package_key(key)
        if not selector_allows(entry.get("os"), EXPECTED_PLATFORM, "LOCK_OS"):
            continue
        if not selector_allows(entry.get("cpu"), EXPECTED_ARCH, "LOCK_CPU"):
            continue
        validate_registry_url(entry.get("resolved"))
        parse_sha512_integrity(entry.get("integrity"))
        selected.append((key, entry))
    return selected


def bin_mapping(package_key: str, entry: Mapping[str, Any]) -> List[Tuple[str, str, str]]:
    raw = entry.get("bin")
    if raw is None:
        return []
    package_name = package_key.split("/")[-1]
    pairs: List[Tuple[str, str, str]] = []
    if isinstance(raw, str):
        raw_items = [(package_name, raw)]
    elif isinstance(raw, dict):
        raw_items = sorted(raw.items())
    else:
        fail(Exit.CACHE_LOCK, "BIN_SCHEMA")
    for name, target in raw_items:
        if not isinstance(name, str) or not isinstance(target, str):
            fail(Exit.CACHE_LOCK, "BIN_SCHEMA")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
            fail(Exit.CACHE_LOCK, "BIN_NAME")
        validate_relative(target, "BIN_TARGET", forbid_vault=False)
        pairs.append((package_key, name, target))
    return pairs


def open_cache_object(cache_fd: int, digest_raw: bytes) -> Tuple[int, str]:
    digest_hex = digest_raw.hex()
    relative = "_cacache/content-v2/sha512/%s/%s/%s" % (
        digest_hex[:2],
        digest_hex[2:4],
        digest_hex[4:],
    )
    components = validate_relative(relative, "CACHE_CONTENT", forbid_vault=False)
    current = os.dup(cache_fd)
    try:
        for component in components[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            os.close(current)
            current = next_fd
        fd = os.open(components[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=current)
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_CACHE_OBJECT_BYTES:
            os.close(fd)
            fail(Exit.CACHE_LOCK, "CACHE_CONTENT_TYPE")
        return fd, relative
    except ContractError:
        raise
    except OSError:
        fail(Exit.CACHE_LOCK, "CACHE_CONTENT_MISSING")
    finally:
        os.close(current)
    raise AssertionError("unreachable")


def cache_census(cache_fd: int, selected: Sequence[Tuple[str, Mapping[str, Any]]]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]], int]:
    manifest: List[Dict[str, Any]] = []
    bins: List[Tuple[str, str, str]] = []
    total_bytes = 0
    for package_key, entry in selected:
        integrity_b64, digest_raw = parse_sha512_integrity(entry.get("integrity"))
        fd, cache_relative = open_cache_object(cache_fd, digest_raw)
        try:
            actual_hex, length = hash_fd(fd, "sha512", MAX_CACHE_OBJECT_BYTES, "CACHE_CONTENT")
        finally:
            os.close(fd)
        if not hmac.compare_digest(actual_hex, digest_raw.hex()):
            fail(Exit.CACHE_LOCK, "CACHE_CONTENT_HASH")
        total_bytes += length
        bins.extend(bin_mapping(package_key, entry))
        manifest.append(
            {
                "package_key": package_key,
                "resolved": entry.get("resolved"),
                "integrity_sha512": integrity_b64,
                "content_relative": cache_relative,
                "bytes": length,
            }
        )
    return manifest, bins, total_bytes


def freeze_expected_bytes(
    cache_fd: int,
    expected: Mapping[str, Any],
) -> Tuple[Dict[str, bytes], Dict[str, bytes]]:
    selected = expected.get("selected")
    records = expected.get("package_records")
    layout = expected.get("layout")
    if not isinstance(selected, dict) or not isinstance(records, dict) or not isinstance(layout, dict):
        fail(Exit.CHECKER_DRIFT, "VERIFIER_EXPECTED_SCHEMA")
    compressed_blobs: Dict[str, bytes] = {}
    compressed_total = 0
    for package_key in sorted(selected, key=lambda value: value.encode("utf-8")):
        meta = selected[package_key]
        if not isinstance(meta, dict):
            fail(Exit.CHECKER_DRIFT, "VERIFIER_SELECTED_SCHEMA")
        _, digest_raw = parse_sha512_integrity(meta.get("integrity"))
        fd, _ = open_cache_object(cache_fd, digest_raw)
        try:
            raw = read_fd(fd, MAX_CACHE_OBJECT_BYTES, "CACHE_CONTENT_FREEZE")
        finally:
            os.close(fd)
        if not hmac.compare_digest(hashlib.sha512(raw).digest(), digest_raw):
            fail(Exit.CACHE_LOCK, "CACHE_CONTENT_FREEZE_HASH")
        compressed_total += len(raw)
        if compressed_total > MAX_COMPRESSED_CLOSURE:
            fail(Exit.CACHE_LOCK, "CACHE_CONTENT_FREEZE_BOUND")
        compressed_blobs[package_key] = raw
    if compressed_total != expected.get("compressed_bytes") or len(compressed_blobs) != EXPECTED_SELECTED_PACKAGES:
        fail(Exit.CACHE_LOCK, "CACHE_CONTENT_FREEZE_CLOSURE")

    payloads: Dict[str, bytes] = {}
    payload_total = 0
    for package_key in sorted(records, key=lambda value: value.encode("utf-8")):
        record = records[package_key]
        if not isinstance(record, dict) or not isinstance(record.get("files"), dict):
            fail(Exit.CHECKER_DRIFT, "VERIFIER_RETAIN_BYTES")
        for logical_path, payload in record["files"].items():
            if not isinstance(logical_path, str) or not isinstance(payload, bytes) or logical_path in payloads:
                fail(Exit.CHECKER_DRIFT, "VERIFIER_PAYLOAD_SCHEMA")
            frozen_layout = layout.get(logical_path)
            if (
                not isinstance(frozen_layout, tuple)
                or len(frozen_layout) != 4
                or frozen_layout[0] != "F"
                or frozen_layout[2] != len(payload)
                or frozen_layout[3] != sha256(payload)
            ):
                fail(Exit.CHECKER_DRIFT, "VERIFIER_PAYLOAD_LAYOUT")
            payloads[logical_path] = payload
            payload_total += len(payload)
            if payload_total > MAX_PAYLOAD_CLOSURE:
                fail(Exit.ARCHIVE, "PAYLOAD_FREEZE_BOUND")
    expected_files = {path for path, value in layout.items() if isinstance(value, tuple) and value[0] == "F"}
    if set(payloads) != expected_files:
        fail(Exit.CHECKER_DRIFT, "VERIFIER_PAYLOAD_CLOSURE")
    if payload_total != expected.get("payload_bytes") or len(payloads) != expected.get("raw_regular_count"):
        fail(Exit.ARCHIVE, "PAYLOAD_FREEZE_TOTAL")
    if "node_modules/.package-lock.json" in layout:
        fail(Exit.ARCHIVE, "HIDDEN_PACKAGE_LOCK_PROHIBITED")
    return compressed_blobs, payloads


def process_census(
    repo_root: str,
    key: bytes,
    pgrep_binary: str,
    lsof_binary: str,
) -> Dict[str, Any]:
    process_env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"}
    # First narrow to Claude candidates.  Never perform a machine-wide lsof walk.
    pgrep_raw = run_process(
        [pgrep_binary, "-if", r"(^|[/ ])claude([ ]|$)|@anthropic-ai/claude-code"],
        process_env,
        1024 * 1024,
        "PGREP_CLAUDE",
        allowed_returncodes=(0, 1),
    )
    candidate_pids: List[int] = []
    for line in pgrep_raw.splitlines():
        if not line.isdigit():
            fail(Exit.PREFLIGHT_DRIFT, "PGREP_FORMAT")
        pid = int(line)
        if pid <= 1 or pid == os.getpid():
            continue
        candidate_pids.append(pid)
    candidate_pids = sorted(set(candidate_pids))
    if len(candidate_pids) > 1024:
        fail(Exit.PREFLIGHT_DRIFT, "PGREP_BOUND")
    active: List[Dict[str, Any]] = []
    repo_prefix = repo_root + os.sep
    lsof_hasher = hashlib.sha256()
    for pid in candidate_pids:
        lsof_raw = run_process(
            [lsof_binary, "-nP", "-a", "-p", str(pid), "-d", "cwd", "-Fpn"],
            process_env,
            64 * 1024,
            "LSOF_CLAUDE_PID",
        )
        lsof_hasher.update(len(lsof_raw).to_bytes(8, "big"))
        lsof_hasher.update(lsof_raw)
        cwd: Optional[str] = None
        current_pid: Optional[int] = None
        for raw_line in lsof_raw.splitlines():
            if raw_line.startswith(b"p") and raw_line[1:].isdigit():
                current_pid = int(raw_line[1:])
            elif raw_line.startswith(b"n") and current_pid == pid:
                try:
                    cwd = raw_line[1:].decode("utf-8", "strict")
                except UnicodeDecodeError:
                    fail(Exit.PREFLIGHT_DRIFT, "LSOF_ENCODING")
        if cwd != repo_root and (cwd is None or not cwd.startswith(repo_prefix)):
            continue
        active.append(
            {
                "pid": pid,
                "cwd_commitment": locator_commitment(key, "process-cwd", cwd or ""),
            }
        )
    return {
        "claude_sessions": active,
        "claude_session_count": len(active),
        "candidate_count": len(candidate_pids),
        "pgrep_sha256": sha256(pgrep_raw),
        "candidate_lsof_sha256": lsof_hasher.hexdigest(),
    }


def mkdir_private_child(
    parent_fd: int,
    name: str,
    expected_uid: int,
    expected_gid: int,
    before_create: Optional[Callable[[], None]] = None,
    on_created: Optional[Callable[[], None]] = None,
) -> int:
    validate_relative(name, "PRIVATE_CHILD", forbid_vault=False)
    if before_create is not None:
        before_create()
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent_fd)
    except FileExistsError:
        fail(Exit.REPLAY, "PRIVATE_CHILD_EXISTS")
    except OSError:
        fail(Exit.EVIDENCE, "PRIVATE_CHILD_CREATE")
    # This callback is deliberately the first operation after successful
    # mkdirat: the persistent single-use claim has already consumed authority.
    if on_created is not None:
        on_created()
    try:
        child = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except OSError:
        fail(Exit.EVIDENCE, "PRIVATE_CHILD_OPEN")
    metadata = os.fstat(child)
    if (
        metadata.st_uid != expected_uid
        or metadata.st_gid != expected_gid
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        os.close(child)
        fail(Exit.EVIDENCE, "PRIVATE_CHILD_POLICY")
    return child


def write_exclusive(fd_parent: int, name: str, data: bytes, mode: int = 0o600) -> None:
    validate_relative(name, "EVIDENCE_NAME", forbid_vault=False)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(name, flags, mode, dir_fd=fd_parent)
    except FileExistsError:
        fail(Exit.REPLAY, "EVIDENCE_EXISTS")
    except OSError:
        fail(Exit.EVIDENCE, "EVIDENCE_CREATE")
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != mode:
            fail(Exit.EVIDENCE, "EVIDENCE_POLICY")
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:])
            if written <= 0:
                fail(Exit.EVIDENCE, "EVIDENCE_WRITE")
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(fd_parent)


def logical_child_path(logical_path: str) -> str:
    validate_relative(logical_path, "EXPECTED_TREE_PATH")
    if logical_path == TARGET_NAME:
        return ""
    prefix = TARGET_NAME + "/"
    if not logical_path.startswith(prefix):
        fail(Exit.CHECKER_DRIFT, "EXPECTED_TREE_ROOT")
    return logical_path[len(prefix) :]


def open_relative_directory(root_fd: int, relative: str, label: str) -> int:
    if relative == "":
        return os.dup(root_fd)
    components = validate_relative(relative, label, forbid_vault=False)
    current = os.dup(root_fd)
    try:
        for component in components:
            next_fd = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            os.close(current)
            current = next_fd
        return current
    except OSError:
        os.close(current)
        fail(Exit.EXTRACT, label + "_OPEN")
    raise AssertionError("unreachable")


def split_parent(relative: str, label: str) -> Tuple[str, str]:
    components = validate_relative(relative, label, forbid_vault=False)
    parent = "/".join(components[:-1])
    return parent, components[-1]


def create_stage_directory(stage_fd: int, relative: str) -> None:
    parent, leaf = split_parent(relative, "STAGE_DIRECTORY")
    parent_fd = open_relative_directory(stage_fd, parent, "STAGE_DIRECTORY_PARENT")
    try:
        try:
            os.mkdir(leaf, 0o700, dir_fd=parent_fd)
        except FileExistsError:
            fail(Exit.EXTRACT, "STAGE_DIRECTORY_COLLISION")
        except OSError:
            fail(Exit.EXTRACT, "STAGE_DIRECTORY_CREATE")
        child_fd = open_relative_directory(parent_fd, leaf, "STAGE_DIRECTORY_CHILD")
        try:
            os.fchmod(child_fd, 0o700)
            metadata = os.fstat(child_fd)
            if metadata.st_uid != os.getuid() or metadata.st_gid != os.getgid():
                fail(Exit.EXTRACT, "STAGE_DIRECTORY_OWNER")
            os.fsync(child_fd)
        finally:
            os.close(child_fd)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def write_stage_file(stage_fd: int, relative: str, payload: bytes, mode: int) -> None:
    if mode not in (0o644, 0o755):
        fail(Exit.EXTRACT, "STAGE_FILE_MODE")
    parent, leaf = split_parent(relative, "STAGE_FILE")
    parent_fd = open_relative_directory(stage_fd, parent, "STAGE_FILE_PARENT")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        try:
            file_fd = os.open(leaf, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            fail(Exit.EXTRACT, "STAGE_FILE_COLLISION")
        except OSError:
            fail(Exit.EXTRACT, "STAGE_FILE_CREATE")
        try:
            metadata = os.fstat(file_fd)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_gid != os.getgid()
                or metadata.st_nlink != 1
            ):
                fail(Exit.EXTRACT, "STAGE_FILE_POLICY")
            offset = 0
            while offset < len(payload):
                try:
                    written = os.write(file_fd, payload[offset:])
                except OSError:
                    fail(Exit.EXTRACT, "STAGE_FILE_WRITE")
                if written <= 0:
                    fail(Exit.EXTRACT, "STAGE_FILE_WRITE")
                offset += written
            os.fchmod(file_fd, mode)
            os.fsync(file_fd)
        finally:
            os.close(file_fd)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def create_stage_symlink(stage_fd: int, relative: str, link_text: str) -> None:
    parent, leaf = split_parent(relative, "STAGE_SYMLINK")
    parent_fd = open_relative_directory(stage_fd, parent, "STAGE_SYMLINK_PARENT")
    try:
        if not isinstance(link_text, str) or link_text.startswith("/") or "\\" in link_text:
            fail(Exit.BIN_LINK, "STAGE_SYMLINK_TEXT")
        resolved = posixpath.normpath(posixpath.join(TARGET_NAME, parent, link_text))
        if resolved != TARGET_NAME and not resolved.startswith(TARGET_NAME + "/"):
            fail(Exit.BIN_LINK, "STAGE_SYMLINK_ESCAPE")
        try:
            os.symlink(link_text, leaf, dir_fd=parent_fd)
        except FileExistsError:
            fail(Exit.BIN_LINK, "STAGE_SYMLINK_COLLISION")
        except OSError:
            fail(Exit.BIN_LINK, "STAGE_SYMLINK_CREATE")
        metadata = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISLNK(metadata.st_mode) or metadata.st_uid != os.getuid():
            fail(Exit.BIN_LINK, "STAGE_SYMLINK_POLICY")
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def seal_stage_directories(stage_fd: int, layout: Mapping[str, Any]) -> None:
    directories = [logical_child_path(path) for path, value in layout.items() if value[0] == "D" and path != TARGET_NAME]
    for relative in sorted(directories, key=lambda value: (-value.count("/"), value.encode("utf-8"))):
        directory_fd = open_relative_directory(stage_fd, relative, "SEAL_DIRECTORY")
        try:
            os.fchmod(directory_fd, 0o755)
            os.fsync(directory_fd)
        except OSError:
            fail(Exit.SEAL, "SEAL_DIRECTORY")
        finally:
            os.close(directory_fd)
    os.fsync(stage_fd)


def marker_bytes(key: bytes, challenge: str, receipt_digest: str) -> bytes:
    body = canonical_json(
        {
            "schema_version": "gov01-static-acquisition-incomplete-v2",
            "challenge": challenge,
            "receipt_digest": receipt_digest,
        }
    )
    return canonical_json(
        {
            "body_sha256": sha256(body),
            "hmac_sha256": hmac_frame(key, MARKER_DOMAIN, body),
            "state": "incomplete-do-not-use",
        }
    )


def fingerprint_stage_with_marker(
    stage_fd: int,
    expected_marker: bytes,
    verifier: types.ModuleType,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    layout: Dict[str, Any] = {TARGET_NAME: ("D", 0o755, 0, "-")}
    marker_seen = False
    owner_uid = os.getuid()
    owner_gid = os.getgid()
    root_meta = os.fstat(stage_fd)
    if (
        not stat.S_ISDIR(root_meta.st_mode)
        or stat.S_IMODE(root_meta.st_mode) != 0o700
        or root_meta.st_uid != owner_uid
        or root_meta.st_gid != owner_gid
    ):
        fail(Exit.POST_INSTALL, "STAGE_ROOT_POLICY")

    def walk(directory_fd: int, logical_parent: str, is_root: bool = False) -> None:
        nonlocal marker_seen
        try:
            entries = list(os.scandir(directory_fd))
        except OSError:
            fail(Exit.POST_INSTALL, "STAGE_SCAN")
        for entry in sorted(entries, key=lambda item: item.name.encode("utf-8")):
            name = entry.name
            if is_root and name == INCOMPLETE_MARKER:
                if marker_seen:
                    fail(Exit.POST_INSTALL, "STAGE_MARKER_DUPLICATE")
                marker_seen = True
                marker_fd, marker_meta = open_relative_regular(directory_fd, name, "STAGE_MARKER", len(expected_marker))
                try:
                    raw = read_fd(marker_fd, len(expected_marker), "STAGE_MARKER")
                finally:
                    os.close(marker_fd)
                if (
                    raw != expected_marker
                    or stat.S_IMODE(marker_meta.st_mode) != 0o600
                    or marker_meta.st_uid != owner_uid
                    or marker_meta.st_gid != owner_gid
                    or marker_meta.st_nlink != 1
                ):
                    fail(Exit.POST_INSTALL, "STAGE_MARKER_POLICY")
                continue
            validate_relative(name, "STAGE_ENTRY", forbid_vault=False)
            logical_path = logical_parent + "/" + name
            metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if metadata.st_uid != owner_uid or metadata.st_gid != owner_gid:
                fail(Exit.POST_INSTALL, "STAGE_ENTRY_OWNER")
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                child_fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    layout[logical_path] = ("D", mode, 0, "-")
                    walk(child_fd, logical_path)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(metadata.st_mode):
                if metadata.st_nlink != 1:
                    fail(Exit.POST_INSTALL, "STAGE_FILE_HARDLINK")
                file_fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                try:
                    digest, length = hash_fd(file_fd, "sha256", MAX_PAYLOAD_CLOSURE, "STAGE_FILE_VERIFY")
                finally:
                    os.close(file_fd)
                if length != metadata.st_size:
                    fail(Exit.POST_INSTALL, "STAGE_FILE_RACE")
                layout[logical_path] = ("F", mode, length, digest)
            elif stat.S_ISLNK(metadata.st_mode):
                try:
                    link_text = os.readlink(name, dir_fd=directory_fd)
                except OSError:
                    fail(Exit.POST_INSTALL, "STAGE_LINK_READ")
                if not isinstance(link_text, str) or link_text.startswith("/") or "\\" in link_text:
                    fail(Exit.POST_INSTALL, "STAGE_LINK_TEXT")
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(logical_path), link_text))
                if resolved != TARGET_NAME and not resolved.startswith(TARGET_NAME + "/"):
                    fail(Exit.POST_INSTALL, "STAGE_LINK_ESCAPE")
                layout[logical_path] = ("L", mode, len(link_text.encode("utf-8")), link_text)
            else:
                fail(Exit.POST_INSTALL, "STAGE_SPECIAL_FILE")

    walk(stage_fd, TARGET_NAME, is_root=True)
    if not marker_seen:
        fail(Exit.POST_INSTALL, "STAGE_MARKER_MISSING")
    try:
        tree = verifier.layout_manifest(layout)
    except Exception:
        fail(Exit.POST_INSTALL, "STAGE_LAYOUT_MANIFEST")
    return layout, tree


def materialize_stage(
    repo_fd: int,
    stage_name: str,
    marker: bytes,
    expected: Mapping[str, Any],
    payloads: Mapping[str, bytes],
    attempt: Optional[AttemptState] = None,
) -> Tuple[int, os.stat_result]:
    try:
        os.mkdir(stage_name, 0o700, dir_fd=repo_fd)
    except FileExistsError:
        fail(Exit.REPLAY, "STAGE_PREEXISTS")
    except OSError:
        fail(Exit.EXTRACT, "STAGE_CREATE")
    if attempt is not None:
        attempt.stage_directory_created()
    try:
        stage_fd = os.open(
            stage_name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=repo_fd,
        )
    except OSError:
        fail(Exit.EXTRACT, "STAGE_OPEN")
    root_meta = os.fstat(stage_fd)
    if root_meta.st_uid != os.getuid() or root_meta.st_gid != os.getgid():
        os.close(stage_fd)
        fail(Exit.EXTRACT, "STAGE_OWNER")
    try:
        os.fchmod(stage_fd, 0o700)
        write_exclusive(stage_fd, INCOMPLETE_MARKER, marker, mode=0o600)
        if attempt is not None:
            attempt.stage_marker_created()
        layout = expected.get("layout")
        if not isinstance(layout, dict):
            fail(Exit.CHECKER_DRIFT, "EXPECTED_LAYOUT_SCHEMA")
        directories = [path for path, value in layout.items() if value[0] == "D" and path != TARGET_NAME]
        for logical_path in sorted(directories, key=lambda value: (value.count("/"), value.encode("utf-8"))):
            create_stage_directory(stage_fd, logical_child_path(logical_path))
        for logical_path in sorted(payloads, key=lambda value: value.encode("utf-8")):
            frozen = layout.get(logical_path)
            if not isinstance(frozen, tuple) or frozen[0] != "F":
                fail(Exit.CHECKER_DRIFT, "EXPECTED_FILE_LAYOUT")
            write_stage_file(stage_fd, logical_child_path(logical_path), payloads[logical_path], frozen[1])
        links = [(path, value) for path, value in layout.items() if value[0] == "L"]
        for logical_path, frozen in sorted(links, key=lambda item: item[0].encode("utf-8")):
            create_stage_symlink(stage_fd, logical_child_path(logical_path), frozen[3])
        seal_stage_directories(stage_fd, layout)
        return stage_fd, root_meta
    except BaseException:
        os.close(stage_fd)
        raise


class PrivateLedger:
    def __init__(
        self,
        claim_fd: int,
        key: bytes,
        challenge: str,
        receipt_digest: str,
        expected_uid: int,
        expected_gid: int,
    ):
        self._key = key
        self._challenge = challenge
        self._receipt_digest = receipt_digest
        self._previous = "0" * 64
        self._sequence = 0
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            self._fd = os.open("ledger.jsonl", flags, 0o600, dir_fd=claim_fd)
        except FileExistsError:
            fail(Exit.REPLAY, "LEDGER_PREEXISTS")
        except OSError:
            fail(Exit.EVIDENCE, "LEDGER_CREATE")
        metadata = os.fstat(self._fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != expected_uid
            or metadata.st_gid != expected_gid
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            os.close(self._fd)
            fail(Exit.EVIDENCE, "LEDGER_POLICY")
        try:
            self.append("receipt-consumed", {"authority": "single-use-consumed-before-stage-write"})
            os.fsync(claim_fd)
        except BaseException as error:
            try:
                os.close(self._fd)
            except OSError:
                pass
            if isinstance(error, OSError):
                fail(Exit.EVIDENCE, "LEDGER_DIRECTORY_FSYNC")
            raise

    def append(self, event: str, data: Mapping[str, Any]) -> str:
        if not isinstance(event, str) or not re.fullmatch(r"[a-z0-9-]{3,64}", event):
            fail(Exit.EVIDENCE, "LEDGER_EVENT")
        base = {
            "schema_version": "gov01-static-acquisition-ledger-event-v2",
            "sequence": self._sequence,
            "at_utc": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "challenge": self._challenge,
            "receipt_digest": self._receipt_digest,
            "event": event,
            "previous_hmac_sha256": self._previous,
            "data": dict(data),
        }
        mac = hmac_frame(self._key, LEDGER_DOMAIN, canonical_json(base))
        record = dict(base)
        record["hmac_sha256"] = mac
        raw = canonical_json(record)
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(self._fd, raw[offset:])
            except OSError:
                fail(Exit.EVIDENCE, "LEDGER_WRITE")
            if written <= 0:
                fail(Exit.EVIDENCE, "LEDGER_WRITE")
            offset += written
        try:
            os.fsync(self._fd)
        except OSError:
            fail(Exit.EVIDENCE, "LEDGER_FSYNC")
        self._previous = mac
        self._sequence += 1
        return mac

    @property
    def head(self) -> str:
        return self._previous

    @property
    def sequence(self) -> int:
        return self._sequence

    def verify_terminal(self) -> Dict[str, Any]:
        try:
            os.fsync(self._fd)
            os.lseek(self._fd, 0, os.SEEK_SET)
        except OSError:
            fail(Exit.EVIDENCE, "LEDGER_VERIFY_SEEK")
        raw = read_fd(self._fd, MAX_JSON_BYTES, "LEDGER_VERIFY")
        return validate_ledger_jsonl(
            raw,
            self._key,
            self._challenge,
            self._receipt_digest,
            expected_head=self._previous,
        )

    def close(self) -> None:
        try:
            os.close(self._fd)
        except OSError:
            fail(Exit.EVIDENCE, "LEDGER_CLOSE")


def open_existing_private_container(
    parent_fd: int,
    name: str,
    expected_uid: Optional[int] = None,
    expected_gid: Optional[int] = None,
) -> int:
    validate_relative(name, "PRIVATE_CONTAINER", forbid_vault=False)
    try:
        child_fd = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except OSError:
        fail(Exit.EVIDENCE, "PRIVATE_CONTAINER_OPEN")
    try:
        assert_no_extended_acl_fd(child_fd, "PRIVATE_CONTAINER")
    except BaseException:
        os.close(child_fd)
        raise
    metadata = os.fstat(child_fd)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != (os.getuid() if expected_uid is None else expected_uid)
        or (expected_gid is not None and metadata.st_gid != expected_gid)
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        os.close(child_fd)
        fail(Exit.EVIDENCE, "PRIVATE_CONTAINER_POLICY")
    return child_fd


def private_directory_identity(metadata: os.stat_result) -> Dict[str, int]:
    return {
        "dev": metadata.st_dev,
        "ino": metadata.st_ino,
        "mode": metadata.st_mode,
        "uid": metadata.st_uid,
        "gid": metadata.st_gid,
        "nlink": metadata.st_nlink,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "flags": getattr(metadata, "st_flags", 0),
    }


def build_private_control_identity_body(
    claim_preimage: Mapping[str, Any],
    key_file: str,
) -> Dict[str, Any]:
    state_identity = claim_preimage.get("state_root")
    claims_identity = claim_preimage.get("claims")
    if not isinstance(state_identity, dict) or not isinstance(claims_identity, dict):
        fail(Exit.PRIVATE_STATE, "PRIVATE_CONTROL_PREIMAGE_SCHEMA")
    key_metadata = assert_no_symlink_components(key_file, "HMAC_KEY_IDENTITY")
    if (
        not stat.S_ISREG(key_metadata.st_mode)
        or stat.S_IMODE(key_metadata.st_mode) != 0o600
        or key_metadata.st_nlink != 1
    ):
        fail(Exit.PRIVATE_STATE, "HMAC_KEY_IDENTITY_POLICY")
    owner_uid = os.getuid()
    owner_values = (state_identity.get("uid"), claims_identity.get("uid"), key_metadata.st_uid)
    if owner_values != (owner_uid, owner_uid, owner_uid):
        fail(Exit.PRIVATE_STATE, "PRIVATE_CONTROL_OWNER")
    group_gid = state_identity.get("gid")
    if not isinstance(group_gid, int) or isinstance(group_gid, bool):
        fail(Exit.PRIVATE_STATE, "PRIVATE_CONTROL_GROUP_SCHEMA")
    if (claims_identity.get("gid"), key_metadata.st_gid) != (group_gid, group_gid):
        fail(Exit.PRIVATE_STATE, "PRIVATE_CONTROL_GROUP_MISMATCH")
    if (
        stat.S_IMODE(state_identity.get("mode", 0)) != 0o700
        or stat.S_IMODE(claims_identity.get("mode", 0)) != 0o700
    ):
        fail(Exit.PRIVATE_STATE, "PRIVATE_CONTROL_MODE")
    return {
        "schema_version": "gov01-private-control-identity-v2",
        "owner_uid": owner_uid,
        "group_gid": group_gid,
        "state_root_mode": "0700",
        "claims_mode": "0700",
        "hmac_key_mode": "0600",
        "created_claim_expected_mode": "0700",
        "created_ledger_expected_mode": "0600",
        "created_objects_inherit_claims_owner_group": True,
    }


def private_control_identity_commitment(key: bytes, body: Mapping[str, Any]) -> str:
    require_exact_object(
        body,
        (
            "schema_version owner_uid group_gid state_root_mode claims_mode hmac_key_mode "
            "created_claim_expected_mode created_ledger_expected_mode "
            "created_objects_inherit_claims_owner_group"
        ).split(),
        "PRIVATE_CONTROL_IDENTITY_BODY",
    )
    return hmac_frame(key, PRIVATE_CONTROL_IDENTITY_DOMAIN, canonical_json(body))


def compare_private_control_identity(
    envelope: Mapping[str, Any],
    actual_commitment: str,
) -> None:
    private = envelope.get("private_state_authorization")
    if not isinstance(private, dict):
        fail(Exit.CONTRACT, "PRIVATE_CONTROL_AUTHORIZATION_SCHEMA")
    expected = private.get("private_control_identity_commitment")
    if (
        not isinstance(expected, str)
        or not SHA256_RE.fullmatch(expected)
        or not hmac.compare_digest(expected, actual_commitment)
    ):
        fail(Exit.PREFLIGHT_DRIFT, "PRIVATE_CONTROL_IDENTITY_DRIFT")


def create_permanent_claim(
    state_root: str,
    key: bytes,
    challenge: str,
    receipt_digest: str,
    expected_preimage: Mapping[str, Any],
    expected_owner_uid: int,
    expected_group_gid: int,
    not_after_utc: str,
    attempt: Optional[AttemptState] = None,
    clock: Callable[[], _datetime.datetime] = utc_now,
) -> Tuple[int, PrivateLedger]:
    state_fd = open_directory(state_root, "STATE_ROOT")
    claims_fd: Optional[int] = None
    claim_fd: Optional[int] = None
    transferred = False
    try:
        state_metadata = os.fstat(state_fd)
        if private_directory_identity(state_metadata) != expected_preimage.get("state_root"):
            fail(Exit.PRE_WORKTREE_CAS, "STATE_ROOT_IDENTITY_DRIFT")
        if (
            state_metadata.st_uid != expected_owner_uid
            or state_metadata.st_gid != expected_group_gid
            or stat.S_IMODE(state_metadata.st_mode) != 0o700
        ):
            fail(Exit.PRIVATE_STATE, "STATE_ROOT_CONTROL_IDENTITY")
        # `claims` is an approved pre-existing control directory.  The challenge
        # mkdir below is therefore the first write performed by this attempt.
        claims_fd = open_existing_private_container(
            state_fd,
            "claims",
            expected_uid=expected_owner_uid,
            expected_gid=expected_group_gid,
        )
        if private_directory_identity(os.fstat(claims_fd)) != expected_preimage.get("claims"):
            fail(Exit.PRE_WORKTREE_CAS, "CLAIMS_CONTAINER_IDENTITY_DRIFT")
        claim_fd = mkdir_private_child(
            claims_fd,
            challenge,
            expected_owner_uid,
            expected_group_gid,
            before_create=lambda: assert_deadline_not_expired(not_after_utc, clock),
            on_created=(attempt.claim_directory_created if attempt is not None else None),
        )
        try:
            os.fsync(claims_fd)
        except OSError:
            fail(Exit.EVIDENCE, "CLAIM_DIRECTORY_FSYNC")
        ledger = PrivateLedger(
            claim_fd,
            key,
            challenge,
            receipt_digest,
            expected_owner_uid,
            expected_group_gid,
        )
        if attempt is not None:
            attempt.claim_created()
        transferred = True
        return claim_fd, ledger
    finally:
        if claim_fd is not None and not transferred:
            os.close(claim_fd)
        if claims_fd is not None:
            os.close(claims_fd)
        os.close(state_fd)


def verify_claim_preimage(
    state_root: str,
    challenge: str,
    expected_uid: Optional[int] = None,
    expected_gid: Optional[int] = None,
) -> Dict[str, Any]:
    state_fd = open_directory(state_root, "STATE_ROOT")
    claims_fd: Optional[int] = None
    try:
        state_metadata = os.fstat(state_fd)
        owner_uid = os.getuid() if expected_uid is None else expected_uid
        if (
            state_metadata.st_uid != owner_uid
            or (expected_gid is not None and state_metadata.st_gid != expected_gid)
            or stat.S_IMODE(state_metadata.st_mode) != 0o700
        ):
            fail(Exit.PRIVATE_STATE, "STATE_ROOT_CONTROL_POLICY")
        claims_fd = open_existing_private_container(
            state_fd,
            "claims",
            expected_uid=owner_uid,
            expected_gid=expected_gid,
        )
        observation = {
            "state_root": private_directory_identity(os.fstat(state_fd)),
            "claims": private_directory_identity(os.fstat(claims_fd)),
        }
        try:
            os.stat(challenge, dir_fd=claims_fd, follow_symlinks=False)
        except FileNotFoundError:
            return observation
        except OSError:
            fail(Exit.PRIVATE_STATE, "CHALLENGE_CLAIM_LSTAT")
        fail(Exit.REPLAY, "CHALLENGE_ALREADY_CLAIMED")
    finally:
        if claims_fd is not None:
            os.close(claims_fd)
        os.close(state_fd)


def require_host() -> None:
    if sys.version_info < (3, 9) or sys.version_info >= (4, 0):
        fail(Exit.RUNTIME, "PYTHON_VERSION")
    if sys.platform != EXPECTED_PLATFORM:
        fail(Exit.RUNTIME, "HOST_PLATFORM")
    machine = platform.machine().lower()
    if machine not in ("arm64", "aarch64"):
        fail(Exit.RUNTIME, "HOST_ARCH")


def require_same_filesystem(repo_meta: os.stat_result, state_meta: os.stat_result) -> None:
    if repo_meta.st_dev != state_meta.st_dev:
        fail(Exit.PRIVATE_STATE, "STATE_FILESYSTEM")


def verify_open_directory_identity(path: str, opened_fd: int, label: str) -> None:
    current = require_owned_directory(path, label)
    opened = os.fstat(opened_fd)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or (current.st_dev, current.st_ino, current.st_uid, current.st_gid)
        != (opened.st_dev, opened.st_ino, opened.st_uid, opened.st_gid)
    ):
        fail(Exit.PRE_WORKTREE_CAS, label + "_IDENTITY_DRIFT")


def verify_private_input_cas(
    args: argparse.Namespace,
    key: bytes,
    envelope_raw: bytes,
    receipt_digest: str,
    envelope: Mapping[str, Any],
    expected_owner_uid: int,
    expected_group_gid: int,
) -> None:
    validate_locator_boundaries(args)
    current_key = load_hmac_key(args.key_file, expected_owner_uid, expected_group_gid)
    if not hmac.compare_digest(current_key, key):
        fail(Exit.PRE_WORKTREE_CAS, "HMAC_KEY_DRIFT")
    current_envelope, current_raw, current_receipt = load_envelope(args.envelope, receipt_digest)
    if current_raw != envelope_raw or not hmac.compare_digest(current_receipt, receipt_digest):
        fail(Exit.PRE_WORKTREE_CAS, "ENVELOPE_DRIFT")
    if current_envelope.get("approval_challenge_id") != envelope.get("approval_challenge_id"):
        fail(Exit.PRE_WORKTREE_CAS, "ENVELOPE_CHALLENGE_DRIFT")
    compare_private_authorization(envelope, key, locator_commitments(args, key))


def assert_entry_absent(parent_fd: int, name: str, label: str) -> None:
    validate_relative(name, label, forbid_vault=False)
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_LSTAT")
    fail(Exit.PREFLIGHT_DRIFT, label + "_NOT_ABSENT")


def capture_control_state(repo_fd: int) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for path in PROTECTED_CONTROL_PATHS:
        fd, metadata = open_relative_regular(repo_fd, path, "PROTECTED_CONTROL", MAX_JSON_BYTES)
        try:
            opened = os.fstat(fd)
            digest, length = hash_fd(fd, "sha256", MAX_JSON_BYTES, "PROTECTED_CONTROL")
            final = os.fstat(fd)
        finally:
            os.close(fd)
        before = (
            metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid, metadata.st_gid,
            metadata.st_nlink, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns,
        )
        opened_tuple = (
            opened.st_dev, opened.st_ino, opened.st_mode, opened.st_uid, opened.st_gid,
            opened.st_nlink, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns,
        )
        final_tuple = (
            final.st_dev, final.st_ino, final.st_mode, final.st_uid, final.st_gid,
            final.st_nlink, final.st_size, final.st_mtime_ns, final.st_ctime_ns,
        )
        if before != opened_tuple or opened_tuple != final_tuple or length != metadata.st_size:
            fail(Exit.PREFLIGHT_DRIFT, "PROTECTED_CONTROL_RACE")
        result[path] = {
            "sha256": digest,
            "bytes": length,
            "mode": stat.S_IMODE(metadata.st_mode),
            "uid": metadata.st_uid,
            "gid": metadata.st_gid,
            "nlink": metadata.st_nlink,
            "mtime_ns": metadata.st_mtime_ns,
            "ctime_ns": metadata.st_ctime_ns,
        }
    return result


def assert_absent_control_paths(repo_fd: int) -> None:
    for path in ABSENT_CONTROL_PATHS:
        assert_entry_absent(repo_fd, path, "ALTERNATE_CONTROL")


def verify_control_containment(repo_fd: int, baseline: Mapping[str, Any], code: Exit) -> None:
    current = capture_control_state(repo_fd)
    compare_frozen(baseline, current, code, "PROTECTED_CONTROL_DRIFT")
    assert_absent_control_paths(repo_fd)


def compare_frozen(left: Any, right: Any, code: Exit, public_code: str) -> None:
    # Verifier layouts intentionally use immutable tuples, which are outside
    # the envelope JSON profile.  Native deep equality is exact for the closed
    # dict/list/tuple/scalar structures compared at these checkpoints.
    if left != right:
        fail(code, public_code)


def compare_git_containment(baseline: Mapping[str, Any], current: Mapping[str, Any]) -> None:
    keys = (
        "head",
        "tree",
        "object_format",
        "status_sha256",
        "status_bytes",
        "dirty_manifest_commitment",
        "refs_sha256",
        "refs_bytes",
        "index",
        "config",
        "hooks",
        "hooks_config_state",
        "git_binary_sha256",
        "commitment",
    )
    for key in keys:
        if baseline.get(key) != current.get(key):
            fail(Exit.GIT_CONTAINMENT, "GIT_CONTAINMENT_DRIFT")


def assert_deadline_not_expired(
    not_after_utc: Any,
    clock: Callable[[], _datetime.datetime] = utc_now,
) -> None:
    if clock() >= parse_utc(not_after_utc, "EXPIRY"):
        fail(Exit.EXPIRED, "ENVELOPE_EXPIRED_DURING_ATTEMPT")


def assert_envelope_not_expired(envelope: Mapping[str, Any]) -> None:
    assert_deadline_not_expired(envelope.get("not_after_utc"))


def finalize_stage_marker(
    stage_fd: int,
    expected_marker: bytes,
) -> os.stat_result:
    marker_fd, marker_meta = open_relative_regular(stage_fd, INCOMPLETE_MARKER, "FINAL_MARKER", len(expected_marker))
    try:
        raw = read_fd(marker_fd, len(expected_marker), "FINAL_MARKER")
    finally:
        os.close(marker_fd)
    if (
        raw != expected_marker
        or stat.S_IMODE(marker_meta.st_mode) != 0o600
        or marker_meta.st_uid != os.getuid()
        or marker_meta.st_gid != os.getgid()
        or marker_meta.st_nlink != 1
    ):
        fail(Exit.PRE_WORKTREE_CAS, "FINAL_MARKER_DRIFT")
    try:
        os.unlink(INCOMPLETE_MARKER, dir_fd=stage_fd)
        os.fchmod(stage_fd, 0o755)
        os.fsync(stage_fd)
    except OSError:
        fail(Exit.SEAL, "FINALIZE_STAGE")
    try:
        os.stat(INCOMPLETE_MARKER, dir_fd=stage_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    except OSError:
        fail(Exit.SEAL, "FINAL_MARKER_POSTCHECK")
    else:
        fail(Exit.SEAL, "FINAL_MARKER_REMAINS")
    return os.fstat(stage_fd)


def stable_tree_attestation(
    tree_fd: int,
    verifier: types.ModuleType,
    expected: Mapping[str, Any],
    code: Exit,
    label: str,
) -> Dict[str, Any]:
    observations = []
    for _ in range(2):
        try:
            result = verifier.fingerprint_tree_fd(tree_fd)
            if not isinstance(result, tuple) or len(result) != 2:
                fail(Exit.CHECKER_DRIFT, label + "_VERIFIER_ABI")
            layout, volatile_xattr_path_count = result
            if not isinstance(layout, dict) or not isinstance(volatile_xattr_path_count, int):
                fail(Exit.CHECKER_DRIFT, label + "_VERIFIER_RESULT")
            tree = verifier.layout_manifest(layout)
        except ContractError:
            raise
        except Exception:
            fail(code, label + "_VERIFY")
        compare_frozen(layout, expected.get("layout"), code, label + "_LAYOUT_MISMATCH")
        compare_frozen(tree, expected.get("tree"), code, label + "_TREE_MISMATCH")
        observations.append(
            {
                "layout": layout,
                "tree": tree,
                "volatile_xattr_path_count": volatile_xattr_path_count,
            }
        )
    compare_frozen(observations[0], observations[1], code, label + "_UNSTABLE")
    return observations[1]["tree"]


def renameatx_exclusive(repo_fd: int, source: str, target: str) -> None:
    validate_relative(source, "PROMOTE_SOURCE", forbid_vault=False)
    validate_relative(target, "PROMOTE_TARGET", forbid_vault=False)
    if "/" in source or "/" in target:
        fail(Exit.PROMOTE, "PROMOTE_PATH_SHAPE")
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        function = libc.renameatx_np
    except (OSError, AttributeError):
        fail(Exit.PROMOTE, "RENAMEATX_UNAVAILABLE")
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = function(repo_fd, source.encode("ascii"), repo_fd, target.encode("ascii"), RENAME_EXCL)
    if result != 0:
        fail(Exit.PROMOTE, "RENAMEATX_EXCL_FAILED")


def verify_promoted_tree(
    repo_fd: int,
    expected_inode: Tuple[int, int],
    verifier: types.ModuleType,
    expected: Mapping[str, Any],
) -> Dict[str, Any]:
    try:
        target_fd = os.open(
            TARGET_NAME,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=repo_fd,
        )
    except OSError:
        fail(Exit.POST_INSTALL, "PROMOTED_TARGET_OPEN")
    try:
        metadata = os.fstat(target_fd)
        if (metadata.st_dev, metadata.st_ino) != expected_inode or stat.S_IMODE(metadata.st_mode) != 0o755:
            fail(Exit.POST_INSTALL, "PROMOTED_TARGET_IDENTITY")
        return stable_tree_attestation(
            target_fd,
            verifier,
            expected,
            Exit.POST_INSTALL,
            "PROMOTED_TREE",
        )
    finally:
        os.close(target_fd)


def verify_envelope_preimage(envelope: Mapping[str, Any], git_state: Mapping[str, Any]) -> None:
    preimage = envelope.get("authorization_preimage")
    if not isinstance(preimage, dict):
        fail(Exit.CONTRACT, "PREIMAGE_SCHEMA")
    comparisons = (
        ("head_commit_oid", "head"),
        ("head_tree_oid", "tree"),
        ("git_object_format", "object_format"),
    )
    for envelope_key, state_key in comparisons:
        if preimage.get(envelope_key) != git_state.get(state_key):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_PREIMAGE_DRIFT")
    expected_commitment = preimage.get("git_snapshot_commitment")
    actual_commitment = git_state.get("commitment")
    if (
        not isinstance(expected_commitment, str)
        or not isinstance(actual_commitment, str)
        or not hmac.compare_digest(expected_commitment, actual_commitment)
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_SNAPSHOT_COMMITMENT_DRIFT")
    if preimage.get("node_modules_state") != "ABSENT":
        fail(Exit.CONTRACT, "NODE_MODULES_PREIMAGE")
    observed_worktree_state = "clean" if git_state.get("status_bytes") == 0 else "dirty-user-owned-do-not-normalize"
    if preimage.get("worktree_state") != observed_worktree_state:
        fail(Exit.PREFLIGHT_DRIFT, "WORKTREE_STATE_DRIFT")
    if (
        preimage.get("target_worktree_claude_sessions") != 0
        or preimage.get("forbidden_process_match_count") != 0
    ):
        fail(Exit.CONTRACT, "SESSION_PREIMAGE")


def verify_lock_contract(
    envelope: Mapping[str, Any],
    expected: Mapping[str, Any],
    count: int,
    total_bytes: int,
    bin_count: int,
    strict: bool,
) -> Dict[str, Any]:
    closure = envelope.get("lock_closure")
    success = envelope.get("success_contract")
    if not isinstance(closure, dict) or not isinstance(success, dict):
        fail(Exit.CONTRACT, "LOCK_CONTRACT_SCHEMA")
    resolution = expected.get("resolution")
    tree = expected.get("tree")
    if not isinstance(resolution, dict) or not isinstance(tree, dict):
        fail(Exit.CHECKER_DRIFT, "LOCK_EXPECTED_SCHEMA")
    if count != EXPECTED_SELECTED_PACKAGES or expected.get("selected_package_count") != count:
        fail(Exit.CACHE_LOCK, "LOCK_PACKAGE_COUNT")
    if bin_count != EXPECTED_BIN_LINKS or expected.get("bin_link_count") != bin_count:
        fail(Exit.CACHE_LOCK, "BIN_CENSUS_DRIFT")
    if total_bytes != expected.get("compressed_bytes") or total_bytes > MAX_COMPRESSED_CLOSURE:
        fail(Exit.CACHE_LOCK, "LOCK_CACHE_BYTES")
    if resolution.get("required_missing") != 0:
        fail(Exit.CACHE_LOCK, "LOCK_REQUIRED_DEPENDENCY_MISSING")
    observed = {
        "host_selected_package_count": count,
        "host_selected_cache_bytes": total_bytes,
        "host_bin_link_count": bin_count,
        "expected_archive_member_count": expected.get("raw_member_count"),
        "expected_resolved_tree_entry_count": tree.get("entry_count"),
        "content_receipt_sha256": expected.get("content_receipt_sha256"),
        "ustar_closure_sha256": expected.get("ustar_closure_sha256"),
        "resolution_receipt_sha256": resolution.get("sha256"),
        "expected_tree_sha256": tree.get("sha256"),
    }
    if strict:
        if success.get("host_package_count") != count:
            fail(Exit.CONTRACT, "LOCK_SUCCESS_COUNT")
        for key_name, value in observed.items():
            if closure.get(key_name) != value:
                fail(Exit.CACHE_LOCK, "LOCK_CLOSURE_DRIFT")
    return observed


def record_expected_closure_gates(
    recorder: GateRecorder,
    expected: Mapping[str, Any],
    lock_observation: Mapping[str, Any],
) -> None:
    resolution = expected.get("resolution")
    tree = expected.get("tree")
    if not isinstance(resolution, dict) or not isinstance(tree, dict):
        fail(Exit.CHECKER_DRIFT, "GATE_EXPECTED_SCHEMA")
    recorder.begin("G05", "source-content-receipt")
    recorder.passed(
        "G05",
        {
            "selected_package_count": lock_observation.get("host_selected_package_count"),
            "compressed_bytes": lock_observation.get("host_selected_cache_bytes"),
            "content_receipt_sha256": expected.get("content_receipt_sha256"),
        },
    )
    recorder.begin("G06", "ustar-member-receipt")
    recorder.passed(
        "G06",
        {
            "raw_member_count": expected.get("raw_member_count"),
            "ustar_closure_sha256": expected.get("ustar_closure_sha256"),
        },
    )
    recorder.begin("G07", "ustar-format-header")
    recorder.passed(
        "G07",
        {
            "parser": "custom-fixed-512-byte-ustar",
            "gzip_stream_count": 1,
            "required_zero_eoa_blocks": 2,
        },
    )
    recorder.begin("G08", "member-path-type")
    recorder.passed(
        "G08",
        {
            "accepted_member_types": ["regular-file", "directory"],
            "raw_regular_count": expected.get("raw_regular_count"),
            "raw_directory_count": expected.get("raw_directory_count"),
            "generated_symlink_count": expected.get("bin_link_count"),
            "bundled_node_modules_allowed": False,
        },
    )
    recorder.begin("G09", "resource-limits")
    recorder.passed(
        "G09",
        {
            "compressed_bytes": expected.get("compressed_bytes"),
            "payload_bytes": expected.get("payload_bytes"),
            "tar_stream_bytes": expected.get("tar_stream_bytes"),
            "limits_enforced_by_frozen_verifier": True,
        },
    )
    recorder.begin("G14", "expected-closure")
    recorder.passed(
        "G14",
        {
            "entry_count": tree.get("entry_count"),
            "file_count": tree.get("file_count"),
            "directory_count": tree.get("directory_count"),
            "symlink_count": tree.get("symlink_count"),
            "expected_tree_sha256": tree.get("sha256"),
        },
    )
    recorder.begin("G15", "resolution-receipt")
    recorder.passed(
        "G15",
        {
            "profile": "package-lock-path-closure-not-semver-proof",
            "row_count": resolution.get("row_count"),
            "required_missing": resolution.get("required_missing"),
            "allowed_missing": resolution.get("allowed_missing"),
            "resolution_receipt_sha256": resolution.get("sha256"),
        },
    )


def read_only_terminal_state() -> Dict[str, Any]:
    return {
        "challenge_state": "not-consumed-read-only",
        "claim_state": "not-created",
        "stage_state": "not-created",
        "publication_state": "not-attempted",
        "ledger_terminal_state": "not-created",
        "target_disposition": "target-absent",
    }


def authority_projection(
    retry_authorized: bool,
    public_success_attestation_allowed: bool,
    next_required_authority: str,
) -> Dict[str, Any]:
    return {
        "retry_authorized": retry_authorized,
        "public_success_attestation_allowed": public_success_attestation_allowed,
        "automatic_cleanup_authorized": False,
        "openspec_execution_allowed": False,
        "openspec_scaffold_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "next_required_authority": next_required_authority,
    }


def public_error_identity(error: BaseException) -> Tuple[Exit, str]:
    if isinstance(error, ContractError):
        return error.code, error.public_code
    if isinstance(error, KeyboardInterrupt):
        return Exit.INTERNAL, "INTERRUPTED"
    return Exit.INTERNAL, "INTERNAL_FAIL_CLOSED"


def public_exit_category(exit_value: int) -> str:
    if type(exit_value) is not int:
        fail(Exit.EVIDENCE, "PUBLIC_ERROR_EXIT_TYPE")
    try:
        category = Exit(exit_value)
    except ValueError:
        fail(Exit.EVIDENCE, "PUBLIC_ERROR_EXIT_VALUE")
    if category is Exit.OK:
        fail(Exit.EVIDENCE, "PUBLIC_ERROR_EXIT_OK")
    return category.name + "_FAIL_CLOSED"


def public_error_projection(code: Exit, detail_code: str) -> Dict[str, Any]:
    if not isinstance(code, Exit):
        fail(Exit.EVIDENCE, "PUBLIC_ERROR_CODE_TYPE")
    if not isinstance(detail_code, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", detail_code) is None:
        detail_code = "INTERNAL_FAIL_CLOSED"
        code = Exit.INTERNAL
    return {
        "code": public_exit_category(int(code)),
        "detail_code": detail_code,
        "exit": int(code),
    }


def generic_public_failure(error: BaseException, mode: str = "unknown") -> Dict[str, Any]:
    code, public_code = public_error_identity(error)
    selected_mode = mode if mode in ("census", "verify", "acquire") else "unknown"
    terminal = read_only_terminal_state()
    if selected_mode == "acquire":
        terminal["challenge_state"] = "preclaim-rejected-new-envelope-required"
    result = base_public_result(
        False,
        selected_mode,
        "entry-fail-closed",
        "failed",
        terminal,
        {
            "profile": "gov01-static-acquisition-gate-set-v2",
            "complete": False,
            "reached_gate_count": 0,
            "reached_gates": [],
            "unreached_gate_ids": [gate_id for gate_id, _ in GATE_SCOPES],
            "gate_set_receipt_sha256": None,
        },
    )
    result["authority"] = authority_projection(
        False,
        False,
        "new explicit user approval after fail-closed evidence review",
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": selected_mode == "acquire",
    }
    validate_gate_projection(result["gate_results"])
    validate_public_result_projection(result)
    return result


def read_only_failure_result(
    error: BaseException,
    mode: str,
    recorder: GateRecorder,
) -> Dict[str, Any]:
    code, public_code = public_error_identity(error)
    recorder.failed(public_code, int(code))
    gate_results = recorder.partial_projection()
    g03_records = [
        record
        for record in gate_results["reached_gates"]
        if record.get("gate_id") == "G03" and record.get("status") == "PASS"
    ]
    toolchain_context: Optional[Dict[str, Any]] = None
    trusted_authority_binding = recorder.authority_binding()
    if trusted_authority_binding is not None:
        # Read-only failure stdout intentionally carries no approval pair.  The
        # run binding is still frozen before G00 for a later success, but it is
        # not part of this failure projection's hidden checker ABI.
        trusted_authority_binding.pop("approval_challenge_id", None)
        trusted_authority_binding.pop("receipt_digest", None)
        if not trusted_authority_binding:
            trusted_authority_binding = None
    trusted_toolchain_binding = recorder.toolchain_authority_binding()
    if g03_records:
        evidence = g03_records[0].get("evidence")
        if not isinstance(evidence, Mapping):
            fail(Exit.EVIDENCE, "READ_ONLY_FAILURE_G03_EVIDENCE")
        if trusted_toolchain_binding is None:
            fail(Exit.EVIDENCE, "READ_ONLY_FAILURE_TOOLCHAIN_AUTHORITY")
        toolchain_context = dict(trusted_toolchain_binding)
        if (
            evidence.get("toolchain_set_receipt_sha256") != toolchain_context["toolchain_set_receipt_sha256"]
            or evidence.get("dynamic_closure_receipt_sha256") != toolchain_context["dynamic_closure_receipt_sha256"]
        ):
            fail(Exit.EVIDENCE, "READ_ONLY_FAILURE_TOOLCHAIN_AUTHORITY_DRIFT")
    elif trusted_toolchain_binding is not None:
        fail(Exit.EVIDENCE, "READ_ONLY_FAILURE_UNREACHED_TOOLCHAIN_AUTHORITY")
    result = base_public_result(
        False,
        mode,
        "read-only-fail-closed",
        "failed",
        read_only_terminal_state(),
        gate_results,
        toolchain_context,
    )
    result["authority"] = authority_projection(
        False,
        False,
        "new explicit user approval after fail-closed evidence review",
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": False,
    }
    validate_gate_projection(result["gate_results"])
    bound_result = AuthorityBoundPublicResult(result, trusted_authority_binding)
    validate_public_result_projection(bound_result)
    return bound_result


def observe_retained_publication_state(
    repo_fd: int,
    stage_name: str,
    attempt: AttemptState,
    promoted_by_this_attempt: bool = False,
    expected_target_inode: Optional[Tuple[int, int]] = None,
) -> None:
    """Read only the two exact authorized entries after an acquire failure."""
    def stage_uncertain(state: str, hard: bool = False) -> None:
        attempt.stage_state = state
        if hard:
            attempt.target_disposition = "unknown-user-decision-required"
        elif attempt.publication_state == "not-attempted":
            attempt.target_disposition = "target-absent-stage-retained-user-decision-required"

    target_attributed = False
    target_lookup_failed = False
    try:
        target_meta = os.stat(TARGET_NAME, dir_fd=repo_fd, follow_symlinks=False)
    except FileNotFoundError:
        target_meta = None
    except OSError:
        target_lookup_failed = True
        attempt.publication_state = "unknown-fail-closed"
        attempt.target_disposition = "unknown-user-decision-required"
        target_meta = None
    if target_meta is not None:
        if stat.S_ISDIR(target_meta.st_mode):
            observed_inode = (target_meta.st_dev, target_meta.st_ino)
            if promoted_by_this_attempt and expected_target_inode == observed_inode:
                attempt.target_promoted()
                target_attributed = True
            else:
                attempt.publication_state = "target-observed-unattributed-fail-closed"
                attempt.target_disposition = "retain-unattributed-target-user-decision-required"
        else:
            attempt.publication_state = "unexpected-target-type-fail-closed"
            attempt.target_disposition = "retain-unauthorized-target-user-decision-required"
    elif promoted_by_this_attempt and not target_lookup_failed:
        attempt.publication_state = "promoted-target-missing-fail-closed"
        attempt.target_disposition = "unknown-user-decision-required"
    try:
        stage_meta = os.stat(stage_name, dir_fd=repo_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError:
        stage_uncertain("unknown-fail-closed", hard=True)
        return
    if not stat.S_ISDIR(stage_meta.st_mode):
        stage_uncertain("unexpected-stage-type-fail-closed", hard=True)
        return
    if target_attributed:
        attempt.publication_state = "attributed-target-and-stage-both-observed-fail-closed"
        attempt.target_disposition = "retain-unauthorized-target-user-decision-required"
    attempt.stage_directory_created()
    observed_stage_fd: Optional[int] = None
    try:
        try:
            observed_stage_fd = os.open(
                stage_name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=repo_fd,
            )
        except OSError:
            stage_uncertain("retained-marker-state-unknown")
            return
        try:
            marker_meta = os.stat(INCOMPLETE_MARKER, dir_fd=observed_stage_fd, follow_symlinks=False)
        except FileNotFoundError:
            observed_mode = stat.S_IMODE(os.fstat(observed_stage_fd).st_mode)
            if observed_mode == 0o700:
                # mkdir succeeded but the incomplete marker was never created.
                attempt.stage_directory_created()
            elif observed_mode == 0o755:
                attempt.stage_marker_removed()
            else:
                stage_uncertain("retained-marker-state-unknown")
            return
        except OSError:
            stage_uncertain("retained-marker-state-unknown")
            return
        if stat.S_ISREG(marker_meta.st_mode):
            attempt.stage_marker_created()
        else:
            stage_uncertain("retained-marker-unexpected-type")
    except OSError:
        stage_uncertain("retained-marker-state-unknown")
    finally:
        if observed_stage_fd is not None:
            os.close(observed_stage_fd)


def ledger_public_evidence(report: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "checker_interface": report.get("checker_interface"),
        "record_count": report.get("record_count"),
        "terminal_kind": report.get("terminal_kind"),
        "head_hmac_sha256": report.get("head_hmac_sha256"),
        "raw_sha256": report.get("raw_sha256"),
        "raw_bytes": report.get("raw_bytes"),
    }


def recover_terminal_success_report(
    ledger: Any,
    last_verified_report: Optional[Mapping[str, Any]],
    attempt: AttemptState,
) -> Optional[Dict[str, Any]]:
    """Recover a durable success without erasing an earlier verified report.

    The second verification is useful drift detection, but it is not allowed
    to rewrite history: once this process has completely verified the six-line
    success ledger, a later read failure means inspection is required, not that
    the success ledger, consumed challenge, or published target never existed.
    """

    possible_terminal: Optional[Mapping[str, Any]] = None
    try:
        observed = ledger.verify_terminal()
    except BaseException:
        if isinstance(last_verified_report, Mapping):
            possible_terminal = last_verified_report
    else:
        if isinstance(observed, Mapping):
            possible_terminal = observed
    if (
        not isinstance(possible_terminal, Mapping)
        or possible_terminal.get("checker_interface") != LEDGER_CHECKER_INTERFACE
        or possible_terminal.get("terminal_kind") != "success"
        or type(possible_terminal.get("record_count")) is not int
        or possible_terminal.get("record_count") != 6
        or not isinstance(possible_terminal.get("head_hmac_sha256"), str)
        or SHA256_RE.fullmatch(possible_terminal["head_hmac_sha256"]) is None
    ):
        attempt.ledger_invalid()
        return None
    recovered = copy.deepcopy(dict(possible_terminal))
    attempt.terminal_success_publication_failed()
    return recovered


def acquire_failure_result(
    error: BaseException,
    attempt: AttemptState,
    recorder: GateRecorder,
    challenge: Optional[str],
    receipt_digest: Optional[str],
    toolchain: Optional[Mapping[str, Any]],
    ledger_report: Optional[Mapping[str, Any]],
    gate_results: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    code, public_code = public_error_identity(error)
    selected_gate_results = recorder.partial_projection() if gate_results is None else dict(gate_results)
    g03_passed = any(
        isinstance(record, Mapping)
        and record.get("gate_id") == "G03"
        and record.get("status") == "PASS"
        for record in selected_gate_results.get("reached_gates", [])
    )
    trusted_authority_binding = recorder.authority_binding()
    trusted_toolchain_binding = recorder.toolchain_authority_binding() if g03_passed else None
    if g03_passed:
        if trusted_toolchain_binding is None or toolchain is None:
            fail(Exit.EVIDENCE, "ACQUIRE_FAILURE_TOOLCHAIN_AUTHORITY")
        for receipt_name in ("toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256"):
            if toolchain.get(receipt_name) != trusted_toolchain_binding.get(receipt_name):
                fail(Exit.EVIDENCE, "ACQUIRE_FAILURE_TOOLCHAIN_AUTHORITY_DRIFT")
    result = base_public_result(
        False,
        "acquire",
        attempt.phase,
        "failed",
        attempt.failure_projection(),
        selected_gate_results,
        trusted_toolchain_binding,
    )
    if (
        isinstance(challenge, str)
        and CHALLENGE_RE.fullmatch(challenge)
        and isinstance(receipt_digest, str)
        and SHA256_RE.fullmatch(receipt_digest)
    ):
        result["approval_challenge_id"] = challenge
        result["receipt_digest"] = receipt_digest
    result["authority"] = authority_projection(
        False,
        False,
        "new explicit user approval after retained-state inspection; never retry automatically",
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": attempt.claim_state != "not-created",
    }
    if ledger_report is not None:
        result["ledger_evidence"] = ledger_public_evidence(ledger_report)
    validate_gate_projection(result["gate_results"])
    failure_authority_binding = (
        None if trusted_authority_binding is None else copy.deepcopy(dict(trusted_authority_binding))
    )
    if ledger_report is not None:
        if failure_authority_binding is None:
            fail(Exit.EVIDENCE, "ACQUIRE_FAILURE_LEDGER_WITHOUT_AUTHORITY")
        failure_authority_binding["ledger_evidence"] = ledger_public_evidence(ledger_report)
    bound_result = AuthorityBoundPublicResult(result, failure_authority_binding)
    validate_public_result_projection(bound_result)
    return bound_result


def close_acquire_resources(
    stage_fd: Optional[int],
    ledger: Optional[PrivateLedger],
    claim_fd: Optional[int],
    cache_fd: int,
    repo_fd: int,
) -> int:
    """Best-effort descriptor finalization that never exposes exception text."""
    close_error_count = 0
    if stage_fd is not None:
        try:
            os.close(stage_fd)
        except BaseException:
            close_error_count += 1
    if ledger is not None:
        try:
            ledger.close()
        except BaseException:
            close_error_count += 1
    if claim_fd is not None:
        try:
            os.close(claim_fd)
        except BaseException:
            close_error_count += 1
    for opened_fd in (cache_fd, repo_fd):
        try:
            os.close(opened_fd)
        except BaseException:
            close_error_count += 1
    return close_error_count


def resource_finalization_failure_result(
    attempt: AttemptState,
    recorder: GateRecorder,
    challenge: Optional[str],
    receipt_digest: Optional[str],
    toolchain: Optional[Mapping[str, Any]],
    ledger_report: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    attempt.terminal_success_publication_failed()
    attempt.set_phase("resource-finalization")
    close_error = ContractError(Exit.EVIDENCE, "RESOURCE_FINALIZATION_CLOSE")
    payload = acquire_failure_result(
        close_error,
        attempt,
        recorder,
        challenge,
        receipt_digest,
        toolchain,
        ledger_report,
        gate_results=recorder.complete_projection(),
    )
    validate_public_result_projection(payload)
    return payload


def recover_linearized_success(
    recorder: GateRecorder,
    committed_candidate: Optional[AuthorityBoundPublicResult],
) -> Optional[AuthorityBoundPublicResult]:
    """Return a prevalidated success only after all 25 live PASS receipts exist."""
    if committed_candidate is None:
        return None
    try:
        committed_gate_results = recorder.complete_projection()
    except BaseException:
        return None
    if committed_gate_results != committed_candidate.get("gate_results"):
        return None
    validate_public_result_projection(committed_candidate)
    return committed_candidate


def build_census(
    args: argparse.Namespace,
    strict: bool,
    recorder: Optional[GateRecorder] = None,
) -> Dict[str, Any]:
    if recorder is None:
        recorder = GateRecorder()
    require_python_isolation()
    require_host()
    validate_locator_boundaries(args)
    if strict and args.receipt_digest is None:
        fail(Exit.RECEIPT, "APPROVED_RECEIPT_REQUIRED")
    repo_meta = require_owned_directory(args.repo_root, "REPO_ROOT")
    state_meta = require_owned_directory(args.state_root, "STATE_ROOT", exact_mode=0o700)
    require_same_filesystem(repo_meta, state_meta)
    require_owned_directory(args.cache_root, "CACHE_ROOT")
    key = load_hmac_key(args.key_file)
    envelope, _envelope_raw, receipt_digest = load_envelope(
        args.envelope,
        args.receipt_digest if strict else None,
    )
    challenge = envelope.get("approval_challenge_id")
    recorder.bind_run_authority(challenge, receipt_digest)
    stage_name = ".gov01-toolchain-stage-" + str(challenge)
    exclusions = (stage_name, TARGET_NAME)
    repo_fd = open_directory(args.repo_root, "REPO_ROOT")
    cache_fd = open_directory(args.cache_root, "CACHE_ROOT")
    try:
        # The bound schema and manual critical field set are checked before any
        # verifier source is compiled or any external evidence command runs.
        recorder.begin("G00", "schema-contract")
        schema_observation = verify_bound_schema_artifact(repo_fd, envelope)
        validate_manual_envelope_contract(envelope)
        artifacts = verify_artifacts(repo_fd, envelope)
        schema_bundle = verify_projection_schema_bundle(repo_fd, artifacts, schema_observation)
        public_schema_observation = dict(schema_observation)
        public_schema_observation.update(
            {
                "schema_count": schema_bundle["schema_count"],
                "schema_bundle_receipt_sha256": schema_bundle["schema_bundle_receipt_sha256"],
            }
        )
        recorder.passed_with_authority(
            "G00",
            {
                "schema_sha256": schema_observation["sha256"],
                "schema_bytes": schema_observation["bytes"],
                "schema_count": schema_bundle["schema_count"],
                "schema_bundle_receipt_sha256": schema_bundle["schema_bundle_receipt_sha256"],
                "manual_critical_contract_passed": True,
            },
            "schema",
            public_schema_observation,
        )
        recorder.begin("G02", "private-public-boundary")
        locators = locator_commitments(args, key)
        if strict:
            compare_private_authorization(envelope, key, locators)
        claim_preimage = verify_claim_preimage(args.state_root, str(challenge))
        control_identity_body = build_private_control_identity_body(claim_preimage, args.key_file)
        control_identity_receipt = private_control_identity_commitment(key, control_identity_body)
        if strict:
            compare_private_control_identity(envelope, control_identity_receipt)
        recorder.passed_with_authority(
            "G02",
            {
                "authorized_locator_commitment_count": len(locators),
                "private_control_identity_commitment": control_identity_receipt,
                "private_locator_public_count": 0,
                "private_vault_read_count": 0,
            },
            "private",
            {
                "private_control_identity_commitment": control_identity_receipt,
                "hmac_key_id": hmac_key_id(key),
                "authorized_locator_commitments": locators,
            },
        )
        recorder.begin("G10", "control-root-before")
        control_state = capture_control_state(repo_fd)
        assert_absent_control_paths(repo_fd)
        recorder.passed(
            "G10",
            {
                "protected_control_count": len(control_state),
                "absent_alternate_control_count": len(ABSENT_CONTROL_PATHS),
            },
        )
        recorder.begin("G03", "content-addressed-toolchain")
        toolchain = verify_runtime_toolchain(args.repo_root, envelope, artifacts, strict=strict)
        verifier = load_bound_verifier(repo_fd, artifacts)
        recorder.passed_with_authority(
            "G03",
            {
                "toolchain_role_count": len(toolchain["entries"]),
                "toolchain_set_receipt_sha256": toolchain["toolchain_set_receipt_sha256"],
                "dynamic_closure_receipt_sha256": toolchain["dynamic_closure_receipt_sha256"],
                "assurance": toolchain["assurance"],
                "pre_exec_launcher_attested": False,
            },
            "toolchain",
            toolchain,
        )
        recorder.begin("G11", "target-preimage")
        require_node_modules_absent(args.repo_root)
        assert_entry_absent(repo_fd, stage_name, "CENSUS_STAGE")
        recorder.passed("G11", {"target_absent": True, "stage_absent": True})
        git_state = git_snapshot(
            args.repo_root,
            key,
            toolchain["git_binary"],
            authorized_excludes=exclusions,
        )
        if strict:
            verify_envelope_preimage(envelope, git_state)
        recorder.begin("G12", "process-census-before")
        processes = process_census(
            args.repo_root,
            key,
            toolchain["pgrep_binary"],
            toolchain["lsof_binary"],
        )
        if processes["claude_session_count"] != 0:
            fail(Exit.PREFLIGHT_DRIFT, "ACTIVE_CLAUDE_SESSION")
        recorder.passed(
            "G12",
            {
                "candidate_count": processes["candidate_count"],
                "target_worktree_claude_sessions": processes["claude_session_count"],
                "pgrep_sha256": processes["pgrep_sha256"],
                "candidate_lsof_sha256": processes["candidate_lsof_sha256"],
            },
        )
        recorder.begin("G04", "authorized-child-process-static-structural-ceiling")
        recorder.passed(
            "G04",
            {
                "authorized_subprocess_role_count": len(TOOLCHAIN_ROLES[4:]),
                "shell_allowed": False,
                "network_capable_child_authorized": False,
                "authorized_network_call_site_invocation_count": 0,
                "runtime_network_syscall_observation_available": False,
                "assurance": "static-structural-self-attestation-not-syscall-observation",
            },
        )
        lock, lock_raw, _ = read_json_relative(repo_fd, "package-lock.json", "PACKAGE_LOCK")
        if not isinstance(lock, dict):
            fail(Exit.CACHE_LOCK, "LOCK_ROOT")
        selected = selected_lock_entries(lock)
        cache_manifest, bins, total_bytes = cache_census(cache_fd, selected)
        try:
            expected = verifier.build_expected(args.repo_root, args.cache_root, retain_bytes=False)
        except Exception:
            fail(Exit.ARCHIVE, "STATIC_VERIFIER_BUILD")
        if not isinstance(expected, dict):
            fail(Exit.CHECKER_DRIFT, "STATIC_VERIFIER_RESULT")
        derived_stage = validate_static_contract(
            envelope,
            verifier,
            expected,
            artifacts,
            strict_expected=strict,
        )
        if derived_stage != stage_name:
            fail(Exit.CONTRACT, "STATIC_STAGE_DERIVATION")
        lock_observation = verify_lock_contract(
            envelope,
            expected,
            len(selected),
            total_bytes,
            len(bins),
            strict=strict,
        )
        record_expected_closure_gates(recorder, expected, lock_observation)
        artifact_receipt = public_artifact_set_receipt(artifacts)
        if strict:
            frozen_artifact_receipt = envelope["authorization_preimage"].get(
                "public_repo_artifact_set_receipt_sha256"
            )
            if not isinstance(frozen_artifact_receipt, str) or not hmac.compare_digest(
                frozen_artifact_receipt,
                artifact_receipt,
            ):
                fail(Exit.PREFLIGHT_DRIFT, "PUBLIC_ARTIFACT_SET_RECEIPT")
        preapproval_body = build_private_preapproval_body(
            envelope,
            key,
            locators,
            control_identity_receipt,
            artifact_receipt,
            git_state,
            toolchain,
            lock_raw,
            processes,
            len(selected),
            total_bytes,
            len(bins),
            expected,
        )
        preapproval_commitment = private_preapproval_commitment(key, preapproval_body)
        if strict:
            compare_private_preapproval(envelope, preapproval_commitment)
        verify_control_containment(repo_fd, control_state, Exit.PREFLIGHT_DRIFT)
    finally:
        os.close(cache_fd)
        os.close(repo_fd)
    del cache_manifest
    mode = "verify" if strict else "census"
    state = "preconditions-reverified-read-only" if strict else "read-only-preapproval-census"
    result = base_public_result(
        True,
        mode,
        state + "-complete",
        state,
        read_only_terminal_state(),
        recorder.partial_projection(),
        toolchain,
    )
    result["approval_challenge_id"] = challenge
    result["receipt_digest"] = receipt_digest
    result["authority"] = authority_projection(
        True,
        False,
        "exact user-approved acquisition receipt and challenge required before any mutation",
    )
    result["observation"] = {
        "selected_packages": len(selected),
        "selected_cache_bytes": total_bytes,
        "bin_links": len(bins),
        "claude_sessions": processes["claude_session_count"],
        "hmac_key_id": hmac_key_id(key),
        "authorized_locator_commitments": locators,
        "private_control_identity_commitment": control_identity_receipt,
        "schema_binding_observation": public_schema_observation,
        "public_repo_artifact_set_receipt_sha256": artifact_receipt,
        "git_snapshot_commitment": git_state["commitment"],
        "toolchain_set_receipt_sha256": toolchain["toolchain_set_receipt_sha256"],
        "dynamic_closure_receipt_sha256": toolchain["dynamic_closure_receipt_sha256"],
        "toolchain_hashes": {
            entry["role"]: entry["raw_digest_sha256"] for entry in toolchain["entries"]
        },
        "package_lock_raw_sha256": sha256(lock_raw),
        "lock_closure_observed": lock_observation,
        "static_expected": verifier.public_summary(expected),
        "private_preapproval_commitment": preapproval_commitment,
    }
    validate_gate_projection(result["gate_results"])
    public_authority_binding = completed_public_authority_binding(recorder, {
        "toolchain_hashes": result["observation"]["toolchain_hashes"],
        "public_repo_artifact_set_receipt_sha256": artifact_receipt,
        "git_snapshot_commitment": git_state["commitment"],
        "private_preapproval_commitment": preapproval_commitment,
        "package_lock_raw_sha256": sha256(lock_raw),
    })
    bound_result = AuthorityBoundPublicResult(result, public_authority_binding)
    validate_public_result_projection(bound_result)
    return bound_result


def command_census(args: argparse.Namespace) -> Dict[str, Any]:
    recorder = GateRecorder()
    try:
        return build_census(args, strict=False, recorder=recorder)
    except BaseException as error:
        code, public_code = public_error_identity(error)
        payload = read_only_failure_result(error, "census", recorder)
        raise ContractError(code, public_code, payload) from None


def command_verify(args: argparse.Namespace) -> Dict[str, Any]:
    recorder = GateRecorder()
    try:
        return build_census(args, strict=True, recorder=recorder)
    except BaseException as error:
        code, public_code = public_error_identity(error)
        payload = read_only_failure_result(error, "verify", recorder)
        raise ContractError(code, public_code, payload) from None


def command_acquire(args: argparse.Namespace) -> Dict[str, Any]:
    attempt = AttemptState()
    recorder = GateRecorder()
    challenge: Optional[str] = (
        args.approval_challenge
        if isinstance(args.approval_challenge, str) and CHALLENGE_RE.fullmatch(args.approval_challenge)
        else None
    )
    receipt_digest: Optional[str] = (
        args.receipt_digest
        if isinstance(args.receipt_digest, str) and SHA256_RE.fullmatch(args.receipt_digest)
        else None
    )
    baseline_toolchain: Optional[Dict[str, Any]] = None
    schema_observation: Optional[Dict[str, Any]] = None
    artifact_receipt: Optional[str] = None
    preapproval_commitment: Optional[str] = None
    control_identity_receipt: Optional[str] = None
    lock_observation: Optional[Dict[str, Any]] = None
    expected_public: Optional[Dict[str, Any]] = None
    attempt.set_phase("host-and-private-arguments")
    require_python_isolation()
    require_host()
    validate_locator_boundaries(args)
    if args.receipt_digest is None:
        fail(Exit.RECEIPT, "APPROVED_RECEIPT_REQUIRED")
    repo_meta = require_owned_directory(args.repo_root, "REPO_ROOT")
    state_meta = require_owned_directory(args.state_root, "STATE_ROOT", exact_mode=0o700)
    require_same_filesystem(repo_meta, state_meta)
    require_owned_directory(args.cache_root, "CACHE_ROOT")
    key = load_hmac_key(args.key_file)
    envelope, envelope_raw, receipt_digest = load_envelope(args.envelope, args.receipt_digest)
    challenge = envelope.get("approval_challenge_id")
    if args.approval_challenge != challenge:
        fail(Exit.RECEIPT, "APPROVAL_CHALLENGE_MISMATCH")
    preliminary_stage = ".gov01-toolchain-stage-" + str(challenge)
    validate_relative(preliminary_stage, "STATIC_STAGE")
    exclusions = (preliminary_stage, TARGET_NAME)

    repo_fd = open_directory(args.repo_root, "REPO_ROOT")
    cache_fd = open_directory(args.cache_root, "CACHE_ROOT")
    claim_fd: Optional[int] = None
    stage_fd: Optional[int] = None
    ledger: Optional[PrivateLedger] = None
    last_ledger_report: Optional[Dict[str, Any]] = None
    promoted = False
    promoted_inode: Optional[Tuple[int, int]] = None
    committed_success_candidate: Optional[AuthorityBoundPublicResult] = None
    returning_linearized_success = False
    attempt.set_phase("schema-contract")
    recorder.bind_run_authority(challenge, receipt_digest)
    try:
        # No verifier source is compiled and no child is started until the
        # receipt-bound schema and manual critical contract have passed.
        recorder.begin("G00", "schema-contract")
        schema_observation = verify_bound_schema_artifact(repo_fd, envelope)
        validate_manual_envelope_contract(envelope)
        baseline_artifacts = verify_artifacts(repo_fd, envelope)
        schema_bundle = verify_projection_schema_bundle(repo_fd, baseline_artifacts, schema_observation)
        public_schema_observation = dict(schema_observation)
        public_schema_observation.update(
            {
                "schema_count": schema_bundle["schema_count"],
                "schema_bundle_receipt_sha256": schema_bundle["schema_bundle_receipt_sha256"],
            }
        )
        recorder.passed_with_authority(
            "G00",
            {
                "schema_sha256": schema_observation["sha256"],
                "schema_bytes": schema_observation["bytes"],
                "schema_count": schema_bundle["schema_count"],
                "schema_bundle_receipt_sha256": schema_bundle["schema_bundle_receipt_sha256"],
                "manual_critical_contract_passed": True,
            },
            "schema",
            public_schema_observation,
        )
        attempt.set_phase("private-public-boundary")
        recorder.begin("G02", "private-public-boundary")
        locators = locator_commitments(args, key)
        compare_private_authorization(envelope, key, locators)
        baseline_claim_preimage = verify_claim_preimage(args.state_root, str(challenge))
        control_identity_body = build_private_control_identity_body(baseline_claim_preimage, args.key_file)
        control_identity_receipt = private_control_identity_commitment(key, control_identity_body)
        compare_private_control_identity(envelope, control_identity_receipt)
        recorder.passed_with_authority(
            "G02",
            {
                "authorized_locator_commitment_count": len(locators),
                "private_control_identity_commitment": control_identity_receipt,
                "private_locator_public_count": 0,
                "private_vault_read_count": 0,
            },
            "private",
            {
                "private_control_identity_commitment": control_identity_receipt,
                "hmac_key_id": hmac_key_id(key),
                "authorized_locator_commitments": locators,
            },
        )
        attempt.set_phase("control-root-before")
        recorder.begin("G10", "control-root-before")
        baseline_controls = capture_control_state(repo_fd)
        assert_absent_control_paths(repo_fd)
        recorder.passed(
            "G10",
            {
                "protected_control_count": len(baseline_controls),
                "absent_alternate_control_count": len(ABSENT_CONTROL_PATHS),
            },
        )
        attempt.set_phase("content-addressed-toolchain")
        recorder.begin("G03", "content-addressed-toolchain")
        baseline_toolchain = verify_runtime_toolchain(
            args.repo_root,
            envelope,
            baseline_artifacts,
            strict=True,
        )
        verifier = load_bound_verifier(repo_fd, baseline_artifacts)
        recorder.passed_with_authority(
            "G03",
            {
                "toolchain_role_count": len(baseline_toolchain["entries"]),
                "toolchain_set_receipt_sha256": baseline_toolchain["toolchain_set_receipt_sha256"],
                "dynamic_closure_receipt_sha256": baseline_toolchain["dynamic_closure_receipt_sha256"],
                "assurance": baseline_toolchain["assurance"],
                "pre_exec_launcher_attested": False,
            },
            "toolchain",
            baseline_toolchain,
        )
        attempt.set_phase("git-preimage")
        baseline_git = git_snapshot(
            args.repo_root,
            key,
            baseline_toolchain["git_binary"],
            authorized_excludes=exclusions,
        )
        verify_envelope_preimage(envelope, baseline_git)
        attempt.set_phase("process-census-before")
        recorder.begin("G12", "process-census-before")
        baseline_processes = process_census(
            args.repo_root,
            key,
            baseline_toolchain["pgrep_binary"],
            baseline_toolchain["lsof_binary"],
        )
        if baseline_processes["claude_session_count"] != 0:
            fail(Exit.PREFLIGHT_DRIFT, "ACTIVE_CLAUDE_SESSION")
        recorder.passed(
            "G12",
            {
                "candidate_count": baseline_processes["candidate_count"],
                "target_worktree_claude_sessions": baseline_processes["claude_session_count"],
                "pgrep_sha256": baseline_processes["pgrep_sha256"],
                "candidate_lsof_sha256": baseline_processes["candidate_lsof_sha256"],
            },
        )
        recorder.begin("G04", "authorized-child-process-static-structural-ceiling")
        recorder.passed(
            "G04",
            {
                "authorized_subprocess_role_count": len(TOOLCHAIN_ROLES[4:]),
                "shell_allowed": False,
                "network_capable_child_authorized": False,
                "authorized_network_call_site_invocation_count": 0,
                "runtime_network_syscall_observation_available": False,
                "assurance": "static-structural-self-attestation-not-syscall-observation",
            },
        )
        attempt.set_phase("target-preimage")
        recorder.begin("G11", "target-preimage")
        assert_entry_absent(repo_fd, TARGET_NAME, "TARGET")
        assert_entry_absent(repo_fd, preliminary_stage, "STAGE")
        recorder.passed("G11", {"target_absent": True, "stage_absent": True})

        attempt.set_phase("cache-and-expected-closure")
        lock, lock_raw, _ = read_json_relative(repo_fd, "package-lock.json", "PACKAGE_LOCK")
        if not isinstance(lock, dict):
            fail(Exit.CACHE_LOCK, "LOCK_ROOT")
        selected = selected_lock_entries(lock)
        baseline_cache, baseline_bins, baseline_cache_bytes = cache_census(cache_fd, selected)
        try:
            expected = verifier.build_expected(args.repo_root, args.cache_root, retain_bytes=True)
        except Exception:
            fail(Exit.ARCHIVE, "STATIC_VERIFIER_BUILD")
        if not isinstance(expected, dict):
            fail(Exit.CHECKER_DRIFT, "STATIC_VERIFIER_RESULT")
        stage_name = validate_static_contract(envelope, verifier, expected, baseline_artifacts)
        if stage_name != preliminary_stage:
            fail(Exit.CONTRACT, "STATIC_STAGE_DERIVATION")
        lock_observation = verify_lock_contract(
            envelope,
            expected,
            len(selected),
            baseline_cache_bytes,
            len(baseline_bins),
            strict=True,
        )
        record_expected_closure_gates(recorder, expected, lock_observation)
        expected_public = verifier.public_summary(expected)
        artifact_receipt = public_artifact_set_receipt(baseline_artifacts)
        frozen_artifact_receipt = envelope["authorization_preimage"].get(
            "public_repo_artifact_set_receipt_sha256"
        )
        if not isinstance(frozen_artifact_receipt, str) or not hmac.compare_digest(
            frozen_artifact_receipt,
            artifact_receipt,
        ):
            fail(Exit.PREFLIGHT_DRIFT, "PUBLIC_ARTIFACT_SET_RECEIPT")
        preapproval_body = build_private_preapproval_body(
            envelope,
            key,
            locators,
            control_identity_receipt,
            artifact_receipt,
            baseline_git,
            baseline_toolchain,
            lock_raw,
            baseline_processes,
            len(selected),
            baseline_cache_bytes,
            len(baseline_bins),
            expected,
        )
        preapproval_commitment = private_preapproval_commitment(key, preapproval_body)
        compare_private_preapproval(envelope, preapproval_commitment)
        verify_open_directory_identity(args.repo_root, repo_fd, "REPO_ROOT")
        verify_open_directory_identity(args.cache_root, cache_fd, "CACHE_ROOT")

        # Both compressed SRI blobs and all extracted payload bytes stay strongly
        # referenced in memory before the permanent claim or any stage write.
        compressed_blobs, payloads = freeze_expected_bytes(cache_fd, expected)
        if len(compressed_blobs) != expected.get("selected_package_count"):
            fail(Exit.CACHE_LOCK, "COMPRESSED_MEMORY_CLOSURE")
        if sum(len(value) for value in payloads.values()) != expected.get("payload_bytes"):
            fail(Exit.ARCHIVE, "PAYLOAD_MEMORY_CLOSURE")
        verify_private_input_cas(
            args, key, envelope_raw, receipt_digest, envelope,
            control_identity_body["owner_uid"], control_identity_body["group_gid"],
        )
        verify_control_containment(repo_fd, baseline_controls, Exit.PRE_WORKTREE_CAS)
        verify_open_directory_identity(args.repo_root, repo_fd, "REPO_ROOT")
        verify_open_directory_identity(args.cache_root, cache_fd, "CACHE_ROOT")
        assert_envelope_not_expired(envelope)

        attempt.set_phase("persistent-claim")
        recorder.begin("G01", "single-use-authorization-ledger")
        claim_fd, ledger = create_permanent_claim(
            args.state_root,
            key,
            challenge,
            receipt_digest,
            baseline_claim_preimage,
            control_identity_body["owner_uid"],
            control_identity_body["group_gid"],
            envelope["not_after_utc"],
            attempt=attempt,
        )
        recorder.passed(
            "G01",
            {
                "challenge_claim_created": True,
                "ledger_receipt_consumed_recorded": True,
                "first_authorized_write_contract": "exclusive-0700-challenge-mkdir",
            },
        )
        ledger.append(
            "preflight-frozen",
            {
                "envelope_raw_sha256": sha256(envelope_raw),
                "artifact_manifest_commitment": hmac_frame(
                    key, b"CLS/GOV01/ARTIFACT-MANIFEST/v2", canonical_json(baseline_artifacts)
                ),
                "git_commitment": baseline_git["commitment"],
                "cache_manifest_commitment": hmac_frame(
                    key, b"CLS/GOV01/CACHE-MANIFEST/v2", canonical_json(baseline_cache)
                ),
                "selected_package_count": len(compressed_blobs),
                "compressed_bytes": sum(len(value) for value in compressed_blobs.values()),
                "payload_bytes": sum(len(value) for value in payloads.values()),
                "tree_sha256": expected["tree"]["sha256"],
                "network_attempt_count": 0,
                "lifecycle_execution_count": 0,
                "installed_code_execution_count": 0,
            },
        )

        # The permanent claim already exists, so a drift here is recorded as a
        # consumed terminal attempt.  No stage/target write has occurred yet.
        claimed_toolchain = verify_runtime_toolchain(
            args.repo_root,
            envelope,
            baseline_artifacts,
            strict=True,
        )
        compare_frozen(
            baseline_toolchain,
            claimed_toolchain,
            Exit.PRE_WORKTREE_CAS,
            "POST_CLAIM_TOOLCHAIN_DRIFT",
        )

        attempt.set_phase("stage-materialization")
        recorder.begin("G13", "stage-scope-device")
        incomplete = marker_bytes(key, challenge, receipt_digest)
        stage_fd, stage_preimage = materialize_stage(
            repo_fd,
            stage_name,
            incomplete,
            expected,
            payloads,
            attempt=attempt,
        )
        attempt.stage_created()
        recorder.passed(
            "G13",
            {
                "same_filesystem": stage_preimage.st_dev == repo_meta.st_dev,
                "stage_root_mode": "0700",
                "incomplete_marker_present": True,
                "stage_entry_write_scope_exact": True,
            },
        )
        ledger.append(
            "stage-materialized",
            {
                "file_count": expected["tree"]["file_count"],
                "directory_count": expected["tree"]["directory_count"],
                "symlink_count": expected["tree"]["symlink_count"],
                "tree_sha256": expected["tree"]["sha256"],
                "incomplete_marker_present": True,
            },
        )
        attempt.set_phase("stage-tree-attestation")
        recorder.begin("G16", "stage-tree-merkle")
        staged_layout, staged_tree = fingerprint_stage_with_marker(stage_fd, incomplete, verifier)
        compare_frozen(staged_layout, expected.get("layout"), Exit.POST_INSTALL, "STAGED_LAYOUT_MISMATCH")
        compare_frozen(staged_tree, expected.get("tree"), Exit.POST_INSTALL, "STAGED_TREE_MISMATCH")
        recorder.passed(
            "G16",
            {
                "tree_sha256": staged_tree["sha256"],
                "entry_count": staged_tree["entry_count"],
                "incomplete_marker_excluded_from_tree": True,
                "double_stable_fingerprint_required_before_publication": True,
            },
        )
        recorder.begin("G17", "payload-and-lifecycle-static-structural-ceiling")
        recorder.passed(
            "G17",
            {
                "authorized_payload_execution_call_site_invocation_count": 0,
                "authorized_lifecycle_execution_call_site_invocation_count": 0,
                "authorized_installed_code_call_site_invocation_count": 0,
                "authorized_node_npm_npx_call_site_invocation_count": 0,
                "runtime_exec_syscall_observation_available": False,
                "assurance": "static-structural-self-attestation-not-syscall-observation",
            },
        )

        # Full CAS immediately before marker removal and promotion.
        attempt.set_phase("pre-promotion-cas")
        assert_envelope_not_expired(envelope)
        verify_private_input_cas(
            args, key, envelope_raw, receipt_digest, envelope,
            control_identity_body["owner_uid"], control_identity_body["group_gid"],
        )
        verify_open_directory_identity(args.repo_root, repo_fd, "REPO_ROOT")
        verify_open_directory_identity(args.cache_root, cache_fd, "CACHE_ROOT")
        verify_control_containment(repo_fd, baseline_controls, Exit.PRE_WORKTREE_CAS)
        pre_promote_artifacts = verify_artifacts(repo_fd, envelope)
        compare_frozen(
            baseline_artifacts,
            pre_promote_artifacts,
            Exit.PRE_WORKTREE_CAS,
            "PRE_PROMOTE_ARTIFACT_DRIFT",
        )
        pre_promote_toolchain = verify_runtime_toolchain(
            args.repo_root,
            envelope,
            pre_promote_artifacts,
            strict=True,
        )
        compare_frozen(
            baseline_toolchain,
            pre_promote_toolchain,
            Exit.PRE_WORKTREE_CAS,
            "PRE_PROMOTE_TOOLCHAIN_DRIFT",
        )
        pre_promote_git = git_snapshot(
            args.repo_root,
            key,
            pre_promote_toolchain["git_binary"],
            authorized_excludes=exclusions,
        )
        compare_git_containment(baseline_git, pre_promote_git)
        pre_promote_processes = process_census(
            args.repo_root,
            key,
            pre_promote_toolchain["pgrep_binary"],
            pre_promote_toolchain["lsof_binary"],
        )
        if pre_promote_processes["claude_session_count"] != 0:
            fail(Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_CLAUDE_SESSION")
        current_lock, current_lock_raw, _ = read_json_relative(repo_fd, "package-lock.json", "PACKAGE_LOCK")
        if not isinstance(current_lock, dict) or sha256(current_lock_raw) != sha256(lock_raw):
            fail(Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_LOCK_DRIFT")
        current_selected = selected_lock_entries(current_lock)
        current_cache, current_bins, current_cache_bytes = cache_census(cache_fd, current_selected)
        compare_frozen(baseline_cache, current_cache, Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_CACHE_DRIFT")
        compare_frozen(baseline_bins, current_bins, Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_BIN_DRIFT")
        if current_cache_bytes != baseline_cache_bytes:
            fail(Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_CACHE_BYTES")
        assert_entry_absent(repo_fd, TARGET_NAME, "PRE_PROMOTE_TARGET")
        current_stage_meta = os.fstat(stage_fd)
        stage_path_meta = os.stat(stage_name, dir_fd=repo_fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(stage_path_meta.st_mode)
            or (stage_path_meta.st_dev, stage_path_meta.st_ino)
            != (current_stage_meta.st_dev, current_stage_meta.st_ino)
            or (stage_preimage.st_dev, stage_preimage.st_ino)
            != (current_stage_meta.st_dev, current_stage_meta.st_ino)
        ):
            fail(Exit.PRE_WORKTREE_CAS, "PRE_PROMOTE_STAGE_IDENTITY")
        ledger.append(
            "pre-promotion-cas-pass",
            {
                "artifact_manifest_unchanged": True,
                "git_unchanged": True,
                "cache_unchanged": True,
                "claude_sessions": 0,
                "target_absent": True,
                "incomplete_marker_present": True,
            },
        )
        final_staged_layout, final_staged_tree = fingerprint_stage_with_marker(stage_fd, incomplete, verifier)
        compare_frozen(
            final_staged_layout,
            expected.get("layout"),
            Exit.PRE_WORKTREE_CAS,
            "FINAL_PRE_PROMOTE_LAYOUT_MISMATCH",
        )
        compare_frozen(
            final_staged_tree,
            expected.get("tree"),
            Exit.PRE_WORKTREE_CAS,
            "FINAL_PRE_PROMOTE_TREE_MISMATCH",
        )
        sealed_meta = finalize_stage_marker(stage_fd, incomplete)
        attempt.stage_marker_removed()
        attempt.set_phase("sealed-marker-removed")
        stable_tree_attestation(
            stage_fd,
            verifier,
            expected,
            Exit.PRE_WORKTREE_CAS,
            "SEALED_PRE_PROMOTE_TREE",
        )
        sealed_final_meta = os.fstat(stage_fd)
        if (
            sealed_final_meta.st_dev,
            sealed_final_meta.st_ino,
            stat.S_IMODE(sealed_final_meta.st_mode),
        ) != (sealed_meta.st_dev, sealed_meta.st_ino, 0o755):
            fail(Exit.PRE_WORKTREE_CAS, "SEALED_STAGE_IDENTITY_DRIFT")
        verify_control_containment(repo_fd, baseline_controls, Exit.PRE_WORKTREE_CAS)
        recorder.begin("G18", "rename-excl-publication")
        assert_envelope_not_expired(envelope)
        assert_entry_absent(repo_fd, TARGET_NAME, "PROMOTE_TARGET")
        renameatx_exclusive(repo_fd, stage_name, TARGET_NAME)
        promoted = True
        promoted_inode = (sealed_final_meta.st_dev, sealed_final_meta.st_ino)
        attempt.target_promoted()
        attempt.set_phase("rename-succeeded-attestation-incomplete")
        try:
            os.fsync(repo_fd)
        except OSError:
            fail(Exit.EVIDENCE, "REPO_FSYNC_AFTER_PROMOTE")
        recorder.passed(
            "G18",
            {
                "publish_syscall": "renameatx_np",
                "publish_flag": "RENAME_EXCL",
                "publish_attempt_count": 1,
                "target_parent_fsynced": True,
                "overwrite_allowed": False,
            },
        )
        ledger.append(
            "stage-promoted",
            {
                "tree_sha256": expected["tree"]["sha256"],
                "incomplete_marker_present": False,
                "root_mode": "0755",
                "rename_profile": "renameatx_np-RENAME_EXCL",
            },
        )
        recorder.begin("G21", "final-tree-merkle")
        promoted_tree = verify_promoted_tree(
            repo_fd,
            (sealed_meta.st_dev, sealed_meta.st_ino),
            verifier,
            expected,
        )
        recorder.passed(
            "G21",
            {
                "tree_sha256": promoted_tree["sha256"],
                "entry_count": promoted_tree["entry_count"],
                "file_count": promoted_tree["file_count"],
                "directory_count": promoted_tree["directory_count"],
                "symlink_count": promoted_tree["symlink_count"],
                "double_stable_fingerprint_passed": True,
            },
        )

        # Post-promotion containment reuses the same public artifact and cache
        # closure and ignores only the exact approved stage/target pathspecs.
        attempt.set_phase("post-promotion-containment")
        verify_private_input_cas(
            args, key, envelope_raw, receipt_digest, envelope,
            control_identity_body["owner_uid"], control_identity_body["group_gid"],
        )
        verify_open_directory_identity(args.repo_root, repo_fd, "REPO_ROOT")
        verify_open_directory_identity(args.cache_root, cache_fd, "CACHE_ROOT")
        recorder.begin("G19", "control-root-after")
        verify_control_containment(repo_fd, baseline_controls, Exit.GIT_CONTAINMENT)
        recorder.passed(
            "G19",
            {
                "protected_control_count": len(baseline_controls),
                "protected_controls_unchanged": True,
                "absent_alternate_control_count": len(ABSENT_CONTROL_PATHS),
            },
        )
        recorder.begin("G20", "outside-scope-postimage")
        post_artifacts = verify_artifacts(repo_fd, envelope)
        compare_frozen(baseline_artifacts, post_artifacts, Exit.GIT_CONTAINMENT, "POST_ARTIFACT_DRIFT")
        post_toolchain = verify_runtime_toolchain(
            args.repo_root,
            envelope,
            post_artifacts,
            strict=True,
        )
        compare_frozen(
            baseline_toolchain,
            post_toolchain,
            Exit.GIT_CONTAINMENT,
            "POST_TOOLCHAIN_DRIFT",
        )
        post_git = git_snapshot(
            args.repo_root,
            key,
            post_toolchain["git_binary"],
            authorized_excludes=exclusions,
        )
        compare_git_containment(baseline_git, post_git)
        post_lock, post_lock_raw, _ = read_json_relative(repo_fd, "package-lock.json", "PACKAGE_LOCK")
        if not isinstance(post_lock, dict) or sha256(post_lock_raw) != sha256(lock_raw):
            fail(Exit.GIT_CONTAINMENT, "POST_LOCK_DRIFT")
        post_selected = selected_lock_entries(post_lock)
        post_cache, post_bins, post_cache_bytes = cache_census(cache_fd, post_selected)
        compare_frozen(baseline_cache, post_cache, Exit.GIT_CONTAINMENT, "POST_CACHE_DRIFT")
        compare_frozen(baseline_bins, post_bins, Exit.GIT_CONTAINMENT, "POST_BIN_DRIFT")
        if post_cache_bytes != baseline_cache_bytes:
            fail(Exit.GIT_CONTAINMENT, "POST_CACHE_BYTES")
        verify_control_containment(repo_fd, baseline_controls, Exit.GIT_CONTAINMENT)
        assert_entry_absent(repo_fd, stage_name, "POST_STAGE")
        recorder.passed(
            "G20",
            {
                "public_artifacts_unchanged": True,
                "toolchain_unchanged": True,
                "git_snapshot_unchanged": True,
                "cache_closure_unchanged": True,
                "protected_controls_unchanged": True,
                "stage_path_absent_after_publication": True,
                "outside_scope_mutation_count": 0,
                "assurance": "targeted-content-and-metadata-CAS-not-machine-wide-audit",
            },
        )
        recorder.begin("G22", "process-census-after")
        post_processes = process_census(
            args.repo_root,
            key,
            post_toolchain["pgrep_binary"],
            post_toolchain["lsof_binary"],
        )
        if post_processes["claude_session_count"] != 0:
            fail(Exit.GIT_CONTAINMENT, "POST_CLAUDE_SESSION")
        recorder.passed(
            "G22",
            {
                "candidate_count": post_processes["candidate_count"],
                "target_worktree_claude_sessions": post_processes["claude_session_count"],
                "pgrep_sha256": post_processes["pgrep_sha256"],
                "candidate_lsof_sha256": post_processes["candidate_lsof_sha256"],
            },
        )
        attempt.set_phase("ledger-terminal-success")
        recorder.begin("G23", "ledger-terminal")
        ledger.append(
            "static-attestation-complete",
            {
                "state": "static-attested-unexecuted",
                "tree_sha256": promoted_tree["sha256"],
                "selected_package_count": expected["selected_package_count"],
                "network_attempt_count": 0,
                "lifecycle_execution_count": 0,
                "installed_code_execution_count": 0,
                "openspec_execution_allowed": False,
                "openspec_scaffold_allowed": False,
            },
        )
        ledger_report = ledger.verify_terminal()
        # Preserve the first successfully verified terminal report as immutable
        # in-process recovery evidence.  A later re-open/re-read failure must
        # not erase a success record that was already checked before G23 or a
        # subsequent public-projection failure.
        last_ledger_report = copy.deepcopy(ledger_report)
        if ledger_report.get("terminal_kind") != "success":
            fail(Exit.EVIDENCE, "LEDGER_SUCCESS_TERMINAL")
        executor_bindings = [entry for entry in baseline_artifacts if entry.get("role") == "static-executor"]
        if len(executor_bindings) != 1:
            fail(Exit.CHECKER_DRIFT, "PRIVATE_PROJECTION_EXECUTOR_BINDING")
        private_projection = build_private_ledger_projection(
            ledger_report,
            executor_bindings[0]["sha256"],
            executor_bindings[0]["bytes"],
        )
        attempt.terminal_success_recorded()
        attempt.set_phase("static-attestation-complete")
        recorder.passed(
            "G23",
            {
                "checker_interface": ledger_report["checker_interface"],
                "record_count": ledger_report["record_count"],
                "terminal_kind": ledger_report["terminal_kind"],
                "ledger_head_hmac_sha256": ledger_report["head_hmac_sha256"],
                "canonical_jsonl_and_hmac_chain_valid": True,
                "private_projection_schema_version": private_projection["schema_version"],
            },
        )
        attestation = {
            "schema_version": "gov01-static-acquisition-success-attestation-v2",
            "approval_challenge_id": challenge,
            "receipt_digest": receipt_digest,
            "schema_binding_observation": public_schema_observation,
            "public_repo_artifact_set_receipt_sha256": artifact_receipt,
            "git_snapshot_commitment": baseline_git["commitment"],
            "private_preapproval_commitment": preapproval_commitment,
            "private_control_identity_commitment": control_identity_receipt,
            "toolchain": {
                "assurance": baseline_toolchain["assurance"],
                "pre_exec_launcher_attested": False,
                "toolchain_set_receipt_sha256": baseline_toolchain["toolchain_set_receipt_sha256"],
                "dynamic_closure_receipt_sha256": baseline_toolchain["dynamic_closure_receipt_sha256"],
                "hashes": {
                    entry["role"]: entry["raw_digest_sha256"] for entry in baseline_toolchain["entries"]
                },
            },
            "source_and_receipts": {
                "lock_closure_observed": lock_observation,
                "static_expected": expected_public,
            },
            "publication": {
                "publish_syscall": "renameatx_np",
                "publish_flag": "RENAME_EXCL",
                "tree_sha256": promoted_tree["sha256"],
                "private_ledger_head_hmac_sha256": ledger_report["head_hmac_sha256"],
                "target_state": "static-attested-unexecuted",
            },
            "containment": {
                "protected_controls_unchanged": True,
                "absent_alternate_controls": True,
                "public_artifacts_unchanged": True,
                "toolchain_unchanged": True,
                "git_snapshot_unchanged": True,
                "cache_closure_unchanged": True,
                "outside_scope_mutation_count": 0,
                "target_worktree_claude_sessions": 0,
            },
            "execution_counters": {
                "network_attempt_count": 0,
                "lifecycle_execution_count": 0,
                "installed_code_execution_count": 0,
                "node_npm_npx_execution_count": 0,
                "counter_scope": "executor-authorized-call-sites-only",
                "runtime_syscall_observation_available": False,
            },
            "next_required_authorization": "new runtime-use envelope binding this final tree and a fresh single-use challenge",
        }
        candidate = base_public_result(
            True,
            "acquire",
            attempt.phase,
            "static-attested-unexecuted",
            attempt.projection(),
            recorder.partial_projection(),
            baseline_toolchain,
        )
        candidate["approval_challenge_id"] = challenge
        candidate["receipt_digest"] = receipt_digest
        candidate["authority"] = authority_projection(
            False,
            True,
            "new runtime-use envelope binding this final tree and a fresh single-use challenge",
        )
        candidate["attestation"] = attestation
        recorder.begin("G24", "privacy-redaction")
        if has_forbidden_public_value(candidate):
            fail(Exit.PRIVACY, "PUBLIC_SUCCESS_PROJECTION_PRIVATE_VALUE")
        g24_evidence = {
            "private_locator_public_count": 0,
            "private_vault_read_count": 0,
            "raw_command_output_public_count": 0,
            "projection_preflight_passed": True,
        }
        # G24 is a real preflight gate, not an assertion recorded before its
        # subject was checked.  Validate the exact prospective final bytes with
        # a cloned recorder.  On any error the live recorder remains active, so
        # the failure path records G24=FAIL and retains a valid partial prefix.
        prospective_recorder = copy.deepcopy(recorder)
        prospective_recorder.passed(
            "G24",
            g24_evidence,
        )
        candidate["gate_results"] = prospective_recorder.complete_projection()
        validate_gate_projection(candidate["gate_results"])
        success_authority_binding = completed_public_authority_binding(recorder, {
            "toolchain_hashes": attestation["toolchain"]["hashes"],
            "public_repo_artifact_set_receipt_sha256": artifact_receipt,
            "git_snapshot_commitment": baseline_git["commitment"],
            "private_preapproval_commitment": preapproval_commitment,
            "package_lock_raw_sha256": sha256(lock_raw),
        })
        candidate = AuthorityBoundPublicResult(candidate, success_authority_binding)
        validate_public_result_projection(candidate)
        # The prospective result is frozen before the live G24 receipt.  The
        # live PASS below is the linearization point: if interruption happens
        # after the receipt becomes visible, the except path returns these
        # already validated bytes instead of inventing a partial 25-PASS state.
        committed_success_candidate = copy.deepcopy(candidate)
        recorder.passed("G24", g24_evidence)
        final_gate_results = recorder.complete_projection()
        if final_gate_results != candidate["gate_results"]:
            fail(Exit.EVIDENCE, "G24_PROSPECTIVE_RECEIPT_DRIFT")
        candidate["gate_results"] = final_gate_results
        return candidate
    except BaseException as error:
        recovered_success = recover_linearized_success(recorder, committed_success_candidate)
        if recovered_success is not None:
            returning_linearized_success = True
            return recovered_success
        error_code, public_code = public_error_identity(error)
        recorder.failed(public_code, int(error_code))
        try:
            observe_retained_publication_state(
                repo_fd,
                preliminary_stage,
                attempt,
                promoted_by_this_attempt=promoted,
                expected_target_inode=promoted_inode,
            )
        except BaseException:
            attempt.stage_state = "unknown-fail-closed"
            attempt.publication_state = "unknown-fail-closed"
            attempt.target_disposition = "unknown-user-decision-required"
        ledger_report: Optional[Dict[str, Any]] = None
        if ledger is not None:
            if ledger.sequence >= 6:
                ledger_report = recover_terminal_success_report(
                    ledger,
                    last_ledger_report,
                    attempt,
                )
                if ledger_report is not None:
                    last_ledger_report = copy.deepcopy(ledger_report)
            else:
                try:
                    ledger.append(
                        "attempt-failed",
                        {
                            "public_code": public_code,
                            "promoted": promoted,
                            "stage_deleted_or_moved_on_failure": False,
                            "automatic_rollback_performed": False,
                        },
                    )
                    possible_terminal = ledger.verify_terminal()
                    if possible_terminal.get("terminal_kind") != "failure":
                        fail(Exit.EVIDENCE, "LEDGER_FAILURE_TERMINAL")
                except BaseException:
                    attempt.ledger_invalid()
                else:
                    ledger_report = possible_terminal
                    last_ledger_report = possible_terminal
                    attempt.terminal_failure_recorded()
        elif attempt.claim_state != "not-created":
            attempt.ledger_invalid()
        payload = acquire_failure_result(
            error,
            attempt,
            recorder,
            challenge,
            receipt_digest,
            baseline_toolchain,
            ledger_report,
        )
        raise ContractError(error_code, public_code, payload) from None
    finally:
        primary_error_active = (
            sys.exc_info()[0] is not None and not returning_linearized_success
        )
        close_error_count = close_acquire_resources(stage_fd, ledger, claim_fd, cache_fd, repo_fd)
        if close_error_count and not primary_error_active:
            payload = resource_finalization_failure_result(
                attempt,
                recorder,
                challenge,
                receipt_digest,
                baseline_toolchain,
                last_ledger_report,
            )
            raise ContractError(Exit.EVIDENCE, "RESOURCE_FINALIZATION_CLOSE", payload) from None


def parser() -> argparse.ArgumentParser:
    result = SafeArgumentParser(
        prog="gov01-static-acquisition",
        description="Fail-closed, no-Node GOV-01 static acquisition executor",
    )
    result.add_argument("--version", action="version", version=SCRIPT_VERSION)
    subparsers = result.add_subparsers(dest="mode", required=True, parser_class=SafeArgumentParser)
    for name in ("census", "verify", "acquire"):
        child = subparsers.add_parser(name)
        child.add_argument("--repo-root", required=True)
        child.add_argument("--cache-root", required=True)
        child.add_argument("--state-root", required=True)
        child.add_argument("--key-file", required=True)
        child.add_argument("--envelope", required=True)
        child.add_argument("--receipt-digest")
        if name == "acquire":
            child.add_argument("--approval-challenge", required=True)
            child.set_defaults(handler=command_acquire)
        elif name == "census":
            child.set_defaults(handler=command_census)
        else:
            child.set_defaults(handler=command_verify)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    mode = "unknown"
    try:
        args = parser().parse_args(argv)
        mode = args.mode
        payload = args.handler(args)
        return emit(payload)
    except ContractError as error:
        return emit(error.public_payload if error.public_payload is not None else generic_public_failure(error, mode))
    except KeyboardInterrupt as error:
        return emit(generic_public_failure(error, mode))
    except Exception as error:
        # Never serialize exception text, arguments, paths, or a traceback.
        return emit(generic_public_failure(error, mode))


if __name__ == "__main__":
    sys.exit(main())
