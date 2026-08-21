#!/usr/bin/env python3
"""Issue and consume a GOV-01 static-envelope generation authorization.

The ``issue`` command is deliberately public-only: it hashes an exact set of
versioned repository artifacts, records the current commit boundary, creates a
fresh generation challenge, and writes one pending micro-envelope.  It never
opens the npm cache, the prepared control root, the HMAC key, a Vault, or a
private settings source.

The ``generate`` command consumes one exact, committed micro-envelope.  It
loads the frozen acquisition executor by approved source digest, derives every
private locator inside that executor, and creates at most one GEN-keyed public
pending acquisition envelope identity.  A durable private GEN claim fixes the
single acquisition challenge, timestamps, and final raw bytes before public
publication.  A deleted complete output can only be recreated byte-for-byte;
partial or drifted claim/output state is retained and rejected.
"""

import argparse
import ctypes
import datetime as _datetime
import errno
import hashlib
import hmac
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import types
import unicodedata
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Tuple


class Exit(IntEnum):
    OK = 0
    USAGE = 10
    CONTRACT = 11
    PREFLIGHT = 20
    UNSAFE_PATH = 21
    RUNTIME = 22
    WRITE = 30
    PRIVACY = 55
    INTERNAL = 70


class GitReadBoundary(NamedTuple):
    developer_root: str
    git_dir: str
    common_dir: str


class GenerationError(Exception):
    def __init__(self, code: Exit, public_code: str):
        super().__init__(public_code)
        self.code = code
        self.public_code = public_code


class PrivacySafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        self.exit(int(Exit.USAGE), self.prog + ": error: arguments-invalid\n")


SCRIPT_VERSION = "gov01-static-envelope-generation-v1"
PLAN_ID = "PLAN-CLS-PRODUCTIVITY-2026-08-20"
CONTROL_PREFIX = "_bmad-output/审查/phase0a-annotation-truth/"
GENERATOR_RELATIVE = CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-v1.py"
GENERATION_SCHEMA_RELATIVE = (
    CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json"
)
GENERATION_FIXTURE_RELATIVE = (
    CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py"
)
MICRO_BASENAME_PREFIX = "GOV-01-toolchain-static-envelope-generation-envelope-v1."
FINAL_BASENAME_PREFIX = "GOV-01-toolchain-static-acquisition-pending-"
GENERATION_DOMAIN = b"CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1"
ACQUISITION_DOMAIN = b"CLS/GOV01-TOOLCHAIN-STATIC-ACQUISITION-RECEIPT/v2"
HEAD_REF_DOMAIN = b"CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1"
GENERATION_CLAIM_PROFILE = (
    "exclusive-0700-generation-claim-directory-with-exclusive-0600-canonical-HMAC-record-v1"
)
GENERATION_CLAIM_RECORD_PROFILE = (
    "HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/STATIC-ENVELOPE-"
    "GENERATION-CLAIM/v1) || NUL || uint64be(canonical-body-byte-length) || canonical JSON binding "
    "GEN receipt/raw, C1/C2 identities, one SA/time tuple and final raw SHA-256/bytes/domain receipt"
)
GENERATION_CLAIM_RETENTION = (
    "retain permanently; never delete, overwrite or repair; a complete valid claim permits only byte-exact "
    "recovery with its recorded SA and times"
)
GENERATION_GIT_CHILD_SANDBOX_PROFILE_V1 = (
    "every Git child calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated "
    "default-deny profile; permits only the content-bound CommandLineTools tree, validated Git control metadata, "
    "exact object and ref stores and required path ancestors; denies network, writes, worktree payload reads, config "
    "includes, alternates, grafts and all other reads; sandbox initialization failure is terminal; "
    "/usr/bin/sandbox-exec is never executed"
)
MAX_FILE_BYTES = 4_000_000
MAX_GIT_BYTES = 32 * 1024 * 1024
MAX_GIT_CONTROL_BYTES = 1024 * 1024
GENERATION_CHALLENGE_RE = re.compile(r"\AGOV01-GEN-[0-9]{8}-[0-9a-f]{64}\Z")
ACQUISITION_CHALLENGE_RE = re.compile(r"\AGOV01-SA-[0-9]{8}-[0-9a-f]{64}\Z")
SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
GIT_OID_RE = re.compile(r"\A(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
HEAD_REF_RE = re.compile(r"\Arefs/heads/[A-Za-z0-9._/-]{1,240}\Z")
UTC_SECOND_RE = re.compile(
    r"\A[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z\Z"
)
FIRST_ENVELOPE_SHA256 = "0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410"
FIRST_RECEIPT_SHA256 = "c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740"
BOOTSTRAP_PATCH_SHA256 = "d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa"
BOOTSTRAP_COMMIT_OID = "0e0f0150be184f4dad83a859b0fdd232ec53e8b5"
CONTROL_PREP_ENVELOPE_SHA256 = "ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b"
CONTROL_PREP_RECEIPT_SHA256 = "dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c"

ARTIFACT_SPECS: Tuple[Tuple[str, str], ...] = (
    ("goal", "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md"),
    (
        "governance-decision",
        CONTROL_PREFIX + "2026-08-20-GOV-01-追踪真相源修复决策稿.md",
    ),
    (
        "phase0a-contract",
        CONTROL_PREFIX + "2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md",
    ),
    ("first-receipt-envelope", CONTROL_PREFIX + "GOV-01-first-receipt-envelope-v1.json"),
    ("first-receipt-schema", CONTROL_PREFIX + "GOV-01-first-receipt-envelope-v1.schema.json"),
    ("bootstrap-patch", CONTROL_PREFIX + "2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch"),
    ("control-prep-envelope", CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.json"),
    ("control-prep-schema", CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.schema.json"),
    ("static-envelope-generator", GENERATOR_RELATIVE),
    ("generation-envelope-schema", GENERATION_SCHEMA_RELATIVE),
    ("generation-hostile-fixture", GENERATION_FIXTURE_RELATIVE),
    ("static-executor", CONTROL_PREFIX + "GOV-01-toolchain-static-acquisition-v2.py"),
    ("static-verifier", CONTROL_PREFIX + "GOV-01-toolchain-static-verifier-v2.py"),
    ("static-hostile-fixture", CONTROL_PREFIX + "GOV-01-static-acquisition-hostile-fixtures-v2.py"),
    (
        "pending-envelope-schema",
        CONTROL_PREFIX + "GOV-01-toolchain-static-acquisition-envelope-v2.schema.json",
    ),
    (
        "private-evidence-schema",
        CONTROL_PREFIX + "GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json",
    ),
    (
        "public-attestation-schema",
        CONTROL_PREFIX + "GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json",
    ),
    ("package-manifest", "package.json"),
    ("package-lock", "package-lock.json"),
    ("gitignore", ".gitignore"),
)

GENERATION_CLAIM_RECORD_FIELDS = frozenset(
    (
        "profile",
        "generation_authorization_challenge_id",
        "generation_authorization_envelope_raw_sha256",
        "generation_authorization_receipt_digest",
        "generation_authorization_parent_commit_oid",
        "generation_authorization_parent_tree_oid",
        "generation_authorization_commit_oid",
        "generation_authorization_tree_oid",
        "acquisition_approval_challenge_id",
        "census_at_utc",
        "not_after_utc",
        "final_envelope_repo_relative_path",
        "final_envelope_raw_sha256",
        "final_envelope_bytes",
        "final_envelope_receipt_digest",
        "state",
        "record_hmac_sha256",
    )
)


def fail(code: Exit, public_code: str) -> None:
    raise GenerationError(code, public_code)


def is_nfc(value: str) -> bool:
    return unicodedata.normalize("NFC", value) == value


def canonical_json(value: Any) -> bytes:
    validate_json_value(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeError):
        fail(Exit.CONTRACT, "CANONICAL_JSON")
    raise AssertionError("unreachable")


def validate_json_value(value: Any) -> None:
    if isinstance(value, str):
        if not is_nfc(value):
            fail(Exit.CONTRACT, "JSON_NON_NFC")
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, list):
        for child in value:
            validate_json_value(child)
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or not is_nfc(key):
                fail(Exit.CONTRACT, "JSON_NON_NFC")
            validate_json_value(child)
        return
    fail(Exit.CONTRACT, "JSON_VALUE_TYPE")


def no_duplicate_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(Exit.CONTRACT, "JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def reject_float(_value: str) -> None:
    fail(Exit.CONTRACT, "JSON_NUMBER_PROFILE")


def parse_json(raw: bytes, label: str) -> Any:
    if not raw or len(raw) > MAX_FILE_BYTES or raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        fail(Exit.CONTRACT, label + "_ENCODING")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.CONTRACT, label + "_UTF8")
    if not is_nfc(text):
        fail(Exit.CONTRACT, label + "_NFC")
    try:
        result = json.loads(
            text,
            object_pairs_hook=no_duplicate_object,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    except GenerationError:
        raise
    except (TypeError, ValueError):
        fail(Exit.CONTRACT, label + "_JSON")
    validate_json_value(result)
    return result


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def receipt_digest(raw: bytes) -> str:
    return sha256(GENERATION_DOMAIN + b"\x00" + raw)


def acquisition_receipt_digest(raw: bytes) -> str:
    return sha256(ACQUISITION_DOMAIN + b"\x00" + raw)


def head_ref_digest(value: str) -> str:
    validated = validate_head_ref(value)
    raw = validated.encode("ascii", "strict")
    return sha256(HEAD_REF_DOMAIN + b"\x00" + raw)


def utc_now_second() -> _datetime.datetime:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)


def format_utc(value: _datetime.datetime) -> str:
    if value.tzinfo != _datetime.timezone.utc or value.microsecond:
        fail(Exit.INTERNAL, "UTC_INTERNAL")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(value: Any, label: str) -> _datetime.datetime:
    if not isinstance(value, str) or UTC_SECOND_RE.fullmatch(value) is None:
        fail(Exit.CONTRACT, label + "_FORMAT")
    try:
        parsed = _datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_datetime.timezone.utc
        )
    except ValueError:
        fail(Exit.CONTRACT, label + "_CALENDAR")
    if format_utc(parsed) != value:
        fail(Exit.CONTRACT, label + "_CANONICAL")
    return parsed


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
    if sys.version_info < (3, 9) or sys.version_info >= (4, 0):
        fail(Exit.RUNTIME, "PYTHON_VERSION")
    if sys.platform != "darwin":
        fail(Exit.RUNTIME, "HOST_PLATFORM")


def forbidden_component(component: str) -> bool:
    folded = unicodedata.normalize("NFC", component).casefold()
    return folded == ".git" or folded == ".obsidian" or "canvas-vault" in folded


def validate_relative(path: Any, label: str) -> List[str]:
    if not isinstance(path, str) or not path or not is_nfc(path):
        fail(Exit.UNSAFE_PATH, label + "_FORMAT")
    if path.startswith("/") or "\\" in path:
        fail(Exit.UNSAFE_PATH, label + "_FORMAT")
    components = path.split("/")
    if any(not component or component in (".", "..") for component in components):
        fail(Exit.UNSAFE_PATH, label + "_TRAVERSAL")
    for component in components:
        if forbidden_component(component):
            fail(Exit.PRIVACY, label + "_PRIVATE_COMPONENT")
        if any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in component):
            fail(Exit.PRIVACY, label + "_CONTROL_OR_FORMAT")
    return components


def validate_head_ref(value: Any) -> str:
    if not isinstance(value, str) or HEAD_REF_RE.fullmatch(value) is None:
        fail(Exit.PREFLIGHT, "GIT_HEAD_REF")
    suffix = value[len("refs/heads/") :]
    components = suffix.split("/")
    if any(not component or component in (".", "..") for component in components):
        fail(Exit.PREFLIGHT, "GIT_HEAD_REF_COMPONENT")
    for component in components:
        if forbidden_component(component):
            fail(Exit.PRIVACY, "GIT_HEAD_REF_PRIVATE_COMPONENT")
        if any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in component):
            fail(Exit.PRIVACY, "GIT_HEAD_REF_CONTROL_OR_FORMAT")
    return value


def no_symlink_path(path: str, label: str) -> os.stat_result:
    if not os.path.isabs(path) or os.path.normpath(path) != path:
        fail(Exit.UNSAFE_PATH, label + "_ABSOLUTE")
    current = os.sep
    metadata = os.lstat(current)
    for component in [part for part in path.split(os.sep) if part]:
        current = os.path.join(current, component)
        try:
            metadata = os.lstat(current)
        except OSError:
            fail(Exit.UNSAFE_PATH, label + "_MISSING")
        if stat.S_ISLNK(metadata.st_mode):
            fail(Exit.UNSAFE_PATH, label + "_SYMLINK")
    return metadata


def derive_repo_root() -> Tuple[str, os.stat_result]:
    source = os.path.realpath(__file__)
    if os.path.abspath(__file__) != source:
        fail(Exit.UNSAFE_PATH, "GENERATOR_SOURCE_SYMLINK")
    suffix = os.sep + GENERATOR_RELATIVE.replace("/", os.sep)
    if not source.endswith(suffix):
        fail(Exit.UNSAFE_PATH, "GENERATOR_SOURCE_SUFFIX")
    repo_root = source[: -len(suffix)]
    if not repo_root or os.path.normpath(repo_root) != repo_root:
        fail(Exit.UNSAFE_PATH, "REPO_ROOT_DERIVATION")
    source_meta = no_symlink_path(source, "GENERATOR_SOURCE")
    repo_meta = no_symlink_path(repo_root, "REPO_ROOT")
    if not stat.S_ISREG(source_meta.st_mode) or not stat.S_ISDIR(repo_meta.st_mode):
        fail(Exit.UNSAFE_PATH, "GENERATOR_SOURCE_TYPE")
    if source_meta.st_uid != os.getuid() or repo_meta.st_uid != os.getuid():
        fail(Exit.UNSAFE_PATH, "GENERATOR_SOURCE_OWNER")
    if stat.S_IMODE(source_meta.st_mode) & 0o022 or stat.S_IMODE(repo_meta.st_mode) & 0o022:
        fail(Exit.UNSAFE_PATH, "GENERATOR_SOURCE_MODE")
    return repo_root, repo_meta


