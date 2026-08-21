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
import fcntl
import hashlib
import hmac
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import threading
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


class RawGitTreeEntry(NamedTuple):
    mode: str
    kind: str
    oid: str
    name: bytes
    raw_record: bytes


class RequiredPathTrieResolution(NamedTuple):
    root_tree_oid: str
    tree_contexts: Tuple[Tuple[str, str], ...]
    path_entries: Tuple[Tuple[str, str, str], ...]
    tree_raw: Tuple[Tuple[str, bytes], ...]


class CapturedIndexTreeProof(NamedTuple):
    root_tree_oid: str
    entry_count: int
    raw_sha256: str
    version: int
    opaque_gitlink_count: int


class CapturedRefs(NamedTuple):
    """One canonical, object-independent view of the frozen ref namespace."""

    effective_raw: Tuple[Tuple[str, bytes], ...]
    expected: Tuple[Tuple[str, str], ...]
    head_oid: str
    head_ref: str
    oid_width: int


class GitReadBoundary:
    """One sealed, self-contained Git metadata adapter.

    ``git_dir`` is always the private temporary adapter.  The live Git control
    paths are retained only so the parent Python process can revalidate the
    source capture; they are never placed on a Git child read allowlist.
    """

    __slots__ = (
        "developer_root",
        "repo_root",
        "live_git_dir",
        "live_common_dir",
        "adapter_root",
        "adapter_device",
        "adapter_inode",
        "adapter_root_fd",
        "git_dir",
        "git_device",
        "git_inode",
        "adapter_git_fd",
        "source_fingerprint",
        "adapter_fingerprint",
        "expected_refs",
        "expected_object_oids",
        "expected_object_types",
        "current_required_blob_paths",
        "parent_required_absent_paths",
        "current_path_resolution",
        "parent_path_resolution",
        "head_oid",
        "head_tree",
        "parent_oid",
        "parent_tree",
        "index_tree_proof",
        "one_file_transition_receipt",
        "git_removed",
        "closed",
    )

    def __init__(
        self,
        developer_root: str,
        repo_root: str,
        live_git_dir: str,
        live_common_dir: str,
        adapter_root: str,
        adapter_device: int,
        adapter_inode: int,
        adapter_root_fd: int,
        git_dir: str,
        git_device: int,
        git_inode: int,
        adapter_git_fd: int,
        source_fingerprint: str,
        adapter_fingerprint: str,
        expected_refs: Sequence[Tuple[str, str]],
        expected_object_types: Mapping[str, str],
        current_required_blob_paths: Sequence[str],
        parent_required_absent_paths: Sequence[str],
        current_path_resolution: RequiredPathTrieResolution,
        parent_path_resolution: Optional[RequiredPathTrieResolution],
        head_oid: str,
        head_tree: str,
        parent_oid: Optional[str],
        parent_tree: Optional[str],
        index_tree_proof: CapturedIndexTreeProof,
        one_file_transition_receipt: Optional[str],
    ) -> None:
        self.developer_root = developer_root
        self.repo_root = repo_root
        self.live_git_dir = live_git_dir
        self.live_common_dir = live_common_dir
        self.adapter_root = adapter_root
        self.adapter_device = adapter_device
        self.adapter_inode = adapter_inode
        self.adapter_root_fd = adapter_root_fd
        self.git_dir = git_dir
        self.git_device = git_device
        self.git_inode = git_inode
        self.adapter_git_fd = adapter_git_fd
        self.source_fingerprint = source_fingerprint
        self.adapter_fingerprint = adapter_fingerprint
        self.expected_refs = tuple(expected_refs)
        self.expected_object_types = tuple(sorted(expected_object_types.items()))
        self.expected_object_oids = tuple(oid for oid, _kind in self.expected_object_types)
        self.current_required_blob_paths = tuple(current_required_blob_paths)
        self.parent_required_absent_paths = tuple(parent_required_absent_paths)
        self.current_path_resolution = current_path_resolution
        self.parent_path_resolution = parent_path_resolution
        self.head_oid = head_oid
        self.head_tree = head_tree
        self.parent_oid = parent_oid
        self.parent_tree = parent_tree
        self.index_tree_proof = index_tree_proof
        self.one_file_transition_receipt = one_file_transition_receipt
        self.git_removed = False
        self.closed = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GitReadBoundary):
            return NotImplemented
        return (
            self.developer_root,
            self.repo_root,
            self.live_git_dir,
            self.live_common_dir,
            self.source_fingerprint,
        ) == (
            other.developer_root,
            other.repo_root,
            other.live_git_dir,
            other.live_common_dir,
            other.source_fingerprint,
        )

    def __del__(self) -> None:
        # Best-effort cleanup only.  Security revalidation is explicit and may
        # raise; destructors must never turn a retained exception into noise.
        try:
            cleanup_git_metadata_adapter(self)
        except Exception:
            pass


class StagedGitAdapter:
    """An identity-bound adapter root registered before materialization."""

    __slots__ = (
        "adapter_root",
        "adapter_device",
        "adapter_inode",
        "adapter_root_fd",
        "git_device",
        "git_inode",
        "adapter_git_fd",
        "git_removed",
        "closed",
        "scope",
    )

    def __init__(
        self,
        adapter_root: str,
        adapter_device: int,
        adapter_inode: int,
        scope: Optional["GitAdapterScope"],
    ) -> None:
        self.adapter_root = adapter_root
        self.adapter_device = adapter_device
        self.adapter_inode = adapter_inode
        self.adapter_root_fd = -1
        self.git_device: Optional[int] = None
        self.git_inode: Optional[int] = None
        self.adapter_git_fd = -1
        self.git_removed = False
        self.closed = False
        self.scope = scope


_OPEN_GIT_ADAPTERS: List[Any] = []
_GIT_ADAPTER_SCOPE_LOCK = threading.Lock()
_ACTIVE_GIT_ADAPTER_SCOPE: Optional["GitAdapterScope"] = None


class GitAdapterScope:
    """Close every Git adapter opened inside one production operation."""

    __slots__ = ("registrations", "entered", "owner_thread")

    def __enter__(self) -> "GitAdapterScope":
        global _ACTIVE_GIT_ADAPTER_SCOPE
        if not _GIT_ADAPTER_SCOPE_LOCK.acquire(blocking=False):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
        if _ACTIVE_GIT_ADAPTER_SCOPE is not None or _OPEN_GIT_ADAPTERS:
            _GIT_ADAPTER_SCOPE_LOCK.release()
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
        self.registrations: List[Any] = []
        self.entered = True
        self.owner_thread = threading.get_ident()
        _ACTIVE_GIT_ADAPTER_SCOPE = self
        return self

    def __exit__(self, _error_type: Any, _error: Any, _traceback: Any) -> bool:
        global _ACTIVE_GIT_ADAPTER_SCOPE
        if (
            not getattr(self, "entered", False)
            or _ACTIVE_GIT_ADAPTER_SCOPE is not self
            or self.owner_thread != threading.get_ident()
        ):
            fail(Exit.INTERNAL, "GIT_ADAPTER_SCOPE_STATE")
        cleanup_error: Optional[BaseException] = None
        try:
            for registration in reversed(tuple(self.registrations)):
                try:
                    cleanup_git_adapter_registration(registration)
                except BaseException as error:
                    if cleanup_error is None:
                        cleanup_error = error
        finally:
            self.registrations.clear()
            self.entered = False
            _ACTIVE_GIT_ADAPTER_SCOPE = None
            _GIT_ADAPTER_SCOPE_LOCK.release()
        if cleanup_error is not None:
            raise cleanup_error
        return False


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
    "default-deny profile; before every Git exec the parent passes only one per-child duplicate of the "
    "pinned adapter-Git directory FD, and preexec performs fchdir of that exact identity, closes the duplicate, then "
    "calls sandbox_init exactly once; no usable directory FD reaches Git, fixed argv uses relative --git-dir=., and "
    "no path discovery is permitted; the git-metadata-adapter-bootstrap role permits only the content-bound "
    "CommandLineTools tree, one unsealed checkpoint-scoped private-temporary adapter, captured live pack or loose "
    "object containers needed to extract the exact approved OID set, and adapter-only writes needed by index-pack; it "
    "denies network, worktree payload, every live Git control path, alternates and graft bytes, and all other reads or "
    "writes; after source CAS and sealing, git-read-only-evidence permits only the CommandLineTools tree and sealed "
    "adapter and denies writes and all live Git or worktree reads; the parent revalidates captured live source before "
    "adapter removal; every child profile explicitly denies create rename unlink or write authority over the "
    "private-temporary parent namespace and sibling adapter roots, while index-pack writes are restricted to the "
    "pinned current adapter objects/pack directory; sandbox initialization failure is terminal; "
    "/usr/bin/sandbox-exec is never executed"
)
GENERATION_GIT_CHILD_ENVIRONMENT_PROFILE_V2 = (
    "new exact sanitized environment; HOME=/var/empty and TMPDIR=DARWIN_USER_TEMP_DIR=/tmp; every Git child starts "
    "only after fchdir to the exact identity-bound adapter Git directory and uses relative --git-dir=.; bootstrap Git "
    "receives only exact captured GIT_OBJECT_DIRECTORY while global/system config, inherited alternates and protocols "
    "are disabled; final Git evidence unsets live object access and uses only the sealed adapter; fsmonitor, hooks, "
    "attributes, includes, alternates, grafts, network, and worktree reads are rejected or sandbox-denied"
)
GENERATION_GIT_ADAPTER_PROFILE_V5 = (
    "checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-"
    "one-exact-public-opaque-gitlink-identity-bound-git-fd-metadata-adapter-v5"
)
GENERATION_CAPTURED_INDEX_ROOT_PROFILE_V1 = (
    "strict captured DIRC v2 or v3 canonical bottom-up root-tree recomputation equal to authenticated HEAD; "
    "require the mode 160000 opaque-leaf path set to equal the exact public singleton "
    "_reference/obsidian-sample-plugin without opening requesting or dereferencing its object OID; reject a "
    "missing or mode-replaced singleton and every extra or substituted gitlink; in a parsed required-path ancestor "
    "tree permit that same singleton only as an unselected opaque sibling, and reject it if selected as a required "
    "terminal or ancestor"
)
GENERATION_OPAQUE_GITLINK_INDEX_PATH_V1 = b"_reference/obsidian-sample-plugin"
GENERATION_GIT_ADAPTER_WRITE_PROFILE_V2 = (
    "write only its 0600 sanitized Git control metadata through pinned root and Git directory FDs; resolve bootstrap "
    "and import argv only from the identity-bound adapter Git cwd with relative --git-dir=., keep index-pack "
    "pack/index "
    "output beneath objects/pack, verify every exact-OID partial-pack object hash, then seal files 0400 beneath "
    "0500 directories through pinned FDs; no adapter locator or raw metadata may enter public output"
)
GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1 = (
    "the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other "
    "UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly "
    "one owning process and compliant same-UID product processes never mutate another invocation's root; "
    "non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process "
    "access to the 0600 private HMAC key are outside the supported threat model"
)
GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1 = (
    "every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the "
    "private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter "
    "entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host "
    "namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant "
    "scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process "
    "exclusion"
)
GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1 = (
    "under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable "
    "pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal "
    "absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized "
    "pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a "
    "non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the "
    "supported guarantee"
)
ISSUE_PUBLICATION_CHECKPOINT_PROFILE_V1 = (
    "capture one initial exact Git-source index-root and public-artifact checkpoint; while holding a nonblocking "
    "advisory lock on the exact shared control-parent directory FD, recapture an equal checkpoint immediately before "
    "micro-envelope O_EXCL and require both micro and generation-output preimages absent; after fsync and same-FD "
    "byte-exact reopen, require generation-output absence, recapture the same equal checkpoint, and require "
    "generation-output absence again before success"
)
MAX_FILE_BYTES = 4_000_000
MAX_GIT_BYTES = 32 * 1024 * 1024
MAX_GIT_CONTROL_BYTES = 1024 * 1024
MAX_GIT_INDEX_BYTES = 64 * 1024 * 1024
MAX_GIT_REACHABLE_PACK_BYTES = 1024 * 1024 * 1024
MAX_GIT_REACHABLE_OBJECTS = 250_000
MAX_GIT_PACK_CONTAINER_ENTRIES = 4096
MAX_CAPTURED_REF_BYTES = MAX_GIT_BYTES
MAX_CAPTURED_REF_ENTRIES = MAX_GIT_REACHABLE_OBJECTS
MAX_CAPTURED_REF_DIRECTORIES = MAX_GIT_PACK_CONTAINER_ENTRIES
MAX_CAPTURED_REF_SYMREF_DEPTH = 4
WORKTREE_REF_NAMESPACES = ("bisect/", "worktree/", "rewritten/")
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


def git_source_metadata(metadata: os.stat_result) -> Dict[str, int]:
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "uid": metadata.st_uid,
        "gid": metadata.st_gid,
        "nlink": metadata.st_nlink,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
    }


def read_git_source_regular(path: str, label: str, max_bytes: int) -> Tuple[bytes, Dict[str, Any]]:
    metadata = no_symlink_path(path, label)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or metadata.st_nlink != 1
        or metadata.st_size <= 0
        or metadata.st_size > max_bytes
    ):
        fail(Exit.PREFLIGHT, label + "_POLICY")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        fail(Exit.PREFLIGHT, label + "_OPEN")
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            fail(Exit.PREFLIGHT, label + "_OPEN_RACE")
        pieces: List[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            if not chunk:
                fail(Exit.PREFLIGHT, label + "_SHORT_READ")
            pieces.append(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            fail(Exit.PREFLIGHT, label + "_GROWTH")
        final = os.fstat(fd)
    finally:
        os.close(fd)
    if git_source_metadata(opened) != git_source_metadata(final):
        fail(Exit.PREFLIGHT, label + "_READ_RACE")
    path_metadata = os.stat(path, follow_symlinks=False)
    if (path_metadata.st_dev, path_metadata.st_ino) != (opened.st_dev, opened.st_ino):
        fail(Exit.PREFLIGHT, label + "_PATH_RACE")
    raw = b"".join(pieces)
    return raw, {
        "state": "PRESENT",
        "metadata": git_source_metadata(opened),
        "raw_sha256": sha256(raw),
        "bytes": len(raw),
    }


def optional_git_source_regular(path: str, label: str, max_bytes: int) -> Tuple[Optional[bytes], Dict[str, Any]]:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return None, {"state": "ABSENT"}
    except OSError:
        fail(Exit.PREFLIGHT, label + "_LSTAT")
    return read_git_source_regular(path, label, max_bytes)


def capture_git_source_tree(
    path: str,
    label: str,
    frozen_raw: Optional[Dict[str, bytes]] = None,
    budget: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    if budget is None:
        budget = {"bytes": 0, "entries": 0, "directories": 0}
    elif set(budget) != {"bytes", "entries", "directories"} or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in budget.values()
    ):
        fail(Exit.INTERNAL, "GIT_SOURCE_REF_BUDGET")
    try:
        root_metadata = no_symlink_path(path, label)
    except GenerationError as error:
        if error.public_code == label + "_MISSING":
            return {"state": "ABSENT", "directories": [], "files": []}
        raise
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or stat.S_IMODE(root_metadata.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT, label + "_POLICY")
    files: List[Dict[str, Any]] = []
    directories: List[Dict[str, Any]] = []

    def walk(current_path: str, relative: str) -> None:
        budget["directories"] += 1
        if budget["directories"] > MAX_CAPTURED_REF_DIRECTORIES:
            fail(Exit.PREFLIGHT, "GIT_SOURCE_REFS_DIRECTORY_LIMIT")
        before = no_symlink_path(current_path, label + "_DIRECTORY")
        if (
            not stat.S_ISDIR(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) & 0o022
        ):
            fail(Exit.PREFLIGHT, label + "_DIRECTORY_POLICY")
        entries = []
        try:
            with os.scandir(current_path) as scanner:
                for entry in scanner:
                    entries.append(entry)
                    if budget["entries"] + len(entries) > MAX_CAPTURED_REF_ENTRIES:
                        fail(Exit.PREFLIGHT, "GIT_SOURCE_REFS_ENTRY_LIMIT")
        except GenerationError:
            raise
        except OSError:
            fail(Exit.PREFLIGHT, label + "_SCAN")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            budget["entries"] += 1
            if budget["entries"] > MAX_CAPTURED_REF_ENTRIES:
                fail(Exit.PREFLIGHT, "GIT_SOURCE_REFS_ENTRY_LIMIT")
            name = entry.name
            if (
                not isinstance(name, str)
                or not is_nfc(name)
                or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in name)
            ):
                fail(Exit.PREFLIGHT, label + "_NAME")
            child_relative = name if not relative else relative + "/" + name
            try:
                child_relative_bytes = child_relative.encode("utf-8", "strict")
            except UnicodeEncodeError:
                fail(Exit.PREFLIGHT, label + "_NAME_ENCODING")
            if len(child_relative_bytes) > 1024:
                fail(Exit.PREFLIGHT, label + "_NAME_LENGTH")
            child_path = os.path.join(current_path, name)
            child_metadata = os.lstat(child_path)
            if stat.S_ISLNK(child_metadata.st_mode):
                fail(Exit.PREFLIGHT, label + "_SYMLINK")
            if stat.S_ISDIR(child_metadata.st_mode):
                walk(child_path, child_relative)
            elif stat.S_ISREG(child_metadata.st_mode):
                raw, observation = read_git_source_regular(
                    child_path,
                    label + "_FILE",
                    MAX_GIT_CONTROL_BYTES,
                )
                if frozen_raw is not None:
                    frozen_raw[child_relative] = raw
                budget["bytes"] += len(raw)
                if budget["bytes"] > MAX_CAPTURED_REF_BYTES:
                    fail(Exit.PREFLIGHT, "GIT_SOURCE_REFS_BYTE_LIMIT")
                files.append({"relative": child_relative, "observation": observation})
            else:
                fail(Exit.PREFLIGHT, label + "_SPECIAL")
        after = os.stat(current_path, follow_symlinks=False)
        if git_source_metadata(before) != git_source_metadata(after):
            fail(Exit.PREFLIGHT, label + "_DIRECTORY_RACE")
        directories.append({"relative": relative, "metadata": git_source_metadata(before)})

    walk(path, "")
    return {
        "state": "PRESENT",
        "directories": sorted(directories, key=lambda item: item["relative"]),
        "files": sorted(files, key=lambda item: item["relative"]),
    }


def capture_git_source(repo_root: str) -> Dict[str, Any]:
    observation, (git_dir, common_dir) = inspect_git_control(repo_root)
    fixed_specs = (
        ("marker", os.path.join(repo_root, ".git"), MAX_GIT_CONTROL_BYTES, observation["marker_kind"] == "gitfile"),
        ("head", os.path.join(git_dir, "HEAD"), MAX_GIT_CONTROL_BYTES, True),
        ("index", os.path.join(git_dir, "index"), MAX_GIT_INDEX_BYTES, True),
        ("commondir", os.path.join(git_dir, "commondir"), MAX_GIT_CONTROL_BYTES, git_dir != common_dir),
        ("reverse_gitdir", os.path.join(git_dir, "gitdir"), MAX_GIT_CONTROL_BYTES, git_dir != common_dir),
        ("common_config", os.path.join(common_dir, "config"), MAX_GIT_CONTROL_BYTES, False),
        ("worktree_config", os.path.join(git_dir, "config.worktree"), MAX_GIT_CONTROL_BYTES, False),
        ("packed_refs", os.path.join(common_dir, "packed-refs"), MAX_GIT_INDEX_BYTES, False),
        ("shallow", os.path.join(common_dir, "shallow"), MAX_GIT_INDEX_BYTES, False),
    )
    raw_files: Dict[str, Optional[bytes]] = {}
    file_observations: Dict[str, Any] = {}
    for role, path, limit, required in fixed_specs:
        if role == "marker" and not required:
            raw_files[role] = None
            file_observations[role] = {"state": "DIRECTORY"}
            continue
        if required:
            raw, entry = read_git_source_regular(path, "GIT_SOURCE_" + role.upper(), limit)
        else:
            raw, entry = optional_git_source_regular(path, "GIT_SOURCE_" + role.upper(), limit)
        raw_files[role] = raw
        file_observations[role] = entry
    common_ref_raw: Dict[str, bytes] = {}
    worktree_ref_raw: Dict[str, bytes] = {}
    ref_budget = {"bytes": 0, "entries": 0, "directories": 0}
    common_refs = capture_git_source_tree(
        os.path.join(common_dir, "refs"),
        "GIT_SOURCE_COMMON_REFS",
        common_ref_raw,
        ref_budget,
    )
    worktree_refs = (
        capture_git_source_tree(
            os.path.join(git_dir, "refs"),
            "GIT_SOURCE_WORKTREE_REFS",
            worktree_ref_raw,
            ref_budget,
        )
        if git_dir != common_dir
        else {"state": "ABSENT", "directories": [], "files": []}
    )
    objects_metadata = no_symlink_path(os.path.join(common_dir, "objects"), "GIT_SOURCE_OBJECTS")
    if (
        not stat.S_ISDIR(objects_metadata.st_mode)
        or objects_metadata.st_uid != os.getuid()
        or stat.S_IMODE(objects_metadata.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT, "GIT_SOURCE_OBJECTS_POLICY")
    identity = {
        "git_control": observation,
        "repo_marker_metadata": git_source_metadata(no_symlink_path(os.path.join(repo_root, ".git"), "GIT_SOURCE_MARKER")),
        "git_dir_metadata": git_source_metadata(no_symlink_path(git_dir, "GIT_SOURCE_GIT_DIR")),
        "common_dir_metadata": git_source_metadata(no_symlink_path(common_dir, "GIT_SOURCE_COMMON_DIR")),
        "objects_dir_metadata": git_source_metadata(objects_metadata),
        "files": file_observations,
        "common_refs": common_refs,
        "worktree_refs": worktree_refs,
    }
    return {
        "git_dir": git_dir,
        "common_dir": common_dir,
        "git_control": observation,
        "raw_files": raw_files,
        "common_ref_raw": common_ref_raw,
        "worktree_ref_raw": worktree_ref_raw,
        "identity": identity,
        "fingerprint": sha256(canonical_json(identity)),
    }


def parse_git_pack_index_v2(
    raw: bytes,
    oid_bytes: int,
    index_name: str,
    requested_oids: Sequence[str],
) -> Tuple[Tuple[str, ...], int]:
    """Validate one v2 pack index and return requested OIDs present in it."""

    raw_oid_bytes = oid_bytes // 2
    if (
        oid_bytes not in (40, 64)
        or re.fullmatch(r"pack-[0-9a-f]{%d}\.idx" % oid_bytes, index_name) is None
        or any(
            len(oid) != oid_bytes or GIT_OID_RE.fullmatch(oid) is None
            for oid in requested_oids
        )
        or len(raw) < 8 + 256 * 4 + 2 * raw_oid_bytes
        or raw[:4] != b"\xfftOc"
        or int.from_bytes(raw[4:8], "big") != 2
    ):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_FORMAT")
    fanout = tuple(
        int.from_bytes(raw[8 + index * 4 : 12 + index * 4], "big")
        for index in range(256)
    )
    if any(fanout[index] < fanout[index - 1] for index in range(1, 256)):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_FANOUT")
    object_count = fanout[-1]
    if object_count <= 0 or object_count > MAX_GIT_REACHABLE_OBJECTS:
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_COUNT")
    names_start = 8 + 256 * 4
    names_end = names_start + object_count * raw_oid_bytes
    crc_end = names_end + object_count * 4
    offsets_end = crc_end + object_count * 4
    if offsets_end + 2 * raw_oid_bytes > len(raw):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_LENGTH")
    large_offset_indexes: List[int] = []
    for index in range(object_count):
        value = int.from_bytes(raw[crc_end + index * 4 : crc_end + (index + 1) * 4], "big")
        if value & 0x80000000:
            large_offset_indexes.append(value & 0x7FFFFFFF)
    if sorted(large_offset_indexes) != list(range(len(large_offset_indexes))):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_LARGE_OFFSET")
    trailer_start = offsets_end + len(large_offset_indexes) * 8
    if trailer_start + 2 * raw_oid_bytes != len(raw):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_LENGTH")
    index_digest = hashlib.sha1() if oid_bytes == 40 else hashlib.sha256()
    index_digest.update(raw[:-raw_oid_bytes])
    if not hmac.compare_digest(index_digest.digest(), raw[-raw_oid_bytes:]):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_CHECKSUM")
    expected_pack_checksum = index_name[len("pack-") : -len(".idx")]
    if raw[trailer_start : trailer_start + raw_oid_bytes].hex() != expected_pack_checksum:
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_PACK_BINDING")

    counts = [0] * 256
    previous = b""
    for index in range(object_count):
        start = names_start + index * raw_oid_bytes
        current = raw[start : start + raw_oid_bytes]
        if index and current <= previous:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_ORDER")
        counts[current[0]] += 1
        previous = current
    cumulative = 0
    for index, count in enumerate(counts):
        cumulative += count
        if fanout[index] != cumulative:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_FANOUT")

    matches: List[str] = []
    for oid in sorted(set(requested_oids)):
        raw_oid = bytes.fromhex(oid)
        first = raw_oid[0]
        low = fanout[first - 1] if first else 0
        high = fanout[first]
        while low < high:
            middle = (low + high) // 2
            start = names_start + middle * raw_oid_bytes
            candidate = raw[start : start + raw_oid_bytes]
            if candidate < raw_oid:
                low = middle + 1
            else:
                high = middle
        start = names_start + low * raw_oid_bytes
        if low < fanout[first] and raw[start : start + raw_oid_bytes] == raw_oid:
            matches.append(oid)
    return tuple(matches), object_count


def capture_git_pack_file(
    path: str,
    label: str,
    oid_bytes: int,
    expected_object_count: int,
) -> Dict[str, Any]:
    """Hash and validate one selected, non-thin on-disk pack container."""

    metadata = no_symlink_path(path, label)
    raw_oid_bytes = oid_bytes // 2
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or metadata.st_nlink != 1
        or metadata.st_size <= 12 + raw_oid_bytes
        or metadata.st_size > MAX_GIT_REACHABLE_PACK_BYTES
    ):
        fail(Exit.PREFLIGHT, label + "_POLICY")
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        fail(Exit.PREFLIGHT, label + "_OPEN")
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            fail(Exit.PREFLIGHT, label + "_OPEN_RACE")
        pack_digest = hashlib.sha1() if oid_bytes == 40 else hashlib.sha256()
        container_digest = hashlib.sha256()
        prefix = bytearray()
        trailer = b""
        length = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            length += len(chunk)
            if length > MAX_GIT_REACHABLE_PACK_BYTES:
                fail(Exit.PREFLIGHT, label + "_SIZE")
            container_digest.update(chunk)
            if len(prefix) < 12:
                prefix.extend(chunk[: 12 - len(prefix)])
            combined = trailer + chunk
            if len(combined) > raw_oid_bytes:
                pack_digest.update(combined[:-raw_oid_bytes])
                trailer = combined[-raw_oid_bytes:]
            else:
                trailer = combined
        final = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        length != metadata.st_size
        or len(prefix) != 12
        or bytes(prefix[:4]) != b"PACK"
        or int.from_bytes(prefix[4:8], "big") not in (2, 3)
        or int.from_bytes(prefix[8:12], "big") != expected_object_count
        or len(trailer) != raw_oid_bytes
    ):
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    expected_checksum = os.path.basename(path)[len("pack-") : -len(".pack")]
    if (
        trailer.hex() != expected_checksum
        or not hmac.compare_digest(pack_digest.digest(), trailer)
    ):
        fail(Exit.PREFLIGHT, label + "_CHECKSUM")
    if git_source_metadata(opened) != git_source_metadata(final):
        fail(Exit.PREFLIGHT, label + "_READ_RACE")
    try:
        named = os.stat(path, follow_symlinks=False)
    except OSError:
        fail(Exit.PREFLIGHT, label + "_PATH_RACE")
    if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        fail(Exit.PREFLIGHT, label + "_PATH_RACE")
    return {
        "state": "PRESENT",
        "metadata": git_source_metadata(opened),
        "raw_sha256": container_digest.hexdigest(),
        "bytes": length,
    }