def open_relative_regular(repo_root: str, relative: str, label: str) -> Tuple[bytes, os.stat_result]:
    components = validate_relative(relative, label)
    repo_fd = os.open(
        repo_root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    current = repo_fd
    try:
        for component in components[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            if current != repo_fd:
                os.close(current)
            current = next_fd
        fd = os.open(
            components[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=current,
        )
        try:
            before = os.fstat(fd)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size <= 0
                or before.st_size > MAX_FILE_BYTES
                or before.st_uid != os.getuid()
                or stat.S_IMODE(before.st_mode) & 0o022
            ):
                fail(Exit.UNSAFE_PATH, label + "_POLICY")
            pieces: List[bytes] = []
            remaining = before.st_size
            while remaining:
                chunk = os.read(fd, min(1024 * 1024, remaining))
                if not chunk:
                    fail(Exit.PREFLIGHT, label + "_SHORT_READ")
                pieces.append(chunk)
                remaining -= len(chunk)
            if os.read(fd, 1):
                fail(Exit.PREFLIGHT, label + "_GROWTH")
            after = os.fstat(fd)
            if (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                fail(Exit.PREFLIGHT, label + "_READ_RACE")
            raw = b"".join(pieces)
        finally:
            os.close(fd)
        path_meta = os.stat(components[-1], dir_fd=current, follow_symlinks=False)
        if (path_meta.st_dev, path_meta.st_ino) != (before.st_dev, before.st_ino):
            fail(Exit.PREFLIGHT, label + "_PATH_RACE")
        return raw, before
    except GenerationError:
        raise
    except OSError:
        fail(Exit.UNSAFE_PATH, label + "_OPEN")
    finally:
        if current != repo_fd:
            os.close(current)
        os.close(repo_fd)
    raise AssertionError("unreachable")


def read_absolute_small_regular(path: str, label: str) -> bytes:
    metadata = no_symlink_path(path, label)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or metadata.st_nlink != 1
        or metadata.st_size <= 0
        or metadata.st_size > MAX_GIT_CONTROL_BYTES
    ):
        fail(Exit.PREFLIGHT, label + "_POLICY")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        fail(Exit.PREFLIGHT, label + "_OPEN")
    try:
        before = os.fstat(fd)
        pieces: List[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                fail(Exit.PREFLIGHT, label + "_SHORT_READ")
            pieces.append(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            fail(Exit.PREFLIGHT, label + "_GROWTH")
        after = os.fstat(fd)
    finally:
        os.close(fd)
    if (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        fail(Exit.PREFLIGHT, label + "_READ_RACE")
    return b"".join(pieces)


def require_absent_control(path: str, label: str) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        fail(Exit.PREFLIGHT, label + "_LSTAT")
    fail(Exit.PREFLIGHT, label + "_PRESENT")


def linked_git_common_anchor(repo_root: str, git_dir: str) -> str:
    """Resolve this project's exact linked-worktree admin-root relation."""

    if not os.path.isabs(git_dir) or os.path.normpath(git_dir) != git_dir:
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_LOCATOR")
    for component in pathlib.PurePath(git_dir).parts:
        folded = component.casefold()
        if (
            not is_nfc(component)
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in component)
            or folded == ".obsidian"
            or "canvas-vault" in folded
        ):
            fail(Exit.PRIVACY, "GIT_DIRECTORY_PRIVATE_COMPONENT")
    worktree_name = os.path.basename(git_dir)
    worktrees_dir = os.path.dirname(git_dir)
    candidate_common = os.path.dirname(worktrees_dir)
    main_root = os.path.dirname(candidate_common)
    if (
        os.path.basename(worktrees_dir) != "worktrees"
        or os.path.basename(candidate_common).casefold() != ".git"
        or validate_relative(worktree_name, "GIT_WORKTREE_ID") != [worktree_name]
    ):
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_ADMIN_ANCHOR")
    try:
        repo_relative = os.path.relpath(repo_root, main_root).replace(os.sep, "/")
        repo_components = validate_relative(repo_relative, "GIT_WORKTREE_REPO")
    except (GenerationError, ValueError):
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_ADMIN_ANCHOR")
    if repo_components != [".claude", "worktrees", worktree_name]:
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_ADMIN_ANCHOR")
    if git_dir != os.path.join(candidate_common, "worktrees", worktree_name):
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_ADMIN_ANCHOR")
    return candidate_common


def inspect_git_control(repo_root: str) -> Tuple[Dict[str, Any], Tuple[str, str]]:
    """Reject Git includes and alternate object roots before invoking Git."""

    marker = os.path.join(repo_root, ".git")
    marker_meta = no_symlink_path(marker, "GIT_MARKER")
    marker_kind: str
    if stat.S_ISREG(marker_meta.st_mode):
        marker_kind = "gitfile"
        raw = read_absolute_small_regular(marker, "GIT_MARKER")
        if raw.count(b"\n") != 1 or not raw.endswith(b"\n") or not raw.startswith(b"gitdir: "):
            fail(Exit.PREFLIGHT, "GIT_MARKER_FORMAT")
        try:
            declared = raw[len(b"gitdir: ") : -1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_MARKER_ENCODING")
        if not is_nfc(declared) or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in declared):
            fail(Exit.PREFLIGHT, "GIT_MARKER_VALUE")
        git_dir = declared if os.path.isabs(declared) else os.path.join(repo_root, declared)
        git_dir = os.path.normpath(git_dir)
        expected_common_dir = linked_git_common_anchor(repo_root, git_dir)
    elif stat.S_ISDIR(marker_meta.st_mode):
        marker_kind = "directory"
        git_dir = marker
        expected_common_dir = marker
    else:
        fail(Exit.PREFLIGHT, "GIT_MARKER_KIND")
    git_dir_meta = no_symlink_path(git_dir, "GIT_DIRECTORY")
    if (
        not stat.S_ISDIR(git_dir_meta.st_mode)
        or git_dir_meta.st_uid != os.getuid()
        or stat.S_IMODE(git_dir_meta.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT, "GIT_DIRECTORY_POLICY")

    commondir_path = os.path.join(git_dir, "commondir")
    try:
        commondir_meta = os.lstat(commondir_path)
    except FileNotFoundError:
        if marker_kind == "gitfile":
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_REQUIRED")
        common_dir = git_dir
        relation = "git-directory-is-common-directory"
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_COMMONDIR_LSTAT")
    else:
        if marker_kind != "gitfile":
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_UNEXPECTED")
        if stat.S_ISLNK(commondir_meta.st_mode) or not stat.S_ISREG(commondir_meta.st_mode):
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_KIND")
        raw = read_absolute_small_regular(commondir_path, "GIT_COMMONDIR")
        if raw != b"../..\n":
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_FORMAT")
        try:
            declared_common = raw[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_ENCODING")
        if (
            not declared_common
            or not is_nfc(declared_common)
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in declared_common)
        ):
            fail(Exit.PREFLIGHT, "GIT_COMMONDIR_VALUE")
        common_dir = declared_common if os.path.isabs(declared_common) else os.path.join(git_dir, declared_common)
        common_dir = os.path.normpath(common_dir)
        relation = "git-directory-contained-under-common-worktrees"
    if common_dir != expected_common_dir:
        fail(Exit.PREFLIGHT, "GIT_COMMONDIR_ADMIN_ANCHOR")
    if marker_kind == "gitfile":
        reverse_raw = read_absolute_small_regular(os.path.join(git_dir, "gitdir"), "GIT_WORKTREE_GITDIR")
        if reverse_raw.count(b"\n") != 1 or not reverse_raw.endswith(b"\n"):
            fail(Exit.PREFLIGHT, "GIT_WORKTREE_GITDIR_FORMAT")
        try:
            reverse_path = reverse_raw[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_WORKTREE_GITDIR_ENCODING")
        if (
            not is_nfc(reverse_path)
            or os.path.normpath(reverse_path) != os.path.join(repo_root, ".git")
        ):
            fail(Exit.PREFLIGHT, "GIT_WORKTREE_GITDIR_BINDING")
    common_meta = no_symlink_path(common_dir, "GIT_COMMON_DIRECTORY")
    try:
        contained = os.path.commonpath([git_dir, common_dir]) == common_dir
    except ValueError:
        contained = False
    if (
        not stat.S_ISDIR(common_meta.st_mode)
        or common_meta.st_uid != os.getuid()
        or stat.S_IMODE(common_meta.st_mode) & 0o022
        or not contained
    ):
        fail(Exit.PREFLIGHT, "GIT_COMMON_DIRECTORY_POLICY")
    if git_dir != common_dir:
        relative_git_dir = os.path.relpath(git_dir, common_dir).replace(os.sep, "/")
        components = validate_relative(relative_git_dir, "GIT_WORKTREE_CONTROL")
        if len(components) != 2 or components[0] != "worktrees":
            fail(Exit.PREFLIGHT, "GIT_WORKTREE_CONTROL_RELATION")

    for config_path, label in (
        (os.path.join(common_dir, "config"), "GIT_COMMON_CONFIG"),
        (os.path.join(git_dir, "config.worktree"), "GIT_WORKTREE_CONFIG"),
    ):
        try:
            os.lstat(config_path)
        except FileNotFoundError:
            continue
        except OSError:
            fail(Exit.PREFLIGHT, label + "_LSTAT")
        config = read_absolute_small_regular(config_path, label)
        lowered = config.lower()
        if b"[include" in lowered or b"alternates" in lowered:
            fail(Exit.PREFLIGHT, label + "_EXTERNAL_CONTROL")

    for prohibited, label in (
        (os.path.join(common_dir, "objects", "info", "alternates"), "GIT_ALTERNATES"),
        (os.path.join(common_dir, "objects", "info", "http-alternates"), "GIT_HTTP_ALTERNATES"),
        (os.path.join(git_dir, "objects", "info", "alternates"), "GIT_WORKTREE_ALTERNATES"),
        (os.path.join(git_dir, "objects", "info", "http-alternates"), "GIT_WORKTREE_HTTP_ALTERNATES"),
        (os.path.join(common_dir, "info", "grafts"), "GIT_GRAFTS"),
    ):
        require_absent_control(prohibited, label)
    objects = os.path.join(common_dir, "objects")
    objects_meta = no_symlink_path(objects, "GIT_OBJECTS")
    if not stat.S_ISDIR(objects_meta.st_mode) or objects_meta.st_uid != os.getuid():
        fail(Exit.PREFLIGHT, "GIT_OBJECTS_POLICY")
    observation = {
        "marker_kind": marker_kind,
        "common_directory_relation": relation,
        "include_controls_absent": True,
        "alternate_object_controls_absent": True,
    }
    return observation, (git_dir, common_dir)


def git_control_preflight(repo_root: str) -> Dict[str, Any]:
    observation, _private_paths = inspect_git_control(repo_root)
    return observation


def artifact_observations(repo_root: str) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    seen = set()
    for role, path in ARTIFACT_SPECS:
        if path in seen:
            fail(Exit.INTERNAL, "ARTIFACT_PATH_DUPLICATE")
        seen.add(path)
        raw, metadata = open_relative_regular(repo_root, path, "ARTIFACT")
        observations.append(
            {
                "role": role,
                "path": path,
                "file_kind": "regular",
                "byte_length": len(raw),
                "raw_file_sha256": sha256(raw),
            }
        )
        if len(raw) != metadata.st_size:
            fail(Exit.PREFLIGHT, "ARTIFACT_SIZE_RACE")
    by_role = {entry["role"]: entry for entry in observations}
    if by_role["first-receipt-envelope"]["raw_file_sha256"] != FIRST_ENVELOPE_SHA256:
        fail(Exit.PREFLIGHT, "FIRST_ENVELOPE_DRIFT")
    if by_role["bootstrap-patch"]["raw_file_sha256"] != BOOTSTRAP_PATCH_SHA256:
        fail(Exit.PREFLIGHT, "BOOTSTRAP_PATCH_DRIFT")
    if by_role["control-prep-envelope"]["raw_file_sha256"] != CONTROL_PREP_ENVELOPE_SHA256:
        fail(Exit.PREFLIGHT, "CONTROL_PREP_ENVELOPE_DRIFT")
    return observations


def assert_artifacts_match_head(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    observations: Sequence[Mapping[str, Any]],
) -> None:
    """Bind every public artifact byte-for-byte to the current HEAD tree."""

    if len(observations) != len(ARTIFACT_SPECS):
        fail(Exit.INTERNAL, "ARTIFACT_HEAD_COUNT")
    for observed, (role, path) in zip(observations, ARTIFACT_SPECS):
        if observed.get("role") != role or observed.get("path") != path:
            fail(Exit.INTERNAL, "ARTIFACT_HEAD_ORDER")
        row = run_git(
            git_binary,
            repo_root,
            boundary,
            ["ls-tree", "-z", "--full-tree", "HEAD", "--", path],
            "GIT_ARTIFACT_TREE",
            max_bytes=4096,
        )
        if row.count(b"\x00") != 1 or not row.endswith(b"\x00") or b"\t" not in row:
            fail(Exit.PREFLIGHT, "ARTIFACT_HEAD_ENTRY")
        header, encoded_path = row[:-1].split(b"\t", 1)
        fields = header.split(b" ")
        if len(fields) != 3 or fields[0] not in (b"100644", b"100755") or fields[1] != b"blob":
            fail(Exit.PREFLIGHT, "ARTIFACT_HEAD_KIND")
        try:
            tree_path = encoded_path.decode("utf-8", "strict")
            object_id = fields[2].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "ARTIFACT_HEAD_ENCODING")
        if tree_path != path or GIT_OID_RE.fullmatch(object_id) is None:
            fail(Exit.PREFLIGHT, "ARTIFACT_HEAD_IDENTITY")
        current_raw, current_meta = open_relative_regular(repo_root, path, "ARTIFACT_HEAD_WORKTREE")
        expected_mode = 0o755 if fields[0] == b"100755" else 0o644
        if (
            stat.S_IMODE(current_meta.st_mode) != expected_mode
            or len(current_raw) != observed.get("byte_length")
            or sha256(current_raw) != observed.get("raw_file_sha256")
        ):
            fail(Exit.PREFLIGHT, "ARTIFACT_WORKTREE_NOT_HEAD")
        head_raw = run_git(
            git_binary,
            repo_root,
            boundary,
            ["show", "HEAD:" + path],
            "GIT_ARTIFACT_BLOB",
            max_bytes=MAX_FILE_BYTES,
        )
        if (
            len(head_raw) != observed.get("byte_length")
            or sha256(head_raw) != observed.get("raw_file_sha256")
        ):
            fail(Exit.PREFLIGHT, "ARTIFACT_NOT_HEAD_BYTES")


def child_env() -> Dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": "/var/empty",
        "TMPDIR": "/tmp",
        "DARWIN_USER_TEMP_DIR": "/tmp",
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


def run_process(
    argv: Sequence[str],
    label: str,
    max_bytes: int = MAX_GIT_BYTES,
    allowed_returncodes: Sequence[int] = (0,),
    sandbox_profile: Optional[bytes] = None,
) -> bytes:
    if not argv or not os.path.isabs(argv[0]):
        fail(Exit.INTERNAL, "PROCESS_ARGV")
    preexec_fn: Optional[Callable[[], None]] = None
    if sandbox_profile is not None:
        if not isinstance(sandbox_profile, bytes) or not sandbox_profile:
            fail(Exit.INTERNAL, "PROCESS_SANDBOX_PROFILE")
        try:
            sandbox_library = ctypes.CDLL("/usr/lib/libsandbox.1.dylib")
            sandbox_library.sandbox_init.argtypes = [
                ctypes.c_char_p,
                ctypes.c_uint64,
                ctypes.POINTER(ctypes.c_char_p),
            ]
            sandbox_library.sandbox_init.restype = ctypes.c_int
        except (OSError, AttributeError):
            fail(Exit.PREFLIGHT, label + "_SANDBOX_LOAD")

        def initialize_child_sandbox() -> None:
            error_pointer = ctypes.c_char_p()
            if sandbox_library.sandbox_init(sandbox_profile, 0, ctypes.byref(error_pointer)) != 0:
                os._exit(126)

        preexec_fn = initialize_child_sandbox
    try:
        completed = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=child_env(),
            check=False,
            timeout=60,
            preexec_fn=preexec_fn,
        )
    except (OSError, subprocess.SubprocessError):
        fail(Exit.PREFLIGHT, label + "_EXEC")
    if sandbox_profile is not None and completed.returncode == 126:
        fail(Exit.PREFLIGHT, label + "_SANDBOX_INIT")
    if completed.returncode not in allowed_returncodes:
        fail(Exit.PREFLIGHT, label + "_RETURN")
    if len(completed.stdout) > max_bytes or len(completed.stderr) > max_bytes:
        fail(Exit.PREFLIGHT, label + "_OUTPUT_LIMIT")
    if completed.stderr:
        fail(Exit.PREFLIGHT, label + "_STDERR")
    return completed.stdout


def resolve_git() -> Tuple[str, str]:
    developer_raw = run_process(["/usr/bin/xcode-select", "-p"], "XCODE_SELECT", 4096)
    git_raw = run_process(["/usr/bin/xcrun", "--find", "git"], "XCRUN_GIT", 4096)
    if developer_raw.count(b"\n") != 1 or git_raw.count(b"\n") != 1:
        fail(Exit.PREFLIGHT, "GIT_RESOLUTION_FORMAT")
    try:
        developer = developer_raw[:-1].decode("utf-8", "strict")
        git_binary = git_raw[:-1].decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT, "GIT_RESOLUTION_ENCODING")
    if not is_nfc(developer) or not is_nfc(git_binary):
        fail(Exit.PREFLIGHT, "GIT_RESOLUTION_NFC")
    developer_meta = no_symlink_path(developer, "DEVELOPER_ROOT")
    git_meta = no_symlink_path(git_binary, "GIT_BINARY")
    try:
        contained = os.path.commonpath([developer, git_binary]) == developer
    except ValueError:
        contained = False
    if not contained or not stat.S_ISDIR(developer_meta.st_mode) or not stat.S_ISREG(git_meta.st_mode):
        fail(Exit.PREFLIGHT, "GIT_RESOLUTION_CONTAINMENT")
    if git_meta.st_uid != 0 or stat.S_IMODE(git_meta.st_mode) & 0o022 or not (git_meta.st_mode & stat.S_IXUSR):
        fail(Exit.PREFLIGHT, "GIT_BINARY_POLICY")
    return git_binary, developer


def sbpl_literal(path: str, label: str) -> str:
    if (
        not os.path.isabs(path)
        or os.path.normpath(path) != path
        or any(ord(character) < 0x20 or ord(character) > 0x7E or character in ('"', "\\") for character in path)
    ):
        fail(Exit.PREFLIGHT, label + "_SBPL_LITERAL")
    return '(literal "' + path + '")'


def sbpl_subpath(path: str, label: str) -> str:
    sbpl_literal(path, label)
    return '(subpath "' + path + '")'


def git_read_sandbox_profile(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
) -> bytes:
    marker = os.path.join(repo_root, ".git")
    literals = [
        git_binary,
        repo_root,
        marker,
        boundary.git_dir,
        boundary.common_dir,
        os.path.join(boundary.git_dir, "HEAD"),
        os.path.join(boundary.git_dir, "index"),
        os.path.join(boundary.git_dir, "commondir"),
        os.path.join(boundary.git_dir, "config.worktree"),
        os.path.join(boundary.common_dir, "HEAD"),
        os.path.join(boundary.common_dir, "config"),
        os.path.join(boundary.common_dir, "packed-refs"),
        os.path.join(boundary.common_dir, "shallow"),
        os.path.join(boundary.common_dir, "info", "exclude"),
    ]
    subpaths = [
        boundary.developer_root,
        os.path.join(boundary.common_dir, "objects"),
        os.path.join(boundary.common_dir, "refs"),
    ]
    prohibited = [
        os.path.join(boundary.common_dir, "objects", "info", "alternates"),
        os.path.join(boundary.common_dir, "objects", "info", "http-alternates"),
        os.path.join(boundary.git_dir, "objects", "info", "alternates"),
        os.path.join(boundary.git_dir, "objects", "info", "http-alternates"),
        os.path.join(boundary.common_dir, "info", "grafts"),
    ]
    allow_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in literals)
    allow_rules += "\n " + "\n ".join(sbpl_subpath(path, "GIT_SANDBOX") for path in subpaths)
    ancestor_rules_list: List[str] = []
    for path in literals + subpaths:
        sbpl_literal(path, "GIT_SANDBOX")
        ancestor_rules_list.append('(path-ancestors "' + path + '")')
    ancestor_rules = "\n ".join(ancestor_rules_list)
    deny_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in prohibited)
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        '(deny network*)\n'
        '(allow process-exec ' + sbpl_literal(git_binary, "GIT_SANDBOX") + ')\n'
        '(allow process-fork)\n'
        '(allow signal (target self))\n'
        '(allow file-read* file-test-existence\n ' + allow_rules + '\n)\n'
        '(allow file-read-metadata file-test-existence\n ' + ancestor_rules + '\n)\n'
        '(allow file-read-metadata file-test-existence\n ' + deny_rules + '\n)\n'
        '(deny file-read-data\n ' + deny_rules + '\n)\n'
    )
    return profile.encode("ascii", "strict")


def run_git(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    arguments: Sequence[str],
    label: str,
    max_bytes: int = MAX_GIT_BYTES,
    allowed_returncodes: Sequence[int] = (0,),
) -> bytes:
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
    return run_process(
        [git_binary] + hardened + ["-C", repo_root, "--no-pager"] + list(arguments),
        label,
        max_bytes=max_bytes,
        allowed_returncodes=allowed_returncodes,
        sandbox_profile=git_read_sandbox_profile(git_binary, repo_root, boundary),
    )


def git_scalar(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    arguments: Sequence[str],
    label: str,
) -> str:
    raw = run_git(git_binary, repo_root, boundary, arguments, label)
    if b"\x00" in raw or b"\r" in raw or raw.count(b"\n") != 1:
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    try:
        value = raw[:-1].decode("ascii", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT, label + "_ENCODING")
    if not value:
        fail(Exit.PREFLIGHT, label + "_EMPTY")
    return value


def other_refs_observation(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    head_ref: str,
) -> Tuple[str, int]:
    raw = run_git(git_binary, repo_root, boundary, ["show-ref"], "GIT_SHOW_REF")
    rows: List[bytes] = []
    for row in raw.splitlines(keepends=True):
        if not row.endswith(b"\n") or row.count(b" ") != 1:
            fail(Exit.PREFLIGHT, "GIT_SHOW_REF_FORMAT")
        oid, reference = row[:-1].split(b" ", 1)
        try:
            reference_text = reference.decode("ascii", "strict")
            oid_text = oid.decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_SHOW_REF_ENCODING")
        if GIT_OID_RE.fullmatch(oid_text) is None or not reference_text.startswith("refs/"):
            fail(Exit.PREFLIGHT, "GIT_SHOW_REF_VALUE")
        if reference_text != head_ref:
            rows.append(row)
    body = b"".join(sorted(rows))
    return sha256(body), len(body)


def repository_baseline(repo_root: str) -> Dict[str, Any]:
    git_binary, developer_root = resolve_git()
    git_control, (git_dir, common_dir) = inspect_git_control(repo_root)
    boundary = GitReadBoundary(developer_root, git_dir, common_dir)
    head = git_scalar(git_binary, repo_root, boundary, ["rev-parse", "--verify", "HEAD"], "GIT_HEAD")
    tree = git_scalar(git_binary, repo_root, boundary, ["rev-parse", "--verify", "HEAD^{tree}"], "GIT_TREE")
    head_ref = git_scalar(git_binary, repo_root, boundary, ["symbolic-ref", "-q", "HEAD"], "GIT_HEAD_REF")
    if GIT_OID_RE.fullmatch(head) is None or GIT_OID_RE.fullmatch(tree) is None:
        fail(Exit.PREFLIGHT, "GIT_OID")
    validate_head_ref(head_ref)
    run_git(
        git_binary,
        repo_root,
        boundary,
        ["diff-index", "--cached", "--quiet", "HEAD", "--"],
        "GIT_INDEX_HEAD",
    )
    refs_sha256, refs_bytes = other_refs_observation(git_binary, repo_root, boundary, head_ref)
    return {
        "git_binary": git_binary,
        "git_boundary": boundary,
        "head": head,
        "tree": tree,
        "head_ref": head_ref,
        "head_ref_sha256": head_ref_digest(head_ref),
        "head_ref_bytes": len(head_ref.encode("ascii", "strict")),
        "other_refs_sha256": refs_sha256,
        "other_refs_bytes": refs_bytes,
        "git_control_profile": git_control,
    }


def micro_relative(challenge: str) -> str:
    if GENERATION_CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE")
    return CONTROL_PREFIX + MICRO_BASENAME_PREFIX + challenge + ".json"


def final_relative(challenge: str) -> str:
    if GENERATION_CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE")
    return CONTROL_PREFIX + FINAL_BASENAME_PREFIX + challenge + ".json"