def capture_git_object_store(objects_path: str, oid_bytes: int) -> Dict[str, Any]:
    """Freeze only pack-directory metadata and validated v2 index bytes."""

    root_before = no_symlink_path(objects_path, "GIT_OBJECT_SOURCE_DIRECTORY")
    if (
        not stat.S_ISDIR(root_before.st_mode)
        or root_before.st_uid != os.getuid()
        or stat.S_IMODE(root_before.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_SOURCE_DIRECTORY_POLICY")
    pack_path = os.path.join(objects_path, "pack")
    try:
        pack_before = os.lstat(pack_path)
    except FileNotFoundError:
        pack_state: Dict[str, Any] = {"state": "ABSENT"}
        entries: List[os.DirEntry[str]] = []
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_LSTAT")
    else:
        if (
            stat.S_ISLNK(pack_before.st_mode)
            or not stat.S_ISDIR(pack_before.st_mode)
            or pack_before.st_uid != os.getuid()
            or stat.S_IMODE(pack_before.st_mode) & 0o022
        ):
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_POLICY")
        try:
            entries = list(os.scandir(pack_path))
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_SCAN")
        if len(entries) > MAX_GIT_PACK_CONTAINER_ENTRIES:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_LIMIT")
        pack_state = {
            "state": "PRESENT",
            "metadata": git_source_metadata(pack_before),
            "entry_names_sha256": sha256(
                canonical_json(sorted((entry.name for entry in entries), key=os.fsencode))
            ),
        }
    main_pattern = re.compile(
        r"\A(pack-[0-9a-f]{" + str(oid_bytes) + r"})\.(pack|idx)\Z"
    )
    pair_names: Dict[str, set[str]] = {}
    pack_metadata: Dict[str, Dict[str, Any]] = {}
    index_bytes: Dict[str, bytes] = {}
    index_observations: Dict[str, Dict[str, Any]] = {}
    auxiliary_names = set()
    total_index_bytes = 0
    for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
        name = entry.name
        if (
            not isinstance(name, str)
            or not is_nfc(name)
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in name)
        ):
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_NAME")
        matched = main_pattern.fullmatch(name)
        if matched is None:
            auxiliary_names.add(name)
            continue
        stem, suffix = matched.groups()
        candidate = os.path.join(pack_path, name)
        pair_names.setdefault(stem, set()).add(suffix)
        if suffix == "idx":
            raw, observation = read_git_source_regular(
                candidate,
                "GIT_OBJECT_PACK_INDEX",
                MAX_GIT_INDEX_BYTES,
            )
            total_index_bytes += len(raw)
            if total_index_bytes > MAX_GIT_INDEX_BYTES:
                fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_INDEX_TOTAL_BYTES")
            index_bytes[name] = raw
            index_observations[name] = observation
        else:
            metadata = no_symlink_path(candidate, "GIT_OBJECT_PACK_FILE")
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) & 0o022
                or metadata.st_nlink != 1
                or metadata.st_size <= 0
                or metadata.st_size > MAX_GIT_REACHABLE_PACK_BYTES
            ):
                fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_FILE_POLICY")
            pack_metadata[name] = git_source_metadata(metadata)
    if any(suffixes != {"idx", "pack"} for suffixes in pair_names.values()):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_PAIR")
    if pack_state["state"] == "PRESENT":
        try:
            pack_after = os.stat(pack_path, follow_symlinks=False)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_RACE")
        if git_source_metadata(pack_before) != git_source_metadata(pack_after):
            fail(Exit.PREFLIGHT, "GIT_OBJECT_PACK_CONTAINER_RACE")
    root_after = os.stat(objects_path, follow_symlinks=False)
    if git_source_metadata(root_before) != git_source_metadata(root_after):
        fail(Exit.PREFLIGHT, "GIT_OBJECT_SOURCE_DIRECTORY_RACE")
    public = {
        "profile": "exact-oid-loose-plus-frozen-v2-index-selected-pack-container-v1",
        "root_metadata": git_source_metadata(root_before),
        "pack_container": pack_state,
        "pair_count": len(pair_names),
        "index_receipt_sha256": sha256(canonical_json(index_observations)),
    }
    return {
        **public,
        "fingerprint": sha256(canonical_json(public)),
        "pack_path": pack_path,
        "index_bytes": index_bytes,
        "index_observations": index_observations,
        "pack_metadata": pack_metadata,
        "auxiliary_names": tuple(sorted(auxiliary_names, key=os.fsencode)),
    }


def capture_git_object_dependencies(
    capture: Mapping[str, Any],
    object_oids: Sequence[str],
) -> Dict[str, Any]:
    """Bind exact loose paths or exact pack/index containers for known OIDs."""

    if not object_oids or len(set(object_oids)) != len(object_oids):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_OIDS")
    oid_bytes = len(object_oids[0])
    if oid_bytes not in (40, 64) or any(
        len(oid) != oid_bytes or GIT_OID_RE.fullmatch(oid) is None for oid in object_oids
    ):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_OIDS")
    objects_path = os.path.join(str(capture["common_dir"]), "objects")
    captured_identity = capture.get("identity")
    if not isinstance(captured_identity, dict):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_CAPTURE")
    captured_root = captured_identity.get("objects_dir_metadata")
    current_root = git_source_metadata(no_symlink_path(objects_path, "GIT_OBJECT_DEPENDENCY_ROOT"))
    if current_root != captured_root:
        fail(Exit.PREFLIGHT, "GIT_OBJECT_DEPENDENCY_ROOT_DRIFT")

    loose_records: List[Dict[str, Any]] = []
    allowed_loose_paths: List[str] = []
    missing = set(object_oids)
    for oid in sorted(object_oids):
        loose_path = os.path.join(objects_path, oid[:2], oid[2:])
        _raw, observation = optional_git_source_regular(
            loose_path,
            "GIT_OBJECT_DEPENDENCY_LOOSE",
            MAX_GIT_BYTES,
        )
        if observation["state"] == "PRESENT":
            missing.remove(oid)
        allowed_loose_paths.append(loose_path)
        loose_records.append({"oid": oid, "observation": observation})

    store = capture_git_object_store(objects_path, oid_bytes)
    candidates: Dict[str, List[Tuple[str, int]]] = {oid: [] for oid in missing}
    searched_indexes: List[Dict[str, Any]] = []
    for index_name in sorted(store["index_bytes"], key=os.fsencode):
        raw = store["index_bytes"][index_name]
        matches, count = parse_git_pack_index_v2(raw, oid_bytes, index_name, tuple(missing))
        searched_indexes.append(
            {"name": index_name, "observation": store["index_observations"][index_name]}
        )
        for oid in matches:
            candidates[oid].append((index_name[:-4], count))
    selected: Dict[str, int] = {}
    for oid in sorted(missing):
        choices = sorted(candidates[oid])
        if not choices:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_DEPENDENCY_MISSING")
        stem, count = choices[0]
        previous = selected.setdefault(stem, count)
        if previous != count:
            fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_PACK_COUNT")

    selected_records: List[Dict[str, Any]] = []
    allowed_pack_paths: List[str] = []
    for stem in sorted(selected):
        if stem + ".promisor" in store["auxiliary_names"]:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_DEPENDENCY_PROMISOR")
        index_name = stem + ".idx"
        pack_name = stem + ".pack"
        index_observation = store["index_observations"].get(index_name)
        initial_pack_metadata = store["pack_metadata"].get(pack_name)
        if not isinstance(index_observation, dict) or not isinstance(initial_pack_metadata, dict):
            fail(Exit.PREFLIGHT, "GIT_OBJECT_DEPENDENCY_PACK_PAIR")
        pack_path = os.path.join(store["pack_path"], pack_name)
        pack_observation = capture_git_pack_file(
            pack_path,
            "GIT_OBJECT_DEPENDENCY_PACK",
            oid_bytes,
            selected[stem],
        )
        if pack_observation["metadata"] != initial_pack_metadata:
            fail(Exit.PREFLIGHT, "GIT_OBJECT_DEPENDENCY_PACK_RACE")
        index_path = os.path.join(store["pack_path"], index_name)
        selected_records.extend(
            (
                {"name": index_name, "observation": index_observation},
                {"name": pack_name, "observation": pack_observation},
            )
        )
        allowed_pack_paths.extend((index_path, pack_path))
    body = {
        "profile": "exact-oid-loose-plus-frozen-v2-index-selected-pack-container-v1",
        "object_count": len(object_oids),
        "oid_set_sha256": sha256(canonical_json(sorted(object_oids))),
        "object_store_fingerprint": store["fingerprint"],
        "loose_dependency_receipt_sha256": sha256(canonical_json(loose_records)),
        "searched_index_receipt_sha256": sha256(canonical_json(searched_indexes)),
        "selected_pack_container_count": len(selected),
        "selected_pack_container_receipt_sha256": sha256(canonical_json(selected_records)),
    }
    return {
        **body,
        "fingerprint": sha256(canonical_json(body)),
        "objects_path": objects_path,
        "allowed_loose_paths": tuple(allowed_loose_paths),
        "allowed_pack_paths": tuple(allowed_pack_paths),
    }


def write_adapter_file(path: str, raw: bytes, label: str) -> None:
    try:
        fd = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError:
        fail(Exit.PREFLIGHT, label + "_CREATE")
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(fd, raw[offset:])
            if written <= 0:
                fail(Exit.PREFLIGHT, label + "_WRITE")
            offset += written
        os.fsync(fd)
        final = os.fstat(fd)
        if final.st_size != len(raw) or final.st_nlink != 1:
            fail(Exit.PREFLIGHT, label + "_FINAL")
    finally:
        os.close(fd)


def write_adapter_file_at(directory_fd: int, name: str, raw: bytes, label: str) -> None:
    if not name or "/" in name or name in (".", ".."):
        fail(Exit.INTERNAL, label + "_NAME")
    try:
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
    except OSError:
        fail(Exit.PREFLIGHT, label + "_CREATE")
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(fd, raw[offset:])
            if written <= 0:
                fail(Exit.PREFLIGHT, label + "_WRITE")
            offset += written
        os.fsync(fd)
        final = os.fstat(fd)
        if final.st_size != len(raw) or final.st_nlink != 1:
            fail(Exit.PREFLIGHT, label + "_FINAL")
    finally:
        os.close(fd)


def open_adapter_directory_at(parent_fd: int, name: str, create: bool, label: str) -> int:
    if not name or "/" in name or name in (".", ".."):
        fail(Exit.INTERNAL, label + "_NAME")
    if create:
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except FileExistsError:
            pass
        except OSError:
            fail(Exit.PREFLIGHT, label + "_CREATE")
    try:
        directory_fd = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        metadata = os.fstat(directory_fd)
    except OSError:
        fail(Exit.PREFLIGHT, label + "_OPEN")
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        os.close(directory_fd)
        fail(Exit.PREFLIGHT, label + "_POLICY")
    return directory_fd


def parse_bootstrap_commit(raw: bytes, oid_bytes: int, require_single_parent: bool) -> Tuple[str, Tuple[str, ...]]:
    """Return the exact root tree and parents named by one commit object."""

    header, separator, _message = raw.partition(b"\n\n")
    if not separator or not header:
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_FORMAT")
    tree: Optional[str] = None
    parents: List[str] = []
    for line in header.split(b"\n"):
        if line.startswith(b" "):
            continue
        if line.startswith(b"tree "):
            if tree is not None:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_TREE")
            candidate = line[5:]
            try:
                tree = candidate.decode("ascii", "strict")
            except UnicodeDecodeError:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_TREE")
            if len(tree) != oid_bytes or GIT_OID_RE.fullmatch(tree) is None:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_TREE")
        elif line.startswith(b"parent "):
            try:
                parent = line[7:].decode("ascii", "strict")
            except UnicodeDecodeError:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_PARENT")
            if len(parent) != oid_bytes or GIT_OID_RE.fullmatch(parent) is None:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_PARENT")
            parents.append(parent)
    if tree is None or (require_single_parent and len(parents) != 1):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_COMMIT_SHAPE")
    return tree, tuple(parents)