def _build_issue_envelope_unchecked(
    challenge: str,
    issued_at: _datetime.datetime,
    repo: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    by_role = {str(entry["role"]): entry for entry in artifacts}
    schema_artifact = by_role.get("generation-envelope-schema")
    if not isinstance(schema_artifact, dict):
        fail(Exit.INTERNAL, "GENERATION_SCHEMA_ARTIFACT")
    relative = micro_relative(challenge)
    expires = issued_at + _datetime.timedelta(hours=24)
    envelope = {
        "schema_version": "gov-01-toolchain-static-envelope-generation-envelope-v1",
        "artifact_type": "gov-01-toolchain-static-envelope-generation-envelope",
        "artifact_id": "GOV-01-STATIC-ENVELOPE-GENERATION-" + issued_at.strftime("%Y%m%d") + "-" + challenge[-16:],
        "plan_id": PLAN_ID,
        "state": "pending-user-confirmation",
        "approval_challenge_id": challenge,
        "single_use": True,
        "issued_at_utc": format_utc(issued_at),
        "not_after_utc": format_utc(expires),
        "encoding_profile": "UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys",
        "receipt_digest_profile": "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally",
        "predecessor": {
            "first_approval_envelope_raw_sha256": FIRST_ENVELOPE_SHA256,
            "first_receipt_domain_sha256": FIRST_RECEIPT_SHA256,
            "bootstrap_patch_raw_sha256": BOOTSTRAP_PATCH_SHA256,
            "bootstrap_commit_oid": BOOTSTRAP_COMMIT_OID,
            "control_preparation_envelope_raw_sha256": CONTROL_PREP_ENVELOPE_SHA256,
            "control_preparation_receipt_domain_sha256": CONTROL_PREP_RECEIPT_SHA256,
            "control_preparation_state": "independently-verified-control-prepared",
            "static_contract_commit_oid": repo["head"],
            "static_contract_tree_oid": repo["tree"],
        },
        "artifacts": [dict(entry) for entry in artifacts],
        "schema_binding": {
            "schema_id": "urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1",
            "schema_artifact_path": GENERATION_SCHEMA_RELATIVE,
            "schema_raw_file_sha256": schema_artifact["raw_file_sha256"],
            "external_draft202012_validation_required": True,
            "content_addressed_manual_checker_required": True,
            "whole_envelope_privacy_checker_required": True,
        },
        "repository_transition": {
            "authorization_baseline_head": repo["head"],
            "authorization_baseline_tree": repo["tree"],
            "authorization_baseline_head_symbolic": True,
            "authorization_baseline_head_ref_sha256": repo["head_ref_sha256"],
            "authorization_baseline_head_ref_bytes": repo["head_ref_bytes"],
            "authorization_baseline_head_ref_profile": "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized",
            "authorization_baseline_other_refs_sha256": repo["other_refs_sha256"],
            "authorization_baseline_other_refs_bytes": repo["other_refs_bytes"],
            "git_control_profile": dict(repo["git_control_profile"]),
            "micro_envelope_repo_relative": relative,
            "micro_envelope_preimage": "ABSENT",
            "generation_output_repo_relative": final_relative(challenge),
            "generation_output_preimage": "ABSENT",
            "approved_commit_shape": "current HEAD has exactly one parent equal to authorization_baseline_head; diff-tree against that parent contains exactly the micro envelope regular file with bytes equal to the approved raw envelope; no other path is added modified deleted renamed or type-changed",
            "index_must_equal_head": True,
            "refs_except_head_must_be_unchanged": True,
        },
        "generation_claim_contract": {
            "generation_claim_required": True,
            "generation_claim_profile": GENERATION_CLAIM_PROFILE,
            "generation_claim_record_profile": GENERATION_CLAIM_RECORD_PROFILE,
            "generation_claim_retention": GENERATION_CLAIM_RETENTION,
        },
        "locator_derivation_contract": {
            "caller_supplied_locator_count": 0,
            "repo_root": "derive from the no-symlink realpath of the content-addressed generator __file__ by removing its exact repo-relative suffix",
            "state_root": "read the exact target.absolute_path from the content-addressed committed control-preparation envelope only after this generation receipt is approved",
            "key_file": "exact direct child hmac.key beneath the derived state root",
            "claims_root": "exact direct child claims beneath the derived state root; validate retained GOV01-SA claim directories and generation-claim-GOV01-GEN directories, require this GEN claim preimage ABSENT before fresh entropy, and require the fresh acquisition challenge child preimage ABSENT",
            "cache_root": "pwd.getpwuid(the control-preparation expected created uid).pw_dir plus exact suffix .npm; normalize once, require absolute realpath equality, owner uid equality, no symlink component and no Vault component",
            "generation_output": "repo root plus exact control-prefix regular-file name GOV-01-toolchain-static-acquisition-pending-<approved-GOV01-GEN-challenge>.json; the final envelope separately carries one fresh GOV01-SA acquisition challenge",
            "final_locator_commitment_timing": "resolve derived private locators and calculate domain-separated keyed commitments only after approval; serialize commitments but never raw private locators into the final acquisition envelope",
        },
        "authorized_reads": {
            "public_repo_artifact_policy": "only exact versioned artifact paths listed in this envelope plus package.json package-lock.json .gitignore and Git control evidence required by the frozen static executor",
            "private_roles_after_approval": [
                "exact 0600 32-byte hmac.key for domain-separated HMAC only",
                "derived control root and claims metadata plus exact fresh acquisition challenge child absence",
                "exact locator-free canonical control-preparation receipt content for predecessor-chain verification",
                "Git marker commondir local config index refs contained hooks and dirty or untracked metadata and regular content, with Vault and .obsidian paths rejected before open",
                "package-lock-selected direct-SRI npm cache content-v2 blobs only",
                "target-worktree-associated Claude process census evidence",
            ],
            "git_generation_output_exclusion": "exclude exactly the one derived regular-file generation output path from Git status and dirty-content commitment; never exclude its parent directory or a wildcard subtree; separately require output preimage ABSENT and later bind raw output bytes by the external acquisition receipt",
            "vault_read_count": 0,
            "npm_cache_index_read_count": 0,
            "user_or_managed_settings_read_count": 0,
        },
        "authorized_subprocesses": {
            "roles": [
                "xcode-select-resolver",
                "xcrun-resolver",
                "git-read-only-evidence",
                "pgrep-read-only-evidence",
                "lsof-read-only-evidence",
            ],
            "shell_allowed": False,
            "network_allowed": False,
            "node_npm_npx_openspec_allowed": False,
            "environment_profile": "new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp for public resolver and Git evidence; GIT_OPTIONAL_LOCKS=0; global and system config disabled; protocol.allow=never; fsmonitor hooks attributes and external alternates rejected before Git status",
            "git_child_sandbox_profile": GENERATION_GIT_CHILD_SANDBOX_PROFILE_V1,
        },
        "mutation_scope": {
            "first_authorized_write": "exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge",
            "allowed_persistent_mutations": [
                "create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container",
                "create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories",
                "create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix",
                "fsync its already-existing parent directory",
            ],
            "output_mode": "0644",
            "overwrite_allowed": False,
            "cleanup_allowed": False,
            "sidecar_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
        },
        "challenge_and_time_contract": {
            "generation_entropy": "exactly one os.urandom(32) call before the public generation micro-envelope is written; lowercase 64-hex suffix; caller-supplied entropy forbidden",
            "acquisition_entropy": "exactly one os.urandom(32) call after generation approval and before private census; lowercase 64-hex suffix; caller-supplied entropy forbidden",
            "namespace_separation": "generation challenge uses GOV01-GEN and acquisition challenge uses GOV01-SA; equality or cross-namespace reuse is impossible by grammar",
            "challenge_date_binding": "each challenge YYYYMMDD component equals its own canonical UTC issued or census date",
            "clock_skew_ceiling_seconds": 300,
            "ttl_ceiling_seconds": 86400,
            "expiry_checkpoints": [
                "micro-envelope load",
                "immediately before the persistent generation claim mkdir",
                "after generation claim verification and immediately before the public output create",
                "after output reopen before emitting pending-user-confirmation",
            ],
        },
        "failure_contract": {
            "pre_output_failure": "before the generation claim mkdir, zero write; the exact approved read-only generation preflight may rerun before expiry only while every bound public and private input is unchanged and both claim and output remain absent",
            "post_create_failure": "after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority",
            "existing_complete_output": "under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything",
            "existing_partial_or_invalid_output": "a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope",
            "retry_policy": "single-use begins at successful exclusive generation claim mkdir; pre-claim read-only failures may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest",
        },
        "success_contract": {
            "maximum_state": "ACQUISITION-ENVELOPE-FROZEN-PENDING-USER-CONFIRMATION",
            "stdout_fields": [
                "state",
                "artifact_path",
                "raw_envelope_receipt_digest",
                "generation_approval_challenge_id",
                "approval_challenge_id",
                "not_after_utc",
            ],
            "acquisition_execution_authorized": False,
            "runtime_use_authorized": False,
            "next_required_authority": "user must separately cite the exact final acquisition raw-envelope receipt digest and GOV01-SA challenge before verify or acquire; acquisition success still stops at static-attested-unexecuted",
        },
        "privacy": {
            "whole_envelope_checker": "field-aware recursive checker before write and before stdout; repo paths use strict relative grammar; tool logical IDs and versions use role-specific ASCII grammar; only schema-enumerated fixed public system command locators and placeholders are allowed; all other absolute home file-URI Vault .obsidian control bidi and secret-bearing values are rejected",
            "raw_private_locator_public_count": 0,
            "private_key_publication_allowed": False,
            "raw_command_output_publication_allowed": False,
            "vault_read_count": 0,
            "graphiti_call_count": 0,
            "network_call_count": 0,
        },
    }
    return envelope


def build_issue_envelope(
    challenge: str,
    issued_at: _datetime.datetime,
    repo: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    envelope = _build_issue_envelope_unchecked(challenge, issued_at, repo, artifacts)
    validate_generation_envelope(envelope, now=issued_at, require_pending=True)
    return envelope


def require_exact_keys(value: Any, expected: Iterable[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != set(expected):
        fail(Exit.CONTRACT, label + "_FIELDS")
    return value


def validate_generation_envelope(
    envelope: Any,
    now: _datetime.datetime,
    require_pending: bool,
) -> None:
    top = require_exact_keys(
        envelope,
        (
            "schema_version", "artifact_type", "artifact_id", "plan_id", "state",
            "approval_challenge_id", "single_use", "issued_at_utc", "not_after_utc",
            "encoding_profile", "receipt_digest_profile", "predecessor", "artifacts",
            "schema_binding", "repository_transition", "locator_derivation_contract",
            "generation_claim_contract",
            "authorized_reads", "authorized_subprocesses", "mutation_scope",
            "challenge_and_time_contract", "failure_contract", "success_contract", "privacy",
        ),
        "ENVELOPE",
    )
    constants = {
        "schema_version": "gov-01-toolchain-static-envelope-generation-envelope-v1",
        "artifact_type": "gov-01-toolchain-static-envelope-generation-envelope",
        "plan_id": PLAN_ID,
        "state": "pending-user-confirmation",
        "single_use": True,
        "encoding_profile": "UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys",
        "receipt_digest_profile": "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-envelope-bytes); digest supplied by user and stored externally",
    }
    for key, expected in constants.items():
        if top.get(key) != expected:
            fail(Exit.CONTRACT, "ENVELOPE_" + key.upper())
    challenge = top.get("approval_challenge_id")
    if not isinstance(challenge, str) or GENERATION_CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE")
    issued = parse_utc(top.get("issued_at_utc"), "ISSUED_AT")
    expires = parse_utc(top.get("not_after_utc"), "NOT_AFTER")
    if challenge[10:18] != issued.strftime("%Y%m%d"):
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE_DATE")
    if expires <= issued or (expires - issued).total_seconds() != 86400:
        fail(Exit.CONTRACT, "GENERATION_TTL")
    if require_pending and (issued > now or now >= expires):
        fail(Exit.CONTRACT, "GENERATION_EXPIRY")
    if top.get("artifact_id") != "GOV-01-STATIC-ENVELOPE-GENERATION-" + issued.strftime("%Y%m%d") + "-" + challenge[-16:]:
        fail(Exit.CONTRACT, "ARTIFACT_ID")
    predecessor = require_exact_keys(
        top.get("predecessor"),
        (
            "first_approval_envelope_raw_sha256", "first_receipt_domain_sha256",
            "bootstrap_patch_raw_sha256", "bootstrap_commit_oid",
            "control_preparation_envelope_raw_sha256",
            "control_preparation_receipt_domain_sha256", "control_preparation_state",
            "static_contract_commit_oid", "static_contract_tree_oid",
        ),
        "PREDECESSOR",
    )
    predecessor_constants = {
        "first_approval_envelope_raw_sha256": FIRST_ENVELOPE_SHA256,
        "first_receipt_domain_sha256": FIRST_RECEIPT_SHA256,
        "bootstrap_patch_raw_sha256": BOOTSTRAP_PATCH_SHA256,
        "bootstrap_commit_oid": BOOTSTRAP_COMMIT_OID,
        "control_preparation_envelope_raw_sha256": CONTROL_PREP_ENVELOPE_SHA256,
        "control_preparation_receipt_domain_sha256": CONTROL_PREP_RECEIPT_SHA256,
        "control_preparation_state": "independently-verified-control-prepared",
    }
    for key, expected in predecessor_constants.items():
        if predecessor.get(key) != expected:
            fail(Exit.CONTRACT, "PREDECESSOR_" + key.upper())
    for key in ("static_contract_commit_oid", "static_contract_tree_oid"):
        if not isinstance(predecessor.get(key), str) or GIT_OID_RE.fullmatch(str(predecessor.get(key))) is None:
            fail(Exit.CONTRACT, "PREDECESSOR_GIT_OID")
    artifacts = top.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(ARTIFACT_SPECS):
        fail(Exit.CONTRACT, "ARTIFACT_COUNT")
    for observed, (role, path) in zip(artifacts, ARTIFACT_SPECS):
        artifact = require_exact_keys(
            observed,
            ("role", "path", "file_kind", "byte_length", "raw_file_sha256"),
            "ARTIFACT",
        )
        if artifact.get("role") != role or artifact.get("path") != path or artifact.get("file_kind") != "regular":
            fail(Exit.CONTRACT, "ARTIFACT_ROLE_PATH")
        validate_relative(path, "ARTIFACT_PATH")
        if not isinstance(artifact.get("byte_length"), int) or isinstance(artifact.get("byte_length"), bool) or not 1 <= int(artifact["byte_length"]) <= MAX_FILE_BYTES:
            fail(Exit.CONTRACT, "ARTIFACT_SIZE")
        if not isinstance(artifact.get("raw_file_sha256"), str) or SHA256_RE.fullmatch(str(artifact["raw_file_sha256"])) is None:
            fail(Exit.CONTRACT, "ARTIFACT_SHA256")
    by_role = {entry["role"]: entry for entry in artifacts}
    predecessor_artifact_digests = {
        "first-receipt-envelope": FIRST_ENVELOPE_SHA256,
        "bootstrap-patch": BOOTSTRAP_PATCH_SHA256,
        "control-prep-envelope": CONTROL_PREP_ENVELOPE_SHA256,
    }
    if any(
        by_role[role]["raw_file_sha256"] != expected
        for role, expected in predecessor_artifact_digests.items()
    ):
        fail(Exit.CONTRACT, "PREDECESSOR_ARTIFACT_SHA256")
    schema_binding = require_exact_keys(
        top.get("schema_binding"),
        (
            "schema_id", "schema_artifact_path", "schema_raw_file_sha256",
            "external_draft202012_validation_required", "content_addressed_manual_checker_required",
            "whole_envelope_privacy_checker_required",
        ),
        "SCHEMA_BINDING",
    )
    if (
        schema_binding.get("schema_id") != "urn:canvas-learning-system:gov-01:toolchain-static-envelope-generation-envelope:v1"
        or schema_binding.get("schema_artifact_path") != GENERATION_SCHEMA_RELATIVE
        or schema_binding.get("schema_raw_file_sha256") != by_role["generation-envelope-schema"]["raw_file_sha256"]
        or schema_binding.get("external_draft202012_validation_required") is not True
        or schema_binding.get("content_addressed_manual_checker_required") is not True
        or schema_binding.get("whole_envelope_privacy_checker_required") is not True
    ):
        fail(Exit.CONTRACT, "SCHEMA_BINDING")
    transition = require_exact_keys(
        top.get("repository_transition"),
        (
            "authorization_baseline_head", "authorization_baseline_tree",
            "authorization_baseline_head_symbolic", "authorization_baseline_head_ref_sha256",
            "authorization_baseline_head_ref_bytes", "authorization_baseline_head_ref_profile",
            "authorization_baseline_other_refs_sha256",
            "authorization_baseline_other_refs_bytes", "git_control_profile", "micro_envelope_repo_relative",
            "micro_envelope_preimage", "generation_output_repo_relative", "generation_output_preimage",
            "approved_commit_shape", "index_must_equal_head",
            "refs_except_head_must_be_unchanged",
        ),
        "REPOSITORY_TRANSITION",
    )
    if transition.get("authorization_baseline_head") != predecessor.get("static_contract_commit_oid") or transition.get("authorization_baseline_tree") != predecessor.get("static_contract_tree_oid"):
        fail(Exit.CONTRACT, "REPOSITORY_TRANSITION_PREDECESSOR")
    if transition.get("micro_envelope_repo_relative") != micro_relative(challenge):
        fail(Exit.CONTRACT, "MICRO_ENVELOPE_PATH")
    if transition.get("generation_output_repo_relative") != final_relative(challenge):
        fail(Exit.CONTRACT, "GENERATION_OUTPUT_PATH")
    if transition.get("authorization_baseline_head_symbolic") is not True:
        fail(Exit.CONTRACT, "HEAD_SYMBOLIC")
    if not isinstance(transition.get("authorization_baseline_head_ref_sha256"), str) or SHA256_RE.fullmatch(str(transition.get("authorization_baseline_head_ref_sha256"))) is None:
        fail(Exit.CONTRACT, "HEAD_REF_SHA256")
    if not isinstance(transition.get("authorization_baseline_head_ref_bytes"), int) or isinstance(transition.get("authorization_baseline_head_ref_bytes"), bool) or not 1 <= int(transition["authorization_baseline_head_ref_bytes"]) <= 251:
        fail(Exit.CONTRACT, "HEAD_REF_BYTES")
    if transition.get("authorization_baseline_head_ref_profile") != "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-HEAD-REF/v1) || NUL || exact symbolic HEAD ref ASCII bytes); raw ref is never serialized":
        fail(Exit.CONTRACT, "HEAD_REF_PROFILE")
    if not isinstance(transition.get("authorization_baseline_other_refs_sha256"), str) or SHA256_RE.fullmatch(str(transition.get("authorization_baseline_other_refs_sha256"))) is None:
        fail(Exit.CONTRACT, "OTHER_REFS_SHA256")
    if not isinstance(transition.get("authorization_baseline_other_refs_bytes"), int) or isinstance(transition.get("authorization_baseline_other_refs_bytes"), bool) or not 0 <= int(transition["authorization_baseline_other_refs_bytes"]) <= MAX_GIT_BYTES:
        fail(Exit.CONTRACT, "OTHER_REFS_BYTES")
    if transition.get("git_control_profile") != {
        "marker_kind": transition.get("git_control_profile", {}).get("marker_kind")
        if isinstance(transition.get("git_control_profile"), dict)
        else None,
        "common_directory_relation": transition.get("git_control_profile", {}).get("common_directory_relation")
        if isinstance(transition.get("git_control_profile"), dict)
        else None,
        "include_controls_absent": True,
        "alternate_object_controls_absent": True,
    }:
        fail(Exit.CONTRACT, "GIT_CONTROL_PROFILE_FIELDS")
    if transition["git_control_profile"].get("marker_kind") not in ("gitfile", "directory"):
        fail(Exit.CONTRACT, "GIT_CONTROL_PROFILE_MARKER")
    if transition["git_control_profile"].get("common_directory_relation") not in (
        "git-directory-is-common-directory",
        "git-directory-contained-under-common-worktrees",
    ):
        fail(Exit.CONTRACT, "GIT_CONTROL_PROFILE_RELATION")
    if (
        transition["git_control_profile"].get("marker_kind"),
        transition["git_control_profile"].get("common_directory_relation"),
    ) not in {
        ("directory", "git-directory-is-common-directory"),
        ("gitfile", "git-directory-contained-under-common-worktrees"),
    }:
        fail(Exit.CONTRACT, "GIT_CONTROL_PROFILE_RELATION_BINDING")
    if (
        transition.get("micro_envelope_preimage") != "ABSENT"
        or transition.get("generation_output_preimage") != "ABSENT"
        or transition.get("index_must_equal_head") is not True
        or transition.get("refs_except_head_must_be_unchanged") is not True
    ):
        fail(Exit.CONTRACT, "REPOSITORY_TRANSITION_AUTHORITY")
    for section_name in (
        "locator_derivation_contract", "generation_claim_contract", "authorized_reads", "authorized_subprocesses",
        "mutation_scope", "challenge_and_time_contract", "failure_contract",
        "success_contract", "privacy",
    ):
        if not isinstance(top.get(section_name), dict):
            fail(Exit.CONTRACT, section_name.upper() + "_SHAPE")
    claim_contract = require_exact_keys(
        top.get("generation_claim_contract"),
        (
            "generation_claim_required",
            "generation_claim_profile",
            "generation_claim_record_profile",
            "generation_claim_retention",
        ),
        "GENERATION_CLAIM_CONTRACT",
    )
    if claim_contract != {
        "generation_claim_required": True,
        "generation_claim_profile": GENERATION_CLAIM_PROFILE,
        "generation_claim_record_profile": GENERATION_CLAIM_RECORD_PROFILE,
        "generation_claim_retention": GENERATION_CLAIM_RETENTION,
    }:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_CONTRACT")
    mutation = top["mutation_scope"]
    for key in ("overwrite_allowed", "cleanup_allowed", "sidecar_allowed", "commit_allowed", "push_allowed"):
        if mutation.get(key) is not False:
            fail(Exit.CONTRACT, "MUTATION_AUTHORITY")
    privacy = top["privacy"]
    for key in ("raw_private_locator_public_count", "vault_read_count", "graphiti_call_count", "network_call_count"):
        if privacy.get(key) != 0 or isinstance(privacy.get(key), bool):
            fail(Exit.PRIVACY, "PRIVACY_COUNT")
    for key in ("private_key_publication_allowed", "raw_command_output_publication_allowed"):
        if privacy.get(key) is not False:
            fail(Exit.PRIVACY, "PRIVACY_AUTHORITY")
    # This public micro-envelope must not contain any machine-private locator.
    def walk(value: Any) -> None:
        if isinstance(value, str):
            lowered = value.casefold()
            if (
                any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in value)
                or value.startswith("/")
                or value.startswith("~")
                or "\\" in value
                or "/users/" in lowered
                or "file://" in lowered
            ):
                fail(Exit.PRIVACY, "MICRO_ENVELOPE_PRIVATE_VALUE")
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            for key, child in value.items():
                walk(key)
                walk(child)
    walk(envelope)
    expected = _build_issue_envelope_unchecked(
        challenge,
        issued,
        {
            "head": predecessor["static_contract_commit_oid"],
            "tree": predecessor["static_contract_tree_oid"],
            "head_ref_sha256": transition["authorization_baseline_head_ref_sha256"],
            "head_ref_bytes": transition["authorization_baseline_head_ref_bytes"],
            "other_refs_sha256": transition["authorization_baseline_other_refs_sha256"],
            "other_refs_bytes": transition["authorization_baseline_other_refs_bytes"],
            "git_control_profile": transition["git_control_profile"],
        },
        artifacts,
    )
    if envelope != expected:
        fail(Exit.CONTRACT, "ENVELOPE_EXACT_CONTRACT")


def open_output_parent(repo_root: str, relative: str) -> Tuple[int, str]:
    components = validate_relative(relative, "OUTPUT_PATH")
    repo_fd = os.open(
        repo_root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    current = repo_fd
    try:
        for component in components[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            if current != repo_fd:
                os.close(current)
            current = next_fd
        result = os.dup(current)
    except OSError:
        fail(Exit.UNSAFE_PATH, "OUTPUT_PARENT")
    finally:
        if current != repo_fd:
            os.close(current)
        os.close(repo_fd)
    return result, components[-1]


def assert_absent(parent_fd: int, name: str, label: str) -> None:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError:
        fail(Exit.PREFLIGHT, label + "_LSTAT")
    fail(Exit.PREFLIGHT, label + "_NOT_ABSENT")


def write_exclusive_public_file(repo_root: str, relative: str, raw: bytes) -> None:
    parent_fd, name = open_output_parent(repo_root, relative)
    fd: Optional[int] = None
    try:
        assert_absent(parent_fd, name, "OUTPUT")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(name, flags, 0o644, dir_fd=parent_fd)
        except FileExistsError:
            fail(Exit.WRITE, "OUTPUT_ALREADY_EXISTS")
        except OSError:
            fail(Exit.WRITE, "OUTPUT_CREATE")
        os.fchmod(fd, 0o644)
        created = os.fstat(fd)
        if (
            not stat.S_ISREG(created.st_mode)
            or created.st_uid != os.getuid()
            or stat.S_IMODE(created.st_mode) != 0o644
            or created.st_nlink != 1
        ):
            fail(Exit.WRITE, "OUTPUT_POLICY")
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(fd, raw[offset:])
            except OSError as error:
                if error.errno == errno.EINTR:
                    continue
                fail(Exit.WRITE, "OUTPUT_WRITE")
            if written <= 0:
                fail(Exit.WRITE, "OUTPUT_WRITE")
            offset += written
        os.fsync(fd)
        final = os.fstat(fd)
        path_meta = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            final.st_dev,
            final.st_ino,
            final.st_uid,
            final.st_gid,
            stat.S_IMODE(final.st_mode),
            final.st_nlink,
            final.st_size,
        ) != (
            path_meta.st_dev,
            path_meta.st_ino,
            path_meta.st_uid,
            path_meta.st_gid,
            stat.S_IMODE(path_meta.st_mode),
            path_meta.st_nlink,
            path_meta.st_size,
        ) or final.st_size != len(raw):
            fail(Exit.WRITE, "OUTPUT_FINAL_IDENTITY")
        os.fsync(parent_fd)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        os.close(parent_fd)
    reopened, metadata = open_relative_regular(repo_root, relative, "OUTPUT_REOPEN")
    if reopened != raw or metadata.st_size != len(raw):
        fail(Exit.WRITE, "OUTPUT_REOPEN_MISMATCH")


def issue() -> Dict[str, Any]:
    require_python_isolation()
    repo_root, _repo_meta = derive_repo_root()
    baseline = repository_baseline(repo_root)
    artifacts = artifact_observations(repo_root)
    assert_artifacts_match_head(baseline["git_binary"], repo_root, baseline["git_boundary"], artifacts)
    issued_at = utc_now_second()
    entropy = os.urandom(32)
    if len(entropy) != 32:
        fail(Exit.RUNTIME, "GENERATION_ENTROPY")
    challenge = "GOV01-GEN-" + issued_at.strftime("%Y%m%d") + "-" + entropy.hex()
    relative = micro_relative(challenge)
    final_output_relative = final_relative(challenge)
    parent_fd, name = open_output_parent(repo_root, relative)
    try:
        assert_absent(parent_fd, name, "MICRO_ENVELOPE")
    finally:
        os.close(parent_fd)
    final_parent_fd, final_name = open_output_parent(repo_root, final_output_relative)
    try:
        assert_absent(final_parent_fd, final_name, "GENERATION_OUTPUT")
    finally:
        os.close(final_parent_fd)
    envelope = build_issue_envelope(challenge, issued_at, baseline, artifacts)
    raw = canonical_json(envelope)
    parsed = parse_json(raw, "MICRO_ENVELOPE")
    if parsed != envelope:
        fail(Exit.INTERNAL, "MICRO_ENVELOPE_ROUNDTRIP")
    validate_generation_envelope(parsed, issued_at, require_pending=True)
    # Artifact and repository inputs must remain stable through the first write.
    current_artifacts = artifact_observations(repo_root)
    current_baseline = repository_baseline(repo_root)
    assert_artifacts_match_head(
        current_baseline["git_binary"],
        repo_root,
        current_baseline["git_boundary"],
        current_artifacts,
    )
    if current_artifacts != artifacts or current_baseline != baseline:
        fail(Exit.PREFLIGHT, "ISSUE_INPUT_DRIFT")
    validate_generation_envelope(parsed, utc_now_second(), require_pending=True)
    write_exclusive_public_file(repo_root, relative, raw)
    validate_generation_envelope(parsed, utc_now_second(), require_pending=True)
    return {
        "state": "GEN-ENVELOPE-WRITTEN-REQUIRES-EXTERNAL-DRAFT-VALIDATION-AND-EXACT-COMMIT",
        "artifact_path": relative,
        "raw_envelope_receipt_digest": receipt_digest(raw),
        "approval_challenge_id": challenge,
        "not_after_utc": envelope["not_after_utc"],
        "private_control_key_cache_process_read_count": 0,
        "authorized_repository_git_control_read": True,
        "network_call_count": 0,
        "commit_allowed": False,
        "push_allowed": False,
    }


def load_approved_generation_request(
    expected_receipt: str,
    expected_challenge: str,
) -> Dict[str, Any]:
    """Verify the public GEN receipt and its exact one-file commit transition.

    This function performs no control-root, key, cache, passwd, process, Vault,
    or acquisition read.  Callers may derive those private inputs only after it
    returns successfully.
    """

    if not isinstance(expected_receipt, str) or SHA256_RE.fullmatch(expected_receipt) is None:
        fail(Exit.USAGE, "GENERATION_RECEIPT_FORMAT")
    if not isinstance(expected_challenge, str) or GENERATION_CHALLENGE_RE.fullmatch(expected_challenge) is None:
        fail(Exit.USAGE, "GENERATION_CHALLENGE_FORMAT")
    repo_root, _repo_meta = derive_repo_root()
    relative = micro_relative(expected_challenge)
    raw, _metadata = open_relative_regular(repo_root, relative, "APPROVED_MICRO_ENVELOPE")
    actual_receipt = receipt_digest(raw)
    if not hmac.compare_digest(actual_receipt, expected_receipt):
        fail(Exit.CONTRACT, "GENERATION_RECEIPT_MISMATCH")
    envelope = parse_json(raw, "APPROVED_MICRO_ENVELOPE")
    now = utc_now_second()
    validate_generation_envelope(envelope, now, require_pending=True)
    if envelope.get("approval_challenge_id") != expected_challenge:
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE_MISMATCH")

    # Only after raw receipt, challenge, calendar and manual contract pass may
    # the public repository transition be inspected.
    current = repository_baseline(repo_root)
    transition = envelope["repository_transition"]
    parent_line = run_git(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["rev-list", "--parents", "-n", "1", "HEAD"],
        "GIT_MICRO_PARENT",
        max_bytes=4096,
    )
    if parent_line.count(b"\n") != 1 or not parent_line.endswith(b"\n"):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_FORMAT")
    try:
        parent_fields = parent_line[:-1].decode("ascii", "strict").split(" ")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_ENCODING")
    if (
        len(parent_fields) != 2
        or parent_fields[0] != current["head"]
        or parent_fields[1] != transition.get("authorization_baseline_head")
        or GIT_OID_RE.fullmatch(parent_fields[1]) is None
    ):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_IDENTITY")
    parent_tree = git_scalar(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["rev-parse", "--verify", parent_fields[1] + "^{tree}"],
        "GIT_MICRO_PARENT_TREE",
    )
    if parent_tree != transition.get("authorization_baseline_tree"):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_TREE")
    changed = run_git(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent_fields[1], current["head"], "--"],
        "GIT_MICRO_DIFF",
        max_bytes=4096,
    )
    if changed != relative.encode("utf-8") + b"\x00":
        fail(Exit.PREFLIGHT, "GIT_MICRO_DIFF_SCOPE")
    if run_git(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["ls-tree", "-z", "--full-tree", parent_fields[1], "--", relative],
        "GIT_MICRO_PARENT_PREIMAGE",
        max_bytes=4096,
    ):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_PREIMAGE")
    current_entry = run_git(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["ls-tree", "-z", "--full-tree", current["head"], "--", relative],
        "GIT_MICRO_CURRENT_ENTRY",
        max_bytes=4096,
    )
    if (
        current_entry.count(b"\x00") != 1
        or not current_entry.endswith(b"\x00")
        or not current_entry.startswith(b"100644 blob ")
        or b"\t" + relative.encode("utf-8") + b"\x00" not in current_entry
    ):
        fail(Exit.PREFLIGHT, "GIT_MICRO_CURRENT_KIND")
    committed_raw = run_git(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        ["show", "HEAD:" + relative],
        "GIT_MICRO_CURRENT_BYTES",
        max_bytes=MAX_FILE_BYTES,
    )
    if committed_raw != raw:
        fail(Exit.PREFLIGHT, "GIT_MICRO_CURRENT_BYTES")
    if (
        current.get("head_ref_sha256") != transition.get("authorization_baseline_head_ref_sha256")
        or current.get("head_ref_bytes") != transition.get("authorization_baseline_head_ref_bytes")
        or current.get("other_refs_sha256") != transition.get("authorization_baseline_other_refs_sha256")
        or current.get("other_refs_bytes") != transition.get("authorization_baseline_other_refs_bytes")
        or current.get("git_control_profile") != transition.get("git_control_profile")
    ):
        fail(Exit.PREFLIGHT, "GIT_MICRO_AUTHORITY_DRIFT")
    current_artifacts = artifact_observations(repo_root)
    if current_artifacts != envelope.get("artifacts"):
        fail(Exit.PREFLIGHT, "GENERATION_ARTIFACT_DRIFT")
    assert_artifacts_match_head(
        current["git_binary"],
        repo_root,
        current["git_boundary"],
        current_artifacts,
    )
    return {
        "repo_root": repo_root,
        "micro_envelope": envelope,
        "micro_raw": raw,
        "micro_receipt": actual_receipt,
        "micro_relative": relative,
        "generation_output_relative": final_relative(expected_challenge),
        "generation_output_preexisting": output_exists(repo_root, final_relative(expected_challenge)),
        "current_head": current["head"],
        "current_tree": current["tree"],
        "git_binary": current["git_binary"],
    }


def output_exists(repo_root: str, relative: str) -> bool:
    parent_fd, name = open_output_parent(repo_root, relative)
    try:
        try:
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError:
            fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_LSTAT")
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_EXISTING_KIND")
        return True
    finally:
        os.close(parent_fd)


def load_content_addressed_executor(context: Mapping[str, Any]) -> types.ModuleType:
    """Load only the executor bytes approved by the committed GEN envelope."""

    repo_root = context.get("repo_root")
    micro = context.get("micro_envelope")
    if not isinstance(repo_root, str) or not isinstance(micro, dict):
        fail(Exit.INTERNAL, "BOUND_EXECUTOR_CONTEXT")
    artifacts = micro.get("artifacts")
    if not isinstance(artifacts, list):
        fail(Exit.CONTRACT, "BOUND_EXECUTOR_ARTIFACTS")
    matches = [entry for entry in artifacts if isinstance(entry, dict) and entry.get("role") == "static-executor"]
    if len(matches) != 1:
        fail(Exit.CONTRACT, "BOUND_EXECUTOR_ARTIFACT_COUNT")
    artifact = matches[0]
    path = artifact.get("path")
    expected_length = artifact.get("byte_length")
    expected_digest = artifact.get("raw_file_sha256")
    if (
        path != CONTROL_PREFIX + "GOV-01-toolchain-static-acquisition-v2.py"
        or type(expected_length) is not int
        or expected_length <= 0
        or not isinstance(expected_digest, str)
        or SHA256_RE.fullmatch(expected_digest) is None
    ):
        fail(Exit.CONTRACT, "BOUND_EXECUTOR_ARTIFACT")
    raw, metadata = open_relative_regular(repo_root, path, "BOUND_EXECUTOR")
    if (
        len(raw) != expected_length
        or metadata.st_size != expected_length
        or not hmac.compare_digest(sha256(raw), expected_digest)
    ):
        fail(Exit.PREFLIGHT, "BOUND_EXECUTOR_DRIFT")
    namespace = types.ModuleType("_gov01_content_addressed_static_acquisition_v2")
    # The executor independently attests its launch source path and bytes.
    # This absolute path is never serialized or included in an exception.
    namespace.__file__ = os.path.join(repo_root, *path.split("/"))
    namespace.__package__ = None
    try:
        code = compile(raw, namespace.__file__, "exec", dont_inherit=True, optimize=0)
        exec(code, namespace.__dict__)
    except BaseException:
        fail(Exit.PREFLIGHT, "BOUND_EXECUTOR_LOAD")
    if getattr(namespace, "SCRIPT_VERSION", None) != "gov01-static-acquisition-executor-draft-v2":
        fail(Exit.PREFLIGHT, "BOUND_EXECUTOR_VERSION")
    contract_error_type = getattr(namespace, "ContractError", None)
    if not isinstance(contract_error_type, type) or not issubclass(contract_error_type, BaseException):
        fail(Exit.PREFLIGHT, "BOUND_EXECUTOR_ERROR_ABI")
    for name in (
        "derive_generation_runtime_args_v2",
        "collect_generation_observations_v2",
        "build_pending_envelope_v2",
        "probe_generation_claim_v2",
        "create_generation_claim_v2",
        "verify_generation_claim_recovery_v2",
        "canonical_json",
        "parse_json_bytes",
        "validate_manual_envelope_contract",
        "has_forbidden_pending_envelope_value",
    ):
        if not callable(getattr(namespace, name, None)):
            fail(Exit.PREFLIGHT, "BOUND_EXECUTOR_ABI")
    return namespace


def generation_authorization(context: Mapping[str, Any]) -> Dict[str, Any]:
    micro = context.get("micro_envelope")
    raw = context.get("micro_raw")
    if not isinstance(micro, dict) or not isinstance(raw, bytes):
        fail(Exit.INTERNAL, "GENERATION_AUTHORIZATION_CONTEXT")
    transition = micro.get("repository_transition")
    claim_contract = micro.get("generation_claim_contract")
    challenge = micro.get("approval_challenge_id")
    if not isinstance(transition, dict) or not isinstance(claim_contract, dict) or not isinstance(challenge, str):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_SOURCE")
    result = {
        "profile": "gov01-static-envelope-generation-authority-v1",
        "approval_challenge_id": challenge,
        "approval_envelope_repo_relative_path": context.get("micro_relative"),
        "generated_acquisition_envelope_repo_relative_path": context.get("generation_output_relative"),
        "raw_envelope_sha256": sha256(raw),
        "receipt_digest": context.get("micro_receipt"),
        "receipt_domain_profile": (
            "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || "
            "raw-generation-envelope-bytes)"
        ),
        "authorization_parent_commit_oid": transition.get("authorization_baseline_head"),
        "authorization_parent_tree_oid": transition.get("authorization_baseline_tree"),
        "authorization_commit_oid": context.get("current_head"),
        "authorization_tree_oid": context.get("current_tree"),
        "commit_transition_profile": (
            "single parent commit changing exactly the generation approval envelope path from ABSENT to the "
            "approved canonical raw bytes"
        ),
        "state": "approved-single-path-commit",
        "generation_claim_required": True,
        "generation_claim_profile": GENERATION_CLAIM_PROFILE,
        "generation_claim_record_profile": GENERATION_CLAIM_RECORD_PROFILE,
        "generation_claim_retention": GENERATION_CLAIM_RETENTION,
    }
    if (
        GENERATION_CHALLENGE_RE.fullmatch(challenge) is None
        or result["approval_envelope_repo_relative_path"] != micro_relative(challenge)
        or result["generated_acquisition_envelope_repo_relative_path"] != final_relative(challenge)
        or result["receipt_digest"] != receipt_digest(raw)
        or claim_contract
        != {
            "generation_claim_required": True,
            "generation_claim_profile": GENERATION_CLAIM_PROFILE,
            "generation_claim_record_profile": GENERATION_CLAIM_RECORD_PROFILE,
            "generation_claim_retention": GENERATION_CLAIM_RETENTION,
        }
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_BINDING")
    for name in (
        "raw_envelope_sha256",
        "receipt_digest",
    ):
        if not isinstance(result[name], str) or SHA256_RE.fullmatch(result[name]) is None:
            fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_DIGEST")
    for name in (
        "authorization_parent_commit_oid",
        "authorization_parent_tree_oid",
        "authorization_commit_oid",
        "authorization_tree_oid",
    ):
        if not isinstance(result[name], str) or GIT_OID_RE.fullmatch(result[name]) is None:
            fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_OID")
    return result


def call_bound_executor(label: str, function: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return function(*args, **kwargs)
    except BaseException:
        fail(Exit.PREFLIGHT, label)
    raise AssertionError("unreachable")


def validate_pending_candidate(
    executor: types.ModuleType,
    envelope: Any,
    raw: bytes,
) -> Dict[str, Any]:
    if not isinstance(envelope, dict):
        fail(Exit.CONTRACT, "PENDING_ENVELOPE_ROOT")
    canonical = call_bound_executor("PENDING_CANONICAL", executor.canonical_json, envelope)
    if not isinstance(canonical, bytes) or canonical != raw:
        fail(Exit.CONTRACT, "PENDING_ENVELOPE_CANONICAL")
    call_bound_executor(
        "PENDING_MANUAL_CONTRACT",
        executor.validate_manual_envelope_contract,
        envelope,
    )
    if call_bound_executor(
        "PENDING_PRIVACY_CONTRACT",
        executor.has_forbidden_pending_envelope_value,
        envelope,
    ):
        fail(Exit.PRIVACY, "PENDING_ENVELOPE_PRIVACY")
    return envelope


def build_current_pending_candidate(
    executor: types.ModuleType,
    context: Mapping[str, Any],
    authorization: Mapping[str, Any],
    runtime_args: Any,
    acquisition_challenge: str,
    census_at_utc: str,
    not_after_utc: str,
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Tuple[Dict[str, Any], bytes, Dict[str, Any]]:
    generation_trace_event(trace, "OBSERVATION_COLLECTION_BEGIN", "private-observation")
    observations = call_bound_executor(
        "GENERATION_OBSERVATION_COLLECTION",
        executor.collect_generation_observations_v2,
        runtime_args=runtime_args,
        approval_challenge_id=acquisition_challenge,
        census_at_utc=census_at_utc,
        not_after_utc=not_after_utc,
        generation_authorization=authorization,
    )
    generation_trace_event(trace, "OBSERVATION_COLLECTION_COMPLETE", "private-observation")
    generation_trace_event(trace, "PENDING_BUILD_BEGIN", "pure-builder")
    envelope = call_bound_executor(
        "GENERATION_PENDING_BUILDER",
        executor.build_pending_envelope_v2,
        approval_challenge_id=acquisition_challenge,
        census_at_utc=census_at_utc,
        not_after_utc=not_after_utc,
        generation_authorization=authorization,
        observations=observations,
    )
    generation_trace_event(trace, "PENDING_BUILD_COMPLETE", "pure-builder")
    raw = call_bound_executor("GENERATION_PENDING_CANONICAL", executor.canonical_json, envelope)
    if not isinstance(raw, bytes):
        fail(Exit.INTERNAL, "GENERATION_PENDING_BYTES")
    validate_pending_candidate(executor, envelope, raw)
    generation_trace_event(trace, "PENDING_CONTRACT_VALIDATED", "pure-builder")
    return envelope, raw, observations


def checked_generation_claim_record(
    value: Any,
    authorization: Mapping[str, Any],
    now: Optional[_datetime.datetime] = None,
) -> Dict[str, Any]:
    """Validate the public shape of one executor-authenticated GEN claim."""

    if not isinstance(value, dict) or set(value) != GENERATION_CLAIM_RECORD_FIELDS:
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_RECORD_FIELDS")
    record = dict(value)
    expected_authority = {
        "generation_authorization_challenge_id": authorization.get("approval_challenge_id"),
        "generation_authorization_envelope_raw_sha256": authorization.get("raw_envelope_sha256"),
        "generation_authorization_receipt_digest": authorization.get("receipt_digest"),
        "generation_authorization_parent_commit_oid": authorization.get("authorization_parent_commit_oid"),
        "generation_authorization_parent_tree_oid": authorization.get("authorization_parent_tree_oid"),
        "generation_authorization_commit_oid": authorization.get("authorization_commit_oid"),
        "generation_authorization_tree_oid": authorization.get("authorization_tree_oid"),
        "final_envelope_repo_relative_path": authorization.get(
            "generated_acquisition_envelope_repo_relative_path"
        ),
    }
    if any(record.get(field) != expected for field, expected in expected_authority.items()):
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_AUTHORITY_DRIFT")
    if (
        record.get("profile") != "gov01-static-envelope-generation-claim-v1"
        or record.get("state") != "OUTPUT-IDENTITY-FIXED"
        or type(record.get("final_envelope_bytes")) is not int
        or not 1 <= int(record["final_envelope_bytes"]) <= MAX_FILE_BYTES
    ):
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_RECORD_SHAPE")
    acquisition_challenge = record.get("acquisition_approval_challenge_id")
    if not isinstance(acquisition_challenge, str) or ACQUISITION_CHALLENGE_RE.fullmatch(acquisition_challenge) is None:
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_ACQUISITION_CHALLENGE")
    for field in (
        "generation_authorization_envelope_raw_sha256",
        "generation_authorization_receipt_digest",
        "final_envelope_raw_sha256",
        "final_envelope_receipt_digest",
        "record_hmac_sha256",
    ):
        if not isinstance(record.get(field), str) or SHA256_RE.fullmatch(str(record[field])) is None:
            fail(Exit.PREFLIGHT, "GENERATION_CLAIM_DIGEST")
    census_at = parse_utc(record.get("census_at_utc"), "GENERATION_CLAIM_CENSUS")
    not_after = parse_utc(record.get("not_after_utc"), "GENERATION_CLAIM_EXPIRY")
    if acquisition_challenge.split("-")[2] != census_at.strftime("%Y%m%d"):
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_CHALLENGE_DATE")
    if not_after <= census_at or not_after - census_at > _datetime.timedelta(hours=24):
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_TTL")
    current = utc_now_second() if now is None else now
    if (
        current.tzinfo != _datetime.timezone.utc
        or current.microsecond
        or census_at > current + _datetime.timedelta(minutes=5)
        or current >= not_after
    ):
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_TIME_WINDOW")
    return record


def probe_generation_claim(
    executor: types.ModuleType,
    runtime_args: Any,
    authorization: Mapping[str, Any],
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    generation_trace_event(trace, "GENERATION_CLAIM_PROBE_BEGIN", "durable-claim")
    record = call_bound_executor(
        "GENERATION_CLAIM_PROBE",
        executor.probe_generation_claim_v2,
        runtime_args=runtime_args,
        generation_authorization=authorization,
    )
    if record is None:
        generation_trace_event(trace, "GENERATION_CLAIM_ABSENT", "durable-claim")
        return None
    checked = checked_generation_claim_record(record, authorization)
    generation_trace_event(trace, "GENERATION_CLAIM_PRESENT", "durable-claim")
    return checked


def verify_generation_claim_candidate(
    executor: types.ModuleType,
    runtime_args: Any,
    authorization: Mapping[str, Any],
    raw: bytes,
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    generation_trace_event(trace, "GENERATION_CLAIM_VERIFY_BEGIN", "durable-claim")
    record = call_bound_executor(
        "GENERATION_CLAIM_RECOVERY",
        executor.verify_generation_claim_recovery_v2,
        runtime_args=runtime_args,
        generation_authorization=authorization,
        final_envelope_raw=raw,
    )
    checked = checked_generation_claim_record(record, authorization)
    generation_trace_event(trace, "GENERATION_CLAIM_VERIFY_COMPLETE", "durable-claim")
    return checked


def candidate_from_generation_claim(
    executor: types.ModuleType,
    context: Mapping[str, Any],
    authorization: Mapping[str, Any],
    runtime_args: Any,
    record: Mapping[str, Any],
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Tuple[Dict[str, Any], bytes, Dict[str, Any]]:
    checked = checked_generation_claim_record(record, authorization)
    candidate = build_current_pending_candidate(
        executor,
        context,
        authorization,
        runtime_args,
        str(checked["acquisition_approval_challenge_id"]),
        str(checked["census_at_utc"]),
        str(checked["not_after_utc"]),
        trace=trace,
    )
    verified = verify_generation_claim_candidate(
        executor,
        runtime_args,
        authorization,
        candidate[1],
        trace=trace,
    )
    if verified != checked:
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_REOPEN_DRIFT")
    return candidate


def public_context_identity(context: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (
        context.get("micro_raw"),
        context.get("micro_receipt"),
        context.get("micro_relative"),
        context.get("generation_output_relative"),
        context.get("current_head"),
        context.get("current_tree"),
    )


def revalidate_micro_before_create(context: Mapping[str, Any]) -> None:
    repo_root = context.get("repo_root")
    relative = context.get("micro_relative")
    expected_raw = context.get("micro_raw")
    if not isinstance(repo_root, str) or not isinstance(relative, str) or not isinstance(expected_raw, bytes):
        fail(Exit.INTERNAL, "GENERATION_RECHECK_CONTEXT")
    raw, _metadata = open_relative_regular(repo_root, relative, "GENERATION_RECHECK")
    if raw != expected_raw or not hmac.compare_digest(receipt_digest(raw), str(context.get("micro_receipt"))):
        fail(Exit.PREFLIGHT, "GENERATION_RECHECK_DRIFT")
    value = parse_json(raw, "GENERATION_RECHECK")
    validate_generation_envelope(value, utc_now_second(), require_pending=True)


def try_write_exclusive_public_file(
    repo_root: str,
    relative: str,
    raw: bytes,
    before_create: Optional[Callable[[], None]] = None,
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> bool:
    """Create one complete public file; return False only for a lost O_EXCL race."""

    # Revalidate public authority before pinning any directory descriptor.  A
    # callback can be slow and may observe repository drift; opening the parent
    # first would let a concurrently renamed directory escape the authorized
    # repository while remaining reachable through the stale descriptor.
    if before_create is not None:
        before_create()
    parent_fd, name = open_output_parent(repo_root, relative)
    fd: Optional[int] = None
    created = False
    close_failed = False
    parent_close_failed = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            generation_trace_event(trace, "FINAL_CREATE_ATTEMPT", "public-output")
            fd = os.open(name, flags, 0o644, dir_fd=parent_fd)
        except FileExistsError:
            generation_trace_event(trace, "FINAL_CREATE_LOST_RACE", "public-output")
            return False
        except OSError:
            fail(Exit.WRITE, "OUTPUT_CREATE")
        created = True
        os.fchmod(fd, 0o644)
        initial = os.fstat(fd)
        if (
            not stat.S_ISREG(initial.st_mode)
            or initial.st_uid != os.getuid()
            or stat.S_IMODE(initial.st_mode) != 0o644
            or initial.st_nlink != 1
        ):
            fail(Exit.WRITE, "OUTPUT_POLICY")
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(fd, raw[offset:])
            except OSError as error:
                if error.errno == errno.EINTR:
                    continue
                fail(Exit.WRITE, "OUTPUT_WRITE")
            if written <= 0:
                fail(Exit.WRITE, "OUTPUT_WRITE")
            offset += written
        os.fsync(fd)
        final = os.fstat(fd)
        path_meta = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            (final.st_dev, final.st_ino, final.st_uid, stat.S_IMODE(final.st_mode), final.st_nlink, final.st_size)
            != (
                path_meta.st_dev,
                path_meta.st_ino,
                path_meta.st_uid,
                stat.S_IMODE(path_meta.st_mode),
                path_meta.st_nlink,
                path_meta.st_size,
            )
            or final.st_size != len(raw)
        ):
            fail(Exit.WRITE, "OUTPUT_FINAL_IDENTITY")
        os.fsync(parent_fd)
        generation_trace_event(trace, "FINAL_CREATE_DURABLE", "public-output")
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                close_failed = created
        try:
            os.close(parent_fd)
        except OSError:
            parent_close_failed = created
    if close_failed or parent_close_failed:
        fail(Exit.WRITE, "OUTPUT_CLOSE")
    reopened, metadata = open_relative_regular(repo_root, relative, "OUTPUT_REOPEN")
    if reopened != raw or metadata.st_size != len(raw) or stat.S_IMODE(metadata.st_mode) != 0o644:
        fail(Exit.WRITE, "OUTPUT_REOPEN_MISMATCH")
    generation_trace_event(trace, "FINAL_CREATE_REOPEN_VERIFIED", "public-output")
    return True


def recover_existing_pending(
    executor: types.ModuleType,
    context: Mapping[str, Any],
    authorization: Mapping[str, Any],
    runtime_args: Any,
    expected_record: Mapping[str, Any],
    *,
    boundary: Any,
    expected_receipt: str,
    expected_challenge: str,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    generation_trace_event(trace, "EXISTING_OUTPUT_READ_BEGIN", "public-output")
    recovery_context = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    if (
        public_context_identity(recovery_context) != public_context_identity(context)
        or recovery_context.get("generation_output_preexisting") is not True
    ):
        fail(Exit.PREFLIGHT, "GENERATION_RECOVERY_PUBLIC_CONTEXT_DRIFT")
    context = recovery_context
    repo_root = context.get("repo_root")
    relative = context.get("generation_output_relative")
    if not isinstance(repo_root, str) or not isinstance(relative, str):
        fail(Exit.INTERNAL, "RECOVERY_CONTEXT")
    raw, metadata = open_relative_regular(repo_root, relative, "EXISTING_PENDING")
    generation_trace_event(trace, "EXISTING_OUTPUT_READ_COMPLETE", "public-output")
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        fail(Exit.PREFLIGHT, "EXISTING_PENDING_MODE")
    value = call_bound_executor("EXISTING_PENDING_PARSE", executor.parse_json_bytes, raw, "EXISTING_PENDING")
    envelope = validate_pending_candidate(executor, value, raw)
    if envelope.get("generation_authorization") != dict(authorization):
        fail(Exit.CONTRACT, "EXISTING_PENDING_GENERATION_BINDING")
    checked_record = checked_generation_claim_record(expected_record, authorization)
    verified_record = verify_generation_claim_candidate(
        executor,
        runtime_args,
        authorization,
        raw,
        trace=trace,
    )
    if verified_record != checked_record:
        fail(Exit.PREFLIGHT, "EXISTING_PENDING_CLAIM_DRIFT")
    rebuilt, rebuilt_raw, _observations = candidate_from_generation_claim(
        executor,
        context,
        authorization,
        runtime_args,
        checked_record,
        trace=trace,
    )
    if rebuilt != envelope or rebuilt_raw != raw:
        fail(Exit.PREFLIGHT, "EXISTING_PENDING_DRIFT")
    reopened, reopened_meta = open_relative_regular(repo_root, relative, "EXISTING_PENDING_REOPEN")
    if (
        reopened != raw
        or (
            reopened_meta.st_dev,
            reopened_meta.st_ino,
            reopened_meta.st_uid,
            reopened_meta.st_gid,
            reopened_meta.st_mode,
            reopened_meta.st_nlink,
            reopened_meta.st_size,
            reopened_meta.st_mtime_ns,
            reopened_meta.st_ctime_ns,
        )
        != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_uid,
            metadata.st_gid,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )
    ):
        fail(Exit.PREFLIGHT, "EXISTING_PENDING_RACE")
    final_public = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    if (
        public_context_identity(final_public) != public_context_identity(context)
        or final_public.get("generation_output_preexisting") is not True
    ):
        fail(Exit.PREFLIGHT, "GENERATION_RECOVERY_PUBLIC_CONTEXT_DRIFT")
    checked_generation_claim_record(checked_record, authorization)
    generation_trace_event(trace, "EXISTING_OUTPUT_RECOVERY_VERIFIED", "public-output")
    return {
        "state": "ACQUISITION-ENVELOPE-CANDIDATE-REQUIRES-EXTERNAL-DRAFT-VALIDATION",
        "artifact_path": relative,
        "raw_envelope_receipt_digest": acquisition_receipt_digest(raw),
        "generation_approval_challenge_id": authorization["approval_challenge_id"],
        "approval_challenge_id": checked_record["acquisition_approval_challenge_id"],
        "not_after_utc": checked_record["not_after_utc"],
    }


def create_or_observe_generation_claim(
    executor: types.ModuleType,
    runtime_args: Any,
    authorization: Mapping[str, Any],
    raw: bytes,
    *,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Tuple[Dict[str, Any], bool]:
    """Create one durable claim, or authenticate the concurrent winner."""

    generation_trace_event(trace, "GENERATION_CLAIM_CREATE_ATTEMPT", "durable-claim")
    try:
        created = executor.create_generation_claim_v2(
            runtime_args=runtime_args,
            generation_authorization=authorization,
            final_envelope_raw=raw,
        )
    except BaseException as error:
        contract_error_type = getattr(executor, "ContractError", None)
        if (
            not isinstance(contract_error_type, type)
            or not isinstance(error, contract_error_type)
            or getattr(error, "code", None) != getattr(executor.Exit, "REPLAY", None)
            or getattr(error, "public_code", None) != "PRIVATE_CHILD_EXISTS"
        ):
            fail(Exit.PREFLIGHT, "GENERATION_CLAIM_CREATE")
        winner = probe_generation_claim(
            executor,
            runtime_args,
            authorization,
            trace=trace,
        )
        if winner is None:
            fail(Exit.PREFLIGHT, "GENERATION_CLAIM_CREATE")
        generation_trace_event(trace, "GENERATION_CLAIM_CONCURRENT_WINNER", "durable-claim")
        return winner, False
    checked = checked_generation_claim_record(created, authorization)
    reopened = verify_generation_claim_candidate(
        executor,
        runtime_args,
        authorization,
        raw,
        trace=trace,
    )
    if reopened != checked:
        fail(Exit.PREFLIGHT, "GENERATION_CLAIM_POSTCREATE_DRIFT")
    generation_trace_event(trace, "GENERATION_CLAIM_CREATE_DURABLE", "durable-claim")
    return checked, True


def publish_or_recover_claimed_pending(
    executor: types.ModuleType,
    context: Mapping[str, Any],
    authorization: Mapping[str, Any],
    runtime_args: Any,
    record: Mapping[str, Any],
    expected_receipt: str,
    expected_challenge: str,
    *,
    boundary: Any,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Publish or recover only the byte identity fixed by a valid GEN claim."""

    checked = checked_generation_claim_record(record, authorization)
    if context.get("generation_output_preexisting") is True:
        generation_trace_event(trace, "CLAIMED_EXISTING_RECOVERY", "public-output")
        return recover_existing_pending(
            executor,
            context,
            authorization,
            runtime_args,
            checked,
            boundary=boundary,
            expected_receipt=expected_receipt,
            expected_challenge=expected_challenge,
            trace=trace,
        )

    _candidate, raw, observations = candidate_from_generation_claim(
        executor,
        context,
        authorization,
        runtime_args,
        checked,
        trace=trace,
    )
    generation_trace_event(trace, "PUBLIC_APPROVAL_RELOAD_BEGIN", "public-authorization")
    refreshed = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    generation_trace_event(trace, "PUBLIC_APPROVAL_RELOAD_COMPLETE", "public-authorization")
    if public_context_identity(refreshed) != public_context_identity(context):
        fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
    if refreshed.get("generation_output_preexisting") is True:
        generation_trace_event(trace, "PUBLICATION_RACE_RECOVERY", "public-output")
        return recover_existing_pending(
            executor,
            refreshed,
            authorization,
            runtime_args,
            checked,
            boundary=boundary,
            expected_receipt=expected_receipt,
            expected_challenge=expected_challenge,
            trace=trace,
        )
    _confirmed, confirmed_raw, confirmed_observations = candidate_from_generation_claim(
        executor,
        refreshed,
        authorization,
        runtime_args,
        checked,
        trace=trace,
    )
    if confirmed_raw != raw or confirmed_observations != observations:
        fail(Exit.PREFLIGHT, "GENERATION_PRIVATE_CONTEXT_DRIFT")
    generation_trace_event(trace, "PUBLIC_PRECREATE_REVALIDATE_BEGIN", "public-authorization")
    precreate_public = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    if public_context_identity(precreate_public) != public_context_identity(refreshed):
        fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
    generation_trace_event(trace, "PUBLIC_PRECREATE_REVALIDATE_COMPLETE", "public-authorization")
    checked_generation_claim_record(checked, authorization)

    def verify_durable_claim_immediately_before_create() -> None:
        immediate_public = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
        if public_context_identity(immediate_public) != public_context_identity(refreshed):
            fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
        current = verify_generation_claim_candidate(
            executor,
            runtime_args,
            authorization,
            confirmed_raw,
            trace=trace,
        )
        if current != checked:
            fail(Exit.PREFLIGHT, "GENERATION_CLAIM_PRECREATE_DRIFT")

    created = try_write_exclusive_public_file(
        str(refreshed["repo_root"]),
        str(refreshed["generation_output_relative"]),
        confirmed_raw,
        before_create=verify_durable_claim_immediately_before_create,
        trace=trace,
    )
    if not created:
        return recover_existing_pending(
            executor,
            refreshed,
            authorization,
            runtime_args,
            checked,
            boundary=boundary,
            expected_receipt=expected_receipt,
            expected_challenge=expected_challenge,
            trace=trace,
        )
    generation_trace_event(trace, "POSTWRITE_PUBLIC_REVALIDATE_BEGIN", "public-authorization")
    postwrite_public = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    if public_context_identity(postwrite_public) != public_context_identity(refreshed):
        fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
    if postwrite_public.get("generation_output_preexisting") is not True:
        fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_POSTWRITE_ABSENT")
    generation_trace_event(trace, "POSTWRITE_PUBLIC_REVALIDATE_COMPLETE", "public-authorization")
    return recover_existing_pending(
        executor,
        refreshed,
        authorization,
        runtime_args,
        checked,
        boundary=boundary,
        expected_receipt=expected_receipt,
        expected_challenge=expected_challenge,
        trace=trace,
    )


class ProductionGenerationBoundaryV1:
    """Low-level nondeterministic inputs used by the production state machine.

    The boundary deliberately cannot replace authorization projection,
    observation collection, pending-envelope construction, durable-claim
    creation, exclusive publication, or recovery.  Those transitions always
    execute the production functions below, including in hostile fixtures.
    """

    def load_approved_generation_request(self, receipt: str, challenge: str) -> Dict[str, Any]:
        return load_approved_generation_request(receipt, challenge)

    def load_content_addressed_executor(self, context: Mapping[str, Any]) -> types.ModuleType:
        return load_content_addressed_executor(context)

    def derive_generation_runtime_args(
        self,
        executor: types.ModuleType,
        context: Mapping[str, Any],
        authorization: Mapping[str, Any],
    ) -> Any:
        return call_bound_executor(
            "GENERATION_LOCATOR_DERIVATION",
            executor.derive_generation_runtime_args_v2,
            context.get("repo_root"),
            authorization,
        )

    def now_second(self) -> _datetime.datetime:
        return utc_now_second()

    def random_bytes(self, length: int) -> bytes:
        return os.urandom(length)

def generation_trace_event(
    trace: Optional[List[Dict[str, str]]],
    event: str,
    phase: str,
) -> None:
    if trace is not None:
        trace.append({"event": event, "phase": phase})


def generate_with_boundary_v1(
    expected_receipt: str,
    expected_challenge: str,
    *,
    boundary: Any,
    trace: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Run the production state machine through one observable I/O boundary."""

    generation_trace_event(trace, "PUBLIC_APPROVAL_LOAD", "public-authorization")
    context = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    generation_trace_event(trace, "PUBLIC_APPROVAL_VALIDATED", "public-authorization")
    generation_trace_event(trace, "EXECUTOR_LOAD", "public-code-binding")
    executor = boundary.load_content_addressed_executor(context)
    generation_trace_event(trace, "EXECUTOR_BOUND", "public-code-binding")
    authorization = generation_authorization(context)
    generation_trace_event(trace, "GENERATION_AUTHORITY_BOUND", "public-authorization")
    generation_trace_event(trace, "PRIVATE_LOCATOR_DERIVE", "private-observation")
    runtime_args = boundary.derive_generation_runtime_args(executor, context, authorization)
    generation_trace_event(trace, "PRIVATE_LOCATOR_DERIVED", "private-observation")
    existing_claim = probe_generation_claim(
        executor,
        runtime_args,
        authorization,
        trace=trace,
    )
    if existing_claim is not None:
        generation_trace_event(trace, "CLAIMED_RECOVERY_DISPATCH", "public-output")
        result = publish_or_recover_claimed_pending(
            executor,
            context,
            authorization,
            runtime_args,
            existing_claim,
            expected_receipt,
            expected_challenge,
            boundary=boundary,
            trace=trace,
        )
        generation_trace_event(trace, "CLAIMED_RECOVERY_COMPLETE", "public-output")
        return result
    if context.get("generation_output_preexisting") is True:
        fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_WITHOUT_CLAIM")

    generation_trace_event(trace, "CLOCK_READ", "fresh-identity")
    census_at = boundary.now_second()
    generation_trace_event(trace, "ENTROPY_REQUEST_32", "fresh-identity")
    entropy = boundary.random_bytes(32)
    if len(entropy) != 32:
        fail(Exit.RUNTIME, "ACQUISITION_ENTROPY")
    acquisition_challenge = "GOV01-SA-" + census_at.strftime("%Y%m%d") + "-" + entropy.hex()
    not_after = census_at + _datetime.timedelta(hours=24)
    census_at_utc = format_utc(census_at)
    not_after_utc = format_utc(not_after)
    generation_trace_event(trace, "CANDIDATE_BUILD", "private-observation")
    _envelope, raw, observations = build_current_pending_candidate(
        executor,
        context,
        authorization,
        runtime_args,
        acquisition_challenge,
        census_at_utc,
        not_after_utc,
        trace=trace,
    )

    # Revalidate the exact public transition and all private observations just
    # before the durable GEN claim consumes this authority.  If a concurrent
    # winner appears, discard this loser's fresh SA and recover only the
    # winner's claim-authenticated identity.
    generation_trace_event(trace, "PUBLIC_APPROVAL_RELOAD", "public-authorization")
    refreshed = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    generation_trace_event(trace, "PUBLIC_APPROVAL_REVALIDATED", "public-authorization")
    if public_context_identity(refreshed) != public_context_identity(context):
        fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
    context = refreshed
    concurrent_claim = probe_generation_claim(
        executor,
        runtime_args,
        authorization,
        trace=trace,
    )
    if concurrent_claim is not None:
        generation_trace_event(trace, "CONCURRENT_WINNER_RECOVERY_DISPATCH", "public-output")
        result = publish_or_recover_claimed_pending(
            executor,
            context,
            authorization,
            runtime_args,
            concurrent_claim,
            expected_receipt,
            expected_challenge,
            boundary=boundary,
            trace=trace,
        )
        generation_trace_event(trace, "CONCURRENT_WINNER_RECOVERY_COMPLETE", "public-output")
        return result
    if context.get("generation_output_preexisting") is True:
        fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_WITHOUT_CLAIM")
    generation_trace_event(trace, "CANDIDATE_REBUILD", "private-observation")
    _confirmed, confirmed_raw, confirmed_observations = build_current_pending_candidate(
        executor,
        context,
        authorization,
        runtime_args,
        acquisition_challenge,
        census_at_utc,
        not_after_utc,
        trace=trace,
    )
    if confirmed_raw != raw or confirmed_observations != observations:
        fail(Exit.PREFLIGHT, "GENERATION_PRIVATE_CONTEXT_DRIFT")
    generation_trace_event(trace, "PUBLIC_APPROVAL_PRECLAIM_RECHECK", "public-authorization")
    preclaim_public = boundary.load_approved_generation_request(expected_receipt, expected_challenge)
    if public_context_identity(preclaim_public) != public_context_identity(context):
        fail(Exit.PREFLIGHT, "GENERATION_PUBLIC_CONTEXT_DRIFT")
    if preclaim_public.get("generation_output_preexisting") is True:
        fail(Exit.PREFLIGHT, "GENERATION_OUTPUT_WITHOUT_CLAIM")
    context = preclaim_public
    generation_trace_event(trace, "PUBLIC_APPROVAL_PRECLAIM_REVALIDATED", "public-authorization")
    claim_record, _created_by_this_attempt = create_or_observe_generation_claim(
        executor,
        runtime_args,
        authorization,
        confirmed_raw,
        trace=trace,
    )
    generation_trace_event(trace, "GENERATION_CLAIM_AUTHENTICATED", "durable-claim")
    generation_trace_event(trace, "PUBLICATION_OR_RECOVERY_DISPATCH", "public-output")
    result = publish_or_recover_claimed_pending(
        executor,
        context,
        authorization,
        runtime_args,
        claim_record,
        expected_receipt,
        expected_challenge,
        boundary=boundary,
        trace=trace,
    )
    generation_trace_event(trace, "PUBLICATION_OR_RECOVERY_COMPLETE", "public-output")
    return result


def generate(expected_receipt: str, expected_challenge: str) -> Dict[str, Any]:
    require_python_isolation()
    return generate_with_boundary_v1(
        expected_receipt,
        expected_challenge,
        boundary=ProductionGenerationBoundaryV1(),
    )


def emit(payload: Mapping[str, Any]) -> None:
    raw = canonical_json(dict(payload))
    # Public output may contain only a repository-relative path, digests, IDs,
    # timestamps, counters, booleans, and fixed state labels.
    for value in payload.values():
        if isinstance(value, str) and (
            value.startswith("/")
            or value.startswith("~")
            or "\\" in value
            or "/users/" in value.casefold()
            or "file://" in value.casefold()
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in value)
        ):
            fail(Exit.PRIVACY, "PUBLIC_OUTPUT_PRIVACY")
    sys.stdout.write(raw.decode("utf-8", "strict"))
    sys.stdout.flush()


def parser() -> PrivacySafeArgumentParser:
    result = PrivacySafeArgumentParser(
        prog="gov01-static-envelope-generation-v1",
        description="Issue or consume a GOV-01 static-envelope generation authorization",
    )
    result.add_argument("--version", action="version", version=SCRIPT_VERSION)
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("issue", help="create one public pending generation micro-envelope")
    generate_parser = subparsers.add_parser(
        "generate",
        help="consume one committed generation receipt and create or recover its GEN-keyed pending envelope",
    )
    generate_parser.add_argument("--receipt-digest", required=True)
    generate_parser.add_argument("--approval-challenge", required=True)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        if args.command == "issue":
            payload = issue()
        elif args.command == "generate":
            payload = generate(args.receipt_digest, args.approval_challenge)
        else:
            fail(Exit.USAGE, "COMMAND")
        emit(payload)
        return int(Exit.OK)
    except GenerationError as error:
        payload = {
            "state": "GENERATION-STOPPED",
            "ok": False,
            "code": error.public_code,
            "exit": int(error.code),
        }
        try:
            emit(payload)
        except GenerationError:
            sys.stdout.write('{"code":"PRIVACY_FAIL_CLOSED","exit":55,"ok":false,"state":"GENERATION-STOPPED"}\n')
            sys.stdout.flush()
            return int(Exit.PRIVACY)
        return int(error.code)
    except SystemExit:
        raise
    except BaseException:
        sys.stdout.write('{"code":"INTERNAL_FAIL_CLOSED","exit":70,"ok":false,"state":"GENERATION-STOPPED"}\n')
        sys.stdout.flush()
        return int(Exit.INTERNAL)


if __name__ == "__main__":
    raise SystemExit(main())