def git_object_digest(object_type: str, raw: bytes, oid_bytes: int) -> str:
    if object_type not in ("commit", "tree", "blob") or oid_bytes not in (40, 64):
        fail(Exit.INTERNAL, "GIT_OBJECT_DIGEST_ARGUMENT")
    digest = hashlib.new("sha1" if oid_bytes == 40 else "sha256")
    digest.update((object_type + " " + str(len(raw)) + "\x00").encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()


def validate_generated_pack_envelope(raw: bytes, expected_count: int, oid_bytes: int) -> None:
    """Validate the fixed header/count and object-format trailer before import."""

    raw_oid_bytes = oid_bytes // 2
    if (
        oid_bytes not in (40, 64)
        or expected_count <= 0
        or expected_count > MAX_GIT_REACHABLE_OBJECTS
        or len(raw) <= 12 + raw_oid_bytes
        or raw[:4] != b"PACK"
        or int.from_bytes(raw[4:8], "big") not in (2, 3)
        or int.from_bytes(raw[8:12], "big") != expected_count
    ):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_PACK_FORMAT")
    digest = hashlib.new("sha1" if oid_bytes == 40 else "sha256", raw[:-raw_oid_bytes])
    if not hmac.compare_digest(digest.digest(), raw[-raw_oid_bytes:]):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_PACK_CHECKSUM")


def prove_captured_index_root_tree(
    raw: bytes,
    oid_bytes: int,
    expected_root_tree: str,
) -> CapturedIndexTreeProof:
    """Strictly parse a captured v2/v3 index and rebuild its exact root tree.

    Path bytes remain opaque Git-control metadata.  No worktree path or object
    body is opened.  Optional uppercase extensions are framed then ignored;
    split/sparse and every unknown required lowercase extension fail closed.
    """

    raw_oid_bytes = oid_bytes // 2
    if (
        oid_bytes not in (40, 64)
        or len(expected_root_tree) != oid_bytes
        or GIT_OID_RE.fullmatch(expected_root_tree) is None
        or len(raw) < 12 + raw_oid_bytes
        or len(raw) > MAX_GIT_INDEX_BYTES
        or raw[:4] != b"DIRC"
    ):
        fail(Exit.PREFLIGHT, "GIT_INDEX_FORMAT")
    version = int.from_bytes(raw[4:8], "big")
    if version == 4:
        fail(Exit.PREFLIGHT, "GIT_INDEX_VERSION_UNSUPPORTED")
    if version not in (2, 3):
        fail(Exit.PREFLIGHT, "GIT_INDEX_VERSION")
    trailer_start = len(raw) - raw_oid_bytes
    if not hmac.compare_digest(
        hashlib.new("sha1" if oid_bytes == 40 else "sha256", raw[:trailer_start]).digest(),
        raw[trailer_start:],
    ):
        fail(Exit.PREFLIGHT, "GIT_INDEX_CHECKSUM")
    entry_count = int.from_bytes(raw[8:12], "big")
    if entry_count > MAX_GIT_REACHABLE_OBJECTS:
        fail(Exit.PREFLIGHT, "GIT_INDEX_ENTRY_LIMIT")

    entries: List[Tuple[bytes, str, str]] = []
    opaque_gitlink_paths: List[bytes] = []
    cursor = 12
    previous_path: Optional[bytes] = None
    for _entry_index in range(entry_count):
        entry_start = cursor
        fixed_end = cursor + 40 + raw_oid_bytes + 2
        if fixed_end > trailer_start:
            fail(Exit.PREFLIGHT, "GIT_INDEX_ENTRY_TRUNCATED")
        mode_value = int.from_bytes(raw[cursor + 24 : cursor + 28], "big")
        oid_start = cursor + 40
        oid = raw[oid_start : oid_start + raw_oid_bytes].hex()
        flags = int.from_bytes(raw[oid_start + raw_oid_bytes : fixed_end], "big")
        cursor = fixed_end
        if flags & 0x4000:
            if version != 3 or cursor + 2 > trailer_start:
                fail(Exit.PREFLIGHT, "GIT_INDEX_EXTENDED_FLAGS")
            extended_flags = int.from_bytes(raw[cursor : cursor + 2], "big")
            cursor += 2
            if extended_flags != 0:
                # Includes skip-worktree and intent-to-add.  Both make a full
                # index-to-tree equality proof ambiguous for this narrow path.
                fail(Exit.PREFLIGHT, "GIT_INDEX_EXTENDED_FLAGS")
        if flags & 0x3000:
            fail(Exit.PREFLIGHT, "GIT_INDEX_UNMERGED")
        if flags & 0x8000:
            fail(Exit.PREFLIGHT, "GIT_INDEX_ASSUME_VALID")
        if mode_value == 0o040000:
            fail(Exit.PREFLIGHT, "GIT_INDEX_SPARSE_DIRECTORY")
        if mode_value not in (0o100644, 0o100755, 0o120000, 0o160000):
            fail(Exit.PREFLIGHT, "GIT_INDEX_MODE")
        if oid == "0" * oid_bytes or GIT_OID_RE.fullmatch(oid) is None:
            fail(Exit.PREFLIGHT, "GIT_INDEX_OID")
        nul = raw.find(b"\x00", cursor, trailer_start)
        if nul < 0:
            fail(Exit.PREFLIGHT, "GIT_INDEX_PATH_TERMINATOR")
        path = raw[cursor:nul]
        stored_length = flags & 0x0FFF
        if stored_length != min(len(path), 0x0FFF):
            fail(Exit.PREFLIGHT, "GIT_INDEX_PATH_LENGTH")
        if (
            not path
            or path.startswith(b"/")
            or path.endswith(b"/")
            or b"\\" in path
            or any(component in (b"", b".", b"..") for component in path.split(b"/"))
        ):
            fail(Exit.PREFLIGHT, "GIT_INDEX_PATH")
        if any(component.lower() == b".git" for component in path.split(b"/")):
            fail(Exit.PRIVACY, "GIT_INDEX_DOT_GIT")
        if mode_value == 0o160000:
            opaque_gitlink_paths.append(path)
        if previous_path is not None:
            if path <= previous_path:
                fail(Exit.PREFLIGHT, "GIT_INDEX_PATH_ORDER")
            if path.startswith(previous_path + b"/"):
                fail(Exit.PREFLIGHT, "GIT_INDEX_DIRECTORY_FILE_COLLISION")
        previous_path = path
        entry_body_end = nul + 1
        padding = (-(entry_body_end - entry_start)) % 8
        if entry_body_end + padding > trailer_start or raw[entry_body_end : entry_body_end + padding] != b"\x00" * padding:
            fail(Exit.PREFLIGHT, "GIT_INDEX_PADDING")
        cursor = entry_body_end + padding
        entries.append((path, format(mode_value, "o"), oid))

    if tuple(opaque_gitlink_paths) != (GENERATION_OPAQUE_GITLINK_INDEX_PATH_V1,):
        fail(Exit.PRIVACY, "GIT_INDEX_GITLINK_SET")

    seen_extensions = set()
    while cursor < trailer_start:
        if cursor + 8 > trailer_start:
            fail(Exit.PREFLIGHT, "GIT_INDEX_EXTENSION_FORMAT")
        signature = raw[cursor : cursor + 4]
        extension_size = int.from_bytes(raw[cursor + 4 : cursor + 8], "big")
        extension_end = cursor + 8 + extension_size
        if extension_end > trailer_start or signature in seen_extensions:
            fail(Exit.PREFLIGHT, "GIT_INDEX_EXTENSION_FORMAT")
        seen_extensions.add(signature)
        if signature in (b"link", b"sdir"):
            fail(Exit.PREFLIGHT, "GIT_INDEX_REQUIRED_EXTENSION")
        if not signature or not 65 <= signature[0] <= 90:
            fail(Exit.PREFLIGHT, "GIT_INDEX_REQUIRED_EXTENSION")
        cursor = extension_end
    if cursor != trailer_start:
        fail(Exit.PREFLIGHT, "GIT_INDEX_TRAILING")

    tree: Dict[bytes, Any] = {}
    for path, mode, oid in entries:
        components = path.split(b"/")
        node = tree
        for component in components[:-1]:
            existing = node.get(component)
            if existing is None:
                child: Dict[bytes, Any] = {}
                node[component] = child
                node = child
            elif isinstance(existing, dict):
                node = existing
            else:
                fail(Exit.PREFLIGHT, "GIT_INDEX_DIRECTORY_FILE_COLLISION")
        leaf = components[-1]
        if leaf in node:
            fail(Exit.PREFLIGHT, "GIT_INDEX_DIRECTORY_FILE_COLLISION")
        node[leaf] = (mode, oid)

    def hash_index_tree(node: Mapping[bytes, Any]) -> str:
        records: List[Tuple[bytes, bytes]] = []
        for name, value in node.items():
            if isinstance(value, dict):
                mode = "40000"
                oid = hash_index_tree(value)
                ordering_key = name + b"/"
            else:
                mode, oid = value
                ordering_key = name + b"\x00"
            record = mode.encode("ascii") + b" " + name + b"\x00" + bytes.fromhex(oid)
            records.append((ordering_key, record))
        body = b"".join(record for _key, record in sorted(records, key=lambda item: item[0]))
        return git_object_digest("tree", body, oid_bytes)

    computed_root = hash_index_tree(tree)
    if not hmac.compare_digest(computed_root, expected_root_tree):
        fail(Exit.PREFLIGHT, "GIT_INDEX_HEAD_TREE_MISMATCH")
    return CapturedIndexTreeProof(
        computed_root,
        entry_count,
        sha256(raw),
        version,
        len(opaque_gitlink_paths),
    )


def parse_bootstrap_object_batch(
    raw: bytes,
    expected_types: Mapping[str, str],
) -> Dict[str, bytes]:
    """Parse, type-check and independently hash one exact cat-file batch."""

    expected_oids = sorted(expected_types)
    if not expected_oids:
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_BATCH_EXPECTATION")
    oid_bytes = len(expected_oids[0])
    algorithm = "sha1" if oid_bytes == 40 else "sha256"
    cursor = 0
    result: Dict[str, bytes] = {}
    total = 0
    for expected_oid in expected_oids:
        newline = raw.find(b"\n", cursor)
        if newline < 0 or newline - cursor > 256:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_HEADER")
        fields = raw[cursor:newline].split(b" ")
        cursor = newline + 1
        if len(fields) != 3:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_HEADER")
        try:
            observed_oid = fields[0].decode("ascii", "strict")
            object_type = fields[1].decode("ascii", "strict")
            size_text = fields[2].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_HEADER")
        expected_type = expected_types.get(expected_oid)
        if (
            observed_oid != expected_oid
            or object_type != expected_type
            or re.fullmatch(r"0|[1-9][0-9]*", size_text) is None
        ):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_IDENTITY")
        size = int(size_text, 10)
        total += size
        end = cursor + size
        if (
            size > MAX_GIT_BYTES
            or total > MAX_GIT_BYTES
            or end >= len(raw)
            or raw[end : end + 1] != b"\n"
        ):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_LENGTH")
        content = raw[cursor:end]
        digest = hashlib.new(algorithm)
        digest.update((object_type + " " + str(size) + "\x00").encode("ascii"))
        digest.update(content)
        if not hmac.compare_digest(digest.hexdigest(), expected_oid):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_HASH")
        result[expected_oid] = content
        cursor = end + 1
    if cursor != len(raw) or set(result) != set(expected_types):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BATCH_SET")
    return result


def parse_bootstrap_tree_object_entries(
    raw: bytes,
    oid_bytes: int,
    *,
    tree_prefix: str = "",
) -> Tuple[RawGitTreeEntry, ...]:
    """Strictly parse one raw tree while keeping sibling names opaque bytes."""

    raw_oid_bytes = oid_bytes // 2
    if oid_bytes not in (40, 64):
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_RAW_TREE_OID_WIDTH")
    if tree_prefix:
        validate_relative(tree_prefix, "GIT_BOOTSTRAP_RAW_TREE_PREFIX")
    prefix_bytes = tree_prefix.encode("utf-8", "strict")
    cursor = 0
    entries: List[RawGitTreeEntry] = []
    seen_names = set()
    previous_key: Optional[bytes] = None
    while cursor < len(raw):
        space = raw.find(b" ", cursor)
        nul = raw.find(b"\x00", space + 1 if space >= 0 else cursor)
        if space < 0 or nul < 0 or nul == space + 1:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_FORMAT")
        try:
            mode = raw[cursor:space].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_MODE")
        name = raw[space + 1 : nul]
        oid_end = nul + 1 + raw_oid_bytes
        if oid_end > len(raw):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_OID")
        oid = raw[nul + 1 : oid_end].hex()
        if not name or b"/" in name or name in (b".", b".."):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_NAME")
        if name.lower() == b".git":
            fail(Exit.PRIVACY, "GIT_BOOTSTRAP_RAW_TREE_DOT_GIT")
        if name in seen_names:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_DUPLICATE")
        if len(oid) != oid_bytes or GIT_OID_RE.fullmatch(oid) is None:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_OID")
        if mode == "40000":
            kind = "tree"
        elif mode in ("100644", "100755"):
            kind = "blob"
        elif mode == "120000":
            kind = "symlink"
        elif mode == "160000":
            full_path = name if not prefix_bytes else prefix_bytes + b"/" + name
            if full_path != GENERATION_OPAQUE_GITLINK_INDEX_PATH_V1:
                fail(Exit.PRIVACY, "GIT_BOOTSTRAP_RAW_TREE_KIND")
            kind = "gitlink"
        else:
            # Every special mode other than the one exact opaque gitlink.
            fail(Exit.PRIVACY, "GIT_BOOTSTRAP_RAW_TREE_KIND")
        ordering_key = name + (b"/" if kind == "tree" else b"\x00")
        if previous_key is not None and ordering_key <= previous_key:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_RAW_TREE_ORDER")
        previous_key = ordering_key
        seen_names.add(name)
        entries.append(RawGitTreeEntry(mode, kind, oid, name, raw[cursor:oid_end]))
        cursor = oid_end
    return tuple(entries)


def build_required_path_trie(
    required_blob_paths: Sequence[str],
    required_absent_paths: Sequence[str],
) -> Dict[bytes, Any]:
    expectations: Dict[str, str] = {}
    folded_paths: Dict[str, str] = {}
    for expectation, paths in (("blob", required_blob_paths), ("absent", required_absent_paths)):
        for path in paths:
            validate_relative(path, "GIT_BOOTSTRAP_REQUIRED_PATH")
            if path in expectations:
                fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_DUPLICATE")
            folded = unicodedata.normalize("NFC", path).casefold()
            if folded in folded_paths and folded_paths[folded] != path:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_COLLISION")
            folded_paths[folded] = path
            expectations[path] = expectation
    trie: Dict[bytes, Any] = {}
    for path, expectation in sorted(expectations.items()):
        components = tuple(component.encode("utf-8", "strict") for component in path.split("/"))
        node = trie
        for component in components:
            if None in node:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_PREFIX")
            child = node.get(component)
            if child is None:
                child = {}
                node[component] = child
            elif not isinstance(child, dict):
                fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_TRIE")
            node = child
        if node:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_PREFIX")
        node[None] = expectation
    return trie


def resolve_required_path_trie(
    root_tree_oid: str,
    oid_bytes: int,
    required_blob_paths: Sequence[str],
    required_absent_paths: Sequence[str],
    object_loader: Callable[[Sequence[str]], Mapping[str, bytes]],
) -> RequiredPathTrieResolution:
    """Read only ancestor tree objects for explicit public paths.

    Every ancestor tree object necessarily contains its direct sibling names
    and OIDs because those bytes are hashed by Git.  Such sibling names remain
    opaque and are never path-validated, decoded, logged, or dereferenced.
    """

    trie = build_required_path_trie(required_blob_paths, required_absent_paths)
    path_expectations = {
        path: "blob" for path in required_blob_paths
    }
    path_expectations.update({path: "absent" for path in required_absent_paths})
    tree_cache: Dict[str, bytes] = {}
    tree_contexts: Dict[str, str] = {}
    path_entries: Dict[str, Tuple[str, str]] = {}
    pending: List[Tuple[str, str, Dict[bytes, Any]]] = [("", root_tree_oid, trie)]

    def mark_absent_subtree(prefix: str, node: Mapping[Any, Any]) -> None:
        terminal = node.get(None)
        if terminal is not None:
            if terminal != "absent":
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_MISSING")
            path_entries[prefix] = ("ABSENT", "")
        for component, child in node.items():
            if component is None:
                continue
            if not isinstance(component, bytes) or not isinstance(child, dict):
                fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_TRIE")
            try:
                component_text = component.decode("utf-8", "strict")
            except UnicodeDecodeError:
                fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_ENCODING")
            child_prefix = component_text if not prefix else prefix + "/" + component_text
            mark_absent_subtree(child_prefix, child)

    while pending:
        missing = tuple(sorted({oid for _prefix, oid, _node in pending if oid not in tree_cache}))
        if missing:
            loaded = dict(object_loader(missing))
            if set(loaded) != set(missing) or any(not isinstance(value, bytes) for value in loaded.values()):
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_TREE_LOADER_SET")
            tree_cache.update(loaded)
        next_pending: List[Tuple[str, str, Dict[bytes, Any]]] = []
        for prefix, tree_oid, node in pending:
            prior = tree_contexts.get(prefix)
            if prior is not None and prior != tree_oid:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_TREE_CONTEXT_COLLISION")
            if prior is not None:
                fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_TREE_CONTEXT_DUPLICATE")
            tree_contexts[prefix] = tree_oid
            entries = parse_bootstrap_tree_object_entries(
                tree_cache[tree_oid],
                oid_bytes,
                tree_prefix=prefix,
            )
            by_name = {entry.name: entry for entry in entries}
            for component, child in node.items():
                if component is None:
                    continue
                if not isinstance(component, bytes) or not isinstance(child, dict):
                    fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_TRIE")
                component_text = component.decode("utf-8", "strict")
                path = component_text if not prefix else prefix + "/" + component_text
                entry = by_name.get(component)
                terminal = child.get(None)
                descendants = tuple(key for key in child if key is not None)
                if entry is None:
                    mark_absent_subtree(path, child)
                    continue
                if terminal == "absent":
                    fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_PREIMAGE")
                if terminal == "blob":
                    if descendants or entry.kind != "blob" or entry.mode not in ("100644", "100755"):
                        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_MODE")
                    path_entries[path] = (entry.mode, entry.oid)
                    continue
                if terminal is not None:
                    fail(Exit.INTERNAL, "GIT_BOOTSTRAP_REQUIRED_PATH_EXPECTATION")
                if entry.kind != "tree" or entry.mode != "40000":
                    fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_ANCESTOR")
                next_pending.append((path, entry.oid, child))
                if len(tree_contexts) + len(next_pending) > MAX_GIT_REACHABLE_OBJECTS:
                    fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_TREE_LIMIT")
        pending = next_pending
    if set(path_entries) != set(path_expectations):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_SET")
    for path, expectation in path_expectations.items():
        mode, _oid = path_entries[path]
        if (expectation == "blob") != (mode in ("100644", "100755")):
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_REQUIRED_PATH_EXPECTATION")
    return RequiredPathTrieResolution(
        root_tree_oid,
        tuple(sorted(tree_contexts.items())),
        tuple((path, mode, oid) for path, (mode, oid) in sorted(path_entries.items())),
        tuple((prefix, tree_cache[oid]) for prefix, oid in sorted(tree_contexts.items())),
    )


def verify_path_local_one_file_addition(
    current: RequiredPathTrieResolution,
    parent: RequiredPathTrieResolution,
    relative: str,
) -> str:
    """Prove one exact regular-file addition by comparing only its Merkle path."""

    validate_relative(relative, "GIT_MICRO_TRANSITION_PATH")
    components = tuple(component.encode("utf-8", "strict") for component in relative.split("/"))
    current_raw = dict(current.tree_raw)
    parent_raw = dict(parent.tree_raw)
    current_paths = {path: (mode, oid) for path, mode, oid in current.path_entries}
    parent_paths = {path: (mode, oid) for path, mode, oid in parent.path_entries}
    if relative not in current_paths or parent_paths.get(relative) != ("ABSENT", ""):
        fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_ENDPOINT")
    current_mode, current_blob_oid = current_paths[relative]
    if current_mode != "100644" or GIT_OID_RE.fullmatch(current_blob_oid) is None:
        fail(Exit.PREFLIGHT, "GIT_MICRO_CURRENT_KIND")
    prefix = ""
    depth = 0
    while depth < len(components):
        if prefix not in current_raw or prefix not in parent_raw:
            fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_CONTEXT")
        current_entries = {
            entry.name: entry
            for entry in parse_bootstrap_tree_object_entries(
                current_raw[prefix],
                len(current.root_tree_oid),
                tree_prefix=prefix,
            )
        }
        parent_entries = {
            entry.name: entry
            for entry in parse_bootstrap_tree_object_entries(
                parent_raw[prefix],
                len(parent.root_tree_oid),
                tree_prefix=prefix,
            )
        }
        target = components[depth]
        if {
            name: entry.raw_record for name, entry in current_entries.items() if name != target
        } != {
            name: entry.raw_record for name, entry in parent_entries.items() if name != target
        }:
            fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_SIBLING_DRIFT")
        current_entry = current_entries.get(target)
        parent_entry = parent_entries.get(target)
        if current_entry is None:
            fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_CURRENT_MISSING")
        if depth == len(components) - 1:
            if parent_entry is not None or current_entry.mode != "100644" or current_entry.kind != "blob":
                fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_LEAF")
            break
        if current_entry.mode != "40000" or current_entry.kind != "tree":
            fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_CURRENT_ANCESTOR")
        if parent_entry is None:
            # The rest of a newly created directory chain may contain only the
            # next component of the authorized path at every level.
            created_prefix = components[0].decode("utf-8")
            for existing_component in components[1 : depth + 1]:
                created_prefix += "/" + existing_component.decode("utf-8")
            for remaining_depth in range(depth + 1, len(components)):
                if created_prefix not in current_raw:
                    fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_NEW_CHAIN_CONTEXT")
                chain_entries = parse_bootstrap_tree_object_entries(
                    current_raw[created_prefix],
                    len(current.root_tree_oid),
                    tree_prefix=created_prefix,
                )
                expected_component = components[remaining_depth]
                if len(chain_entries) != 1 or chain_entries[0].name != expected_component:
                    fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_NEW_CHAIN_SCOPE")
                chain_entry = chain_entries[0]
                if remaining_depth == len(components) - 1:
                    if chain_entry.mode != "100644" or chain_entry.kind != "blob":
                        fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_LEAF")
                else:
                    if chain_entry.mode != "40000" or chain_entry.kind != "tree":
                        fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_NEW_CHAIN_KIND")
                    created_prefix += "/" + expected_component.decode("utf-8")
            break
        if parent_entry.mode != "40000" or parent_entry.kind != "tree":
            fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_PARENT_ANCESTOR")
        prefix = components[0].decode("utf-8") if not prefix else prefix + "/" + target.decode("utf-8")
        depth += 1
    return sha256(
        canonical_json(
            {
                "profile": "path-local-one-file-merkle-addition-v1",
                "relative": relative,
                "current_root_tree": current.root_tree_oid,
                "parent_root_tree": parent.root_tree_oid,
                "current_blob_oid": current_blob_oid,
            }
        )
    )


def parse_object_oid_lines(raw: bytes, oid_bytes: int, label: str) -> Tuple[str, ...]:
    values: List[str] = []
    if raw and not raw.endswith(b"\n"):
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    for line in raw.splitlines():
        try:
            oid = line.decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, label + "_ENCODING")
        if len(oid) != oid_bytes or GIT_OID_RE.fullmatch(oid) is None:
            fail(Exit.PREFLIGHT, label + "_OID")
        values.append(oid)
    if len(values) != len(set(values)):
        fail(Exit.PREFLIGHT, label + "_DUPLICATE")
    return tuple(values)


def validate_captured_refname(value: Any, label: str) -> str:
    """Validate the strict ASCII refname subset used by the sealed adapter."""

    if not isinstance(value, str) or not value.startswith("refs/") or len(value) > 1024:
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    try:
        raw = value.encode("ascii", "strict")
    except UnicodeEncodeError:
        fail(Exit.PREFLIGHT, label + "_ENCODING")
    if (
        not raw
        or value.endswith(("/", "."))
        or "//" in value
        or ".." in value
        or "@{" in value
        or any(byte <= 0x20 or byte == 0x7F for byte in raw)
        or any(character in value for character in "~^:?*[\\")
    ):
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    components = value.split("/")
    if (
        len(components) < 2
        or components[0] != "refs"
        or any(
            not component
            or component in (".", "..")
            or component.startswith(".")
            or component.endswith(".lock")
            for component in components
        )
    ):
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    return value


def captured_ref_components(reference: str, label: str) -> List[str]:
    """Return safe adapter-path components for an already-private Git ref."""

    return validate_captured_refname(reference, label).split("/")


def parse_captured_ref_value(raw: Any, label: str) -> Tuple[str, str]:
    """Return (kind, value) for one exact frozen loose-ref byte string."""

    if not isinstance(raw, bytes):
        fail(Exit.INTERNAL, label + "_RAW")
    if (
        not raw
        or not raw.endswith(b"\n")
        or raw.count(b"\n") != 1
        or b"\r" in raw
        or b"\x00" in raw
    ):
        fail(Exit.PREFLIGHT, label + "_FORMAT")
    body = raw[:-1]
    if body.startswith(b"ref: "):
        try:
            target = body[5:].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, label + "_ENCODING")
        return "symbolic", validate_captured_refname(target, label + "_TARGET")
    try:
        oid = body.decode("ascii", "strict")
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT, label + "_ENCODING")
    if GIT_OID_RE.fullmatch(oid) is None:
        fail(Exit.PREFLIGHT, label + "_OID")
    if set(oid) == {"0"}:
        fail(Exit.PREFLIGHT, label + "_OID_ZERO")
    return "oid", oid


def parse_captured_packed_refs(raw: Optional[bytes]) -> Tuple[Dict[str, str], Tuple[str, ...]]:
    """Parse the same strict packed-refs grammar as the static executor."""

    if raw is None:
        return {}, ()
    if not isinstance(raw, bytes):
        fail(Exit.INTERNAL, "GIT_CAPTURE_PACKED_REFS")
    if not raw:
        return {}, ()
    if not raw.endswith(b"\n") or b"\r" in raw or b"\x00" in raw:
        fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_FORMAT")
    primary: Dict[str, str] = {}
    peeled_oids: List[str] = []
    peel_allowed = False
    sorted_declared = False
    previous_primary_ref: Optional[str] = None
    for line_index, raw_line in enumerate(raw[:-1].split(b"\n")):
        if not raw_line:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_FORMAT")
        if raw_line.startswith(b"#"):
            if line_index != 0 or not raw_line.startswith(b"# pack-refs with: "):
                fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_HEADER")
            try:
                capabilities_text = raw_line[len(b"# pack-refs with: ") :].decode(
                    "ascii", "strict"
                )
            except UnicodeDecodeError:
                fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_ENCODING")
            capabilities = capabilities_text.strip().split(" ")
            if (
                not capabilities
                or any(not capability for capability in capabilities)
                or len(set(capabilities)) != len(capabilities)
                or not set(capabilities).issubset({"peeled", "fully-peeled", "sorted"})
            ):
                fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_HEADER")
            sorted_declared = "sorted" in capabilities
            peel_allowed = False
            continue
        if raw_line.startswith(b"^"):
            if not peel_allowed:
                fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_PEELED_POSITION")
            peeled_kind, peeled_oid = parse_captured_ref_value(
                raw_line[1:] + b"\n", "GIT_PACKED_REFS_PEELED"
            )
            if peeled_kind != "oid":
                fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_PEELED_VALUE")
            peeled_oids.append(peeled_oid)
            peel_allowed = False
            continue
        if raw_line.count(b" ") != 1:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_FORMAT")
        oid_raw, reference_raw = raw_line.split(b" ", 1)
        try:
            reference = reference_raw.decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_ENCODING")
        reference = validate_captured_refname(reference, "GIT_PACKED_REFS_PRIMARY")
        if reference in primary:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_DUPLICATE")
        if len(primary) >= MAX_CAPTURED_REF_ENTRIES:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_LIMIT")
        oid_kind, oid = parse_captured_ref_value(
            oid_raw + b"\n", "GIT_PACKED_REFS_PRIMARY"
        )
        if oid_kind != "oid":
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_VALUE")
        if sorted_declared and previous_primary_ref is not None and reference <= previous_primary_ref:
            fail(Exit.PREFLIGHT, "GIT_PACKED_REFS_ORDER")
        primary[reference] = oid
        previous_primary_ref = reference
        peel_allowed = True
    return primary, tuple(peeled_oids)


def is_per_worktree_ref(reference: str) -> bool:
    suffix = reference[len("refs/") :] if reference.startswith("refs/") else ""
    return any(suffix.startswith(namespace) for namespace in WORKTREE_REF_NAMESPACES)


def parse_captured_refs(capture: Mapping[str, Any]) -> CapturedRefs:
    """Parse frozen common, worktree and packed refs without object reads."""

    raw_files = capture.get("raw_files")
    identity = capture.get("identity")
    git_dir = capture.get("git_dir")
    common_dir = capture.get("common_dir")
    if (
        not isinstance(raw_files, dict)
        or not isinstance(identity, dict)
        or not isinstance(git_dir, str)
        or not isinstance(common_dir, str)
    ):
        fail(Exit.INTERNAL, "GIT_CAPTURE_SCHEMA")
    linked_worktree = git_dir != common_dir

    all_direct_oids: List[str] = []

    def loose_source(
        tree_key: str,
        raw_key: str,
        label: str,
        worktree_source: bool,
    ) -> Tuple[Dict[str, bytes], Dict[str, Tuple[str, str]]]:
        tree = identity.get(tree_key)
        frozen = capture.get(raw_key)
        if not isinstance(tree, dict) or not isinstance(frozen, dict):
            fail(Exit.INTERNAL, "GIT_CAPTURE_REFS")
        tree_files = tree.get("files", [])
        if not isinstance(tree_files, list):
            fail(Exit.INTERNAL, "GIT_CAPTURE_REF_FILES")
        expected_relatives = set()
        raw_values: Dict[str, bytes] = {}
        parsed_values: Dict[str, Tuple[str, str]] = {}
        for entry in tree_files:
            if not isinstance(entry, dict):
                fail(Exit.INTERNAL, "GIT_CAPTURE_REF_ENTRY")
            relative = entry.get("relative")
            if not isinstance(relative, str):
                fail(Exit.INTERNAL, "GIT_CAPTURE_REF_PATH")
            if relative in expected_relatives:
                fail(Exit.INTERNAL, "GIT_CAPTURE_REF_PATH_DUPLICATE")
            expected_relatives.add(relative)
            raw = frozen.get(relative)
            if not isinstance(raw, bytes):
                fail(Exit.INTERNAL, "GIT_CAPTURE_REF_RAW")
            reference = validate_captured_refname("refs/" + relative, label)
            if worktree_source and (not linked_worktree or not is_per_worktree_ref(reference)):
                fail(Exit.PREFLIGHT, "GIT_WORKTREE_REF_NAMESPACE")
            if linked_worktree and not worktree_source and is_per_worktree_ref(reference):
                # Git hides common loose values in these namespaces before it
                # interprets their contents for a linked worktree.
                continue
            value = parse_captured_ref_value(raw, label)
            raw_values[reference] = raw
            parsed_values[reference] = value
            if value[0] == "oid":
                all_direct_oids.append(value[1])
        if set(frozen) != expected_relatives:
            fail(Exit.INTERNAL, "GIT_CAPTURE_REF_RAW_SET")
        return raw_values, parsed_values

    common_raw, common_values = loose_source(
        "common_refs", "common_ref_raw", "GIT_CAPTURE_COMMON_REF", False
    )
    worktree_raw, worktree_values = loose_source(
        "worktree_refs", "worktree_ref_raw", "GIT_CAPTURE_WORKTREE_REF", True
    )
    packed, peeled_oids = parse_captured_packed_refs(raw_files.get("packed_refs"))
    all_direct_oids.extend(packed.values())
    all_direct_oids.extend(peeled_oids)

    effective_raw: Dict[str, bytes] = {}
    effective_values: Dict[str, Tuple[str, str]] = {}
    for reference, oid in packed.items():
        effective_raw[reference] = (oid + "\n").encode("ascii")
        effective_values[reference] = ("oid", oid)
    for reference, value in common_values.items():
        if not linked_worktree or not is_per_worktree_ref(reference):
            effective_raw[reference] = common_raw[reference]
            effective_values[reference] = value
    effective_raw.update(worktree_raw)
    effective_values.update(worktree_values)
    if len(effective_values) > MAX_CAPTURED_REF_ENTRIES:
        fail(Exit.PREFLIGHT, "GIT_CAPTURE_EFFECTIVE_REF_LIMIT")

    def resolve_value(kind: str, value: str, label: str) -> str:
        seen = set()
        for _depth in range(MAX_CAPTURED_REF_SYMREF_DEPTH + 1):
            if kind == "oid":
                return value
            if value in seen:
                fail(Exit.PREFLIGHT, label + "_CYCLE")
            if len(seen) >= MAX_CAPTURED_REF_SYMREF_DEPTH:
                fail(Exit.PREFLIGHT, label + "_DEPTH")
            seen.add(value)
            target = effective_values.get(value)
            if target is None:
                fail(Exit.PREFLIGHT, label + "_BROKEN")
            kind, value = target
        fail(Exit.INTERNAL, "GIT_CAPTURE_REF_RESOLUTION")
        raise AssertionError("unreachable")

    head_raw = raw_files.get("head")
    if not isinstance(head_raw, bytes):
        fail(Exit.INTERNAL, "GIT_CAPTURE_HEAD")
    head_kind, head_target = parse_captured_ref_value(head_raw, "GIT_CAPTURE_HEAD")
    if head_kind != "symbolic":
        fail(Exit.PREFLIGHT, "GIT_CAPTURE_HEAD_SYMBOLIC")
    head_ref = validate_head_ref(head_target)
    head_oid = resolve_value(head_kind, head_target, "GIT_CAPTURE_HEAD_REF")
    oid_width = len(head_oid)
    if oid_width not in (40, 64):
        fail(Exit.PREFLIGHT, "GIT_CAPTURE_HEAD_OID")
    if any(len(oid) != oid_width for oid in all_direct_oids):
        fail(Exit.PREFLIGHT, "GIT_CAPTURE_REF_OID_WIDTH")
    expected = tuple(
        (
            resolve_value(kind, value, "GIT_CAPTURE_REF_RESOLUTION"),
            reference,
        )
        for reference, (kind, value) in sorted(effective_values.items())
    )
    return CapturedRefs(
        tuple(sorted(effective_raw.items())),
        expected,
        head_oid,
        head_ref,
        oid_width,
    )


def captured_ref_map(capture: Mapping[str, Any]) -> Dict[str, bytes]:
    return dict(parse_captured_refs(capture).effective_raw)


def captured_head_oid_and_ref(capture: Mapping[str, Any]) -> Tuple[str, str]:
    refs = parse_captured_refs(capture)
    return refs.head_oid, refs.head_ref


def copy_captured_refs(capture: Mapping[str, Any], adapter_git_dir: str) -> None:
    refs = captured_ref_map(capture)
    for reference, raw in sorted(refs.items()):
        components = captured_ref_components(reference, "GIT_ADAPTER_REF")
        target = os.path.join(adapter_git_dir, *components)
        os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
        write_adapter_file(target, raw, "GIT_ADAPTER_REF")


def copy_captured_refs_at(capture: Mapping[str, Any], adapter_git_fd: int) -> None:
    """Copy frozen refs beneath the already-open adapter Git directory."""

    refs = captured_ref_map(capture)
    for reference, raw in sorted(refs.items()):
        components = captured_ref_components(reference, "GIT_ADAPTER_REF")
        try:
            current_fd = os.dup(adapter_git_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_REF_ROOT_DUP")
        try:
            for component in components[:-1]:
                child_fd = open_adapter_directory_at(
                    current_fd,
                    component,
                    True,
                    "GIT_ADAPTER_REF_DIRECTORY",
                )
                os.close(current_fd)
                current_fd = child_fd
            write_adapter_file_at(current_fd, components[-1], raw, "GIT_ADAPTER_REF")
        finally:
            os.close(current_fd)


def adapter_tree_fingerprint(adapter_root: str) -> str:
    records: List[Dict[str, Any]] = []

    def walk(path: str, relative: str) -> None:
        metadata = os.lstat(path)
        if stat.S_ISLNK(metadata.st_mode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SYMLINK")
        kind = "D" if stat.S_ISDIR(metadata.st_mode) else "F" if stat.S_ISREG(metadata.st_mode) else "S"
        if kind == "S":
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SPECIAL")
        records.append({"relative": relative, "kind": kind, "metadata": git_source_metadata(metadata)})
        if kind == "D":
            try:
                entries = list(os.scandir(path))
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCAN")
            for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
                child_relative = entry.name if not relative else relative + "/" + entry.name
                walk(os.path.join(path, entry.name), child_relative)

    walk(adapter_root, "")
    return sha256(canonical_json(records))


def adapter_tree_fingerprint_at(
    adapter_root_fd: int,
    pinned_git_fd: Optional[int] = None,
) -> str:
    """Fingerprint an adapter by descriptor-relative, no-follow traversal."""

    records: List[Dict[str, Any]] = []

    def walk(directory_fd: int, relative: str) -> None:
        try:
            directory_metadata = os.fstat(directory_fd)
            names = os.listdir(directory_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCAN")
        if not stat.S_ISDIR(directory_metadata.st_mode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SPECIAL")
        records.append(
            {
                "relative": relative,
                "kind": "D",
                "metadata": git_source_metadata(directory_metadata),
            }
        )
        for name in sorted(names, key=os.fsencode):
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_LSTAT")
            child_relative = name if not relative else relative + "/" + name
            if stat.S_ISDIR(metadata.st_mode):
                try:
                    child_fd = os.open(
                        name,
                        os.O_RDONLY
                        | getattr(os, "O_DIRECTORY", 0)
                        | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_DIRECTORY_OPEN")
                try:
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_DIRECTORY_RACE")
                    walk(child_fd, child_relative)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(metadata.st_mode):
                try:
                    child_fd = os.open(
                        name,
                        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_FILE_OPEN")
                try:
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_FILE_RACE")
                    records.append(
                        {
                            "relative": child_relative,
                            "kind": "F",
                            "metadata": git_source_metadata(opened),
                        }
                    )
                finally:
                    os.close(child_fd)
            else:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SPECIAL")

    if pinned_git_fd is None:
        walk(adapter_root_fd, "")
    else:
        try:
            root_metadata = os.fstat(adapter_root_fd)
            names = os.listdir(adapter_root_fd)
            named_git = os.stat("git", dir_fd=adapter_root_fd, follow_symlinks=False)
            pinned_git = os.fstat(pinned_git_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_GIT_IDENTITY")
        if (
            names != ["git"]
            or not stat.S_ISDIR(named_git.st_mode)
            or (named_git.st_dev, named_git.st_ino) != (pinned_git.st_dev, pinned_git.st_ino)
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_GIT_DRIFT")
        records.append(
            {
                "relative": "",
                "kind": "D",
                "metadata": git_source_metadata(root_metadata),
            }
        )
        walk(pinned_git_fd, "git")
    return sha256(canonical_json(records))


def seal_git_adapter_tree(adapter_root: str) -> None:
    directories: List[str] = []
    for current, names, files in os.walk(adapter_root, topdown=True, followlinks=False):
        directories.append(current)
        for name in names:
            path = os.path.join(current, name)
            if stat.S_ISLNK(os.lstat(path).st_mode):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_SYMLINK")
        for name in files:
            path = os.path.join(current, name)
            if not stat.S_ISREG(os.lstat(path).st_mode):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_FILE")
            os.chmod(path, 0o400, follow_symlinks=False)
    for directory in reversed(directories):
        os.chmod(directory, 0o500, follow_symlinks=False)


def seal_git_adapter_tree_at(adapter_root_fd: int) -> None:
    """Seal only objects reached beneath an already-open adapter root."""

    def seal_directory(directory_fd: int) -> None:
        try:
            names = os.listdir(directory_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_SCAN")
        for name in sorted(names, key=os.fsencode):
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_LSTAT")
            if stat.S_ISDIR(metadata.st_mode):
                try:
                    child_fd = os.open(
                        name,
                        os.O_RDONLY
                        | getattr(os, "O_DIRECTORY", 0)
                        | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_DIRECTORY_OPEN")
                try:
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_DIRECTORY_RACE")
                    seal_directory(child_fd)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(metadata.st_mode):
                try:
                    child_fd = os.open(
                        name,
                        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_FILE_OPEN")
                try:
                    if (
                        (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
                        or opened.st_uid != os.getuid()
                        or opened.st_nlink != 1
                    ):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_FILE_RACE")
                    os.fchmod(child_fd, 0o400)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_FILE_CHMOD")
                finally:
                    os.close(child_fd)
            else:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_FILE")
        try:
            os.fchmod(directory_fd, 0o500)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_DIRECTORY_CHMOD")

    seal_directory(adapter_root_fd)


def remove_git_adapter_root_exact(
    adapter_root: str,
    expected_device: int,
    expected_inode: int,
    expected_git_device: Optional[int] = None,
    expected_git_inode: Optional[int] = None,
    git_already_removed: bool = False,
    git_removed_callback: Optional[Callable[[], None]] = None,
    pinned_root_fd: Optional[int] = None,
    pinned_git_fd: Optional[int] = None,
) -> None:
    """Remove the registered adapter under the declared host trust boundary."""

    if (
        os.path.dirname(adapter_root) != "/private/tmp"
        or not os.path.basename(adapter_root).startswith("gov01-git-adapter-")
        or (expected_git_device is None) != (expected_git_inode is None)
        or (git_already_removed and expected_git_device is not None)
        or (git_removed_callback is not None and expected_git_device is None)
        or (pinned_git_fd is not None and pinned_root_fd is None)
        or (pinned_git_fd is not None and expected_git_device is None)
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_CLEANUP_LOCATOR")
    name = os.path.basename(adapter_root)
    parent_fd: Optional[int] = None
    root_fd: Optional[int] = None

    def descriptor_path(file_descriptor: int, label: str) -> str:
        try:
            raw = fcntl.fcntl(file_descriptor, fcntl.F_GETPATH, bytes(1024))
            value = raw.split(b"\x00", 1)[0].decode("utf-8", "strict")
        except (OSError, UnicodeDecodeError):
            fail(Exit.PREFLIGHT, label + "_DESCRIPTOR_PATH")
        if not value or not os.path.isabs(value) or os.path.normpath(value) != value:
            fail(Exit.PREFLIGHT, label + "_DESCRIPTOR_PATH")
        return value

    def empty_directory(
        directory_fd: int,
        pinned_child: Optional[Tuple[str, int, int]] = None,
    ) -> None:
        try:
            os.fchmod(directory_fd, 0o700)
            names = os.listdir(directory_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_SCAN")
        if pinned_child is not None:
            child_name, child_device, child_inode = pinned_child
            if child_name not in names:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_GIT_MISSING")
            if names != [child_name]:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_GIT_DRIFT")
        for child_name in names:
            try:
                metadata = os.stat(child_name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_LSTAT")
            if pinned_child is not None and (metadata.st_dev, metadata.st_ino) != (
                child_device,
                child_inode,
            ):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_GIT_DRIFT")
            if stat.S_ISDIR(metadata.st_mode):
                child_fd: Optional[int] = None
                try:
                    child_fd = os.open(
                        child_name,
                        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_CHILD_RACE")
                    expected_path = descriptor_path(child_fd, "GIT_ADAPTER_CLEANUP_CHILD")
                    empty_directory(child_fd)
                    before_remove = os.stat(child_name, dir_fd=directory_fd, follow_symlinks=False)
                    if (before_remove.st_dev, before_remove.st_ino) != (opened.st_dev, opened.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_CHILD_FINAL_DRIFT")
                    os.rmdir(child_name, dir_fd=directory_fd)
                    retained = os.fstat(child_fd)
                    if (retained.st_dev, retained.st_ino) != (opened.st_dev, opened.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_CHILD_FINAL_RACE")
                    if descriptor_path(child_fd, "GIT_ADAPTER_CLEANUP_CHILD") != expected_path:
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_CHILD_RETAINED")
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_CHILD_OPEN")
                finally:
                    if child_fd is not None:
                        os.close(child_fd)
            else:
                if not stat.S_ISREG(metadata.st_mode):
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FILE_KIND")
                child_fd = None
                try:
                    child_fd = os.open(
                        child_name,
                        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=directory_fd,
                    )
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FILE_RACE")
                    before_remove = os.stat(child_name, dir_fd=directory_fd, follow_symlinks=False)
                    if (before_remove.st_dev, before_remove.st_ino) != (opened.st_dev, opened.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FILE_FINAL_DRIFT")
                    os.unlink(child_name, dir_fd=directory_fd)
                    retained = os.fstat(child_fd)
                    if (retained.st_dev, retained.st_ino) != (opened.st_dev, opened.st_ino):
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FILE_FINAL_RACE")
                    if retained.st_nlink != 0:
                        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FILE_RETAINED")
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_UNLINK")
                finally:
                    if child_fd is not None:
                        os.close(child_fd)

    try:
        parent_fd = os.open(
            "/private/tmp",
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_ROOT_MISSING")
        if (metadata.st_dev, metadata.st_ino) != (expected_device, expected_inode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_ROOT_DRIFT")
        root_fd = (
            os.dup(pinned_root_fd)
            if pinned_root_fd is not None
            else os.open(
                name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
        )
        opened_root = os.fstat(root_fd)
        if (opened_root.st_dev, opened_root.st_ino) != (expected_device, expected_inode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_ROOT_RACE")
        if pinned_git_fd is not None:
            opened_git = os.fstat(pinned_git_fd)
            if (opened_git.st_dev, opened_git.st_ino) != (
                expected_git_device,
                expected_git_inode,
            ):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_GIT_FD_DRIFT")
        if git_already_removed:
            try:
                os.fchmod(root_fd, 0o700)
                if os.listdir(root_fd):
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_POST_GIT_RESIDUE")
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_POST_GIT_SCAN")
        else:
            pinned_git = (
                ("git", int(expected_git_device), int(expected_git_inode))
                if expected_git_device is not None and expected_git_inode is not None
                else None
            )
            empty_directory(root_fd, pinned_git)
            if pinned_git is not None and git_removed_callback is not None:
                git_removed_callback()
        before_remove = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (before_remove.st_dev, before_remove.st_ino) != (expected_device, expected_inode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FINAL_ROOT_DRIFT")
        os.rmdir(name, dir_fd=parent_fd)
        retained = os.fstat(root_fd)
        if (retained.st_dev, retained.st_ino) != (expected_device, expected_inode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FINAL_ROOT_RACE")
        if descriptor_path(root_fd, "GIT_ADAPTER_CLEANUP_ROOT") != adapter_root:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_EXPECTED_INODE_RETAINED")
        try:
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_RESIDUE")
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_IO")
    finally:
        if root_fd is not None:
            os.close(root_fd)
        if parent_fd is not None:
            os.close(parent_fd)


def register_staged_git_adapter(
    staged: StagedGitAdapter,
    scope: Optional[GitAdapterScope],
) -> None:
    """Register a new root before any adapter subtree is materialized."""

    if staged.closed or staged in _OPEN_GIT_ADAPTERS:
        fail(Exit.INTERNAL, "GIT_ADAPTER_STAGED_REGISTRATION")
    if scope is not None:
        if (
            _ACTIVE_GIT_ADAPTER_SCOPE is not scope
            or not scope.entered
            or scope.owner_thread != threading.get_ident()
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
        scope.registrations.append(staged)
    _OPEN_GIT_ADAPTERS.append(staged)


def promote_staged_git_adapter(
    staged: StagedGitAdapter,
    boundary: GitReadBoundary,
) -> None:
    """Atomically replace one staged registry entry with its sealed boundary."""

    global_matches = [
        index for index, candidate in enumerate(_OPEN_GIT_ADAPTERS) if candidate is staged
    ]
    if len(global_matches) != 1 or staged.closed:
        fail(Exit.INTERNAL, "GIT_ADAPTER_STAGED_PROMOTION")
    if (
        staged.adapter_root_fd != boundary.adapter_root_fd
        or staged.adapter_git_fd != boundary.adapter_git_fd
        or staged.git_device != boundary.git_device
        or staged.git_inode != boundary.git_inode
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_STAGED_PROMOTION_IDENTITY")
    scope = staged.scope
    if scope is not None:
        scope_matches = [
            index for index, candidate in enumerate(scope.registrations) if candidate is staged
        ]
        if (
            len(scope_matches) != 1
            or _ACTIVE_GIT_ADAPTER_SCOPE is not scope
            or not scope.entered
        ):
            fail(Exit.INTERNAL, "GIT_ADAPTER_STAGED_SCOPE_PROMOTION")
        scope.registrations[scope_matches[0]] = boundary
    _OPEN_GIT_ADAPTERS[global_matches[0]] = boundary
    staged.adapter_root_fd = -1
    staged.adapter_git_fd = -1
    staged.closed = True


def create_git_metadata_adapter(
    repo_root: str,
    git_binary: str,
    developer_root: str,
    parent_depth: int = 0,
    required_current_blob_paths: Sequence[str] = (),
    required_parent_absent_paths: Sequence[str] = (),
) -> Tuple[Dict[str, Any], GitReadBoundary]:
    """Create one adapter under the process-wide non-overlap guard."""

    active_scope = _ACTIVE_GIT_ADAPTER_SCOPE
    standalone_guard = False
    if active_scope is None:
        if not _GIT_ADAPTER_SCOPE_LOCK.acquire(blocking=False):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
        standalone_guard = True
        if _ACTIVE_GIT_ADAPTER_SCOPE is not None or _OPEN_GIT_ADAPTERS:
            _GIT_ADAPTER_SCOPE_LOCK.release()
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
    elif (
        not active_scope.entered
        or active_scope.owner_thread != threading.get_ident()
        or _OPEN_GIT_ADAPTERS
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_SCOPE_CONCURRENT")
    try:
        return _create_git_metadata_adapter_guarded(
            repo_root,
            git_binary,
            developer_root,
            parent_depth,
            required_current_blob_paths,
            required_parent_absent_paths,
            active_scope,
        )
    finally:
        if standalone_guard:
            _GIT_ADAPTER_SCOPE_LOCK.release()


def _create_git_metadata_adapter_guarded(
    repo_root: str,
    git_binary: str,
    developer_root: str,
    parent_depth: int,
    required_current_blob_paths: Sequence[str],
    required_parent_absent_paths: Sequence[str],
    registering_scope: Optional[GitAdapterScope],
) -> Tuple[Dict[str, Any], GitReadBoundary]:
    # Explicit path authority must fail before any Git control or object-store
    # stat/open.  Current and parent expectations are separate revisions, so
    # the same transition path is valid in both calls.
    build_required_path_trie(required_current_blob_paths, ())
    build_required_path_trie((), required_parent_absent_paths)
    capture = capture_git_source(repo_root)
    captured_refs = parse_captured_refs(capture)
    head_oid = captured_refs.head_oid
    object_format = "sha1" if len(head_oid) == 40 else "sha256"
    git_binary_before = git_source_metadata(no_symlink_path(git_binary, "GIT_BOOTSTRAP_BINARY"))
    adapter_root = tempfile.mkdtemp(prefix="gov01-git-adapter-", dir="/private/tmp")
    adapter_metadata = os.lstat(adapter_root)
    adapter_device = adapter_metadata.st_dev
    adapter_inode = adapter_metadata.st_ino
    adapter_git_dir = os.path.join(adapter_root, "git")
    adapter_root_fd: Optional[int] = None
    adapter_git_fd: Optional[int] = None
    adapter_git_device: Optional[int] = None
    adapter_git_inode: Optional[int] = None
    boundary: Optional[GitReadBoundary] = None
    staged = StagedGitAdapter(
        adapter_root,
        adapter_device,
        adapter_inode,
        registering_scope,
    )
    register_staged_git_adapter(staged, registering_scope)
    try:
        adapter_root_fd = os.open(
            adapter_root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        staged.adapter_root_fd = adapter_root_fd
        opened_adapter = os.fstat(adapter_root_fd)
        if (
            (opened_adapter.st_dev, opened_adapter.st_ino) != (adapter_device, adapter_inode)
            or not stat.S_ISDIR(opened_adapter.st_mode)
            or opened_adapter.st_uid != os.getuid()
            or stat.S_IMODE(opened_adapter.st_mode) != 0o700
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_ROOT_OPEN_RACE")
        os.mkdir("git", 0o700, dir_fd=adapter_root_fd)
        adapter_git_fd = open_adapter_directory_at(
            adapter_root_fd,
            "git",
            False,
            "GIT_ADAPTER_GIT_DIRECTORY",
        )
        staged.adapter_git_fd = adapter_git_fd
        opened_git = os.fstat(adapter_git_fd)
        adapter_git_device = opened_git.st_dev
        adapter_git_inode = opened_git.st_ino
        staged.git_device = adapter_git_device
        staged.git_inode = adapter_git_inode
        config_lines = [
            "[core]",
            "\trepositoryformatversion = " + ("0" if object_format == "sha1" else "1"),
            "\tbare = false",
            "\tfilemode = true",
            "\tlogallrefupdates = false",
            "\tfsmonitor = false",
            "\tuntrackedCache = false",
            "\thooksPath = /dev/null",
            "\texcludesFile = /dev/null",
            "\tattributesFile = /dev/null",
            "[protocol]",
            "\tallow = never",
            "[submodule]",
            "\trecurse = false",
            "[diff]",
            "\trenames = false",
        ]
        if object_format == "sha256":
            config_lines.extend(("[extensions]", "\tobjectFormat = sha256"))
        safe_config = ("\n".join(config_lines) + "\n").encode("ascii")
        write_adapter_file_at(
            adapter_git_fd,
            "config",
            safe_config,
            "GIT_ADAPTER_CONFIG",
        )
        raw_files = capture["raw_files"]
        write_adapter_file_at(
            adapter_git_fd,
            "HEAD",
            raw_files["head"],
            "GIT_ADAPTER_HEAD",
        )
        write_adapter_file_at(
            adapter_git_fd,
            "index",
            raw_files["index"],
            "GIT_ADAPTER_INDEX",
        )
        # Every effective packed ref is materialized as one strict loose ref.
        # Omitting the raw common packed-refs file is required for linked
        # worktrees because common per-worktree namespaces are hidden there.
        for role, name in (("shallow", "shallow"),):
            raw = raw_files.get(role)
            if raw is not None:
                write_adapter_file_at(
                    adapter_git_fd,
                    name,
                    raw,
                    "GIT_ADAPTER_" + role.upper(),
                )
        copy_captured_refs_at(capture, adapter_git_fd)
        materialized = materialize_reachable_git_objects(
            git_binary,
            developer_root,
            capture,
            ".",
            parent_depth,
            tuple(required_current_blob_paths),
            tuple(required_parent_absent_paths),
            adapter_git_fd,
        )
        if git_source_metadata(no_symlink_path(git_binary, "GIT_BOOTSTRAP_BINARY")) != git_binary_before:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_BINARY_DRIFT")
        recaptured = capture_git_source(repo_root)
        if (
            recaptured["git_dir"] != capture["git_dir"]
            or recaptured["common_dir"] != capture["common_dir"]
            or recaptured["fingerprint"] != capture["fingerprint"]
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SOURCE_DRIFT")
        seal_git_adapter_tree_at(adapter_git_fd)
        try:
            os.fchmod(adapter_root_fd, 0o500)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_SEAL_ROOT_CHMOD")
        adapter_fingerprint = adapter_tree_fingerprint_at(adapter_root_fd, adapter_git_fd)
        adapter_metadata = os.lstat(adapter_root)
        if (adapter_metadata.st_dev, adapter_metadata.st_ino) != (adapter_device, adapter_inode):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_ROOT_DRIFT")
        if (
            adapter_root_fd is None
            or adapter_git_fd is None
            or adapter_git_device is None
            or adapter_git_inode is None
        ):
            fail(Exit.INTERNAL, "GIT_ADAPTER_GIT_IDENTITY")
        boundary = GitReadBoundary(
            developer_root,
            repo_root,
            str(capture["git_dir"]),
            str(capture["common_dir"]),
            adapter_root,
            adapter_device,
            adapter_inode,
            int(adapter_root_fd),
            adapter_git_dir,
            int(adapter_git_device),
            int(adapter_git_inode),
            int(adapter_git_fd),
            str(capture["fingerprint"]),
            adapter_fingerprint,
            captured_refs.expected,
            materialized["expected_object_types"],
            tuple(required_current_blob_paths),
            tuple(required_parent_absent_paths),
            materialized["current_path_resolution"],
            materialized["parent_path_resolution"],
            head_oid,
            materialized["head_tree"],
            materialized["parent_oid"],
            materialized["parent_tree"],
            materialized["index_tree_proof"],
            materialized["one_file_transition_receipt"],
        )
        promote_staged_git_adapter(staged, boundary)
        adapter_root_fd = None
        adapter_git_fd = None
        verify_materialized_git_objects(
            git_binary,
            repo_root,
            boundary,
            head_oid,
            materialized["head_tree"],
            materialized["parent_oid"],
            materialized["parent_tree"],
        )
        revalidate_git_metadata_source(boundary)
        return dict(capture["git_control"]), boundary
    except BaseException:
        if boundary is not None and staged.closed:
            cleanup_git_metadata_adapter(boundary)
        else:
            cleanup_staged_git_adapter(staged)
        raise


def verify_git_metadata_adapter(boundary: GitReadBoundary) -> None:
    if boundary.closed:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLOSED")
    if boundary.git_removed:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_IN_PROGRESS")
    if boundary.adapter_root_fd < 0 or boundary.adapter_git_fd < 0:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_FD_CLOSED")
    if (
        os.path.dirname(boundary.adapter_root) != "/private/tmp"
        or not os.path.basename(boundary.adapter_root).startswith("gov01-git-adapter-")
        or boundary.git_dir != os.path.join(boundary.adapter_root, "git")
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_LOCATOR")
    try:
        named_root = os.stat(boundary.adapter_root, follow_symlinks=False)
        opened_root = os.fstat(boundary.adapter_root_fd)
        named_git = os.stat("git", dir_fd=boundary.adapter_root_fd, follow_symlinks=False)
        opened_git = os.fstat(boundary.adapter_git_fd)
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_IDENTITY_MISSING")
    if (
        (named_root.st_dev, named_root.st_ino)
        != (boundary.adapter_device, boundary.adapter_inode)
        or (opened_root.st_dev, opened_root.st_ino)
        != (boundary.adapter_device, boundary.adapter_inode)
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_ROOT_DRIFT")
    if (
        (named_git.st_dev, named_git.st_ino) != (boundary.git_device, boundary.git_inode)
        or (opened_git.st_dev, opened_git.st_ino) != (boundary.git_device, boundary.git_inode)
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_GIT_DRIFT")
    if (
        adapter_tree_fingerprint_at(boundary.adapter_root_fd, boundary.adapter_git_fd)
        != boundary.adapter_fingerprint
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_DRIFT")


def revalidate_git_metadata_source(boundary: GitReadBoundary) -> None:
    current = capture_git_source(boundary.repo_root)
    if (
        current["git_dir"] != boundary.live_git_dir
        or current["common_dir"] != boundary.live_common_dir
        or current["fingerprint"] != boundary.source_fingerprint
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_SOURCE_DRIFT")


def cleanup_staged_git_adapter(staged: StagedGitAdapter) -> None:
    """Clean or retain one registered pre-boundary adapter identity."""

    if staged.closed:
        return
    if staged.adapter_root_fd < 0:
        try:
            root_fd = os.open(
                staged.adapter_root,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_STAGED_ROOT_OPEN")
        opened = os.fstat(root_fd)
        if (opened.st_dev, opened.st_ino) != (
            staged.adapter_device,
            staged.adapter_inode,
        ):
            os.close(root_fd)
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_STAGED_ROOT_DRIFT")
        staged.adapter_root_fd = root_fd

    def mark_git_removed() -> None:
        staged.git_removed = True

    remove_git_adapter_root_exact(
        staged.adapter_root,
        staged.adapter_device,
        staged.adapter_inode,
        None if staged.git_removed else staged.git_device,
        None if staged.git_removed else staged.git_inode,
        git_already_removed=staged.git_removed,
        git_removed_callback=(
            None
            if staged.git_removed or staged.git_device is None
            else mark_git_removed
        ),
        pinned_root_fd=staged.adapter_root_fd,
        pinned_git_fd=(
            None
            if staged.git_removed or staged.adapter_git_fd < 0
            else staged.adapter_git_fd
        ),
    )
    try:
        if staged.adapter_git_fd >= 0:
            os.close(staged.adapter_git_fd)
        os.close(staged.adapter_root_fd)
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_STAGED_FD_CLOSE")
    staged.adapter_git_fd = -1
    staged.adapter_root_fd = -1
    staged.closed = True
    for index, candidate in enumerate(_OPEN_GIT_ADAPTERS):
        if candidate is staged:
            del _OPEN_GIT_ADAPTERS[index]
            break
    scope = staged.scope
    if scope is not None:
        for index, candidate in enumerate(scope.registrations):
            if candidate is staged:
                del scope.registrations[index]
                break


def cleanup_git_adapter_registration(registration: Any) -> None:
    """Dispatch cleanup for one staged or sealed adapter registration."""

    if isinstance(registration, GitReadBoundary):
        cleanup_git_metadata_adapter(registration)
        return
    if isinstance(registration, StagedGitAdapter):
        cleanup_staged_git_adapter(registration)
        return
    fail(Exit.INTERNAL, "GIT_ADAPTER_REGISTRATION_TYPE")


def cleanup_git_metadata_adapter(boundary: GitReadBoundary) -> None:
    if getattr(boundary, "closed", True):
        return
    adapter_root = boundary.adapter_root
    if (
        os.path.dirname(adapter_root) != "/private/tmp"
        or not os.path.basename(adapter_root).startswith("gov01-git-adapter-")
        or adapter_root == boundary.repo_root
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_CLEANUP_LOCATOR")
    def mark_git_removed() -> None:
        boundary.git_removed = True

    remove_git_adapter_root_exact(
        adapter_root,
        boundary.adapter_device,
        boundary.adapter_inode,
        None if boundary.git_removed else boundary.git_device,
        None if boundary.git_removed else boundary.git_inode,
        git_already_removed=boundary.git_removed,
        git_removed_callback=None if boundary.git_removed else mark_git_removed,
        pinned_root_fd=boundary.adapter_root_fd,
        pinned_git_fd=None if boundary.git_removed else boundary.adapter_git_fd,
    )
    try:
        os.close(boundary.adapter_git_fd)
        os.close(boundary.adapter_root_fd)
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CLEANUP_FD_CLOSE")
    boundary.adapter_git_fd = -1
    boundary.adapter_root_fd = -1
    boundary.closed = True
    for index, candidate in enumerate(_OPEN_GIT_ADAPTERS):
        if candidate is boundary:
            del _OPEN_GIT_ADAPTERS[index]
            break


def finalize_git_metadata_adapter(boundary: GitReadBoundary) -> None:
    try:
        verify_git_metadata_adapter(boundary)
        revalidate_git_metadata_source(boundary)
    finally:
        cleanup_git_metadata_adapter(boundary)


def require_git_adapter_quiescent(label: str) -> None:
    if _OPEN_GIT_ADAPTERS:
        fail(Exit.PREFLIGHT, label + "_GIT_ADAPTER_RESIDUE")


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
        "GIT_NO_LAZY_FETCH": "1",
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
    stdin_bytes: Optional[bytes] = None,
    environment: Optional[Mapping[str, str]] = None,
    inherited_directory_fd: Optional[int] = None,
) -> bytes:
    if not argv or not os.path.isabs(argv[0]):
        fail(Exit.INTERNAL, "PROCESS_ARGV")
    if stdin_bytes is not None and not isinstance(stdin_bytes, bytes):
        fail(Exit.INTERNAL, "PROCESS_STDIN")
    inherited_metadata: Optional[os.stat_result] = None
    if inherited_directory_fd is not None:
        try:
            inherited_metadata = os.fstat(inherited_directory_fd)
        except OSError:
            fail(Exit.INTERNAL, "PROCESS_INHERITED_FD")
        if not stat.S_ISDIR(inherited_metadata.st_mode) or inherited_metadata.st_uid != os.getuid():
            fail(Exit.INTERNAL, "PROCESS_INHERITED_FD")
        if sandbox_profile is None:
            fail(Exit.INTERNAL, "PROCESS_INHERITED_FD_SANDBOX")
    base_environment = child_env()
    process_environment = base_environment if environment is None else dict(environment)
    if any(
        not isinstance(key, str)
        or not key
        or "=" in key
        or "\x00" in key
        or not isinstance(value, str)
        or "\x00" in value
        for key, value in process_environment.items()
    ):
        fail(Exit.INTERNAL, "PROCESS_ENVIRONMENT")
    if environment is not None:
        if (
            set(process_environment) != set(base_environment) | {"GIT_OBJECT_DIRECTORY"}
            or any(process_environment.get(key) != value for key, value in base_environment.items())
            or not os.path.isabs(process_environment.get("GIT_OBJECT_DIRECTORY", ""))
            or os.path.normpath(process_environment["GIT_OBJECT_DIRECTORY"])
            != process_environment["GIT_OBJECT_DIRECTORY"]
        ):
            fail(Exit.INTERNAL, "PROCESS_ENVIRONMENT_SCOPE")
    sandbox_library: Any = None
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

    inherited_fds: Tuple[int, ...] = ()
    dedicated_child_fd: Optional[int] = None
    if inherited_directory_fd is not None:
        try:
            dedicated_child_fd = os.dup(inherited_directory_fd)
            duplicated_metadata = os.fstat(dedicated_child_fd)
        except OSError:
            if dedicated_child_fd is not None:
                os.close(dedicated_child_fd)
            fail(Exit.INTERNAL, "PROCESS_INHERITED_FD_DUP")
        if inherited_metadata is None or (
            duplicated_metadata.st_dev,
            duplicated_metadata.st_ino,
        ) != (
            inherited_metadata.st_dev,
            inherited_metadata.st_ino,
        ):
            os.close(dedicated_child_fd)
            fail(Exit.INTERNAL, "PROCESS_INHERITED_FD_DUP_RACE")
        inherited_fds = (dedicated_child_fd,)

    preexec_fn: Optional[Callable[[], None]] = None
    if sandbox_profile is not None:
        def initialize_child_sandbox() -> None:
            if dedicated_child_fd is not None:
                try:
                    os.fchdir(dedicated_child_fd)
                    os.close(dedicated_child_fd)
                except OSError:
                    os._exit(125)
            error_pointer = ctypes.c_char_p()
            if sandbox_library.sandbox_init(sandbox_profile, 0, ctypes.byref(error_pointer)) != 0:
                os._exit(126)

        preexec_fn = initialize_child_sandbox
    try:
        process_arguments: Dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "env": process_environment,
            "cwd": "/",
            "close_fds": True,
            "pass_fds": inherited_fds,
            "check": False,
            "timeout": 60,
            "preexec_fn": preexec_fn,
        }
        if stdin_bytes is None:
            process_arguments["stdin"] = subprocess.DEVNULL
        else:
            process_arguments["input"] = stdin_bytes
        try:
            completed = subprocess.run(list(argv), **process_arguments)
        finally:
            if dedicated_child_fd is not None:
                os.close(dedicated_child_fd)
    except (OSError, subprocess.SubprocessError):
        fail(Exit.PREFLIGHT, label + "_EXEC")
    if inherited_directory_fd is not None and completed.returncode == 125:
        fail(Exit.PREFLIGHT, label + "_ADAPTER_FCHDIR")
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


def git_adapter_namespace_write_deny_rules(
    adapter_git_directory: str,
    allowed_write_directory: Optional[str],
    label: str,
) -> str:
    """Deny child mutation of the temp parent and every sibling adapter."""

    adapter_root = os.path.dirname(adapter_git_directory)
    if (
        os.path.dirname(adapter_root) != "/private/tmp"
        or not os.path.basename(adapter_root).startswith("gov01-git-adapter-")
        or os.path.basename(adapter_git_directory) != "git"
    ):
        fail(Exit.INTERNAL, label + "_ADAPTER_NAMESPACE")
    filters = [
        sbpl_literal("/private/tmp", label),
        sbpl_literal("/tmp", label),
        sbpl_literal(adapter_root, label),
    ]
    if allowed_write_directory is None:
        filters.extend(
            (
                sbpl_subpath("/private/tmp", label),
                sbpl_subpath("/tmp", label),
            )
        )
    else:
        try:
            contained = os.path.commonpath(
                [adapter_git_directory, allowed_write_directory]
            ) == adapter_git_directory
        except ValueError:
            contained = False
        if (
            not contained
            or allowed_write_directory == adapter_git_directory
            or os.path.normpath(allowed_write_directory) != allowed_write_directory
        ):
            fail(Exit.INTERNAL, label + "_WRITE_SCOPE")
        allowed_literal = sbpl_literal(allowed_write_directory, label)
        allowed_subpath = sbpl_subpath(allowed_write_directory, label)
        filters.extend(
            (
                "(require-all "
                + sbpl_subpath("/private/tmp", label)
                + " (require-not "
                + allowed_literal
                + ") (require-not "
                + allowed_subpath
                + "))",
                sbpl_subpath("/tmp", label),
            )
        )
    return "(deny file-write*\n " + "\n ".join(filters) + "\n)\n"


def identity_bound_directory_path(directory_fd: int, label: str) -> str:
    """Return the current sandbox spelling for an already-open directory."""

    try:
        raw = fcntl.fcntl(directory_fd, fcntl.F_GETPATH, bytes(1024))
        path = raw.split(b"\x00", 1)[0].decode("utf-8", "strict")
        descriptor_metadata = os.fstat(directory_fd)
        path_metadata = os.stat(path, follow_symlinks=False)
    except (OSError, UnicodeDecodeError):
        fail(Exit.PREFLIGHT, label + "_PATH")
    if (
        not path
        or not os.path.isabs(path)
        or os.path.normpath(path) != path
        or not stat.S_ISDIR(descriptor_metadata.st_mode)
        or (path_metadata.st_dev, path_metadata.st_ino)
        != (descriptor_metadata.st_dev, descriptor_metadata.st_ino)
    ):
        fail(Exit.PREFLIGHT, label + "_IDENTITY")
    return path


def git_read_sandbox_profile(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    adapter_git_directory: str,
) -> bytes:
    if repo_root != boundary.repo_root:
        fail(Exit.INTERNAL, "GIT_SANDBOX_REPO_BINDING")
    if adapter_git_directory != boundary.git_dir:
        fail(Exit.PREFLIGHT, "GIT_SANDBOX_ADAPTER_IDENTITY")
    marker = os.path.join(repo_root, ".git")
    literals = [
        git_binary,
        repo_root,
        "/dev/null",
        marker,
        boundary.adapter_root,
        adapter_git_directory,
        os.path.join(adapter_git_directory, "HEAD"),
        os.path.join(adapter_git_directory, "index"),
        os.path.join(adapter_git_directory, "config"),
        os.path.join(adapter_git_directory, "packed-refs"),
        os.path.join(adapter_git_directory, "shallow"),
    ]
    subpaths = [
        boundary.developer_root,
        adapter_git_directory,
    ]
    prohibited = [
        marker,
        os.path.join(boundary.live_git_dir, "HEAD"),
        os.path.join(boundary.live_git_dir, "index"),
        os.path.join(boundary.live_git_dir, "commondir"),
        os.path.join(boundary.live_git_dir, "config.worktree"),
        os.path.join(boundary.live_git_dir, "gitdir"),
        os.path.join(boundary.live_common_dir, "HEAD"),
        os.path.join(boundary.live_common_dir, "config"),
        os.path.join(boundary.live_common_dir, "packed-refs"),
        os.path.join(boundary.live_common_dir, "info", "grafts"),
        os.path.join(boundary.live_common_dir, "objects", "info", "alternates"),
        os.path.join(boundary.live_common_dir, "objects", "info", "http-alternates"),
    ]
    allow_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in literals)
    allow_rules += "\n " + "\n ".join(sbpl_subpath(path, "GIT_SANDBOX") for path in subpaths)
    ancestor_rules_list: List[str] = []
    for path in literals + subpaths:
        sbpl_literal(path, "GIT_SANDBOX")
        ancestor_rules_list.append('(path-ancestors "' + path + '")')
    ancestor_rules = "\n ".join(ancestor_rules_list)
    deny_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in prohibited)
    namespace_write_denies = git_adapter_namespace_write_deny_rules(
        adapter_git_directory,
        None,
        "GIT_SANDBOX_NAMESPACE",
    )
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        + namespace_write_denies
        + '(deny network*)\n'
        + '(allow process-exec ' + sbpl_literal(git_binary, "GIT_SANDBOX") + ')\n'
        + '(allow process-fork)\n'
        + '(allow signal (target self))\n'
        + '(allow file-read* file-test-existence\n ' + allow_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + ancestor_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + deny_rules + '\n)\n'
        + '(deny file-read* file-test-existence\n ' + deny_rules + '\n)\n'
    )
    return profile.encode("ascii", "strict")


def git_bootstrap_sandbox_profile(
    git_binary: str,
    developer_root: str,
    capture: Mapping[str, Any],
    adapter_git_directory: str,
    dependencies: Mapping[str, Any],
) -> bytes:
    """Permit one Git child to read only exact content-bound object files."""

    live_git_dir = str(capture["git_dir"])
    live_common_dir = str(capture["common_dir"])
    live_objects = os.path.join(live_common_dir, "objects")
    if dependencies.get("objects_path") != live_objects:
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_DEPENDENCY_ROOT")
    loose_paths = tuple(dependencies.get("allowed_loose_paths", ()))
    pack_paths = tuple(dependencies.get("allowed_pack_paths", ()))
    pack_container = os.path.join(live_objects, "pack")
    loose_pattern = re.compile(
        re.escape(live_objects) + r"/[0-9a-f]{2}/(?:[0-9a-f]{38}|[0-9a-f]{62})\Z"
    )
    pack_pattern = re.compile(
        re.escape(pack_container) + r"/pack-(?:[0-9a-f]{40}|[0-9a-f]{64})\.(?:idx|pack)\Z"
    )
    if (
        not loose_paths
        or len(loose_paths) != len(set(loose_paths))
        or len(pack_paths) != len(set(pack_paths))
        or any(loose_pattern.fullmatch(path) is None for path in loose_paths)
        or any(pack_pattern.fullmatch(path) is None for path in pack_paths)
    ):
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_DEPENDENCY_SCOPE")
    literals = [
        git_binary,
        "/dev/null",
        adapter_git_directory,
        os.path.join(adapter_git_directory, "config"),
        os.path.join(adapter_git_directory, "HEAD"),
        pack_container,
        *loose_paths,
        *pack_paths,
    ]
    subpaths = [developer_root, adapter_git_directory]
    prohibited = [
        os.path.join(live_git_dir, "HEAD"),
        os.path.join(live_git_dir, "index"),
        os.path.join(live_git_dir, "commondir"),
        os.path.join(live_git_dir, "config.worktree"),
        os.path.join(live_git_dir, "gitdir"),
        os.path.join(live_common_dir, "HEAD"),
        os.path.join(live_common_dir, "config"),
        os.path.join(live_common_dir, "packed-refs"),
        os.path.join(live_common_dir, "refs"),
        os.path.join(live_common_dir, "hooks"),
        os.path.join(live_objects, "info"),
        os.path.join(live_objects, "pack", "multi-pack-index"),
        os.path.join(live_objects, "commit-graph"),
    ]
    external_object_controls = [
        os.path.join(live_common_dir, "info", "grafts"),
        os.path.join(live_objects, "info", "alternates"),
        os.path.join(live_objects, "info", "http-alternates"),
    ]
    allow_rules = "\n ".join(sbpl_literal(path, "GIT_BOOTSTRAP_SANDBOX") for path in literals)
    allow_rules += "\n " + "\n ".join(
        sbpl_subpath(path, "GIT_BOOTSTRAP_SANDBOX") for path in subpaths
    )
    ancestor_rules = "\n ".join(
        '(path-ancestors "' + path + '")'
        for path in literals + subpaths
        if sbpl_literal(path, "GIT_BOOTSTRAP_SANDBOX")
    )
    deny_rules = "\n ".join(
        sbpl_literal(path, "GIT_BOOTSTRAP_SANDBOX") for path in prohibited
    )
    external_control_rules = "\n ".join(
        sbpl_literal(path, "GIT_BOOTSTRAP_SANDBOX") for path in external_object_controls
    )
    object_root_metadata_rule = sbpl_literal(live_objects, "GIT_BOOTSTRAP_SANDBOX")
    namespace_write_denies = git_adapter_namespace_write_deny_rules(
        adapter_git_directory,
        None,
        "GIT_BOOTSTRAP_NAMESPACE",
    )
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        + namespace_write_denies
        + '(deny network*)\n'
        + '(allow process-exec ' + sbpl_literal(git_binary, "GIT_BOOTSTRAP_SANDBOX") + ')\n'
        + '(allow process-fork)\n'
        + '(allow signal (target self))\n'
        + '(allow file-read* file-test-existence\n ' + allow_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + ancestor_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + object_root_metadata_rule + '\n)\n'
        # Git probes these fixed names even when absent.  Existence-only access
        # preserves the normal ENOENT path; default-deny still forbids reading
        # any bytes if a racing writer creates one.
        + '(allow file-read-metadata file-test-existence\n ' + external_control_rules + '\n)\n'
        + '(deny file-read-data\n ' + external_control_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + deny_rules + '\n)\n'
        + '(deny file-read* file-test-existence\n ' + deny_rules + '\n)\n'
    )
    return profile.encode("ascii", "strict")


def git_adapter_import_sandbox_profile(
    git_binary: str,
    developer_root: str,
    adapter_git_directory: str,
) -> bytes:
    """Permit index-pack to mutate only the invocation-scoped adapter."""

    pack_directory = os.path.join(adapter_git_directory, "objects", "pack")
    literals = [git_binary, "/dev/null", adapter_git_directory]
    subpaths = [developer_root, adapter_git_directory]
    allow_rules = "\n ".join(sbpl_literal(path, "GIT_IMPORT_SANDBOX") for path in literals)
    allow_rules += "\n " + "\n ".join(sbpl_subpath(path, "GIT_IMPORT_SANDBOX") for path in subpaths)
    ancestor_rules = "\n ".join(
        '(path-ancestors "' + path + '")'
        for path in literals + subpaths
        if sbpl_literal(path, "GIT_IMPORT_SANDBOX")
    )
    namespace_write_denies = git_adapter_namespace_write_deny_rules(
        adapter_git_directory,
        pack_directory,
        "GIT_IMPORT_NAMESPACE",
    )
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        + namespace_write_denies
        + '(deny network*)\n'
        + '(allow process-exec ' + sbpl_literal(git_binary, "GIT_IMPORT_SANDBOX") + ')\n'
        + '(allow process-fork)\n'
        + '(allow signal (target self))\n'
        + '(allow file-read* file-test-existence\n ' + allow_rules + '\n)\n'
        + '(allow file-read-metadata file-test-existence\n ' + ancestor_rules + '\n)\n'
        + '(allow file-write*\n '
        + sbpl_literal(pack_directory, "GIT_IMPORT_SANDBOX")
        + '\n '
        + sbpl_subpath(pack_directory, "GIT_IMPORT_SANDBOX")
        + '\n)\n'
    )
    return profile.encode("ascii", "strict")


def hardened_git_prefix(git_binary: str, adapter_git_dir: str) -> List[str]:
    return [
        git_binary,
        "--no-optional-locks",
        "-c", "core.fsmonitor=false",
        "-c", "core.untrackedCache=false",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.bare=false",
        "-c", "core.excludesFile=/dev/null",
        "-c", "core.attributesFile=/dev/null",
        "-c", "core.commitGraph=false",
        "-c", "core.multiPackIndex=false",
        "-c", "pack.useBitmap=false",
        "-c", "pack.writeReverseIndex=false",
        "-c", "submodule.recurse=false",
        "-c", "protocol.allow=never",
        "--git-dir=" + adapter_git_dir,
        "--no-pager",
    ]


def bootstrap_git_object_read(
    git_binary: str,
    developer_root: str,
    capture: Mapping[str, Any],
    adapter_git_dir: str,
    operation: str,
    oid: Optional[str] = None,
    object_oids: Sequence[str] = (),
    adapter_git_fd: Optional[int] = None,
) -> bytes:
    """Read a known OID batch or repack one exact known OID set."""

    if adapter_git_dir != "." or adapter_git_fd is None:
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_ADAPTER_BINDING")
    head_oid, _head_ref = captured_head_oid_and_ref(capture)
    oid_bytes = len(head_oid)
    if operation == "objects":
        if oid is not None or not object_oids or len(object_oids) > MAX_GIT_REACHABLE_OBJECTS:
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_OPERATION")
        if any(len(value) != oid_bytes or GIT_OID_RE.fullmatch(value) is None for value in object_oids):
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_OBJECT_SET")
        arguments = ["cat-file", "--batch"]
        stdin_bytes = ("\n".join(sorted(object_oids)) + "\n").encode("ascii", "strict")
        max_bytes = MAX_GIT_BYTES
        label = "GIT_BOOTSTRAP_OBJECTS"
    elif operation == "pack":
        if oid is not None or not object_oids or len(object_oids) > MAX_GIT_REACHABLE_OBJECTS:
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_OPERATION")
        if any(len(value) != oid_bytes or GIT_OID_RE.fullmatch(value) is None for value in object_oids):
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_OBJECT_SET")
        arguments = [
            "pack-objects",
            "--stdout",
            "--no-use-bitmap-index",
            "--no-reuse-delta",
            "--no-reuse-object",
        ]
        stdin_bytes = ("\n".join(sorted(object_oids)) + "\n").encode("ascii", "strict")
        max_bytes = MAX_GIT_REACHABLE_PACK_BYTES
        label = "GIT_BOOTSTRAP_PACK"
    else:
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_OPERATION")
    environment = child_env()
    environment["GIT_OBJECT_DIRECTORY"] = os.path.join(str(capture["common_dir"]), "objects")
    dependency_oids = tuple(sorted(object_oids))
    dependencies_before = capture_git_object_dependencies(capture, dependency_oids)
    sandbox_adapter_git_directory = identity_bound_directory_path(
        adapter_git_fd,
        "GIT_BOOTSTRAP_ADAPTER",
    )
    result: Optional[bytes] = None
    process_error: Optional[BaseException] = None
    try:
        result = run_process(
            hardened_git_prefix(git_binary, adapter_git_dir) + arguments,
            label,
            max_bytes=max_bytes,
            sandbox_profile=git_bootstrap_sandbox_profile(
                git_binary,
                developer_root,
                capture,
                sandbox_adapter_git_directory,
                dependencies_before,
            ),
            stdin_bytes=stdin_bytes,
            environment=environment,
            inherited_directory_fd=adapter_git_fd,
        )
    except BaseException as error:
        process_error = error
    dependencies_after = capture_git_object_dependencies(capture, dependency_oids)
    if (
        dependencies_after["fingerprint"] != dependencies_before["fingerprint"]
        or dependencies_after["allowed_loose_paths"] != dependencies_before["allowed_loose_paths"]
        or dependencies_after["allowed_pack_paths"] != dependencies_before["allowed_pack_paths"]
    ):
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_OBJECT_SOURCE_DRIFT")
    if process_error is not None:
        raise process_error
    if result is None:
        fail(Exit.INTERNAL, "GIT_BOOTSTRAP_RESULT")
    return result


def validate_adapter_object_layout(adapter_git_dir: str, oid_bytes: int) -> None:
    objects = os.path.join(adapter_git_dir, "objects")
    try:
        object_entries = list(os.scandir(objects))
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECT_LAYOUT")
    if len(object_entries) != 1 or object_entries[0].name != "pack":
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECT_LAYOUT")
    pack_dir = os.path.join(objects, "pack")
    pack_dir_metadata = os.lstat(pack_dir)
    if (
        not stat.S_ISDIR(pack_dir_metadata.st_mode)
        or pack_dir_metadata.st_uid != os.getuid()
        or stat.S_IMODE(pack_dir_metadata.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_DIRECTORY")
    try:
        pack_entries = sorted(os.scandir(pack_dir), key=lambda entry: entry.name)
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_LAYOUT")
    stems: Dict[str, set[str]] = {}
    pattern = re.compile(r"\Apack-([0-9a-f]{" + str(oid_bytes) + r"})\.(idx|pack|rev)\Z")
    for entry in pack_entries:
        metadata = os.lstat(entry.path)
        matched = pattern.fullmatch(entry.name)
        if (
            matched is None
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) & 0o022
            or metadata.st_nlink != 1
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_LAYOUT")
        stems.setdefault(matched.group(1), set()).add(matched.group(2))
    if len(stems) != 1:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_COUNT")
    suffixes = next(iter(stems.values()))
    if not {"idx", "pack"}.issubset(suffixes) or not suffixes.issubset({"idx", "pack", "rev"}):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_COMPONENTS")


def validate_adapter_object_layout_at(adapter_git_fd: int, oid_bytes: int) -> None:
    """Validate the imported partial pack beneath the pinned Git directory."""

    objects_fd = open_adapter_directory_at(
        adapter_git_fd,
        "objects",
        False,
        "GIT_ADAPTER_OBJECTS",
    )
    try:
        try:
            object_names = os.listdir(objects_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECT_LAYOUT")
        if object_names != ["pack"]:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECT_LAYOUT")
        try:
            pack_fd = os.open(
                "pack",
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=objects_fd,
            )
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_DIRECTORY")
        try:
            pack_metadata = os.fstat(pack_fd)
            if (
                pack_metadata.st_uid != os.getuid()
                or stat.S_IMODE(pack_metadata.st_mode) & 0o022
            ):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_DIRECTORY")
            try:
                pack_names = sorted(os.listdir(pack_fd))
            except OSError:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_LAYOUT")
            stems: Dict[str, set[str]] = {}
            pattern = re.compile(r"\Apack-([0-9a-f]{" + str(oid_bytes) + r"})\.(idx|pack|rev)\Z")
            for name in pack_names:
                matched = pattern.fullmatch(name)
                file_fd: Optional[int] = None
                try:
                    file_fd = os.open(
                        name,
                        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=pack_fd,
                    )
                    metadata = os.fstat(file_fd)
                except OSError:
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_LAYOUT")
                finally:
                    if file_fd is not None:
                        os.close(file_fd)
                if (
                    matched is None
                    or not stat.S_ISREG(metadata.st_mode)
                    or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) & 0o022
                    or metadata.st_nlink != 1
                ):
                    fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_LAYOUT")
                stems.setdefault(matched.group(1), set()).add(matched.group(2))
            if len(stems) != 1:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_COUNT")
            suffixes = next(iter(stems.values()))
            if not {"idx", "pack"}.issubset(suffixes) or not suffixes.issubset(
                {"idx", "pack", "rev"}
            ):
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_COMPONENTS")
        finally:
            os.close(pack_fd)
    finally:
        os.close(objects_fd)


def discover_required_path_ancestors(
    git_binary: str,
    developer_root: str,
    capture: Mapping[str, Any],
    adapter_git_dir: str,
    adapter_git_fd: int,
    root_tree_oid: str,
    required_blob_paths: Sequence[str],
    required_absent_paths: Sequence[str],
) -> RequiredPathTrieResolution:
    """Resolve only required paths and their authenticated ancestor trees."""

    oid_bytes = len(root_tree_oid)

    def loader(oids: Sequence[str]) -> Mapping[str, bytes]:
        exact = tuple(sorted(set(oids)))
        if len(exact) != len(oids):
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_TREE_LOADER_DUPLICATE")
        return parse_bootstrap_object_batch(
            bootstrap_git_object_read(
                git_binary,
                developer_root,
                capture,
                adapter_git_dir,
                "objects",
                object_oids=exact,
                adapter_git_fd=adapter_git_fd,
            ),
            {oid: "tree" for oid in exact},
        )

    return resolve_required_path_trie(
        root_tree_oid,
        oid_bytes,
        required_blob_paths,
        required_absent_paths,
        loader,
    )


def materialize_reachable_git_objects(
    git_binary: str,
    developer_root: str,
    capture: Mapping[str, Any],
    adapter_git_dir: str,
    parent_depth: int,
    required_current_blob_paths: Sequence[str],
    required_parent_absent_paths: Sequence[str],
    adapter_git_fd: int,
) -> Dict[str, Any]:
    """Materialize commits, required-path ancestors, and exact public blobs."""

    if parent_depth not in (0, 1):
        fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_DEPTH")
    if parent_depth == 0 and required_parent_absent_paths:
        fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_SCOPE")
    if parent_depth == 1 and len(required_parent_absent_paths) != 1:
        fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_TRANSITION_SCOPE")
    head_oid, _head_ref = captured_head_oid_and_ref(capture)
    oid_bytes = len(head_oid)
    head_raw = parse_bootstrap_object_batch(
        bootstrap_git_object_read(
            git_binary,
            developer_root,
            capture,
            adapter_git_dir,
            "objects",
            object_oids=(head_oid,),
            adapter_git_fd=adapter_git_fd,
        ),
        {head_oid: "commit"},
    )[head_oid]
    head_tree, parents = parse_bootstrap_commit(head_raw, oid_bytes, parent_depth == 1)
    raw_index = capture.get("raw_files", {}).get("index")
    if not isinstance(raw_index, bytes):
        fail(Exit.INTERNAL, "GIT_INDEX_CAPTURE")
    index_tree_proof = prove_captured_index_root_tree(raw_index, oid_bytes, head_tree)
    current_resolution = discover_required_path_ancestors(
        git_binary,
        developer_root,
        capture,
        adapter_git_dir,
        adapter_git_fd,
        head_tree,
        required_current_blob_paths,
        (),
    )
    expected_types: Dict[str, str] = {}

    def authorize(oid: str, object_type: str) -> None:
        existing = expected_types.get(oid)
        if existing is not None and existing != object_type:
            fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_OBJECT_TYPE_COLLISION")
        expected_types[oid] = object_type

    authorize(head_oid, "commit")
    for _prefix, tree_oid in current_resolution.tree_contexts:
        authorize(tree_oid, "tree")
    for _path, mode, blob_oid in current_resolution.path_entries:
        if mode not in ("100644", "100755"):
            fail(Exit.INTERNAL, "GIT_BOOTSTRAP_CURRENT_PATH_EXPECTATION")
        authorize(blob_oid, "blob")
    parent_oid: Optional[str] = None
    parent_tree: Optional[str] = None
    parent_resolution: Optional[RequiredPathTrieResolution] = None
    transition_receipt: Optional[str] = None
    if parent_depth == 1:
        parent_oid = parents[0]
        parent_raw = parse_bootstrap_object_batch(
            bootstrap_git_object_read(
                git_binary,
                developer_root,
                capture,
                adapter_git_dir,
                "objects",
                object_oids=(parent_oid,),
                adapter_git_fd=adapter_git_fd,
            ),
            {parent_oid: "commit"},
        )[parent_oid]
        parent_tree, _grandparents = parse_bootstrap_commit(parent_raw, oid_bytes, False)
        authorize(parent_oid, "commit")
        parent_resolution = discover_required_path_ancestors(
            git_binary,
            developer_root,
            capture,
            adapter_git_dir,
            adapter_git_fd,
            parent_tree,
            (),
            required_parent_absent_paths,
        )
        for _prefix, tree_oid in parent_resolution.tree_contexts:
            authorize(tree_oid, "tree")
        transition_receipt = verify_path_local_one_file_addition(
            current_resolution,
            parent_resolution,
            required_parent_absent_paths[0],
        )
    required_blob_oids = tuple(
        sorted(oid for oid, object_type in expected_types.items() if object_type == "blob")
    )
    if required_blob_oids:
        # Verify the exact terminal objects are really blobs and independently
        # recompute every content OID before their names can reach pack-objects.
        parse_bootstrap_object_batch(
            bootstrap_git_object_read(
                git_binary,
                developer_root,
                capture,
                adapter_git_dir,
                "objects",
                object_oids=required_blob_oids,
                adapter_git_fd=adapter_git_fd,
            ),
            {oid: "blob" for oid in required_blob_oids},
        )
    exact_oids = tuple(sorted(expected_types))
    if not exact_oids or len(exact_oids) > MAX_GIT_REACHABLE_OBJECTS:
        fail(Exit.PREFLIGHT, "GIT_BOOTSTRAP_OBJECT_LIMIT")
    pack = bootstrap_git_object_read(
        git_binary,
        developer_root,
        capture,
        adapter_git_dir,
        "pack",
        object_oids=exact_oids,
        adapter_git_fd=adapter_git_fd,
    )
    validate_generated_pack_envelope(pack, len(exact_oids), oid_bytes)
    try:
        os.mkdir("objects", 0o700, dir_fd=adapter_git_fd)
    except OSError:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECTS_CREATE")
    objects_fd = open_adapter_directory_at(
        adapter_git_fd,
        "objects",
        False,
        "GIT_ADAPTER_OBJECTS",
    )
    try:
        try:
            os.mkdir("pack", 0o700, dir_fd=objects_fd)
        except OSError:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_PACK_CREATE")
    finally:
        os.close(objects_fd)
    sandbox_adapter_git_directory = identity_bound_directory_path(
        adapter_git_fd,
        "GIT_IMPORT_ADAPTER",
    )
    imported = run_process(
        hardened_git_prefix(git_binary, adapter_git_dir) + ["index-pack", "--stdin"],
        "GIT_ADAPTER_INDEX_PACK",
        max_bytes=4096,
        sandbox_profile=git_adapter_import_sandbox_profile(
            git_binary,
            developer_root,
            sandbox_adapter_git_directory,
        ),
        stdin_bytes=pack,
        inherited_directory_fd=adapter_git_fd,
    )
    if imported.count(b"\n") != 1 or not imported.startswith(b"pack\t"):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_INDEX_PACK_FORMAT")
    validate_adapter_object_layout_at(adapter_git_fd, oid_bytes)
    return {
        "expected_object_types": expected_types,
        "head_tree": head_tree,
        "parent_oid": parent_oid,
        "parent_tree": parent_tree,
        "current_path_resolution": current_resolution,
        "parent_path_resolution": parent_resolution,
        "index_tree_proof": index_tree_proof,
        "one_file_transition_receipt": transition_receipt,
    }


GENERATION_GIT_READ_LABELS = frozenset(
    (
        "GIT_ADAPTER_OBJECT_ENUMERATION",
        "GIT_ADAPTER_OBJECT_HASHES",
        "GIT_ADAPTER_HEAD",
        "GIT_ADAPTER_HEAD_TREE",
        "GIT_HEAD",
        "GIT_TREE",
        "GIT_HEAD_REF",
        "GIT_FOR_EACH_REF",
        "GIT_ARTIFACT_TREE",
        "GIT_ARTIFACT_BLOB",
        "GIT_MICRO_CURRENT_BYTES",
    )
)


def generation_git_child_prefix(git_binary: str, repo_root: str) -> List[str]:
    return [
        git_binary,
        "--no-optional-locks",
        "-c", "core.fsmonitor=false",
        "-c", "core.untrackedCache=false",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.bare=false",
        "-c", "core.excludesFile=/dev/null",
        "-c", "core.attributesFile=/dev/null",
        "-c", "submodule.recurse=false",
        "-c", "protocol.allow=never",
        "-c", "core.commitGraph=false",
        "-c", "core.multiPackIndex=false",
        "-c", "pack.useBitmap=false",
        "-c", "pack.writeReverseIndex=false",
        "--git-dir=.",
        "--work-tree=" + repo_root,
        "--no-pager",
    ]


def generation_git_child_argv(
    git_binary: str,
    repo_root: str,
    arguments: Sequence[str],
) -> List[str]:
    return generation_git_child_prefix(git_binary, repo_root) + list(arguments)


def require_generation_git_tail(label: str, arguments: Sequence[str]) -> Tuple[str, ...]:
    """Allow exactly one production Git tail for each semantic label."""

    tail = tuple(arguments)
    if label not in GENERATION_GIT_READ_LABELS:
        fail(Exit.PREFLIGHT, "GIT_READ_LABEL")
    fixed: Dict[str, Tuple[str, ...]] = {
        "GIT_ADAPTER_OBJECT_ENUMERATION": (
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname)",
        ),
        "GIT_ADAPTER_OBJECT_HASHES": ("cat-file", "--batch"),
        "GIT_ADAPTER_HEAD": ("rev-parse", "--verify", "HEAD"),
        "GIT_ADAPTER_HEAD_TREE": ("rev-parse", "--verify", "HEAD^{tree}"),
        "GIT_HEAD": ("rev-parse", "--verify", "HEAD"),
        "GIT_TREE": ("rev-parse", "--verify", "HEAD^{tree}"),
        "GIT_HEAD_REF": ("symbolic-ref", "-q", "HEAD"),
        "GIT_FOR_EACH_REF": (
            "for-each-ref",
            "--sort=refname",
            "--format=%(objectname) %(refname)",
            "refs",
        ),
    }
    expected = fixed.get(label)
    artifact_paths = {path for _role, path in ARTIFACT_SPECS}
    if label == "GIT_ARTIFACT_TREE" and len(tail) == 6:
        expected = (
            tail
            if tail[:5] == ("ls-tree", "-z", "--full-tree", "HEAD", "--")
            and tail[5] in artifact_paths
            else None
        )
    elif label == "GIT_ARTIFACT_BLOB" and len(tail) == 2:
        expected = (
            tail
            if tail[0] == "show"
            and tail[1].startswith("HEAD:")
            and tail[1][5:] in artifact_paths
            else None
        )
    elif label == "GIT_MICRO_CURRENT_BYTES" and len(tail) == 2 and tail[0] == "show":
        relative = tail[1][5:] if tail[1].startswith("HEAD:") else ""
        prefix = CONTROL_PREFIX + MICRO_BASENAME_PREFIX
        challenge = relative[len(prefix) : -5] if relative.startswith(prefix) and relative.endswith(".json") else ""
        expected = tail if GENERATION_CHALLENGE_RE.fullmatch(challenge) is not None else None
    if expected is None or tail != expected:
        fail(Exit.PREFLIGHT, "GIT_READ_ARGV_TAIL")
    return tail


def require_generation_git_child_argv(
    argv: Sequence[str],
    git_binary: str,
    repo_root: str,
    arguments: Sequence[str],
    label: str,
    boundary: GitReadBoundary,
    allowed_returncodes: Sequence[int],
    stdin_bytes: Optional[bytes],
) -> None:
    tail = require_generation_git_tail(label, arguments)
    expected = generation_git_child_prefix(git_binary, repo_root) + list(tail)
    if list(argv) != expected:
        fail(Exit.PREFLIGHT, "GIT_READ_ARGV_PREFIX")
    if tuple(allowed_returncodes) != (0,):
        fail(Exit.PREFLIGHT, "GIT_READ_RETURNCODES")
    if label == "GIT_ADAPTER_OBJECT_HASHES":
        expected_stdin = ("\n".join(boundary.expected_object_oids) + "\n").encode(
            "ascii", "strict"
        )
        if stdin_bytes != expected_stdin:
            fail(Exit.PREFLIGHT, "GIT_READ_STDIN")
    elif stdin_bytes is not None:
        fail(Exit.PREFLIGHT, "GIT_READ_STDIN")


def run_git(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    arguments: Sequence[str],
    label: str,
    max_bytes: int = MAX_GIT_BYTES,
    allowed_returncodes: Sequence[int] = (0,),
    stdin_bytes: Optional[bytes] = None,
) -> bytes:
    verify_git_metadata_adapter(boundary)
    adapter_git_directory = identity_bound_directory_path(
        boundary.adapter_git_fd,
        "GIT_EVIDENCE_ADAPTER",
    )
    argv = generation_git_child_argv(git_binary, repo_root, arguments)
    require_generation_git_child_argv(
        argv,
        git_binary,
        repo_root,
        arguments,
        label,
        boundary,
        allowed_returncodes,
        stdin_bytes,
    )
    result = run_process(
        argv,
        label,
        max_bytes=max_bytes,
        allowed_returncodes=allowed_returncodes,
        sandbox_profile=git_read_sandbox_profile(
            git_binary,
            repo_root,
            boundary,
            adapter_git_directory,
        ),
        stdin_bytes=stdin_bytes,
        inherited_directory_fd=boundary.adapter_git_fd,
    )
    verify_git_metadata_adapter(boundary)
    return result


def verify_materialized_git_objects(
    git_binary: str,
    repo_root: str,
    boundary: GitReadBoundary,
    head_oid: str,
    head_tree: str,
    parent_oid: Optional[str],
    parent_tree: Optional[str],
) -> None:
    """Prove the sealed adapter has exactly the approved partial object set."""

    oid_bytes = len(head_oid)
    stored = parse_object_oid_lines(
        run_git(
            git_binary,
            repo_root,
            boundary,
            ["cat-file", "--batch-all-objects", "--batch-check=%(objectname)"],
            "GIT_ADAPTER_OBJECT_ENUMERATION",
            max_bytes=MAX_GIT_BYTES,
        ),
        oid_bytes,
        "GIT_ADAPTER_OBJECT_ENUMERATION",
    )
    if tuple(sorted(stored)) != tuple(boundary.expected_object_oids):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_OBJECT_SCOPE")
    ordered_oids = tuple(boundary.expected_object_oids)
    batch_input = ("\n".join(ordered_oids) + "\n").encode("ascii", "strict")
    expected_types = dict(boundary.expected_object_types)
    sealed_objects = parse_bootstrap_object_batch(
        run_git(
            git_binary,
            repo_root,
            boundary,
            ["cat-file", "--batch"],
            "GIT_ADAPTER_OBJECT_HASHES",
            max_bytes=MAX_GIT_REACHABLE_PACK_BYTES,
            stdin_bytes=batch_input,
        ),
        expected_types,
    )
    sealed_head_tree, sealed_parents = parse_bootstrap_commit(
        sealed_objects[head_oid], oid_bytes, parent_oid is not None
    )
    if sealed_head_tree != head_tree:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_HEAD_TREE_IDENTITY")
    if parent_oid is None:
        if boundary.parent_path_resolution is not None or boundary.parent_required_absent_paths:
            fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_BINDING")
    elif tuple(sealed_parents) != (parent_oid,):
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_PARENT_IDENTITY")
    if git_scalar(
        git_binary, repo_root, boundary, ["rev-parse", "--verify", "HEAD"], "GIT_ADAPTER_HEAD"
    ) != head_oid:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_HEAD_IDENTITY")
    if git_scalar(
        git_binary,
        repo_root,
        boundary,
        ["rev-parse", "--verify", "HEAD^{tree}"],
        "GIT_ADAPTER_HEAD_TREE",
    ) != head_tree:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_HEAD_TREE_IDENTITY")

    def sealed_tree_loader(oids: Sequence[str]) -> Mapping[str, bytes]:
        result: Dict[str, bytes] = {}
        for oid in oids:
            if expected_types.get(oid) != "tree" or oid not in sealed_objects:
                fail(Exit.PREFLIGHT, "GIT_ADAPTER_REQUIRED_TREE_SCOPE")
            result[oid] = sealed_objects[oid]
        return result

    sealed_current = resolve_required_path_trie(
        head_tree,
        oid_bytes,
        boundary.current_required_blob_paths,
        (),
        sealed_tree_loader,
    )
    if sealed_current != boundary.current_path_resolution:
        fail(Exit.PREFLIGHT, "GIT_ADAPTER_CURRENT_PATH_MANIFEST")
    if (parent_oid is None) != (parent_tree is None):
        fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_BINDING")
    if parent_oid is not None and parent_tree is not None:
        sealed_parent_tree, _grandparents = parse_bootstrap_commit(
            sealed_objects[parent_oid], oid_bytes, False
        )
        if sealed_parent_tree != parent_tree:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_PARENT_TREE_IDENTITY")
        sealed_parent = resolve_required_path_trie(
            parent_tree,
            oid_bytes,
            (),
            boundary.parent_required_absent_paths,
            sealed_tree_loader,
        )
        if sealed_parent != boundary.parent_path_resolution:
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_PARENT_PATH_MANIFEST")
        if len(boundary.parent_required_absent_paths) != 1:
            fail(Exit.INTERNAL, "GIT_ADAPTER_PARENT_TRANSITION_SCOPE")
        receipt = verify_path_local_one_file_addition(
            sealed_current,
            sealed_parent,
            boundary.parent_required_absent_paths[0],
        )
        if not isinstance(boundary.one_file_transition_receipt, str) or not hmac.compare_digest(
            receipt, boundary.one_file_transition_receipt
        ):
            fail(Exit.PREFLIGHT, "GIT_ADAPTER_TRANSITION_RECEIPT")


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
    raw = run_git(
        git_binary,
        repo_root,
        boundary,
        [
            "for-each-ref",
            "--sort=refname",
            "--format=%(objectname) %(refname)",
            "refs",
        ],
        "GIT_FOR_EACH_REF",
    )
    if raw and not raw.endswith(b"\n"):
        fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_FORMAT")
    observed: List[Tuple[str, str]] = []
    canonical_rows: List[bytes] = []
    seen = set()
    for row in raw.splitlines(keepends=True):
        if not row.endswith(b"\n") or row.count(b" ") != 1:
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_FORMAT")
        oid, reference = row[:-1].split(b" ", 1)
        try:
            reference_text = reference.decode("ascii", "strict")
            oid_text = oid.decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_ENCODING")
        validate_captured_refname(reference_text, "GIT_FOR_EACH_REF_REFNAME")
        if (
            len(oid_text) != len(boundary.head_oid)
            or GIT_OID_RE.fullmatch(oid_text) is None
            or set(oid_text) == {"0"}
        ):
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_OID")
        if reference_text in seen:
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_DUPLICATE")
        if observed and reference_text <= observed[-1][1]:
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_ORDER")
        seen.add(reference_text)
        observed.append((oid_text, reference_text))
        if len(observed) > MAX_CAPTURED_REF_ENTRIES:
            fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_LIMIT")
        if reference_text != head_ref:
            canonical_rows.append(
                (oid_text + " " + reference_text + "\n").encode("ascii", "strict")
            )
    if tuple(observed) != boundary.expected_refs:
        fail(Exit.PREFLIGHT, "GIT_FOR_EACH_REF_IDENTITY")
    body = b"".join(canonical_rows)
    return sha256(body), len(body)


def repository_baseline(
    repo_root: str,
    parent_depth: int = 0,
    additional_current_blob_paths: Sequence[str] = (),
) -> Dict[str, Any]:
    git_binary, developer_root = resolve_git()
    artifact_paths = tuple(path for _role, path in ARTIFACT_SPECS)
    current_blob_paths = artifact_paths + tuple(additional_current_blob_paths)
    if len(current_blob_paths) != len(set(current_blob_paths)):
        fail(Exit.INTERNAL, "GIT_ADAPTER_BLOB_SCOPE_DUPLICATE")
    git_control, boundary = create_git_metadata_adapter(
        repo_root,
        git_binary,
        developer_root,
        parent_depth=parent_depth,
        required_current_blob_paths=current_blob_paths,
        required_parent_absent_paths=(
            tuple(additional_current_blob_paths) if parent_depth == 1 else ()
        ),
    )
    try:
        head = git_scalar(git_binary, repo_root, boundary, ["rev-parse", "--verify", "HEAD"], "GIT_HEAD")
        tree = git_scalar(git_binary, repo_root, boundary, ["rev-parse", "--verify", "HEAD^{tree}"], "GIT_TREE")
        head_ref = git_scalar(git_binary, repo_root, boundary, ["symbolic-ref", "-q", "HEAD"], "GIT_HEAD_REF")
        if GIT_OID_RE.fullmatch(head) is None or GIT_OID_RE.fullmatch(tree) is None:
            fail(Exit.PREFLIGHT, "GIT_OID")
        validate_head_ref(head_ref)
        if boundary.index_tree_proof.root_tree_oid != tree:
            fail(Exit.PREFLIGHT, "GIT_INDEX_HEAD")
        refs_sha256, refs_bytes = other_refs_observation(git_binary, repo_root, boundary, head_ref)
        revalidate_git_metadata_source(boundary)
    except BaseException:
        cleanup_git_metadata_adapter(boundary)
        raise
    return {
        "git_binary": git_binary,
        "git_boundary": boundary,
        "head": head,
        "tree": tree,
        "parent_head": boundary.parent_oid,
        "parent_tree": boundary.parent_tree,
        "one_file_transition_receipt": boundary.one_file_transition_receipt,
        "index_tree_sha256": boundary.index_tree_proof.raw_sha256,
        "index_tree_entry_count": boundary.index_tree_proof.entry_count,
        "index_tree_version": boundary.index_tree_proof.version,
        "index_opaque_gitlink_count": boundary.index_tree_proof.opaque_gitlink_count,
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
            "issue_publication_checkpoint_profile": ISSUE_PUBLICATION_CHECKPOINT_PROFILE_V1,
            "approved_commit_shape": "current HEAD has exactly one parent equal to authorization_baseline_head; a path-local Merkle comparison of authenticated current and parent ancestor tree objects proves exactly the micro envelope regular file was added with bytes equal to the approved raw envelope and every non-target entry is byte-identical; no other path is added modified deleted renamed or type-changed",
            "captured_index_root_profile": GENERATION_CAPTURED_INDEX_ROOT_PROFILE_V1,
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
                "git-metadata-adapter-bootstrap",
                "git-read-only-evidence",
                "pgrep-read-only-evidence",
                "lsof-read-only-evidence",
            ],
            "shell_allowed": False,
            "network_allowed": False,
            "node_npm_npx_openspec_allowed": False,
            "environment_profile": GENERATION_GIT_CHILD_ENVIRONMENT_PROFILE_V2,
            "git_child_sandbox_profile": GENERATION_GIT_CHILD_SANDBOX_PROFILE_V1,
        },
        "mutation_scope": {
            "first_authority_consuming_persistent_write": "exclusive mkdirat of exact claims/generation-claim-<approved-GOV01-GEN-challenge> mode 0700 after every private read schema manual privacy and drift check has passed; EEXIST permanently forbids minting another acquisition challenge",
            "allowed_ephemeral_mutations": [
                "create one fresh unique checkpoint-scoped private-temporary 0700 Git metadata adapter for each production Git evidence checkpoint after the applicable public issue invocation or exact GEN receipt has authorized Git inspection; permit at most one active adapter owner within a process",
                GENERATION_GIT_ADAPTER_WRITE_PROFILE_V2,
                "within the declared trust boundary and host assurance, remove the unique registered adapter at its authorized pathname only after captured root and Git identity checks, then require authorized-path absence and zero registry residue before success or retryable pre-claim failure",
            ],
            "temporary_git_metadata_adapter_profile": GENERATION_GIT_ADAPTER_PROFILE_V5,
            "git_metadata_adapter_trust_boundary": GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1,
            "git_metadata_adapter_host_assurance": GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1,
            "git_metadata_adapter_cleanup_guarantee": GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1,
            "temporary_adapter_cleanup_required": True,
            "temporary_adapter_residue_allowed": False,
            "allowed_persistent_mutations": [
                "create and fsync exactly one previously-absent 0700 generation claim directory beneath the existing receipt-bound claims container",
                "create and fsync exactly one 0600 canonical HMAC-authenticated generation-record.json beneath that claim and fsync both claim and claims directories",
                "create and fsync exactly one previously-absent public acquisition envelope regular file beneath the repository control prefix",
                "fsync its already-existing parent directory",
            ],
            "output_mode": "0644",
            "overwrite_allowed": False,
            "product_state_cleanup_allowed": False,
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
            "pre_output_failure": "before the generation claim mkdir, no persistent repository control product claim or output write; the exact approved preflight may use only checkpoint-scoped private-temporary Git metadata adapters and may rerun before expiry only after exact cleanup with zero residue while every bound input is unchanged and both claim and output remain absent",
            "temporary_adapter_failure": "adapter cleanup failure root-identity uncertainty or any residue is terminal fail-closed for this attempt: do not publish, do not report retryable, retain evidence for private inspection, and require new authority before another attempt",
            "post_create_failure": "after the generation claim mkdir, retain claim record and any output bytes and stop; never truncate delete overwrite repair or mint another acquisition challenge from this generation authority",
            "existing_complete_output": "under the same still-valid exact GEN receipt, authenticate the retained generation claim, reuse only its fixed acquisition challenge and timestamps, revalidate every public and private commitment including hmac.key-derived commitments, require rebuilt raw bytes exact, then re-emit the same raw receipt digest without writing anything",
            "existing_partial_or_invalid_output": "a partial or invalid generation claim is terminal consumed; a valid claim with absent output may recreate only its exact fixed raw output; any partial invalid or drifted existing output is retained and requires a new generation micro-envelope",
            "retry_policy": "single-use begins at successful exclusive generation claim mkdir; only a pre-claim failure with confirmed temporary-adapter cleanup and zero residue may rerun within the exact receipt TTL; every post-claim path is pinned to the claim-authenticated acquisition challenge timestamps and final raw digest",
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
            "git_metadata_adapter_trust_boundary": GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1,
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
            "issue_publication_checkpoint_profile",
            "approved_commit_shape", "captured_index_root_profile", "index_must_equal_head",
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
    if transition.get("issue_publication_checkpoint_profile") != ISSUE_PUBLICATION_CHECKPOINT_PROFILE_V1:
        fail(Exit.CONTRACT, "ISSUE_PUBLICATION_CHECKPOINT_PROFILE")
    if transition.get("captured_index_root_profile") != GENERATION_CAPTURED_INDEX_ROOT_PROFILE_V1:
        fail(Exit.CONTRACT, "CAPTURED_INDEX_ROOT_PROFILE")
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
    expected_git_control_profile = {
        "marker_kind": transition.get("git_control_profile", {}).get("marker_kind")
        if isinstance(transition.get("git_control_profile"), dict)
        else None,
        "common_directory_relation": transition.get("git_control_profile", {}).get("common_directory_relation")
        if isinstance(transition.get("git_control_profile"), dict)
        else None,
        "include_controls_absent": True,
        "alternate_object_controls_absent": True,
    }
    if (
        not isinstance(transition.get("git_control_profile"), dict)
        or canonical_json(transition["git_control_profile"])
        != canonical_json(expected_git_control_profile)
    ):
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
    if (
        mutation.get("git_metadata_adapter_trust_boundary")
        != GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
        or mutation.get("git_metadata_adapter_host_assurance")
        != GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
        or mutation.get("git_metadata_adapter_cleanup_guarantee")
        != GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
    ):
        fail(Exit.CONTRACT, "GIT_ADAPTER_HOST_CONTRACT")
    expected_mutation = _build_issue_envelope_unchecked(
        challenge,
        issued,
        {
            "head": predecessor["static_contract_commit_oid"],
            "tree": predecessor["static_contract_tree_oid"],
            "head_ref_sha256": transition["authorization_baseline_head_ref_sha256"],
            "head_ref_bytes": transition["authorization_baseline_head_ref_bytes"],
            "other_refs_sha256": transition["authorization_baseline_other_refs_sha256"],
            "other_refs_bytes": transition["authorization_baseline_other_refs_bytes"],
            "git_control_profile": expected_git_control_profile,
        },
        artifacts,
    )["mutation_scope"]
    if mutation != expected_mutation:
        fail(Exit.CONTRACT, "MUTATION_AUTHORITY")
    privacy = top["privacy"]
    if privacy.get("git_metadata_adapter_trust_boundary") != GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1:
        fail(Exit.PRIVACY, "PRIVACY_GIT_ADAPTER_TRUST_BOUNDARY")
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
            "git_control_profile": expected_git_control_profile,
        },
        artifacts,
    )
    # Python considers ``True == 1`` and ``False == 0``.  The public JSON
    # contract does not: booleans and integers are distinct JSON types.  The
    # deterministic reconstruction is the final whole-envelope authority, so
    # compare its canonical JSON bytes rather than Python values.
    if canonical_json(envelope) != canonical_json(expected):
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


def write_exclusive_public_file(
    repo_root: str,
    relative: str,
    raw: bytes,
    *,
    before_create: Optional[Callable[[], None]] = None,
    after_create: Optional[Callable[[], None]] = None,
    companion_absent_relative: Optional[str] = None,
) -> None:
    """Create one public file with optional source and companion-path CAS."""

    parent_fd, name = open_output_parent(repo_root, relative)
    companion_name: Optional[str] = None
    if companion_absent_relative is not None:
        try:
            companion_fd, companion_name = open_output_parent(repo_root, companion_absent_relative)
            try:
                parent_meta = os.fstat(parent_fd)
                companion_parent_meta = os.fstat(companion_fd)
                if (parent_meta.st_dev, parent_meta.st_ino) != (
                    companion_parent_meta.st_dev,
                    companion_parent_meta.st_ino,
                ):
                    fail(Exit.PREFLIGHT, "OUTPUT_COMPANION_PARENT")
            finally:
                os.close(companion_fd)
        except BaseException:
            os.close(parent_fd)
            raise
    fd: Optional[int] = None
    reopened_fd: Optional[int] = None
    locked = False
    try:
        try:
            fcntl.flock(parent_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError:
            fail(Exit.PREFLIGHT, "OUTPUT_PARENT_LOCK")
        if before_create is not None:
            before_create()
        if companion_name is not None:
            assert_absent(parent_fd, companion_name, "GENERATION_OUTPUT")
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
        try:
            reopened_fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except OSError:
            fail(Exit.WRITE, "OUTPUT_REOPEN")
        reopened_meta = os.fstat(reopened_fd)
        if (
            (reopened_meta.st_dev, reopened_meta.st_ino) != (final.st_dev, final.st_ino)
            or reopened_meta.st_size != len(raw)
            or not stat.S_ISREG(reopened_meta.st_mode)
            or reopened_meta.st_nlink != 1
        ):
            fail(Exit.WRITE, "OUTPUT_REOPEN_IDENTITY")
        pieces: List[bytes] = []
        remaining = len(raw)
        while remaining:
            try:
                chunk = os.read(reopened_fd, min(1024 * 1024, remaining))
            except OSError:
                fail(Exit.WRITE, "OUTPUT_REOPEN_READ")
            if not chunk:
                fail(Exit.WRITE, "OUTPUT_REOPEN_SHORT")
            pieces.append(chunk)
            remaining -= len(chunk)
        try:
            growth = os.read(reopened_fd, 1)
        except OSError:
            fail(Exit.WRITE, "OUTPUT_REOPEN_READ")
        if growth or b"".join(pieces) != raw:
            fail(Exit.WRITE, "OUTPUT_REOPEN_MISMATCH")
        if companion_name is not None:
            assert_absent(parent_fd, companion_name, "GENERATION_OUTPUT_POST_CREATE")
        if after_create is not None:
            after_create()
        if companion_name is not None:
            assert_absent(parent_fd, companion_name, "GENERATION_OUTPUT_POST_CHECKPOINT")
    finally:
        if reopened_fd is not None:
            try:
                os.close(reopened_fd)
            except OSError:
                pass
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if locked:
            try:
                fcntl.flock(parent_fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(parent_fd)


def capture_issue_public_checkpoint(repo_root: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    """Capture and close one exact public source/artifact checkpoint."""

    baseline = repository_baseline(repo_root)
    artifacts = artifact_observations(repo_root)
    try:
        assert_artifacts_match_head(
            baseline["git_binary"], repo_root, baseline["git_boundary"], artifacts
        )
        finalize_git_metadata_adapter(baseline["git_boundary"])
    except BaseException:
        cleanup_git_metadata_adapter(baseline["git_boundary"])
        raise
    boundary = baseline["git_boundary"]
    identity = {
        "head": baseline["head"],
        "tree": baseline["tree"],
        "head_ref_sha256": baseline["head_ref_sha256"],
        "head_ref_bytes": baseline["head_ref_bytes"],
        "other_refs_sha256": baseline["other_refs_sha256"],
        "other_refs_bytes": baseline["other_refs_bytes"],
        "git_control_profile": baseline["git_control_profile"],
        "git_source_fingerprint": boundary.source_fingerprint,
        "index_tree_sha256": baseline["index_tree_sha256"],
        "index_tree_entry_count": baseline["index_tree_entry_count"],
        "index_tree_version": baseline["index_tree_version"],
        "index_opaque_gitlink_count": baseline["index_opaque_gitlink_count"],
        "captured_index_root_profile": GENERATION_CAPTURED_INDEX_ROOT_PROFILE_V1,
        "expected_object_types": [list(item) for item in boundary.expected_object_types],
        "artifacts": artifacts,
    }
    return baseline, artifacts, sha256(canonical_json(identity))


def issue() -> Dict[str, Any]:
    require_python_isolation()
    repo_root, _repo_meta = derive_repo_root()
    baseline, artifacts, initial_checkpoint = capture_issue_public_checkpoint(repo_root)
    issued_at = utc_now_second()
    entropy = os.urandom(32)
    if len(entropy) != 32:
        fail(Exit.RUNTIME, "GENERATION_ENTROPY")
    challenge = "GOV01-GEN-" + issued_at.strftime("%Y%m%d") + "-" + entropy.hex()
    relative = micro_relative(challenge)
    final_output_relative = final_relative(challenge)
    envelope = build_issue_envelope(challenge, issued_at, baseline, artifacts)
    raw = canonical_json(envelope)
    parsed = parse_json(raw, "MICRO_ENVELOPE")
    if parsed != envelope:
        fail(Exit.INTERNAL, "MICRO_ENVELOPE_ROUNDTRIP")
    validate_generation_envelope(parsed, issued_at, require_pending=True)
    def revalidate_issue_checkpoint(label: str) -> None:
        _current_baseline, _current_artifacts, current_checkpoint = capture_issue_public_checkpoint(
            repo_root
        )
        if not hmac.compare_digest(current_checkpoint, initial_checkpoint):
            fail(Exit.PREFLIGHT, label + "_INPUT_DRIFT")
        validate_generation_envelope(parsed, utc_now_second(), require_pending=True)

    write_exclusive_public_file(
        repo_root,
        relative,
        raw,
        before_create=lambda: revalidate_issue_checkpoint("ISSUE_PRE_CREATE"),
        after_create=lambda: revalidate_issue_checkpoint("ISSUE_POST_CREATE"),
        companion_absent_relative=final_output_relative,
    )
    validate_generation_envelope(parsed, utc_now_second(), require_pending=True)
    require_git_adapter_quiescent("ISSUE")
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


def _load_approved_generation_request_impl(
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
    current = repository_baseline(
        repo_root,
        parent_depth=1,
        additional_current_blob_paths=(relative,),
    )
    transition = envelope["repository_transition"]
    if (
        current.get("parent_head") != transition.get("authorization_baseline_head")
        or not isinstance(current.get("parent_head"), str)
        or GIT_OID_RE.fullmatch(str(current.get("parent_head"))) is None
    ):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_IDENTITY")
    if current.get("parent_tree") != transition.get("authorization_baseline_tree"):
        fail(Exit.PREFLIGHT, "GIT_MICRO_PARENT_TREE")
    if not isinstance(current.get("one_file_transition_receipt"), str):
        fail(Exit.PREFLIGHT, "GIT_MICRO_TRANSITION_RECEIPT")
    current_entries = {
        path: (mode, oid)
        for path, mode, oid in current["git_boundary"].current_path_resolution.path_entries
    }
    if relative not in current_entries or current_entries[relative][0] != "100644":
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
    finalize_git_metadata_adapter(current["git_boundary"])
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


def load_approved_generation_request(
    expected_receipt: str,
    expected_challenge: str,
) -> Dict[str, Any]:
    """Load one approved request and close every adapter opened by this call."""

    with GitAdapterScope():
        return _load_approved_generation_request_impl(expected_receipt, expected_challenge)


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
        "probe_generation_claim_from_verified_fds_v2",
        "create_generation_claim_from_verified_fds_v2",
        "verify_generation_claim_recovery_from_verified_fds_v2",
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
    result = generate_with_boundary_v1(
        expected_receipt,
        expected_challenge,
        boundary=ProductionGenerationBoundaryV1(),
    )
    require_git_adapter_quiescent("GENERATE")
    return result


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
