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
import fcntl
import hashlib
import hmac
import json
import os
import pathlib
import platform
import posixpath
import pwd
import re
import stat
import subprocess
import sys
import sysconfig
import tempfile
import threading
import types
import unicodedata
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Tuple
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


class GenerationRuntimeArgsV2(NamedTuple):
    """Private locators derived after GEN approval; never accepted from CLI."""

    repo_root: str
    cache_root: str
    state_root: str
    key_file: str
    envelope: str


class GitMetadataAdapter:
    """Private, content-frozen Git metadata boundary for one read sequence."""

    __slots__ = (
        "developer_root",
        "repo_root",
        "live_git_dir",
        "live_common_dir",
        "adapter_root",
        "git_dir",
        "adapter_fd",
        "git_fd",
        "source_fingerprint",
        "object_dependency_oids",
        "object_dependency_fingerprint",
        "adapter_fingerprint",
        "adapter_identity",
        "git_identity",
        "owner_pid",
        "owner_uid",
        "trace",
        "closed",
    )

    def __init__(
        self,
        developer_root: str,
        repo_root: str,
        live_git_dir: str,
        live_common_dir: str,
        adapter_root: str,
        git_dir: str,
        adapter_fd: int,
        git_fd: int,
        source_fingerprint: str,
        object_dependency_oids: Sequence[str],
        object_dependency_fingerprint: str,
        adapter_fingerprint: str,
        adapter_identity: Tuple[int, int],
        git_identity: Tuple[int, int],
        trace: Sequence[Mapping[str, str]],
    ) -> None:
        self.developer_root = developer_root
        self.repo_root = repo_root
        self.live_git_dir = live_git_dir
        self.live_common_dir = live_common_dir
        self.adapter_root = adapter_root
        self.git_dir = git_dir
        self.adapter_fd = adapter_fd
        self.git_fd = git_fd
        self.source_fingerprint = source_fingerprint
        self.object_dependency_oids = tuple(object_dependency_oids)
        self.object_dependency_fingerprint = object_dependency_fingerprint
        self.adapter_fingerprint = adapter_fingerprint
        self.adapter_identity = adapter_identity
        self.git_identity = git_identity
        self.owner_pid = os.getpid()
        self.owner_uid = os.getuid()
        self.trace = [dict(entry) for entry in trace]
        self.closed = False


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
MAX_GIT_CONTROL_BYTES = 2 * 1024 * 1024
MAX_GIT_INDEX_BYTES = 128 * 1024 * 1024
MAX_GIT_ADAPTER_FILE_BYTES = 1024 * 1024 * 1024
MAX_GIT_ADAPTER_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
MAX_GIT_ADAPTER_ENTRIES = 250_000
GIT_METADATA_ADAPTER_PROFILE_V3 = (
    "checkpoint-scoped-private-temp-sanitized-exact-oid-identity-bound-git-fd-metadata-adapter-v3"
)
GIT_METADATA_OBJECT_CLOSURE_PROFILE_V2 = (
    "captured-head-all-current-tree-oids-exact-20-approved-artifact-blobs-pack-v2"
)
GIT_METADATA_PACK_IMPORT_PROFILE_V1 = (
    "sandboxed-exact-oid-pack-objects-stdout-independent-checksum-index-pack-stdin-v1"
)
GIT_OBJECT_DEPENDENCY_PROFILE_V3 = (
    "exact-oid-loose-selected-frozen-v2-index-pack-container-v3"
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
GIT_ADAPTER_TEMP_PREFIX = "gov01-git-adapter-"
CHALLENGE_RE = re.compile(r"\AGOV01-SA-[0-9]{8}-[0-9a-f]{64}\Z")
GENERATION_CHALLENGE_RE = re.compile(r"\AGOV01-GEN-[0-9]{8}-[0-9a-f]{64}\Z")
CONTROL_PREPARATION_CHALLENGE_RE = re.compile(r"\AGOV01-CP-[0-9]{8}-[0-9a-f]{32}\Z")
GENERATION_CLAIM_NAME_RE = re.compile(
    r"\Ageneration-claim-(GOV01-GEN-[0-9]{8}-[0-9a-f]{64})\Z"
)
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
GIT_METADATA_SOURCE_DOMAIN = b"CLS/GOV01/GIT-METADATA-SOURCE/v1"
GIT_DIRTY_MANIFEST_DOMAIN = b"CLS/GOV01/GIT-DIRTY-CONTENT/v2"
PUBLIC_ARTIFACT_SET_DOMAIN = b"CLS/GOV01/PUBLIC-ARTIFACT-SET/v2"
EXECUTOR_ARGV_TEMPLATE_DOMAIN = b"CLS/GOV01/EXECUTOR-ARGV-TEMPLATE/v2"
EVIDENCE_COMMAND_TEMPLATES_DOMAIN = b"CLS/GOV01/EVIDENCE-COMMAND-TEMPLATES/v2"
GENERATION_RECEIPT_DOMAIN = b"CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1"
FIRST_APPROVAL_RECEIPT_DOMAIN = b"CLS/GOV01-FIRST-RECEIPT/v1"
CONTROL_PREPARATION_ENVELOPE_RECEIPT_DOMAIN = b"CLS/GOV01-TOOLCHAIN-CONTROL-PREP-RECEIPT/v1"
PREDECESSOR_CHAIN_DOMAIN = b"CLS/GOV01/STATIC-ACQUISITION-PREDECESSOR-CHAIN/v2"
GENERATION_CLAIM_DOMAIN = b"CLS/GOV01/STATIC-ENVELOPE-GENERATION-CLAIM/v1"
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
PRECLAIM_RETRY_AUTHORITY = (
    "retry the same approved envelope only while unexpired and all receipt-bound inputs remain unchanged; "
    "otherwise obtain new explicit user approval"
)
FAIL_CLOSED_REVIEW_AUTHORITY = "new explicit user approval after fail-closed evidence review"
RETAINED_STATE_AUTHORITY = (
    "new explicit user approval after retained-state inspection; never retry automatically"
)
GIT_ADAPTER_CLEANUP_AUTHORITY = (
    "new explicit user approval after private-state inspection; never retry automatically"
)
ATTEMPT_POLICY_V2 = (
    "single-use begins only at successful exclusive persistent claim; read-only and preclaim failures leave no "
    "consumption record and permit same-envelope retry only while unexpired and every receipt-bound input remains "
    "unchanged; post-claim failure consumes the challenge and requires new authority"
)
ENVIRONMENT_MODE_V2 = (
    "executor requires Python -I -S -B and self-attests those runtime flags; every authorized evidence subprocess "
    "receives a newly constructed exact environment and never inherits caller environment; assurance ceiling is "
    "runtime-self-attested-not-pre-exec"
)
GIT_CHILD_SANDBOX_PROFILE_V3 = (
    "every Git child receives a dedicated duplicate of the identity-bound adapter Git-directory FD, fchdir's "
    "to that inode, closes the child-only FD, then calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once "
    "before exec with a generated "
    "default-deny profile; permits only the content-bound CommandLineTools tree, one initially-0700 then sealed-0500 "
    "/private/tmp metadata adapter, required path ancestors, and the exact repository worktree only for commands "
    "that must enumerate it; every child uses literal --git-dir=. plus an explicit absolute --work-tree "
    "and never -C or repository discovery; "
    "live config, refs, index, HEAD and object stores are denied; an explicit file-write* deny prevents creation, "
    "rename, unlink or mutation of /private/tmp, the adapter root entry and every sibling adapter entry; network, "
    "writes, Vault/.obsidian paths, config "
    "includes, alternates, grafts and all other reads are denied; sandbox initialization failure is terminal; "
    "/usr/bin/sandbox-exec is never executed"
)
GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V3 = (
    "each git-metadata-adapter-bootstrap child receives a dedicated duplicate of the identity-bound adapter Git "
    "directory FD, fchdir's to that inode, closes the child-only FD, then calls /usr/lib/libsandbox.1.dylib "
    "sandbox_init exactly once before exec with a generated default-deny profile; argv always has literal "
    "--git-dir=. and an explicit absolute repo --work-tree with no -C or discovery; only cat-file --batch for "
    "captured HEAD and recursively discovered tree "
    "OIDs plus exact-OID pack-objects --stdout receive GIT_OBJECT_DIRECTORY with only exact loose-object paths or "
    "per-request pack/index pairs selected by independently verified frozen v2 pack-index search receipts under "
    "the live common-dir/objects root; the parent verifies the streamed pack checksum, then index-pack --stdin "
    "materializes only that bounded stream into the adapter with the live bridge unset, and verify-pack also runs "
    "with that bridge unset; live "
    "HEAD,index,configs,refs,hooks,logs,grafts,unselected loose objects and objects/info including alternates and "
    "http-alternates are denied; pack-objects has no child filesystem write authority and only index-pack may write, "
    "only beneath the exact identity-bound private adapter objects/pack subtree; explicit write denies protect the "
    "/private/tmp parent, adapter root/Git/object directory entries, every sibling adapter and every path outside "
    "that exact objects/pack subtree; worktree payload, Vault/.obsidian, other reads/writes, "
    "network and subprocess executables other than "
    "the content-bound Git binary are denied; direct full-source CAS brackets bootstrap and the bridge is absent "
    "from every sealed-adapter evidence child"
)
GIT_SNAPSHOT_COMMITMENT_PROFILE_V2 = (
    "HMAC-SHA-256 with 32-byte private key over ASCII(CLS/GOV01/GIT-SNAPSHOT/v2) || NUL || "
    "uint64be(canonical-body-byte-length) || UTF-8-NFC-LF sorted-key compact canonical JSON of the full private "
    "Git snapshot body excluding commitment; body includes git_control,head,tree,object_format,status_sha256,"
    "status_bytes,dirty_manifest_commitment,worktree_tree_exclusions,worktree_exact_file_exclusions,refs_sha256,"
    "refs_bytes,index,config,hooks,index_locator_commitment,config_locator_commitment,hooks_locator_commitment,"
    "hooks_config_state,git_binary_sha256,git_metadata_source_commitment,git_metadata_adapter_profile,"
    "git_metadata_adapter_cleanup_state,git_metadata_adapter_residue_count,live_git_control_child_read_count; "
    "git_metadata_source_commitment is a framed HMAC under ASCII(CLS/GOV01/GIT-METADATA-SOURCE/v1) over a "
    "path-free canonical body containing the live metadata capture fingerprint for HEAD,index,configs,refs,hooks,"
    "control absences, the object-root anchor and the captured exact pack/index search dependency receipt, plus "
    "the exact private adapter object-manifest receipt for captured HEAD,"
    "all current tree OIDs and exactly 20 approved artifact blob paths, including sealed batch-all exact-set and "
    "parent-side per-object OID recomputation receipts; adapter profile is "
    "checkpoint-scoped-private-temp-sanitized-exact-oid-identity-bound-git-fd-metadata-adapter-v3, "
    "cleanup_state is removed, residue "
    "count and live Git-control child reads are zero; worktree tree exclusions are exactly the challenge stage and "
    "node_modules while the exact-file exclusion contains exactly the challenge-suffixed pending envelope; dirty "
    "manifest is keyed content-and-metadata evidence for every nonexcluded porcelain-v2 path"
)
GIT_ADAPTER_EPHEMERAL_MUTATION_V3 = (
    "before each Git child sequence create one unpredictable exact 0700 /private/tmp/gov01-git-adapter-* scratch "
    "root, freeze sanitized config plus captured HEAD,index,refs,info-exclude and shallow, then use a sandboxed "
    "object-only live bridge to stream a pack containing exactly captured HEAD, every current-tree tree OID and "
    "only approved artifact blob OIDs; independently verify the stream checksum, import it through bridge-free "
    "index-pack, verify the exact pack object set, seal the self-contained adapter 0500/0400, then remove that exact "
    "dev/inode-bound root before returning; "
    "this nonpersistent scratch neither consumes the challenge nor authorizes any repo/state/cache mutation"
)
GIT_ADAPTER_FAILURE_ACTION_V3 = (
    "pre-claim failures may create only the authorized Git adapter scratch; under the declared trust boundary and "
    "host assurance, return and conditional retry require pre-removal root/Git identity agreement, removal of only "
    "the authorized adapter paths, post-removal absence and zero pathname/registry residue; any observed identity "
    "drift, missing pathname, cleanup error or residue is terminal fail-closed, forbids success and automatic retry, "
    "and requires new explicit approval after private-state inspection; no claim, ledger, stage, target or other "
    "persistent write occurs before the challenge claim"
)
FAILURE_EVIDENCE_ACTION_V2 = GIT_ADAPTER_FAILURE_ACTION_V3 + (
    "; after a persistent claim exists, append/fsync and semantically verify a terminal failure event only while "
    "the retained ledger writer is healthy and nonterminal; never repair or delete retained persistent state"
)
FIRST_AUTHORITY_CONSUMING_PERSISTENT_WRITE_V2 = (
    "mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700 is the first authority-consuming "
    "persistent write; EEXIST is terminal replay; earlier writes are limited to the exact nonpersistent "
    "/private/tmp Git adapter scratch, which must be identity-bound and fully removed before any return"
)
FAILURE_CHALLENGE_POLICY_V2 = (
    "before exclusive persistent claim no consumption record exists and same-envelope retry is conditional on "
    "unexpired authority plus byte-exact receipt-bound inputs; after exclusive claim mkdir the challenge is consumed"
)
FAILURE_NEW_AUTHORITY_POLICY_V2 = (
    "preclaim: new approval is required after expiry or any receipt-bound input drift; postclaim: a new complete "
    "envelope, raw envelope digest and challenge are required"
)
TOOLCHAIN_DRIFT_ACTION_V2 = (
    "before exclusive persistent claim, stop without consumption and permit only conditional same-envelope retry "
    "while unexpired and receipt-bound inputs remain unchanged; after claim, append terminal rejection when the "
    "ledger remains writable, perform no stage or target write and require new authority"
)
FIRST_APPROVAL_ENVELOPE_RAW_SHA256 = "0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410"
FIRST_RECEIPT_DOMAIN_SHA256 = "c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740"
BOOTSTRAP_PATCH_RAW_SHA256 = "d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa"
BOOTSTRAP_COMMIT_OID = "0e0f0150be184f4dad83a859b0fdd232ec53e8b5"
CONTROL_PREPARATION_ENVELOPE_RAW_SHA256 = "ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b"
CONTROL_PREPARATION_RECEIPT_DIGEST = "dbb28c7627b63989e98b70ff608c20976d687541364af95804537dda7867541c"
CONTROL_PREPARATION_EVIDENCE_DOMAIN = b"CLS/GOV01-TOOLCHAIN-CONTROL-PREP-EVIDENCE/v1\x00"
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
EXECUTOR_ARGV_TEMPLATE_V2 = (
    "{BOUND_PYTHON_PRIVATE}",
    "-I",
    "-S",
    "-B",
    "{BOUND_EXECUTOR_PRIVATE}",
    "acquire",
    "--generation-challenge",
    "{APPROVED_GENERATION_CHALLENGE_ID_PUBLIC}",
    "--receipt-digest",
    "{APPROVED_RECEIPT_DIGEST_PUBLIC}",
    "--approval-challenge",
    "{APPROVAL_CHALLENGE_ID_PUBLIC}",
)
INCOMPLETE_MARKER = ".gov01-incomplete"
TARGET_NAME = "node_modules"
MAX_COMPRESSED_CLOSURE = 14_000_000
MAX_PAYLOAD_CLOSURE = 64_000_000
RENAME_EXCL = 0x00000004
SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-pending-envelope:v2:draft"
PRIVATE_SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-private-evidence:v2:draft"
PUBLIC_SCHEMA_ID = "urn:canvas-learning-system:gov-01:toolchain-static-acquisition-public-attestation:v2:draft"
CONTROL_PREFIX = "_bmad-output/审查/phase0a-annotation-truth/"
PENDING_ENVELOPE_BASENAME_PREFIX = "GOV-01-toolchain-static-acquisition-pending-"
PENDING_ENVELOPE_GIT_EXCLUSION_PROFILE = (
    "git-status-exact-top-literal-envelope-file-exclusion-v1; no parent, subtree, wildcard or glob exclusion"
)
PENDING_ENVELOPE_PUBLIC_STRING_ALLOWLIST = frozenset(
    {
        "/usr/bin/xcode-select",
        "/usr/bin/xcrun",
        "/usr/bin/pgrep",
        "/usr/sbin/lsof",
        ":(exclude)canvas-vault",
        ":(exclude)canvas-vault/**",
    }
)
PENDING_STATIC_ARTIFACT_SPECS = (
    ("goal", "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md"),
    ("governance-decision", CONTROL_PREFIX + "2026-08-20-GOV-01-追踪真相源修复决策稿.md"),
    ("phase0a-contract", CONTROL_PREFIX + "2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md"),
    ("first-receipt-envelope", CONTROL_PREFIX + "GOV-01-first-receipt-envelope-v1.json"),
    ("first-receipt-schema", CONTROL_PREFIX + "GOV-01-first-receipt-envelope-v1.schema.json"),
    ("bootstrap-patch", CONTROL_PREFIX + "2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch"),
    ("control-prep-envelope", CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.json"),
    ("control-prep-schema", CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.schema.json"),
    ("static-envelope-generator", CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-v1.py"),
    (
        "generation-envelope-schema",
        CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json",
    ),
    (
        "generation-hostile-fixture",
        CONTROL_PREFIX + "GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py",
    ),
    ("static-executor", EXECUTOR_RELATIVE),
    ("static-verifier", VERIFIER_RELATIVE),
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
GENERATION_APPROVAL_ROLE = "generation-approval-envelope"
GENERATION_APPROVAL_PATH_RE = re.compile(
    r"\A_bmad-output/审查/phase0a-annotation-truth/"
    r"GOV-01-toolchain-static-envelope-generation-envelope-v1\."
    r"GOV01-GEN-[0-9]{8}-[0-9a-f]{64}\.json\Z"
)
PRIVATE_PREIMAGE_CHECKS = (
    "five exact HMAC-bound locators; repo, cache and state roots are pairwise separated; "
    "the HMAC key is the exact state-root/hmac.key direct child; the envelope is contained by the "
    "control prefix; no symlink ancestor and no Vault or .obsidian component",
    "cache-root locator and direct-SRI content blob bytes/digests; npm cache index read is prohibited",
    "directly capture Git control marker, commondir, local configs, HEAD, index, refs, hooks and object store with "
    "absent alternate controls before constructing a sealed private adapter; every Git child uses only the adapter "
    "through explicit --git-dir/--work-tree and live metadata is revalidated after capture and before cleanup",
    "pgrep Claude candidates and per-candidate lsof cwd stdout commitments without public command output",
    "state-root, claims-container and HMAC-key owner/group/mode are bound by the private control identity "
    "commitment; exact challenge child absence, HMAC-key bytes, raw envelope bytes and approved receipt "
    "digest are rechecked before the first authority-consuming persistent write; only exact identity-bound Git "
    "adapter scratch creation and mandatory cleanup may occur earlier",
)
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
AUTHORIZED_SUBPROCESS_ROLES = (
    "xcode-select-resolver",
    "xcrun-resolver",
    "git-metadata-adapter-bootstrap",
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
    "git-read-only-evidence": (
        "regular-file",
        "raw-file-sha256",
        "content-bound-git-for-private-adapter-bootstrap-and-read-only-evidence-only",
    ),
    "pgrep-read-only-evidence": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
    "lsof-read-only-evidence": ("regular-file", "raw-file-sha256", "read-only-evidence-command-only"),
}
TOOLCHAIN_LOGICAL_ID_BY_ROLE = {role: role for role in TOOLCHAIN_ROLES}
TOOLCHAIN_FIXED_VERSION_BY_ROLE = {
    "static-executor": SCRIPT_VERSION,
    "static-verifier": "gov-01-toolchain-static-verifier-v2",
    "xcode-select-resolver": "not-observed-content-addressed-only",
    "xcrun-resolver": "not-observed-content-addressed-only",
    "git-read-only-evidence": "not-observed-content-addressed-only",
    "pgrep-read-only-evidence": "not-observed-content-addressed-only",
    "lsof-read-only-evidence": "not-observed-content-addressed-only",
}
FIXED_TOOL_PATHS = {
    "xcode-select-resolver": "/usr/bin/xcode-select",
    "xcrun-resolver": "/usr/bin/xcrun",
    "pgrep-read-only-evidence": "/usr/bin/pgrep",
    "lsof-read-only-evidence": "/usr/sbin/lsof",
}
_AUTHORIZED_EXECUTABLE_HASHES: Dict[str, str] = {}
_GIT_DEVELOPER_ROOTS: Dict[str, str] = {}
_ACL_FUNCTIONS: Optional[Tuple[Any, Any, Any]] = None
_GIT_METADATA_ADAPTER_SCOPE_LOCK = threading.Lock()
_GIT_METADATA_ADAPTER_SCOPE: Optional[Dict[str, Any]] = None
ALLOWED_CHILD_ENV_NAMES = frozenset(
    {
        "PATH", "HOME", "LC_ALL", "LANG", "GIT_OPTIONAL_LOCKS", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_TERMINAL_PROMPT", "GIT_NO_REPLACE_OBJECTS",
        "GIT_PROTOCOL_FROM_USER", "GIT_ALLOW_PROTOCOL",
        "GIT_ATTR_NOSYSTEM", "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_OBJECT_DIRECTORY",
    }
)
TOP_LEVEL_FIELDS = frozenset(
    "schema_version artifact_type artifact_id plan_id state approval_challenge_id single_use census_at_utc "
    "not_after_utc path_base encoding_profile receipt_digest_profile approval_receipt_contract predecessor "
    "generation_authorization "
    "artifacts artifact_path_uniqueness_policy authorization_preimage frozen_toolchain schema_binding "
    "static_acquisition_contract lock_closure execution_plan mutation_scope failure_contract success_contract "
    "private_state_authorization privacy".split()
)
GENERATION_AUTHORIZATION_FIELDS = frozenset(
    "profile approval_challenge_id approval_envelope_repo_relative_path "
    "generated_acquisition_envelope_repo_relative_path raw_envelope_sha256 receipt_digest "
    "receipt_domain_profile authorization_parent_commit_oid authorization_parent_tree_oid "
    "authorization_commit_oid authorization_tree_oid commit_transition_profile state "
    "generation_claim_required generation_claim_profile generation_claim_record_profile "
    "generation_claim_retention".split()
)
PREDECESSOR_FIELDS = (
    "profile",
    "first_approval_envelope_raw_sha256",
    "first_approval_receipt_digest",
    "bootstrap_patch_raw_sha256",
    "bootstrap_commit_oid",
    "control_preparation_envelope_raw_sha256",
    "control_preparation_envelope_receipt_digest",
    "control_preparation_approval_challenge_id",
    "control_preparation_result_raw_sha256",
    "control_preparation_evidence_receipt_sha256",
    "control_preparation_state",
    "generation_authorization_envelope_raw_sha256",
    "generation_authorization_receipt_digest",
    "generation_authorization_challenge_id",
    "generation_authorization_parent_commit_oid",
    "generation_authorization_parent_tree_oid",
    "generation_authorization_commit_oid",
    "generation_authorization_tree_oid",
    "predecessor_chain_receipt_sha256",
)
GENERATION_CLAIM_BODY_FIELDS = (
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
)
GENERATION_CLAIM_FIELDS = GENERATION_CLAIM_BODY_FIELDS + ("record_hmac_sha256",)
AUTHORIZATION_PREIMAGE_FIELDS = frozenset(
    "head_commit_oid head_tree_oid git_object_format git_snapshot_commitment git_snapshot_commitment_profile "
    "private_preapproval_commitment private_preapproval_commitment_profile public_repo_artifact_set_receipt_sha256 "
    "private_preimage_capture worktree_state preexisting_dirty_policy target_preimage acquisition_control_root_state "
    "protected_existing_control_paths protected_existing_control_state absent_control_paths absent_control_state "
    "node_modules_state target_worktree_claude_sessions forbidden_process_match_count "
    "node_modules_parent_or_sibling_reuse_allowed private_vault_census_allowed envelope_repo_relative_path "
    "envelope_git_status_exclusion_profile".split()
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
    "environment_mode environment_name_allowlist git_child_sandbox_profile "
    "git_metadata_adapter_bootstrap_sandbox_profile git_metadata_adapter_trust_boundary "
    "git_metadata_adapter_host_assurance ustar_parser compression_policy "
    "ustar_safety_policy member_type_policy "
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


_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON = r'''{"approval_receipt_contract":{"authority_expansion_allowed":false,"authority_is_exact":true,"challenge_must_match":true,"first_authority_consuming_persistent_write":"mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700 is the first authority-consuming persistent write; EEXIST is terminal replay; earlier writes are limited to the exact nonpersistent /private/tmp Git adapter scratch, which must be identity-bound and fully removed before any return","receipt_before_first_authority_consuming_persistent_write":true,"receipt_must_match_raw_envelope_bytes":true,"required_user_reference":"exact domain-separated envelope SHA-256 plus exact approval_challenge_id"},"artifact_path_uniqueness_policy":"content-addressed checker MUST reject duplicate path even when role, byte_length or raw_file_sha256 differs; JSON Schema uniqueItems is not sufficient","authorization_preimage":{"absent_control_paths":[".npmrc","npm-shrinkwrap.json","pnpm-lock.yaml","yarn.lock","bun.lock","bun.lockb"],"absent_control_state":"all exact repo-root direct children ABSENT before and required ABSENT after","acquisition_control_root_state":"existing-real-directory-no-symlink-ancestor","envelope_git_status_exclusion_profile":"git-status-exact-top-literal-envelope-file-exclusion-v1; no parent, subtree, wildcard or glob exclusion","envelope_repo_relative_path":null,"forbidden_process_match_count":null,"git_object_format":null,"git_snapshot_commitment":null,"git_snapshot_commitment_profile":"HMAC-SHA-256 with 32-byte private key over ASCII(CLS/GOV01/GIT-SNAPSHOT/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF sorted-key compact canonical JSON of the full private Git snapshot body excluding commitment; body includes git_control,head,tree,object_format,status_sha256,status_bytes,dirty_manifest_commitment,worktree_tree_exclusions,worktree_exact_file_exclusions,refs_sha256,refs_bytes,index,config,hooks,index_locator_commitment,config_locator_commitment,hooks_locator_commitment,hooks_config_state,git_binary_sha256,git_metadata_source_commitment,git_metadata_adapter_profile,git_metadata_adapter_cleanup_state,git_metadata_adapter_residue_count,live_git_control_child_read_count; git_metadata_source_commitment is a framed HMAC under ASCII(CLS/GOV01/GIT-METADATA-SOURCE/v1) over a path-free canonical body containing the live metadata capture fingerprint for HEAD,index,configs,refs,hooks,control absences, the object-root anchor and the captured exact pack/index search dependency receipt, plus the exact private adapter object-manifest receipt for captured HEAD,all current tree OIDs and exactly 20 approved artifact blob paths, including sealed batch-all exact-set and parent-side per-object OID recomputation receipts; adapter profile is checkpoint-scoped-private-temp-sanitized-exact-oid-identity-bound-git-fd-metadata-adapter-v3, cleanup_state is removed, residue count and live Git-control child reads are zero; worktree tree exclusions are exactly the challenge stage and node_modules while the exact-file exclusion contains exactly the challenge-suffixed pending envelope; dirty manifest is keyed content-and-metadata evidence for every nonexcluded porcelain-v2 path","head_commit_oid":null,"head_tree_oid":null,"node_modules_parent_or_sibling_reuse_allowed":false,"node_modules_state":"ABSENT","preexisting_dirty_policy":"private exact pre/post inventory required; no public paths or raw dirty/index/local-settings digest; zero mutation outside the exact new target","private_preapproval_commitment":null,"private_preapproval_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-PREAPPROVAL/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON of exactly {schema_version,approval_challenge_id,census_at_utc,hmac_key_id,authorized_locator_commitments,private_control_identity_commitment,public_repo_artifact_set_receipt_sha256,git_snapshot_commitment,toolchain_set_receipt_sha256,package_lock_raw_sha256,host_platform,host_architecture,target_worktree_claude_sessions,forbidden_process_match_count,host_selected_package_count,host_selected_cache_bytes,host_bin_link_count,content_receipt_sha256,ustar_closure_sha256,resolution_receipt_sha256,expected_tree_sha256}; no envelope digest, receipt digest, generated timestamp, raw private locator, inode/device or command bytes are in this deterministic body","private_preimage_capture":"census and post-approval checks may materialize only an identity-bound nonpersistent Git metadata adapter under /private/tmp; every child fchdir's through a dedicated duplicate of the held adapter Git-directory FD, closes that child-only FD, and reads the sealed frozen adapter with literal --git-dir=., explicit --work-tree and zero live Git-control reads; source and adapter CAS run before/after children, exact cleanup and zero residue are required before returning; the persistent O_EXCL challenge claim remains the first authority-consuming persistent write","private_vault_census_allowed":false,"protected_existing_control_paths":["package.json","package-lock.json",".gitignore"],"protected_existing_control_state":"PRESENT regular files; raw SHA-256 bound in artifacts; byte-identical before and after","public_repo_artifact_set_receipt_sha256":null,"target_preimage":"ABSENT","target_worktree_claude_sessions":null,"worktree_state":null},"execution_plan":{"allowed_subprocess_executable_roles":["xcode-select-resolver","xcrun-resolver","git-metadata-adapter-bootstrap","git-read-only-evidence","pgrep-read-only-evidence","lsof-read-only-evidence"],"archive_or_payload_execution_allowed":false,"attempt_policy":"single-use; any failure consumes challenge; retry requires a new envelope and challenge","compression_policy":"exactly one RFC1952 gzip stream through frozen Python stdlib zlib; MAX_TAR_STREAM prebound; eof required; unused_data and unconsumed_tail empty; concatenated/trailing stream rejected","duplicate_collision_policy":"reject duplicate normalized path, file-directory conflict, Unicode NFC collision and case-fold collision before first target write","environment_mode":"executor requires Python -I -S -B and self-attests those runtime flags; every authorized evidence subprocess receives a newly constructed exact environment and never inherits caller environment; assurance ceiling is runtime-self-attested-not-pre-exec","environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM","GIT_OBJECT_DIRECTORY"],"evidence_command_templates":[{"argv_allowlist":[["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","pack-objects","--stdout","--no-reuse-delta","--no-reuse-object"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","index-pack","--stdin","--index-version=2"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","verify-pack","-v","{GIT_METADATA_ADAPTER_PACK_INDEX_RELATIVE_PRIVATE}"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM","GIT_OBJECT_DIRECTORY"],"executable":"{RESOLVED_CLT_GIT_PRIVATE}","read_only":false,"role":"git-metadata-adapter-bootstrap","shell":false,"write_scope":"checkpoint-scoped-private-temp-adapter-only"},{"argv_allowlist":[["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--verify","HEAD"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--verify","HEAD^{tree}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","rev-parse","--show-object-format"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","cat-file","--batch-all-objects","--batch-check=%(objectname) %(objecttype) %(objectsize)"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","ls-tree","-r","-t","-z","--full-tree","HEAD^{tree}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","status","--porcelain=v2","-z","--untracked-files=all","--",".",":(exclude).git",":(exclude).git/**",":(exclude)canvas-vault",":(exclude)canvas-vault/**",":(exclude){STAGE_REPO_RELATIVE}",":(exclude){STAGE_REPO_RELATIVE}/**",":(exclude)node_modules",":(exclude)node_modules/**",":(top,literal,exclude){ENVELOPE_REPO_RELATIVE}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","show-ref"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","ls-tree","-z","--full-tree","{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}","--","{PUBLIC_ARTIFACT_REPO_RELATIVE}"],["{RESOLVED_CLT_GIT_PRIVATE}","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false","-c","core.hooksPath=/dev/null","-c","core.bare=false","-c","core.excludesFile=/dev/null","-c","core.attributesFile=/dev/null","-c","submodule.recurse=false","-c","protocol.allow=never","-c","core.commitGraph=false","-c","core.multiPackIndex=false","-c","pack.useBitmap=false","-c","pack.writeReverseIndex=false","--git-dir=.","--work-tree={REPO_ROOT_PRIVATE}","--no-pager","show","{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}:{PUBLIC_ARTIFACT_REPO_RELATIVE}"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"{RESOLVED_CLT_GIT_PRIVATE}","read_only":true,"role":"git-read-only-evidence","shell":false},{"argv_allowlist":[["/usr/bin/xcode-select","-p"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"/usr/bin/xcode-select","read_only":true,"role":"xcode-select-resolver","shell":false},{"argv_allowlist":[["/usr/bin/xcrun","--find","git"]],"environment_name_allowlist":["PATH","HOME","LC_ALL","LANG","GIT_OPTIONAL_LOCKS","GIT_CONFIG_GLOBAL","GIT_CONFIG_NOSYSTEM","GIT_CONFIG_SYSTEM","GIT_TERMINAL_PROMPT","GIT_NO_REPLACE_OBJECTS","GIT_PROTOCOL_FROM_USER","GIT_ALLOW_PROTOCOL","GIT_ATTR_NOSYSTEM","GIT_DISCOVERY_ACROSS_FILESYSTEM"],"executable":"/usr/bin/xcrun","read_only":true,"role":"xcrun-resolver","shell":false},{"argv_allowlist":[["/usr/bin/pgrep","-if","(^|[/ ])claude([ ]|$)|@anthropic-ai/claude-code"]],"environment_name_allowlist":["PATH","LC_ALL","LANG"],"executable":"/usr/bin/pgrep","read_only":true,"role":"pgrep-read-only-evidence","shell":false},{"argv_allowlist":[["/usr/sbin/lsof","-nP","-a","-p","{CLAUDE_CANDIDATE_PID_DECIMAL}","-d","cwd","-Fpn"]],"environment_name_allowlist":["PATH","LC_ALL","LANG"],"executable":"/usr/sbin/lsof","read_only":true,"role":"lsof-read-only-evidence","shell":false}],"evidence_command_templates_sha256":null,"executor_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{REPO_ROOT_PRIVATE}/_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","acquire","--repo-root","{REPO_ROOT_PRIVATE}","--cache-root","{CACHE_ROOT_PRIVATE}","--state-root","{STATE_ROOT_PRIVATE}","--key-file","{HMAC_KEY_FILE_PRIVATE}","--envelope","{ENVELOPE_PRIVATE}","--receipt-digest","{APPROVED_RECEIPT_DIGEST_PUBLIC}","--approval-challenge","{APPROVAL_CHALLENGE_ID_PUBLIC}"],"executor_argv_template_sha256":null,"executor_interface_state":"frozen-content-addressed-before-user-receipt","executor_interface_version":"gov01-static-acquisition-executor-draft-v2","expiry_checkpoints":["on-envelope-load","immediately-before-persistent-ledger-claim","immediately-before-renameatx_np-RENAME_EXCL"],"forbidden_executable_names":["npm","npx","node","nodejs","openspec","sandbox-exec","tar","bsdtar","gtar"],"git_metadata_adapter_bootstrap_sandbox_profile":"each git-metadata-adapter-bootstrap child receives a dedicated duplicate of the identity-bound adapter Git directory FD, fchdir's to that inode, closes the child-only FD, then calls /usr/lib/libsandbox.1.dylib sandbox_init exactly once before exec with a generated default-deny profile; argv always has literal --git-dir=. and an explicit absolute repo --work-tree with no -C or discovery; only cat-file --batch for captured HEAD and recursively discovered tree OIDs plus exact-OID pack-objects --stdout receive GIT_OBJECT_DIRECTORY with only exact loose-object paths or per-request pack/index pairs selected by independently verified frozen v2 pack-index search receipts under the live common-dir/objects root; the parent verifies the streamed pack checksum, then index-pack --stdin materializes only that bounded stream into the adapter with the live bridge unset, and verify-pack also runs with that bridge unset; live HEAD,index,configs,refs,hooks,logs,grafts,unselected loose objects and objects/info including alternates and http-alternates are denied; pack-objects has no child filesystem write authority and only index-pack may write, only beneath the exact identity-bound private adapter; worktree payload, Vault/.obsidian, other reads/writes, network and subprocess executables other than the content-bound Git binary are denied; direct full-source CAS brackets bootstrap and the bridge is absent from every sealed-adapter evidence child","launcher_executable_role":"python-interpreter","member_type_policy":"archive accepts regular files and directories only; rejects archive symlink, hardlink, fifo, socket, block/character device and unknown types","network_allowed":false,"phase_order":["read-only-verify-user-receipt-envelope-digest-challenge-and-expiry","read-only-hash-bound-schema-compare-schema-binding-and-run-manual-critical-envelope-checks-before-verifier-compilation","read-only-compare-repo-cache-state-key-envelope-locator-commitments","read-only-hash-every-public-artifact-and-load-only-the-bound-verifier-source","directly capture live Git metadata, freeze and seal an exact private-temp adapter, run explicit-adapter Git evidence children with zero live-control reads, revalidate the live source and remove the exact adapter with zero residue before comparing Git-snapshot and private-preapproval commitments","verify-no-active-Claude-session-whose-cwd-is-the-target-worktree; no broader ambient-process absence claim","read-only-direct-SRI-cache-census-build-expected-tree-and-freeze-all-compressed-and-payload-bytes-in-memory","recheck-approval-expiry-immediately-before-persistent-claim","create-persistent-0700-challenge-claim-directory-with-exclusive-mkdirat-and-record-first-authority-consuming-persistent-write","append-frozen-preflight-event-to-persistent-ledger","create-0700-same-parent-same-filesystem-exclusive-stage-with-incomplete-marker","stream-decompress-and-custom-parse-only-approved-USTAR-members","materialize-only-expected-resolution-destinations-without-running-payload","fsync-stage-and-verify-closure-resolution-and-stage-tree-receipts","run-full-pre-promotion-CAS-for-private-inputs-public-artifacts-toolchain-Git-dirty-content-process-census-lock-cache-control-files-stage-identity-and-target-absence","remove-only-the-incomplete-marker-seal-root-0755-and-run-two-stable-fingerprints; failure-after-this-point-retains-a-hidden-unmarked-stage","recheck-approval-expiry-and-target-absence-immediately-before-publication","publish-exact-stage-to-absent-target-with-renameatx_np-RENAME_EXCL","fsync-target-parent-and-recompute-final-tree-and-private-postimage","append-terminal-private-ledger-event-and-emit-locator-free-stdout-projection-only-if-every-success-condition-holds","stop-with-payload-unexecuted"],"runner":"caller invokes exact executor with a CPython 3.9-compatible interpreter and -I -S -B; executor self-attests isolation flags, interpreter, stdlib, executor, verifier, schema and five evidence binaries only after Python startup; no pre-exec launcher or pre-exec hash assurance exists; no shell","shell_allowed":false,"stop_after_static_attestation":true,"subprocess_from_executor_allowed":true,"ustar_parser":"custom Python stdlib fixed-512-byte POSIX.1-1988 USTAR parser; tarfile.extract/extractall forbidden","ustar_safety_policy":"strict magic/version/checksum/octal/padding/two-zero-block terminator; reject PAX, GNU, sparse, base-256 numeric, trailing payload, absolute/dot/dotdot/backslash/NUL/control path, symlink ancestor and path escape","verifier_census_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{BOUND_VERIFIER_PRIVATE}","census","--cache-root","{CACHE_ROOT_PRIVATE}"],"verifier_installed_argv_template":["{BOUND_PYTHON_PRIVATE}","-I","-S","-B","{BOUND_VERIFIER_PRIVATE}","verify-installed","--cache-root","{CACHE_ROOT_PRIVATE}","--expected-tree-sha256","{EXPECTED_TREE_SHA256_PUBLIC}"],"verifier_profile_version":"gov-01-toolchain-static-verifier-v2"},"failure_contract":{"challenge_state":"before the first authority-consuming persistent write no persistent consumption record exists but this envelope/challenge must be treated as rejected and replaced; after exclusive claim mkdir the persistent state is consumed-rejected","evidence_action":"pre-claim failures may create only the authorized Git adapter scratch and must remove its exact identity; adapter cleanup failure, root identity uncertainty or any residue is terminal fail-closed, forbids a success or automatic retry, and requires new explicit approval after private-state inspection; no claim, ledger, stage, target or other persistent write occurs before the challenge claim; after a persistent claim exists, append/fsync and semantically verify a terminal failure event only while the retained ledger writer is healthy and nonterminal; never repair or delete retained persistent state","existing_target_action":"never modify or delete; if a target was newly published before a later failure, retain as unauthorized and require user decision","failed_stage_action":"retain in place with no automatic cleanup, deletion, quarantine move or glob: before marker removal it remains a hidden 0700 stage carrying the 0600 incomplete marker; after marker removal/seal but before rename it remains a hidden 0755 stage without the marker; after successful rename followed by later failure the published target is retained as unauthorized pending user decision","failure_action":"STOP immediately at first failed gate","new_authority_required":"new complete envelope, new raw envelope digest and new challenge","public_success_attestation_allowed":false,"retry_allowed":false},"lock_closure":{"archive_member_types":["regular-file","directory"],"content_receipt_profile":"SHA-256(ASCII(CLS/GOV01-OFFLINE-CACHE/v1) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 6 TAB-separated columns: lock_key, version, resolved, integrity, compressed_bytes, actual_integrity","content_receipt_sha256":null,"direct_sri_policy":"no npm cache index read; sha512 SRI bytes map directly to _cacache/content-v2/sha512/<first-2>/<next-2>/<remainder>; missing or mismatched blob is terminal failure","expected_archive_member_count":null,"expected_resolved_tree_entry_count":null,"expected_tree_receipt_profile":"SHA-256(ASCII(CLS/GOV01/DETERMINISTIC-NODE-MODULES/v2) || NUL || UTF-8 body); body is LF-terminated rows sorted by UTF-8 path bytes with exactly 5 TAB-separated columns: kind,path,mode,size,file_sha256_or_link_text","expected_tree_sha256":null,"generated_symlink_policy":"only exact relative symlink text bound by the resolution receipt; resolved target remains beneath final tree","host_bin_link_count":null,"host_selected_cache_bytes":null,"host_selected_package_count":null,"network_fetch_allowed":false,"resolution_receipt_profile":"SHA-256(ASCII(CLS/GOV01/NODE-RESOLUTION-CLOSURE/v2) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 7 TAB-separated columns: source,edge_type,dependency_name,spec,target,target_version,state; this is deterministic package-lock path-closure evidence only and is not a general semver solver or semantic-version satisfiability proof","resolution_receipt_sha256":null,"resource_limits":{"compressed_closure_bytes_max":14000000,"final_path_utf8_bytes_max":128,"member_count_per_archive_max":5000,"payload_closure_bytes_max":64000000,"required_bin_link_count":12,"required_raw_regular_count":4099,"selected_archive_count":167,"single_file_bytes_max":15000000,"tar_stream_bytes_per_archive_max":24000000},"source_kind":"preapproved-local-content-addressed-ustar-set","source_locator_policy":"private absolute locators omitted; after challenge claim, derive each content-v2 locator directly from the package-lock sha512 SRI and require actual_integrity equality","ustar_closure_receipt_profile":"SHA-256(ASCII(CLS/GOV01/USTAR-CLOSURE/v2) || NUL || UTF-8 body); body is lexicographically sorted LF-terminated rows of exactly 13 TAB-separated columns: lock_key,version,integrity,compressed_bytes,tar_bytes,member_count,raw_regular_count,raw_directory_count,payload_bytes,strip_root,package_name,package_version,member_manifest_sha256; each member_manifest_sha256 uses CLS/GOV01/USTAR-PACKAGE-MEMBERS/v2 NUL plus sorted 8-column member rows","ustar_closure_sha256":null},"mutation_scope":{"allowed_ephemeral_mutations":["before each Git child sequence create one unpredictable exact 0700 /private/tmp/gov01-git-adapter-* scratch root, freeze sanitized config plus captured HEAD,index,refs,info-exclude and shallow, then use a sandboxed object-only live bridge to stream a pack containing exactly captured HEAD, every current-tree tree OID and only approved artifact blob OIDs; independently verify the stream checksum, import it through bridge-free index-pack, verify the exact pack object set, seal the self-contained adapter 0500/0400, then remove that exact dev/inode-bound root before returning; this nonpersistent scratch neither consumes the challenge nor authorizes any repo/state/cache mutation","before each Git child sequence create one unpredictable exact 0700 /private/tmp/gov01-git-adapter-* scratch root, freeze sanitized config plus captured HEAD,index,refs,info-exclude and shallow, then use a sandboxed object-only live bridge to pack exactly captured HEAD, every current-tree tree OID and only approved artifact blob OIDs; verify the pack object set, remove the bridge, seal the self-contained adapter 0500/0400, then remove that exact dev/inode-bound root before returning; this nonpersistent scratch neither consumes the challenge nor authorizes any repo/state/cache mutation","create one exact 0700 same-parent same-filesystem stage with an exact 0600 incomplete marker; this stage is publication-working-state but is retained rather than ephemeral on any failure","write only the frozen expected directories, regular-file payload bytes and generated relative bin symlinks beneath that stage","remove only the exact incomplete marker and chmod the stage root 0755 immediately before two stable fingerprints and exclusive publication; failure in this sealed pre-publication window retains a hidden 0755 stage without the marker"],"allowed_persistent_mutations":["create one exact persistent 0700 challenge claim directory with exclusive mkdirat semantics and create/append one 0600 hash-chained ledger beneath it; the claim and ledger are never automatically deleted","create exactly one previously-absent approved target by a single successful renameatx_np(RENAME_EXCL)"],"forbidden_mutations":["overwrite, merge, unlink, replace or repair any existing target","modify existing repo-root package.json, package-lock.json or .gitignore; create any absent alternate lock file or .npmrc","write outside the exact identity-bound /private/tmp Git adapter scratch, exact persistent challenge claim/ledger, exact stage and exact exclusive target publication","modify Git objects, refs, index, hooks, config or any existing worktree file","modify parent or sibling worktree, user home, private Vault, Graphiti or external service","commit, push, branch/ref creation, OpenSpec execution or governance apply"],"overwrite_allowed":false,"publish_attempt_ceiling":1,"publish_flag":"RENAME_EXCL","publish_syscall":"renameatx_np","target_preimage":"ABSENT"},"privacy":{"graphiti_call_count":0,"network_call_count":0,"private_locator_public_count":0,"private_raw_sha256_only_for":["cache-root and direct-SRI content blob private locator evidence","dirty/untracked inventory","Git index/private config/hooks locator receipts","local settings","command output/open-file/process traces","persistent ledger and challenge claim"],"private_vault_read_count":0,"public_raw_sha256_allowed_for":["public repo artifacts including executor/verifier/schemas","locator-free toolchain content identities","content, USTAR, closure Merkle, resolution, expected-tree and public receipt digests"]},"private_state_authorization":{"all_cli_locators_compared_before_any_write":true,"authorized_locator_commitments":null,"challenge_claim_preimage":"exact state-root/claims/<approval_challenge_id> direct child ABSENT","claims_container_preimage":"state-root/claims already exists as a receipt-bound-owner-and-group real 0700 directory and is not created by this attempt","destruction_authorized":false,"first_authority_consuming_persistent_write":"mkdirat exact state-root/claims/<approval_challenge_id> with mode 0700 is the first authority-consuming persistent write; EEXIST is terminal replay; earlier writes are limited to the exact nonpersistent /private/tmp Git adapter scratch, which must be identity-bound and fully removed before any return","hmac_key_id":null,"hmac_key_id_profile":"HMAC-SHA-256 with the same private key over ASCII(CLS/GOV01/HMAC-KEY-ID/v2) || NUL || eight zero bytes; locator and raw key bytes are never serialized","locator_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-LOCATOR/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON {label,locator}; labels and absolute normalized no-symlink locators are exact and comparison uses hmac.compare_digest","persistent_single_use_ledger_required":true,"private_control_identity_commitment":null,"private_control_identity_commitment_profile":"HMAC-SHA-256 with the authorized 32-byte private key over ASCII(CLS/GOV01/PRIVATE-CONTROL-IDENTITY/v2) || NUL || uint64be(canonical-body-byte-length) || UTF-8-NFC-LF canonical JSON binding the receipt-approved owner UID, inherited control GID, exact state-root/claims/key modes and expected claim/ledger modes without serializing private locators","private_evidence_schema_required":"gov-01-toolchain-static-acquisition-private-evidence-v2","private_file_modes":{"directory":"0700","file":"0600","umask":"0077"},"private_preimage_checks":["five exact HMAC-bound locators; repo, cache and state roots are pairwise separated; the HMAC key is the exact state-root/hmac.key direct child; the envelope is contained by the control prefix; no symlink ancestor and no Vault or .obsidian component","cache-root locator and direct-SRI content blob bytes/digests; npm cache index read is prohibited","directly capture Git control marker, commondir, local configs, HEAD, index, refs, hooks and object store with absent alternate controls before constructing a sealed private adapter; every Git child uses only the adapter through explicit --git-dir/--work-tree and live metadata is revalidated after capture and before cleanup","pgrep Claude candidates and per-candidate lsof cwd stdout commitments without public command output","state-root, claims-container and HMAC-key owner/group/mode are bound by the private control identity commitment; exact challenge child absence, HMAC-key bytes, raw envelope bytes and approved receipt digest are rechecked before the first authority-consuming persistent write; only exact identity-bound Git adapter scratch creation and mandatory cleanup may occur earlier"],"private_read_authority":["resolve and hash exact toolchain realpaths bound by public content digests","derive and read exact local content-v2 archive blobs directly from package-lock sha512 SRI without reading any npm cache index","directly capture live Git control, HEAD, index, refs, config, hooks and object-store evidence into a path-free keyed source receipt; Git children read only the sealed adapter and source CAS is repeated before cleanup","run pgrep only for Claude candidates and lsof only for each returned PID cwd; no machine-wide lsof or broader process absence claim","read the pre-existing state-root/claims directory identities and require the exact challenge child absent; no pre-existing ledger is read"],"private_vault_authorized":false,"private_write_authority":["create, seal and mandatorily remove only the exact dev/inode-bound /private/tmp Git metadata adapter scratch; cleanup uncertainty or residue is terminal and this scratch never consumes the challenge","create exact 0700 persistent challenge claim directory and create/append its exact 0600 ledger.jsonl","create exact same-filesystem stage and publish exact absent target with RENAME_EXCL"],"public_serialization_forbidden":["private absolute or home-relative locator","cache-root locator or direct-SRI content blob private locator","dirty/untracked inventory or its raw digest","environment values, command output or open-file locator list","ledger locator/raw bytes, raw HMAC key or user receipt body","private Vault locator, name, content or digest"],"retention":"persistent challenge claim and ledger are retained outside repo and never automatically deleted; failed stage and any published target are never automatically deleted; the private-temp Git adapter is never retained intentionally and success requires exact cleanup with residue_count zero"},"schema_binding":{"external_validator_profile":"JSON-Schema-draft-2020-12-strict-additionalProperties-false-format-annotation-plus-content-addressed-strict-UTC-calendar-and-duplicate-key-checker","preapproval_external_validation_required":true,"runtime_checkpoint":"after raw receipt/challenge/expiry verification and schema artifact hash verification, before any other envelope-controlled read, verifier-source compilation, subprocess or write","runtime_json_schema_execution_allowed":false,"runtime_manual_critical_field_checks_required":true,"runtime_schema_hash_binding_required":true,"schema_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json","schema_artifact_role":"pending-envelope-schema","schema_digest_must_equal_artifact_entry":true,"schema_id":"urn:canvas-learning-system:gov-01:toolchain-static-acquisition-pending-envelope:v2:draft","schema_raw_file_sha256":null,"validation_failure_action":"fail closed before any authorized write or verifier-source compilation"},"static_acquisition_contract":{"absent_control_paths":[".npmrc","npm-shrinkwrap.json","pnpm-lock.yaml","yarn.lock","bun.lock","bun.lockb"],"absent_control_pre_post_lstat_check_required":true,"compressed_blobs_memory_resident_before_write":true,"executor_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py","executor_sha256":null,"expected":null,"hidden_package_lock_generation_allowed":false,"lifecycle_execution_allowed":false,"network_allowed":false,"node_execution_allowed":false,"npm_execution_allowed":false,"openspec_execution_allowed":false,"openspec_scaffold_allowed":false,"payload_bytes_memory_resident_before_write":true,"protected_control_paths":["package.json","package-lock.json",".gitignore"],"protected_control_pre_post_hash_check_required":true,"stage_repo_relative":null,"target_repo_relative":"node_modules","verifier_artifact_path":"_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py","verifier_profile_version":"gov-01-toolchain-static-verifier-v2","verifier_sha256":null},"success_contract":{"archive_member_execution_count":0,"commit_allowed":false,"content_mismatches":0,"forbidden_control_paths_present":0,"governance_apply_allowed":false,"host_package_count":167,"javascript_execution_count":0,"lifecycle_execution_count":0,"maximum_state":"static-attested-unexecuted","missing_expected_entries":0,"network_attempt_count":0,"next_required_authorization":"new runtime-use envelope binding the final-tree receipt and a fresh single-use challenge","npm_node_npx_execution_count":0,"outside_scope_mutation_count":0,"payload_execution_allowed_after_success":false,"protected_control_paths_changed":0,"push_allowed":false,"sandbox_exec_execution_count":0,"target_created_count":1,"target_tree_must_equal_expected_merkle":true,"unexpected_entries":0}}'''


# Preserve the original literal only as the seed for the fully synchronized
# effective embedded template constructed after the exact adapter contract
# synchronizer is defined.
_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_BASE_JSON = (
    _PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON
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


def public_contract_receipt(domain: bytes, value: Any) -> str:
    return sha256(domain + b"\x00" + canonical_json(value))


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
            any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in value)
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


def pending_public_system_path_allowed(pointer: Tuple[Any, ...], value: str) -> bool:
    if value not in PENDING_ENVELOPE_PUBLIC_STRING_ALLOWLIST:
        return False
    if len(pointer) < 3 or pointer[0:2] != ("execution_plan", "evidence_command_templates"):
        return False
    # Public system paths are authorized only as an exact evidence-command
    # executable or argv element.  The same string in a tool version,
    # logical_id, artifact field or prose remains a privacy violation.
    return pointer[-1] == "executable" or "argv_allowlist" in pointer


def has_forbidden_pending_envelope_value(
    value: Any,
    pointer: Tuple[Any, ...] = (),
) -> bool:
    """Field-aware public-envelope privacy gate."""

    if isinstance(value, str):
        return has_forbidden_public_value(value) and not pending_public_system_path_allowed(pointer, value)
    if isinstance(value, list):
        return any(
            has_forbidden_pending_envelope_value(child, pointer + (index,))
            for index, child in enumerate(value)
        )
    if isinstance(value, dict):
        return any(
            has_forbidden_pending_envelope_value(key, pointer + ("<key>",))
            or has_forbidden_pending_envelope_value(child, pointer + (key,))
            for key, child in value.items()
        )
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
            "git_metadata_adapter_trust_boundary": GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1,
            "git_metadata_adapter_host_assurance": GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1,
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
            "product_state_automatic_cleanup_authorized": False,
            "temporary_adapter_cleanup_required": True,
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
        or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in path)
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


def envelope_repo_relative(args: argparse.Namespace) -> str:
    if not is_same_or_within(args.envelope, args.repo_root):
        fail(Exit.CONTRACT, "ENVELOPE_OUTSIDE_REPO")
    relative = os.path.relpath(args.envelope, args.repo_root).replace(os.sep, "/")
    validate_relative(relative, "ENVELOPE_CONTROL_PATH")
    if not relative.startswith(CONTROL_PREFIX):
        fail(Exit.CONTRACT, "ENVELOPE_OUTSIDE_CONTROL_PREFIX")
    return relative


def derive_repo_root_from_executor_v2() -> str:
    executor = os.path.realpath(__file__)
    suffix = os.sep + EXECUTOR_RELATIVE.replace("/", os.sep)
    if not executor.endswith(suffix):
        fail(Exit.CHECKER_DRIFT, "EXECUTOR_REPO_DERIVATION")
    repo_root = executor[: -len(suffix)]
    assert_absolute(repo_root, "DERIVED_REPO_ROOT")
    if has_forbidden_vault_component(repo_root):
        fail(Exit.PRIVACY, "DERIVED_REPO_ROOT_VAULT_LOCATOR")
    return repo_root


def bind_public_cli_runtime_args_v2(args: argparse.Namespace) -> str:
    generation_challenge = getattr(args, "generation_challenge", None)
    relative = expected_pending_envelope_relative(generation_challenge)
    repo_root = derive_repo_root_from_executor_v2()
    args.repo_root = repo_root
    args.envelope = os.path.join(repo_root, *relative.split("/"))
    args.cache_root = None
    args.state_root = None
    args.key_file = None
    return relative


def validate_public_runtime_boundaries_v2(args: argparse.Namespace) -> str:
    for value, label in ((args.repo_root, "REPO_ROOT"), (args.envelope, "ENVELOPE")):
        assert_absolute(value, label)
        if has_forbidden_vault_component(value):
            fail(Exit.PRIVACY, label + "_VAULT_LOCATOR")
    relative = envelope_repo_relative(args)
    if relative != expected_pending_envelope_relative(getattr(args, "generation_challenge", None)):
        fail(Exit.CONTRACT, "CLI_GENERATION_OUTPUT_PATH")
    return relative


def bind_private_runtime_args_v2(
    args: argparse.Namespace,
    generation_authorization: Mapping[str, Any],
) -> GenerationRuntimeArgsV2:
    derived = derive_generation_runtime_args_v2(args.repo_root, generation_authorization)
    if derived.envelope != args.envelope:
        fail(Exit.CONTRACT, "DERIVED_ENVELOPE_PATH")
    args.cache_root = derived.cache_root
    args.state_root = derived.state_root
    args.key_file = derived.key_file
    validate_locator_boundaries(args)
    return derived


def expected_pending_envelope_relative(generation_challenge: str) -> str:
    if (
        not isinstance(generation_challenge, str)
        or GENERATION_CHALLENGE_RE.fullmatch(generation_challenge) is None
    ):
        fail(Exit.CONTRACT, "GENERATION_CHALLENGE_FORMAT")
    return CONTROL_PREFIX + PENDING_ENVELOPE_BASENAME_PREFIX + generation_challenge + ".json"


def validate_envelope_path_binding(
    args: argparse.Namespace,
    envelope: Mapping[str, Any],
    relative: Optional[str] = None,
) -> str:
    actual = envelope_repo_relative(args) if relative is None else relative
    generation = envelope.get("generation_authorization")
    if not isinstance(generation, Mapping):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_SCHEMA")
    generation_challenge = generation.get("approval_challenge_id")
    expected = expected_pending_envelope_relative(generation_challenge)
    preimage = envelope.get("authorization_preimage")
    if (
        actual != expected
        or generation.get("generated_acquisition_envelope_repo_relative_path") != expected
        or not isinstance(preimage, Mapping)
        or preimage.get("envelope_repo_relative_path") != expected
        or preimage.get("envelope_git_status_exclusion_profile") != PENDING_ENVELOPE_GIT_EXCLUSION_PROFILE
    ):
        fail(Exit.CONTRACT, "ENVELOPE_PATH_BINDING")
    return actual


def validate_locator_boundaries(args: argparse.Namespace) -> str:
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
        (args.cache_root, args.envelope, "CACHE_ENVELOPE_OVERLAP"),
        (args.state_root, args.envelope, "STATE_ENVELOPE_OVERLAP"),
        (args.key_file, args.envelope, "KEY_ENVELOPE_OVERLAP"),
    )
    for left, right, label in separated:
        if paths_overlap(left, right):
            fail(Exit.PRIVATE_STATE, label)
    expected_key = os.path.join(args.state_root, "hmac.key")
    if args.key_file != expected_key:
        fail(Exit.PRIVATE_STATE, "STATE_KEY_EXACT_CHILD")
    return envelope_repo_relative(args)


def derive_generation_runtime_args_v2(
    repo_root: str,
    generation_authorization: Mapping[str, Any],
) -> GenerationRuntimeArgsV2:
    """Derive every private generation locator after public GEN approval.

    The generator CLI supplies only a public GEN challenge and receipt.  This
    helper derives the repository-relative control-preparation contract from
    the content-addressed executor, then derives state/key/cache/output paths;
    no caller-provided private locator participates in the authority.
    """
    repo = assert_absolute(repo_root, "GENERATION_REPO_ROOT")
    if has_forbidden_vault_component(repo):
        fail(Exit.PRIVACY, "GENERATION_REPO_ROOT_VAULT_LOCATOR")
    generation = require_exact_object(
        generation_authorization,
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_AUTHORIZATION",
    )
    challenge = generation.get("approval_challenge_id")
    expected_output = expected_pending_envelope_relative(challenge)
    if generation.get("generated_acquisition_envelope_repo_relative_path") != expected_output:
        fail(Exit.CONTRACT, "GENERATION_OUTPUT_PATH")
    control_path = os.path.join(
        repo,
        CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.json",
    )
    control_raw, _control_meta = read_absolute_regular(
        control_path,
        "CONTROL_PREPARATION_ENVELOPE",
        MAX_JSON_BYTES,
    )
    if not hmac.compare_digest(sha256(control_raw), CONTROL_PREPARATION_ENVELOPE_RAW_SHA256):
        fail(Exit.CHECKER_DRIFT, "CONTROL_PREPARATION_ENVELOPE_DRIFT")
    control = parse_json_bytes(control_raw, "CONTROL_PREPARATION_ENVELOPE")
    if not isinstance(control, dict) or canonical_json(control) != control_raw:
        fail(Exit.CONTRACT, "CONTROL_PREPARATION_ENVELOPE_CANONICAL")
    target = control.get("target")
    if not isinstance(target, dict):
        fail(Exit.CONTRACT, "CONTROL_PREPARATION_TARGET")
    state_root = target.get("absolute_path")
    owner = target.get("expected_created_owner")
    if (
        not isinstance(state_root, str)
        or not isinstance(owner, dict)
        or type(owner.get("uid")) is not int
        or type(owner.get("gid")) is not int
        or target.get("root_mode") != "0700"
        or target.get("claims_mode") != "0700"
        or target.get("key_mode") != "0600"
        or target.get("receipt_mode") != "0600"
    ):
        fail(Exit.CONTRACT, "CONTROL_PREPARATION_TARGET_PROFILE")
    assert_absolute(state_root, "GENERATION_STATE_ROOT")
    if has_forbidden_vault_component(state_root):
        fail(Exit.PRIVACY, "GENERATION_STATE_ROOT_VAULT_LOCATOR")
    try:
        account = pwd.getpwuid(owner["uid"])
    except (KeyError, OSError):
        fail(Exit.PRIVATE_STATE, "GENERATION_ACCOUNT_LOOKUP")
    home = assert_absolute(account.pw_dir, "GENERATION_ACCOUNT_HOME")
    cache_root = os.path.normpath(os.path.join(home, ".npm"))
    assert_absolute(cache_root, "GENERATION_CACHE_ROOT")
    if has_forbidden_vault_component(cache_root):
        fail(Exit.PRIVACY, "GENERATION_CACHE_ROOT_VAULT_LOCATOR")
    key_file = os.path.join(state_root, "hmac.key")
    output_path = os.path.join(repo, *expected_output.split("/"))
    result = GenerationRuntimeArgsV2(repo, cache_root, state_root, key_file, output_path)
    validate_locator_boundaries(argparse.Namespace(**result._asdict()))
    return result


def revalidate_generation_runtime_args_v2(
    runtime_args: GenerationRuntimeArgsV2,
    generation_authorization: Mapping[str, Any],
) -> str:
    if not isinstance(runtime_args, GenerationRuntimeArgsV2):
        fail(Exit.CONTRACT, "GENERATION_RUNTIME_ARGS_TYPE")
    derived = derive_generation_runtime_args_v2(runtime_args.repo_root, generation_authorization)
    if derived != runtime_args:
        fail(Exit.CONTRACT, "GENERATION_RUNTIME_ARGS_DRIFT")
    return envelope_repo_relative(argparse.Namespace(**runtime_args._asdict()))


def verify_control_preparation_projection_v2(
    runtime_args: GenerationRuntimeArgsV2,
) -> Dict[str, Any]:
    """Revalidate the retained control tree; the on-disk receipt is not authority."""
    state_meta = assert_no_symlink_components(runtime_args.state_root, "CONTROL_PREPARATION_STATE")
    if (
        not stat.S_ISDIR(state_meta.st_mode)
        or stat.S_IMODE(state_meta.st_mode) != 0o700
        or state_meta.st_uid != os.getuid()
    ):
        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_STATE_POLICY")
    state_fd = open_directory(runtime_args.state_root, "CONTROL_PREPARATION_STATE")
    try:
        try:
            names = sorted(os.listdir(state_fd), key=lambda item: item.encode("utf-8"))
        except OSError:
            fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_STATE_LIST")
        if names != ["claims", "control-prep-receipt.json", "hmac.key"]:
            fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_STATE_CHILDREN")
        claims_meta = os.stat("claims", dir_fd=state_fd, follow_symlinks=False)
        key_meta = os.stat("hmac.key", dir_fd=state_fd, follow_symlinks=False)
        receipt_meta = os.stat("control-prep-receipt.json", dir_fd=state_fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(claims_meta.st_mode)
            or stat.S_IMODE(claims_meta.st_mode) != 0o700
            or claims_meta.st_uid != state_meta.st_uid
            or claims_meta.st_gid != state_meta.st_gid
            or not stat.S_ISREG(key_meta.st_mode)
            or stat.S_IMODE(key_meta.st_mode) != 0o600
            or key_meta.st_uid != state_meta.st_uid
            or key_meta.st_gid != state_meta.st_gid
            or key_meta.st_nlink != 1
            or key_meta.st_size != 32
            or not stat.S_ISREG(receipt_meta.st_mode)
            or stat.S_IMODE(receipt_meta.st_mode) != 0o600
            or receipt_meta.st_uid != state_meta.st_uid
            or receipt_meta.st_gid != state_meta.st_gid
            or receipt_meta.st_nlink != 1
        ):
            fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_CHILD_POLICY")
        claims_fd = os.open(
            "claims",
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=state_fd,
        )
        try:
            for claim_name in os.listdir(claims_fd):
                is_acquisition_claim = (
                    isinstance(claim_name, str) and CHALLENGE_RE.fullmatch(claim_name) is not None
                )
                is_generation_claim = (
                    isinstance(claim_name, str)
                    and GENERATION_CLAIM_NAME_RE.fullmatch(claim_name) is not None
                )
                if not is_acquisition_claim and not is_generation_claim:
                    fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_HISTORICAL_CLAIM_NAME")
                claim_meta = os.stat(claim_name, dir_fd=claims_fd, follow_symlinks=False)
                if (
                    not stat.S_ISDIR(claim_meta.st_mode)
                    or stat.S_IMODE(claim_meta.st_mode) != 0o700
                    or claim_meta.st_uid != state_meta.st_uid
                    or claim_meta.st_gid != state_meta.st_gid
                ):
                    fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_HISTORICAL_CLAIM_POLICY")
                claim_fd = os.open(
                    claim_name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=claims_fd,
                )
                try:
                    claim_children = sorted(os.listdir(claim_fd))
                    permitted_children = (
                        ([], ["ledger.jsonl"])
                        if is_acquisition_claim
                        else ([], ["generation-record.json"])
                    )
                    if claim_children not in permitted_children:
                        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_HISTORICAL_CLAIM_CHILDREN")
                    if claim_children:
                        record_name = "ledger.jsonl" if is_acquisition_claim else "generation-record.json"
                        record_meta = os.stat(record_name, dir_fd=claim_fd, follow_symlinks=False)
                        if (
                            not stat.S_ISREG(record_meta.st_mode)
                            or stat.S_IMODE(record_meta.st_mode) != 0o600
                            or record_meta.st_uid != state_meta.st_uid
                            or record_meta.st_gid != state_meta.st_gid
                            or record_meta.st_nlink != 1
                        ):
                            fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_HISTORICAL_RECORD_POLICY")
                finally:
                    os.close(claim_fd)
        finally:
            os.close(claims_fd)
        receipt_fd = os.open(
            "control-prep-receipt.json",
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=state_fd,
        )
        try:
            receipt_raw = read_fd(receipt_fd, MAX_JSON_BYTES, "CONTROL_PREPARATION_RECEIPT")
        finally:
            os.close(receipt_fd)
    except ContractError:
        raise
    except OSError:
        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_TREE")
    finally:
        os.close(state_fd)
    receipt = parse_json_bytes(receipt_raw, "CONTROL_PREPARATION_RECEIPT")
    if not isinstance(receipt, dict) or canonical_json(receipt) != receipt_raw:
        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_RECEIPT_CANONICAL")
    evidence = receipt.get("evidence_sha256")
    body = {key: value for key, value in receipt.items() if key != "evidence_sha256"}
    if (
        not isinstance(evidence, str)
        or SHA256_RE.fullmatch(evidence) is None
        or not hmac.compare_digest(
            evidence,
            sha256(CONTROL_PREPARATION_EVIDENCE_DOMAIN + canonical_json(body)),
        )
        or body.get("schema_version") != "gov-01-toolchain-control-prep-evidence-v1"
        or body.get("evidence_state") != "CONTROL-PREPARED-CANDIDATE"
        or body.get("derived_state_if_full_tree_verifies") != "CONTROL-PREPARED"
        or body.get("candidate_is_independently_authoritative") is not False
        or body.get("approved_receipt_digest") != CONTROL_PREPARATION_RECEIPT_DIGEST
        or body.get("envelope_raw_sha256") != CONTROL_PREPARATION_ENVELOPE_RAW_SHA256
        or body.get("single_use_state") != "CONSUMED-BY-DURABLE-SIBLING-CLAIM"
        or body.get("acquisition_challenge_claim_state") != "ABSENT"
        or body.get("private_preimage_sidecar_state") != "ABSENT"
        or body.get("maximum_state") != "CONTROL-PREPARED"
    ):
        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_RECEIPT_SEMANTICS")
    control_raw, _ = read_absolute_regular(
        os.path.join(
            runtime_args.repo_root,
            CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.json",
        ),
        "CONTROL_PREPARATION_ENVELOPE",
        MAX_JSON_BYTES,
    )
    control = parse_json_bytes(control_raw, "CONTROL_PREPARATION_ENVELOPE")
    target = control.get("target") if isinstance(control, dict) else None
    control_challenge = control.get("approval_challenge_id") if isinstance(control, dict) else None
    durable_path = target.get("durable_claim_absolute_path") if isinstance(target, dict) else None
    if (
        not isinstance(durable_path, str)
        or not isinstance(control_challenge, str)
        or CONTROL_PREPARATION_CHALLENGE_RE.fullmatch(control_challenge) is None
        or body.get("approval_challenge_id") != control_challenge
    ):
        fail(Exit.CONTRACT, "CONTROL_PREPARATION_DURABLE_CLAIM_PATH")
    durable_raw, durable_meta = read_absolute_regular(
        durable_path,
        "CONTROL_PREPARATION_DURABLE_CLAIM",
        MAX_JSON_BYTES,
    )
    if (
        stat.S_IMODE(durable_meta.st_mode) != 0o600
        or durable_meta.st_uid != state_meta.st_uid
        or durable_meta.st_gid != state_meta.st_gid
        or durable_meta.st_nlink != 1
        or body.get("durable_claim_raw_sha256") != sha256(durable_raw)
    ):
        fail(Exit.PRIVATE_STATE, "CONTROL_PREPARATION_DURABLE_CLAIM")
    return {
        "control_preparation_result_raw_sha256": sha256(receipt_raw),
        "control_preparation_evidence_receipt_sha256": evidence,
        "control_preparation_approval_challenge_id": control_challenge,
        "control_preparation_state": "CONTROL-PREPARED-FULL-TREE-REVALIDATED-PASS",
    }


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
    if any(any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in part) for part in components):
        fail(Exit.UNSAFE_PATH, label + "_CONTROL")
    for component in components:
        folded = unicodedata.normalize("NFC", component).casefold()
        if folded == ".git":
            fail(Exit.UNSAFE_PATH, label + "_GIT")
        if forbid_vault:
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


def validate_locator_commitment_projection_v2(value: Any) -> Dict[str, Dict[str, str]]:
    expected_labels = {
        "repo_root": "repo-root",
        "cache_root": "npm-cache",
        "state_root": "state-root",
        "key_file": "hmac-key",
        "envelope": "envelope",
    }
    if not isinstance(value, Mapping) or set(value) != set(expected_labels):
        fail(Exit.CONTRACT, "LOCATOR_COMMITMENTS")
    result: Dict[str, Dict[str, str]] = {}
    for name, expected_label in expected_labels.items():
        entry = value.get(name)
        if (
            not isinstance(entry, Mapping)
            or set(entry) != {"label", "commitment"}
            or entry.get("label") != expected_label
        ):
            fail(Exit.CONTRACT, "LOCATOR_COMMITMENT_ENTRY")
        commitment = require_sha256(entry.get("commitment"), "LOCATOR_COMMITMENT")
        result[name] = {"label": expected_label, "commitment": commitment}
    return result


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
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        fail(Exit.CONTRACT, label + "_FORMAT")
    return parsed.replace(tzinfo=_datetime.timezone.utc)


def utc_now() -> _datetime.datetime:
    return _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)


def validate_envelope_temporal_contract(
    envelope: Mapping[str, Any],
    now: Optional[_datetime.datetime] = None,
) -> Tuple[_datetime.datetime, _datetime.datetime]:
    current = utc_now() if now is None else now
    if current.tzinfo is None or current.utcoffset() != _datetime.timedelta(0) or current.microsecond != 0:
        fail(Exit.CONTRACT, "CURRENT_TIME_FORMAT")
    challenge = envelope.get("approval_challenge_id")
    if not isinstance(challenge, str) or CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "CHALLENGE_FORMAT")
    census_at = parse_utc(envelope.get("census_at_utc"), "CENSUS_AT")
    expiry = parse_utc(envelope.get("not_after_utc"), "EXPIRY")
    if challenge.split("-")[2] != census_at.strftime("%Y%m%d"):
        fail(Exit.CONTRACT, "CHALLENGE_CENSUS_DATE")
    if census_at > current + _datetime.timedelta(minutes=5):
        fail(Exit.CONTRACT, "CENSUS_FUTURE_SKEW")
    if expiry <= current:
        fail(Exit.EXPIRED, "ENVELOPE_EXPIRED")
    if expiry <= census_at or expiry - census_at > _datetime.timedelta(hours=24):
        fail(Exit.CONTRACT, "ENVELOPE_TTL")
    return census_at, expiry


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
        (
            "toolchain_assurance",
            "pre_exec_launcher_attested",
            "python_isolation_flags_required",
            "git_metadata_adapter_trust_boundary",
            "git_metadata_adapter_host_assurance",
        )
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
            "retry_authorized", "public_success_attestation_allowed",
            "product_state_automatic_cleanup_authorized", "temporary_adapter_cleanup_required",
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
    cross(
        runtime.get("git_metadata_adapter_trust_boundary")
        == GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1,
        "GIT_METADATA_ADAPTER_TRUST_BOUNDARY",
    )
    cross(
        runtime.get("git_metadata_adapter_host_assurance")
        == GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1,
        "GIT_METADATA_ADAPTER_HOST_ASSURANCE",
    )
    cross(authority.get("temporary_adapter_cleanup_required") is True, "TEMPORARY_ADAPTER_CLEANUP_REQUIRED")
    for denied in (
        "product_state_automatic_cleanup_authorized", "openspec_execution_allowed", "openspec_scaffold_allowed",
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
        cross(
            type(authority.get("retry_authorized")) is bool
            and authority.get("public_success_attestation_allowed") is False,
            "FAILURE_AUTHORITY",
        )
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
        cleanup_uncertain = error_detail.startswith("GIT_ADAPTER_CLEANUP_")
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
        elif mode in ("census", "verify") and authority.get("retry_authorized") is True:
            # Read-only stdout intentionally omits the approval pair, but a
            # retry claim is valid only when the in-process trusted sidecar
            # proves that the receipt and challenge were already bound.
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
        elif mode in ("census", "verify") and authority.get("retry_authorized") is True:
            cross(
                failure_authority is not None
                and isinstance(failure_authority.get("approval_challenge_id"), str)
                and CHALLENGE_RE.fullmatch(failure_authority["approval_challenge_id"]) is not None,
                "READ_ONLY_FAILURE_RUN_CHALLENGE",
            )
            require_sha256(
                failure_authority.get("receipt_digest"),
                "PUBLIC_RESULT_READ_ONLY_FAILURE_RUN_RECEIPT",
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
            cross(result.get("phase") in ("entry-fail-closed", "read-only-fail-closed"), "READ_ONLY_FAILURE_PHASE")
            cross(terminal == read_only_terminal_state(), "READ_ONLY_FAILURE_TERMINAL")
            cross(
                retention.get("private_state_inspection_required") is cleanup_uncertain,
                "READ_ONLY_FAILURE_RETENTION",
            )
            if result.get("phase") == "entry-fail-closed":
                cross(not gates, "READ_ONLY_ENTRY_GATES")
                cross(
                    authority.get("retry_authorized") is False
                    and authority.get("next_required_authority")
                    == (GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY),
                    "READ_ONLY_ENTRY_AUTHORITY",
                )
            else:
                execution_prefix_length(read_only_execution_order, "READ_ONLY_FAILURE_GATE")
                retry_bound = (
                    failure_authority is not None
                    and "approval_challenge_id" in failure_authority
                    and "receipt_digest" in failure_authority
                )
                cross(
                    authority.get("retry_authorized") is retry_bound
                    and authority.get("next_required_authority")
                    == (
                        PRECLAIM_RETRY_AUTHORITY
                        if retry_bound
                        else GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY
                    ),
                    "READ_ONLY_FAILURE_NEXT_AUTHORITY",
                )
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
            cross(authority.get("retry_authorized") is False, "PRIVACY_FAILURE_RETRY")
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
            cross(
                retention.get("private_state_inspection_required") is cleanup_uncertain,
                "UNKNOWN_FAILURE_RETENTION",
            )
            cross(authority.get("retry_authorized") is False, "UNKNOWN_FAILURE_RETRY")
            cross(
                authority.get("next_required_authority")
                == (GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY),
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
            cross(authority.get("retry_authorized") is False, "ACQUIRE_ENTRY_RETRY")
            cross(
                authority.get("next_required_authority")
                == (GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY),
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
                cross(challenge_state == "preclaim-pending", "ACQUIRE_PRECLAIM_CHALLENGE")
                cross(ledger_state == "not-created", "ACQUIRE_PRECLAIM_LEDGER")
                cross(
                    retention.get("private_state_inspection_required") is cleanup_uncertain,
                    "ACQUIRE_PRECLAIM_RETENTION",
                )
                cross(
                    authority.get("retry_authorized") is (not cleanup_uncertain)
                    and authority.get("next_required_authority")
                    == (
                        GIT_ADAPTER_CLEANUP_AUTHORITY
                        if cleanup_uncertain
                        else PRECLAIM_RETRY_AUTHORITY
                    ),
                    "ACQUIRE_PRECLAIM_AUTHORITY",
                )
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
                cross(
                    authority.get("retry_authorized") is False
                    and authority.get("next_required_authority")
                    == (GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else RETAINED_STATE_AUTHORITY),
                    "ACQUIRE_CLAIM_AUTHORITY",
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
                retention.get("private_state_inspection_required")
                is (claim_state != "not-created" or cleanup_uncertain),
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
                authority.get("retry_authorized") is False
                and authority.get("next_required_authority") == RETAINED_STATE_AUTHORITY,
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
        self.adapter_cleanup_state = "not-created"
        self.adapter_residue_count = 0

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

    def adapter_cleanup_uncertain(self) -> None:
        self.adapter_cleanup_state = "residue-or-uncertain"
        self.adapter_residue_count = 1

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
        # The challenge is consumed only by the exclusive persistent claim.
        # A preclaim failure therefore retains the initial pending state; its
        # public authority object separately constrains retry to an unexpired,
        # byte-exact receipt-bound input set.
        return self.projection()


def runtime_assurance_projection(toolchain: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "toolchain_assurance": "runtime-self-attested-not-pre-exec",
        "pre_exec_launcher_attested": False,
        "python_isolation_flags_required": ["-I", "-S", "-B"],
        "git_metadata_adapter_trust_boundary": GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1,
        "git_metadata_adapter_host_assurance": GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1,
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
            "retained_product_state_automatic_cleanup_allowed": False,
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
    # This must precede verifier compilation, subprocess resolution and every
    # private-state read.  Only the six frozen public argv literals are exempt
    # from the generic locator detector; role-specific schema/manual checks
    # prevent those literals from being moved into free-text fields.
    if has_forbidden_pending_envelope_value(value):
        fail(Exit.PRIVACY, "ENVELOPE_PUBLIC_PRIVACY")
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
    validate_envelope_temporal_contract(value)
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


def expected_tool_version(role: str) -> str:
    if role in ("python-interpreter", "python-stdlib-tree"):
        version = platform.python_version()
        if re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version) is None:
            fail(Exit.RUNTIME, "PYTHON_VERSION_PROFILE")
        return version
    version = TOOLCHAIN_FIXED_VERSION_BY_ROLE.get(role)
    if version is None:
        fail(Exit.CONTRACT, "TOOLCHAIN_VERSION_ROLE")
    return version


def validate_tool_identity(entry: Mapping[str, Any], role: str) -> None:
    if entry.get("logical_id") != TOOLCHAIN_LOGICAL_ID_BY_ROLE.get(role):
        fail(Exit.CONTRACT, "FROZEN_TOOL_LOGICAL_ID")
    if entry.get("version") != expected_tool_version(role):
        fail(Exit.CONTRACT, "FROZEN_TOOL_VERSION")


def require_zero(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != 0:
        fail(Exit.CONTRACT, label + "_ZERO")


GATE_PASS_EVIDENCE_FIELDS: Dict[str, Tuple[str, ...]] = {
    "G00": (
        "schema_sha256", "schema_bytes", "schema_count", "schema_bundle_receipt_sha256",
        "manual_critical_contract_passed",
    ),
    "G01": (
        "challenge_claim_created",
        "ledger_receipt_consumed_recorded",
        "first_authority_consuming_persistent_write_contract",
    ),
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
            "first_authority_consuming_persistent_write_contract": "exclusive-0700-challenge-mkdir",
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
            "authorized_subprocess_role_count": len(AUTHORIZED_SUBPROCESS_ROLES),
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


def pending_lock_observation_expected_structure(
    expected: Mapping[str, Any],
) -> Dict[str, Any]:
    """Project the validated frozen expected structure onto lock observations."""
    resolution = expected["resolution"]
    tree = expected["tree"]
    projection = {
        "host_selected_package_count": expected["selected_package_count"],
        "host_selected_cache_bytes": expected["compressed_bytes"],
        "host_bin_link_count": expected["bin_link_count"],
        "expected_archive_member_count": expected["raw_member_count"],
        "expected_resolved_tree_entry_count": tree["entry_count"],
        "content_receipt_sha256": expected["content_receipt_sha256"],
        "ustar_closure_sha256": expected["ustar_closure_sha256"],
        "resolution_receipt_sha256": resolution["sha256"],
        "expected_tree_sha256": tree["sha256"],
    }
    if frozenset(projection) != LOCK_OBSERVATION_FIELDS:
        fail(Exit.INTERNAL, "LOCK_OBSERVATION_PROJECTION")
    return projection


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


def validate_pending_template_scalar_types(template: Any, value: Any) -> None:
    """Enforce exact JSON scalar types frozen by the synchronized template.

    JSON booleans are subclasses of ``int`` in Python, so equality and broad
    ``isinstance(..., int)`` checks cannot preserve the schema intersection.
    ``None`` entries are deliberate dynamic placeholders and therefore do not
    impose a type here; their production consumers validate the filled value.
    """
    expected_type = type(template)
    if expected_type in (str, bool, int, float):
        if type(value) is not expected_type:
            fail(Exit.CONTRACT, "MANUAL_TEMPLATE_SCALAR_TYPE")
        return
    if template is None:
        return
    if isinstance(template, dict):
        if not isinstance(value, Mapping):
            return
        for key, child in template.items():
            if key in value:
                validate_pending_template_scalar_types(child, value[key])
        return
    if isinstance(template, list):
        if not isinstance(value, list):
            return
        for index, child in enumerate(template):
            if index < len(value):
                validate_pending_template_scalar_types(child, value[index])


def validate_manual_envelope_contract(
    envelope: Mapping[str, Any],
    now: Optional[_datetime.datetime] = None,
) -> None:
    if has_forbidden_pending_envelope_value(envelope):
        fail(Exit.PRIVACY, "ENVELOPE_PUBLIC_PRIVACY")
    synchronized_template = json.loads(_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON)
    if not isinstance(synchronized_template, dict):
        fail(Exit.INTERNAL, "PENDING_TEMPLATE")
    validate_pending_template_scalar_types(synchronized_template, envelope)
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
    validate_envelope_temporal_contract(envelope, now=now)
    approval = require_exact_object(
        envelope.get("approval_receipt_contract"),
        "required_user_reference receipt_must_match_raw_envelope_bytes challenge_must_match "
        "receipt_before_first_authority_consuming_persistent_write "
        "first_authority_consuming_persistent_write authority_is_exact authority_expansion_allowed".split(),
        "APPROVAL_RECEIPT_CONTRACT",
    )
    for key in (
        "receipt_must_match_raw_envelope_bytes",
        "challenge_must_match",
        "receipt_before_first_authority_consuming_persistent_write",
        "authority_is_exact",
    ):
        if approval.get(key) is not True:
            fail(Exit.CONTRACT, "APPROVAL_RECEIPT_AUTHORITY")
    if approval.get("authority_expansion_allowed") is not False:
        fail(Exit.CONTRACT, "APPROVAL_EXPANSION")
    if (
        approval.get("first_authority_consuming_persistent_write")
        != FIRST_AUTHORITY_CONSUMING_PERSISTENT_WRITE_V2
    ):
        fail(Exit.CONTRACT, "APPROVAL_FIRST_PERSISTENT_WRITE")
    predecessor = require_exact_object(
        envelope.get("predecessor"),
        PREDECESSOR_FIELDS,
        "PREDECESSOR",
    )
    for key, value in predecessor.items():
        if key.endswith("sha256"):
            require_sha256(value, "PREDECESSOR_" + key.upper())
    predecessor_constants = {
        "profile": "gov01-static-acquisition-predecessor-chain-v2",
        "first_approval_envelope_raw_sha256": FIRST_APPROVAL_ENVELOPE_RAW_SHA256,
        "first_approval_receipt_digest": FIRST_RECEIPT_DOMAIN_SHA256,
        "bootstrap_patch_raw_sha256": BOOTSTRAP_PATCH_RAW_SHA256,
        "bootstrap_commit_oid": BOOTSTRAP_COMMIT_OID,
        "control_preparation_envelope_raw_sha256": CONTROL_PREPARATION_ENVELOPE_RAW_SHA256,
        "control_preparation_envelope_receipt_digest": CONTROL_PREPARATION_RECEIPT_DIGEST,
        "control_preparation_state": "CONTROL-PREPARED-FULL-TREE-REVALIDATED-PASS",
    }
    for key, expected in predecessor_constants.items():
        if predecessor.get(key) != expected:
            fail(Exit.CONTRACT, "PREDECESSOR_" + key.upper())
    for key in (
        "control_preparation_result_raw_sha256",
        "control_preparation_evidence_receipt_sha256",
        "generation_authorization_receipt_digest",
        "generation_authorization_envelope_raw_sha256",
    ):
        require_sha256(predecessor.get(key), "PREDECESSOR_" + key.upper())
    control_preparation_challenge = predecessor.get("control_preparation_approval_challenge_id")
    if (
        not isinstance(control_preparation_challenge, str)
        or CONTROL_PREPARATION_CHALLENGE_RE.fullmatch(control_preparation_challenge) is None
    ):
        fail(Exit.CONTRACT, "PREDECESSOR_CONTROL_PREPARATION_CHALLENGE")
    for key in (
        "bootstrap_commit_oid",
        "generation_authorization_parent_commit_oid",
        "generation_authorization_parent_tree_oid",
        "generation_authorization_commit_oid",
        "generation_authorization_tree_oid",
    ):
        value = predecessor.get(key)
        if not isinstance(value, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
            fail(Exit.CONTRACT, "PREDECESSOR_OID")
    generation_predecessor_challenge = predecessor.get("generation_authorization_challenge_id")
    if (
        not isinstance(generation_predecessor_challenge, str)
        or GENERATION_CHALLENGE_RE.fullmatch(generation_predecessor_challenge) is None
    ):
        fail(Exit.CONTRACT, "PREDECESSOR_GENERATION_CHALLENGE")
    generation = require_exact_object(
        envelope.get("generation_authorization"),
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_AUTHORIZATION",
    )
    generation_challenge = generation.get("approval_challenge_id")
    if (
        generation.get("profile") != "gov01-static-envelope-generation-authority-v1"
        or not isinstance(generation_challenge, str)
        or GENERATION_CHALLENGE_RE.fullmatch(generation_challenge) is None
        or generation.get("receipt_domain_profile")
        != "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-generation-envelope-bytes)"
        or generation.get("commit_transition_profile")
        != "single parent commit changing exactly the generation approval envelope path from ABSENT to the approved canonical raw bytes"
        or generation.get("state") != "approved-single-path-commit"
        or generation.get("generation_claim_required") is not True
        or generation.get("generation_claim_profile") != GENERATION_CLAIM_PROFILE
        or generation.get("generation_claim_record_profile") != GENERATION_CLAIM_RECORD_PROFILE
        or generation.get("generation_claim_retention") != GENERATION_CLAIM_RETENTION
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_PROFILE")
    expected_generation_path = (
        CONTROL_PREFIX
        + "GOV-01-toolchain-static-envelope-generation-envelope-v1."
        + generation_challenge
        + ".json"
    )
    expected_output_path = expected_pending_envelope_relative(generation_challenge)
    if (
        generation.get("approval_envelope_repo_relative_path") != expected_generation_path
        or generation.get("generated_acquisition_envelope_repo_relative_path") != expected_output_path
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_PATH")
    for key in ("raw_envelope_sha256", "receipt_digest"):
        require_sha256(generation.get(key), "GENERATION_AUTHORIZATION_" + key.upper())
    for key in (
        "authorization_parent_commit_oid",
        "authorization_parent_tree_oid",
        "authorization_commit_oid",
        "authorization_tree_oid",
    ):
        value = generation.get(key)
        if not isinstance(value, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
            fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_OID")
    generation_predecessor_bindings = {
        "generation_authorization_envelope_raw_sha256": generation.get("raw_envelope_sha256"),
        "generation_authorization_receipt_digest": generation.get("receipt_digest"),
        "generation_authorization_challenge_id": generation.get("approval_challenge_id"),
        "generation_authorization_parent_commit_oid": generation.get("authorization_parent_commit_oid"),
        "generation_authorization_parent_tree_oid": generation.get("authorization_parent_tree_oid"),
        "generation_authorization_commit_oid": generation.get("authorization_commit_oid"),
        "generation_authorization_tree_oid": generation.get("authorization_tree_oid"),
    }
    if any(predecessor.get(key) != value for key, value in generation_predecessor_bindings.items()):
        fail(Exit.CONTRACT, "PREDECESSOR_GENERATION_RECEIPT_BINDING")
    predecessor_body = {key: predecessor[key] for key in PREDECESSOR_FIELDS if key != "predecessor_chain_receipt_sha256"}
    expected_predecessor_chain = sha256(
        PREDECESSOR_CHAIN_DOMAIN + b"\x00" + canonical_json(predecessor_body)
    )
    if not hmac.compare_digest(
        str(predecessor.get("predecessor_chain_receipt_sha256")),
        expected_predecessor_chain,
    ):
        fail(Exit.CONTRACT, "PREDECESSOR_CHAIN_RECEIPT")
    artifacts = envelope.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(PENDING_STATIC_ARTIFACT_SPECS) + 1:
        fail(Exit.CONTRACT, "MANUAL_ARTIFACT_COUNT")
    seen_paths = set()
    role_counts: Dict[str, int] = {}
    allowed_roles = {role for role, _path in PENDING_STATIC_ARTIFACT_SPECS} | {GENERATION_APPROVAL_ROLE}
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
    actual_static_specs = tuple((entry.get("role"), entry.get("path")) for entry in artifacts[:-1])
    if actual_static_specs != PENDING_STATIC_ARTIFACT_SPECS:
        fail(Exit.CONTRACT, "ARTIFACT_ROLE_PATH_BINDING")
    generation_approval = artifacts[-1]
    if (
        generation_approval.get("role") != GENERATION_APPROVAL_ROLE
        or not isinstance(generation_approval.get("path"), str)
        or GENERATION_APPROVAL_PATH_RE.fullmatch(generation_approval["path"]) is None
    ):
        fail(Exit.CONTRACT, "ARTIFACT_GENERATION_APPROVAL_BINDING")
    if (
        generation_approval.get("path") != generation.get("approval_envelope_repo_relative_path")
        or generation_approval.get("raw_file_sha256") != generation.get("raw_envelope_sha256")
    ):
        fail(Exit.CONTRACT, "ARTIFACT_GENERATION_APPROVAL_CROSS_BINDING")
    artifact_by_role = {entry.get("role"): entry for entry in artifacts}
    predecessor_artifact_bindings = {
        "first-receipt-envelope": predecessor.get("first_approval_envelope_raw_sha256"),
        "bootstrap-patch": predecessor.get("bootstrap_patch_raw_sha256"),
        "control-prep-envelope": predecessor.get("control_preparation_envelope_raw_sha256"),
    }
    for role, expected_digest in predecessor_artifact_bindings.items():
        if artifact_by_role.get(role, {}).get("raw_file_sha256") != expected_digest:
            fail(Exit.CONTRACT, "PREDECESSOR_ARTIFACT_" + role.upper().replace("-", "_"))
    if any(role_counts.get(role) != 1 for role in allowed_roles):
        fail(Exit.CONTRACT, "ARTIFACT_REQUIRED_ROLE")
    preimage = require_exact_object(
        envelope.get("authorization_preimage"), AUTHORIZATION_PREIMAGE_FIELDS, "AUTHORIZATION_PREIMAGE"
    )
    expected_envelope_path = expected_pending_envelope_relative(generation_challenge)
    if (
        preimage.get("envelope_repo_relative_path") != expected_envelope_path
        or preimage.get("envelope_git_status_exclusion_profile") != PENDING_ENVELOPE_GIT_EXCLUSION_PROFILE
    ):
        fail(Exit.CONTRACT, "ENVELOPE_PATH_BINDING")
    if any(entry.get("path") == expected_envelope_path for entry in artifacts):
        fail(Exit.CONTRACT, "ARTIFACT_ENVELOPE_SELF_REFERENCE")
    object_format = preimage.get("git_object_format")
    if object_format not in ("sha1", "sha256"):
        fail(Exit.CONTRACT, "PREIMAGE_OBJECT_FORMAT")
    oid_length = 40 if object_format == "sha1" else 64
    for key in ("head_commit_oid", "head_tree_oid"):
        value = preimage.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{%d}" % oid_length, value):
            fail(Exit.CONTRACT, "PREIMAGE_OID")
    for key in (
        "authorization_parent_commit_oid",
        "authorization_parent_tree_oid",
        "authorization_commit_oid",
        "authorization_tree_oid",
    ):
        if not re.fullmatch(r"[0-9a-f]{%d}" % oid_length, str(generation.get(key))):
            fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_OBJECT_FORMAT")
    if (
        preimage.get("head_commit_oid") != generation.get("authorization_commit_oid")
        or preimage.get("head_tree_oid") != generation.get("authorization_tree_oid")
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_GIT_BINDING")
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
        validate_tool_identity(entry, role)
        expected_kind, expected_digest_profile, expected_authority = TOOLCHAIN_ROLE_PROFILE[role]
        if (
            entry.get("artifact_kind") != expected_kind
            or entry.get("digest_profile") != expected_digest_profile
            or entry.get("execution_authority") != expected_authority
        ):
            fail(Exit.CONTRACT, "FROZEN_TOOL_PROFILE")
        require_sha256(entry.get("raw_digest_sha256"), "FROZEN_TOOL")
    require_sha256(frozen.get("dynamic_closure_receipt_sha256"), "DYNAMIC_CLOSURE")
    require_sha256(frozen.get("toolchain_set_receipt_sha256"), "TOOLCHAIN_SET")
    if frozen.get("recompute_before_first_non_ledger_acquisition_write") is not True:
        fail(Exit.CONTRACT, "TOOLCHAIN_RECOMPUTE")
    if frozen.get("drift_action") != TOOLCHAIN_DRIFT_ACTION_V2:
        fail(Exit.CONTRACT, "TOOLCHAIN_DRIFT_ACTION")
    binding = require_exact_object(envelope.get("schema_binding"), SCHEMA_BINDING_FIELDS, "SCHEMA_BINDING")
    if binding.get("schema_id") != SCHEMA_ID:
        fail(Exit.CONTRACT, "SCHEMA_BINDING_ID")
    static_contract = require_exact_object(
        envelope.get("static_acquisition_contract"), STATIC_CONTRACT_FIELDS, "STATIC_CONTRACT"
    )
    expected_public = validate_static_expected_shape(static_contract.get("expected"))
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
    validate_pending_template_scalar_types(
        pending_lock_observation_expected_structure(expected_public),
        lock_closure,
    )
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
    if execution.get("attempt_policy") != ATTEMPT_POLICY_V2:
        fail(Exit.CONTRACT, "ATTEMPT_POLICY")
    if execution.get("executor_interface_version") != SCRIPT_VERSION:
        fail(Exit.CONTRACT, "EXECUTOR_INTERFACE_VERSION")
    if execution.get("environment_mode") != ENVIRONMENT_MODE_V2:
        fail(Exit.CONTRACT, "ENVIRONMENT_MODE")
    if execution.get("git_child_sandbox_profile") != GIT_CHILD_SANDBOX_PROFILE_V3:
        fail(Exit.CONTRACT, "GIT_CHILD_SANDBOX_PROFILE")
    if (
        execution.get("git_metadata_adapter_bootstrap_sandbox_profile")
        != GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V3
    ):
        fail(Exit.CONTRACT, "GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE")
    if (
        execution.get("git_metadata_adapter_trust_boundary")
        != GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
        or execution.get("git_metadata_adapter_host_assurance")
        != GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
    ):
        fail(Exit.CONTRACT, "GIT_METADATA_ADAPTER_HOST_BOUNDARY")
    if execution.get("launcher_executable_role") != "python-interpreter":
        fail(Exit.CONTRACT, "LAUNCHER_ROLE")
    if execution.get("allowed_subprocess_executable_roles") != list(AUTHORIZED_SUBPROCESS_ROLES):
        fail(Exit.CONTRACT, "SUBPROCESS_ROLES")
    executor_template = execution.get("executor_argv_template")
    verifier_census_template = execution.get("verifier_census_argv_template")
    verifier_installed_template = execution.get("verifier_installed_argv_template")
    for template in (executor_template, verifier_census_template, verifier_installed_template):
        if not isinstance(template, list) or template[:4] != ["{BOUND_PYTHON_PRIVATE}", "-I", "-S", "-B"]:
            fail(Exit.CONTRACT, "PYTHON_LAUNCH_FLAGS")
    if executor_template != list(EXECUTOR_ARGV_TEMPLATE_V2):
        fail(Exit.CONTRACT, "EXECUTOR_ARGV_TEMPLATE")
    if execution.get("executor_argv_template_sha256") != public_contract_receipt(
        EXECUTOR_ARGV_TEMPLATE_DOMAIN,
        executor_template,
    ):
        fail(Exit.CONTRACT, "EXECUTOR_ARGV_TEMPLATE_RECEIPT")
    evidence_templates = execution.get("evidence_command_templates")
    if not isinstance(evidence_templates, list):
        fail(Exit.CONTRACT, "EVIDENCE_COMMAND_TEMPLATES")
    git_templates = [
        entry
        for entry in evidence_templates
        if isinstance(entry, Mapping) and entry.get("role") == "git-read-only-evidence"
    ]
    bootstrap_templates = [
        entry
        for entry in evidence_templates
        if isinstance(entry, Mapping) and entry.get("role") == "git-metadata-adapter-bootstrap"
    ]
    git_template = (
        require_exact_object(
            git_templates[0],
            ("argv_allowlist", "environment_name_allowlist", "executable", "read_only", "role", "shell"),
            "GIT_READ_ONLY_EVIDENCE_TEMPLATE",
        )
        if len(git_templates) == 1
        else {}
    )
    bootstrap_template = (
        require_exact_object(
            bootstrap_templates[0],
            (
                "argv_allowlist", "environment_name_allowlist", "executable", "read_only", "role", "shell",
                "write_scope",
            ),
            "GIT_METADATA_ADAPTER_BOOTSTRAP_TEMPLATE",
        )
        if len(bootstrap_templates) == 1
        else {}
    )
    git_environment_names = list(git_env())
    if (
        len(git_templates) != 1
        or git_template.get("argv_allowlist") != git_read_only_argv_templates_v2()
        or git_template.get("environment_name_allowlist") != git_environment_names
        or git_template.get("executable") != "{RESOLVED_CLT_GIT_PRIVATE}"
        or git_template.get("read_only") is not True
        or git_template.get("shell") is not False
        or len(bootstrap_templates) != 1
        or bootstrap_template.get("argv_allowlist") != git_adapter_bootstrap_argv_templates_v2()
        or bootstrap_template.get("environment_name_allowlist")
        != git_environment_names + ["GIT_OBJECT_DIRECTORY"]
        or bootstrap_template.get("executable") != "{RESOLVED_CLT_GIT_PRIVATE}"
        or bootstrap_template.get("read_only") is not False
        or bootstrap_template.get("shell") is not False
        or bootstrap_template.get("write_scope")
        != "checkpoint-scoped-private-temp-adapter-only"
    ):
        fail(Exit.CONTRACT, "GIT_EVIDENCE_COMMAND_TEMPLATES")
    if execution.get("evidence_command_templates_sha256") != public_contract_receipt(
        EVIDENCE_COMMAND_TEMPLATES_DOMAIN,
        evidence_templates,
    ):
        fail(Exit.CONTRACT, "EVIDENCE_COMMAND_TEMPLATES_RECEIPT")
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
        "publish_attempt_ceiling overwrite_allowed forbidden_mutations git_metadata_adapter_trust_boundary "
        "git_metadata_adapter_host_assurance git_metadata_adapter_cleanup_guarantee".split(),
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
    ephemeral_mutations = mutation.get("allowed_ephemeral_mutations")
    if (
        not isinstance(ephemeral_mutations, list)
        or not ephemeral_mutations
        or ephemeral_mutations[0] != GIT_ADAPTER_EPHEMERAL_MUTATION_V3
    ):
        fail(Exit.CONTRACT, "GIT_ADAPTER_MUTATION_AUTHORITY")
    if (
        mutation.get("git_metadata_adapter_trust_boundary")
        != GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
        or mutation.get("git_metadata_adapter_host_assurance")
        != GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
        or mutation.get("git_metadata_adapter_cleanup_guarantee")
        != GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
    ):
        fail(Exit.CONTRACT, "GIT_ADAPTER_MUTATION_BOUNDARY")
    failure = require_exact_object(
        envelope.get("failure_contract"),
        "failure_action challenge_state preclaim_retry_allowed postclaim_retry_allowed "
        "public_success_attestation_allowed existing_target_action failed_stage_action evidence_action "
        "new_authority_required git_metadata_adapter_cleanup_guarantee".split(),
        "FAILURE_CONTRACT",
    )
    if (
        failure.get("challenge_state") != FAILURE_CHALLENGE_POLICY_V2
        or failure.get("preclaim_retry_allowed") is not True
        or failure.get("postclaim_retry_allowed") is not False
        or failure.get("public_success_attestation_allowed") is not False
        or failure.get("new_authority_required") != FAILURE_NEW_AUTHORITY_POLICY_V2
        or failure.get("evidence_action") != FAILURE_EVIDENCE_ACTION_V2
        or failure.get("git_metadata_adapter_cleanup_guarantee")
        != GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
    ):
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
        "challenge_claim_preimage first_authority_consuming_persistent_write persistent_single_use_ledger_required "
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
    private_writes = private.get("private_write_authority")
    if (
        not isinstance(private_writes, list)
        or not private_writes
        or not private_writes[0].startswith("create, seal and mandatorily remove only the exact dev/inode-bound")
    ):
        fail(Exit.CONTRACT, "GIT_ADAPTER_PRIVATE_WRITE_AUTHORITY")
    require_exact_sequence(
        private.get("private_preimage_checks"),
        PRIVATE_PREIMAGE_CHECKS,
        "PRIVATE_PREIMAGE_CHECKS",
    )
    if (
        private.get("claims_container_preimage")
        != "state-root/claims already exists as a receipt-bound-owner-and-group real 0700 directory and is not created by this attempt"
        or private.get("challenge_claim_preimage")
        != "exact state-root/claims/<approval_challenge_id> direct child ABSENT"
        or private.get("first_authority_consuming_persistent_write")
        != FIRST_AUTHORITY_CONSUMING_PERSISTENT_WRITE_V2
    ):
        fail(Exit.CONTRACT, "PRIVATE_FIRST_WRITE_CONTRACT")
    privacy = require_exact_object(
        envelope.get("privacy"),
        "public_raw_sha256_allowed_for private_raw_sha256_only_for private_locator_public_count "
        "private_vault_read_count graphiti_call_count network_call_count "
        "git_metadata_adapter_trust_boundary".split(),
        "PRIVACY",
    )
    if privacy.get("git_metadata_adapter_trust_boundary") != GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1:
        fail(Exit.CONTRACT, "PRIVACY_GIT_METADATA_ADAPTER_TRUST_BOUNDARY")
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


def observe_pending_artifacts_v2(
    repo_fd: int,
    generation_authorization: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    """Hash the closed pending-envelope artifact set without a caller skeleton.

    The generation approval envelope is the sole dynamic path.  Every other
    role/path pair comes from the executor's frozen allowlist; the final pending
    envelope is deliberately absent to avoid a raw-byte fixed point.
    """
    generation = require_exact_object(
        generation_authorization,
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_AUTHORIZATION",
    )
    generation_path = generation.get("approval_envelope_repo_relative_path")
    if not isinstance(generation_path, str) or GENERATION_APPROVAL_PATH_RE.fullmatch(generation_path) is None:
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_PATH")
    generation_challenge = generation.get("approval_challenge_id")
    if (
        not isinstance(generation_challenge, str)
        or GENERATION_CHALLENGE_RE.fullmatch(generation_challenge) is None
        or generation_path
        != CONTROL_PREFIX
        + "GOV-01-toolchain-static-envelope-generation-envelope-v1."
        + generation_challenge
        + ".json"
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_PATH")
    specs = PENDING_STATIC_ARTIFACT_SPECS + ((GENERATION_APPROVAL_ROLE, generation_path),)
    observations: List[Dict[str, Any]] = []
    seen_paths = set()
    for role, path in specs:
        if path in seen_paths:
            fail(Exit.CONTRACT, "GENERATION_ARTIFACT_DUPLICATE_PATH")
        seen_paths.add(path)
        fd, metadata = open_relative_regular(repo_fd, path, "GENERATION_ARTIFACT", MAX_JSON_BYTES)
        try:
            digest, length = hash_fd(fd, "sha256", MAX_JSON_BYTES, "GENERATION_ARTIFACT")
        finally:
            os.close(fd)
        observations.append(
            {
                "path": path,
                "role": role,
                "sha256": digest,
                "bytes": length,
                "device": metadata.st_dev,
                "inode": metadata.st_ino,
            }
        )
    if observations[-1]["sha256"] != generation.get("raw_envelope_sha256"):
        fail(Exit.PREFLIGHT_DRIFT, "GENERATION_AUTHORIZATION_ARTIFACT_DRIFT")
    return observations


def verify_generation_authorization_artifact(
    repo_fd: int,
    envelope: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    generation = require_exact_object(
        envelope.get("generation_authorization"),
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_AUTHORIZATION",
    )
    matches = [entry for entry in artifacts if entry.get("role") == GENERATION_APPROVAL_ROLE]
    if len(matches) != 1:
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_ARTIFACT_COUNT")
    artifact = matches[0]
    path = artifact.get("path")
    length = artifact.get("bytes")
    digest = artifact.get("sha256")
    if not isinstance(path, str) or type(length) is not int or not isinstance(digest, str):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_ARTIFACT_SCHEMA")
    if (
        path != generation.get("approval_envelope_repo_relative_path")
        or digest != generation.get("raw_envelope_sha256")
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_ARTIFACT_BINDING")
    fd, _metadata = open_relative_regular(
        repo_fd,
        path,
        "GENERATION_AUTHORIZATION_ENVELOPE",
        length,
    )
    try:
        raw = read_fd(fd, length, "GENERATION_AUTHORIZATION_ENVELOPE")
    finally:
        os.close(fd)
    if len(raw) != length or not hmac.compare_digest(sha256(raw), digest):
        fail(Exit.CHECKER_DRIFT, "GENERATION_AUTHORIZATION_REOPEN_DRIFT")
    if not hmac.compare_digest(
        sha256(GENERATION_RECEIPT_DOMAIN + b"\x00" + raw),
        str(generation.get("receipt_digest")),
    ):
        fail(Exit.RECEIPT, "GENERATION_AUTHORIZATION_RECEIPT")
    value = parse_json_bytes(raw, "GENERATION_AUTHORIZATION_ENVELOPE")
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "gov-01-toolchain-static-envelope-generation-envelope-v1"
        or value.get("artifact_type") != "gov-01-toolchain-static-envelope-generation-envelope"
        or value.get("approval_challenge_id") != generation.get("approval_challenge_id")
        or value.get("state") != "pending-user-confirmation"
        or canonical_json(value) != raw
        or has_forbidden_public_value(value)
    ):
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_ENVELOPE_CONTRACT")
    return value


def verify_generation_artifacts_against_micro_and_head_v2(
    repo_root: str,
    key: bytes,
    git_binary: str,
    artifacts: Sequence[Mapping[str, Any]],
    generation_envelope: Mapping[str, Any],
    generation_authorization: Mapping[str, Any],
) -> None:
    approved_artifacts = generation_envelope.get("artifacts")
    if not isinstance(approved_artifacts, list) or len(approved_artifacts) != len(PENDING_STATIC_ARTIFACT_SPECS):
        fail(Exit.CONTRACT, "GENERATION_APPROVED_ARTIFACTS")
    for index, (role, path) in enumerate(PENDING_STATIC_ARTIFACT_SPECS):
        approved = approved_artifacts[index]
        observed = artifacts[index]
        if (
            not isinstance(approved, dict)
            or approved.get("role") != role
            or approved.get("path") != path
            or approved.get("file_kind") != "regular"
            or approved.get("raw_file_sha256") != observed.get("sha256")
            or approved.get("byte_length") != observed.get("bytes")
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GENERATION_APPROVED_ARTIFACT_DRIFT")
    commit_oid = generation_authorization.get("authorization_commit_oid")
    if not isinstance(commit_oid, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit_oid) is None:
        fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_COMMIT")
    _capture, boundary = create_git_metadata_adapter(repo_root, key, git_binary)
    pending: Optional[BaseException] = None
    try:
        for observation in artifacts:
            path = observation.get("path")
            if not isinstance(path, str):
                fail(Exit.CONTRACT, "GENERATION_ARTIFACT_PATH")
            tree_entry = run_git(
                git_binary,
                repo_root,
                boundary,
                ["ls-tree", "-z", "--full-tree", commit_oid, "--", path],
                "GENERATION_ARTIFACT_TREE",
            )
            expected_suffix = b"\t" + path.encode("utf-8") + b"\x00"
            if (
                tree_entry.count(b"\x00") != 1
                or not tree_entry.startswith(b"100644 blob ")
                or not tree_entry.endswith(expected_suffix)
            ):
                fail(Exit.PREFLIGHT_DRIFT, "GENERATION_ARTIFACT_HEAD_KIND")
            committed = run_git(
                git_binary,
                repo_root,
                boundary,
                ["show", commit_oid + ":" + path],
                "GENERATION_ARTIFACT_HEAD_BYTES",
            )
            if (
                len(committed) != observation.get("bytes")
                or not hmac.compare_digest(sha256(committed), str(observation.get("sha256")))
            ):
                fail(Exit.PREFLIGHT_DRIFT, "GENERATION_ARTIFACT_HEAD_DRIFT")
    except BaseException as error:
        pending = error
    if pending is None:
        finalize_git_metadata_adapter(boundary, key)
    else:
        cleanup_git_metadata_adapter(boundary)
        raise pending


def verify_public_predecessor_sources_v2(repo_fd: int) -> Dict[str, Any]:
    first, first_raw, _ = read_json_relative(
        repo_fd,
        CONTROL_PREFIX + "GOV-01-first-receipt-envelope-v1.json",
        "FIRST_APPROVAL_ENVELOPE",
    )
    control, control_raw, _ = read_json_relative(
        repo_fd,
        CONTROL_PREFIX + "GOV-01-toolchain-control-prep-envelope-v1.json",
        "CONTROL_PREPARATION_ENVELOPE",
    )
    bootstrap_fd, _ = open_relative_regular(
        repo_fd,
        CONTROL_PREFIX + "2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch",
        "BOOTSTRAP_PATCH",
        MAX_JSON_BYTES,
    )
    try:
        bootstrap_raw = read_fd(bootstrap_fd, MAX_JSON_BYTES, "BOOTSTRAP_PATCH")
    finally:
        os.close(bootstrap_fd)
    if (
        not isinstance(first, dict)
        or not hmac.compare_digest(sha256(first_raw), FIRST_APPROVAL_ENVELOPE_RAW_SHA256)
        or not hmac.compare_digest(
            sha256(FIRST_APPROVAL_RECEIPT_DOMAIN + b"\x00" + first_raw),
            FIRST_RECEIPT_DOMAIN_SHA256,
        )
        or not isinstance(control, dict)
        or not hmac.compare_digest(sha256(control_raw), CONTROL_PREPARATION_ENVELOPE_RAW_SHA256)
        or not hmac.compare_digest(
            sha256(CONTROL_PREPARATION_ENVELOPE_RECEIPT_DOMAIN + b"\x00" + control_raw),
            CONTROL_PREPARATION_RECEIPT_DIGEST,
        )
        or not hmac.compare_digest(sha256(bootstrap_raw), BOOTSTRAP_PATCH_RAW_SHA256)
    ):
        fail(Exit.CONTRACT, "PUBLIC_PREDECESSOR_SOURCE")
    challenge = control.get("approval_challenge_id")
    if not isinstance(challenge, str) or CONTROL_PREPARATION_CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "CONTROL_PREPARATION_CHALLENGE")
    return {
        "control_preparation_approval_challenge_id": challenge,
    }


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
    sandbox_profile: Optional[bytes] = None,
    stdin_bytes: Optional[bytes] = None,
    working_directory_fd: Optional[int] = None,
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
    child_directory_fd: Optional[int] = None
    if working_directory_fd is not None:
        if type(working_directory_fd) is not int or working_directory_fd < 3:
            fail(Exit.TRACE, "PROCESS_WORKING_DIRECTORY_FD")
        try:
            directory_metadata = os.fstat(working_directory_fd)
            if not stat.S_ISDIR(directory_metadata.st_mode):
                fail(Exit.TRACE, "PROCESS_WORKING_DIRECTORY_FD")
            child_directory_fd = os.dup(working_directory_fd)
        except ContractError:
            raise
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_WORKING_DIRECTORY_DUP")
    sandbox_library: Optional[Any] = None
    if sandbox_profile is not None:
        if not isinstance(sandbox_profile, bytes) or not sandbox_profile:
            fail(Exit.TRACE, "PROCESS_SANDBOX_PROFILE")
        try:
            sandbox_library = ctypes.CDLL("/usr/lib/libsandbox.1.dylib")
            sandbox_library.sandbox_init.argtypes = [
                ctypes.c_char_p,
                ctypes.c_uint64,
                ctypes.POINTER(ctypes.c_char_p),
            ]
            sandbox_library.sandbox_init.restype = ctypes.c_int
        except (OSError, AttributeError):
            fail(Exit.PREFLIGHT_DRIFT, label + "_SANDBOX_LOAD")

    def initialize_child_boundary() -> None:
        if child_directory_fd is not None:
            try:
                os.fchdir(child_directory_fd)
                os.close(child_directory_fd)
            except OSError:
                os._exit(125)
        if sandbox_library is not None:
            error_pointer = ctypes.c_char_p()
            if sandbox_library.sandbox_init(sandbox_profile, 0, ctypes.byref(error_pointer)) != 0:
                os._exit(126)
    preexec_fn: Optional[Callable[[], None]] = (
        initialize_child_boundary
        if child_directory_fd is not None or sandbox_library is not None
        else None
    )
    passed_fds = () if child_directory_fd is None else (child_directory_fd,)
    try:
        try:
            completed = subprocess.run(
                list(argv),
                input=stdin_bytes,
                stdin=subprocess.DEVNULL if stdin_bytes is None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=dict(env),
                cwd="/",
                close_fds=True,
                pass_fds=passed_fds,
                check=False,
                timeout=30,
                preexec_fn=preexec_fn,
            )
        finally:
            if child_directory_fd is not None:
                os.close(child_directory_fd)
    except (OSError, subprocess.SubprocessError):
        fail(Exit.PREFLIGHT_DRIFT, label + "_EXEC")
    if completed.returncode == 125 and working_directory_fd is not None:
        fail(Exit.PREFLIGHT_DRIFT, label + "_WORKING_DIRECTORY")
    if sandbox_profile is not None and completed.returncode == 126:
        fail(Exit.PREFLIGHT_DRIFT, label + "_SANDBOX_INIT")
    if completed.returncode not in allowed_returncodes or len(completed.stdout) > max_output:
        fail(Exit.PREFLIGHT_DRIFT, label + "_RESULT")
    return completed.stdout


def git_env(object_directory: Optional[str] = None) -> Dict[str, str]:
    environment = {
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
    if object_directory is not None:
        assert_absolute(object_directory, "GIT_OBJECT_DIRECTORY")
        environment["GIT_OBJECT_DIRECTORY"] = object_directory
    return environment


def git_child_argv_template_prefix_v2() -> List[str]:
    return [
        "{RESOLVED_CLT_GIT_PRIVATE}",
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
        "--work-tree={REPO_ROOT_PRIVATE}",
        "--no-pager",
    ]


def git_read_only_argv_templates_v2() -> List[List[str]]:
    prefix = git_child_argv_template_prefix_v2()
    return [
        prefix + ["rev-parse", "--verify", "HEAD"],
        prefix + ["rev-parse", "--verify", "HEAD^{tree}"],
        prefix + ["rev-parse", "--show-object-format"],
        prefix + ["cat-file", "--batch"],
        prefix
        + [
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        ],
        prefix + ["ls-tree", "-r", "-t", "-z", "--full-tree", "HEAD^{tree}"],
        prefix
        + [
            "status", "--porcelain=v2", "-z", "--untracked-files=all", "--", ".",
            ":(exclude).git", ":(exclude).git/**",
            ":(exclude)canvas-vault", ":(exclude)canvas-vault/**",
            ":(exclude){STAGE_REPO_RELATIVE}", ":(exclude){STAGE_REPO_RELATIVE}/**",
            ":(exclude)node_modules", ":(exclude)node_modules/**",
            ":(top,literal,exclude){ENVELOPE_REPO_RELATIVE}",
        ],
        prefix + ["show-ref"],
        prefix
        + [
            "ls-tree", "-z", "--full-tree", "{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}", "--",
            "{PUBLIC_ARTIFACT_REPO_RELATIVE}",
        ],
        prefix
        + [
            "show",
            "{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}:{PUBLIC_ARTIFACT_REPO_RELATIVE}",
        ],
    ]


def git_adapter_bootstrap_argv_templates_v2() -> List[List[str]]:
    prefix = git_child_argv_template_prefix_v2()
    return [
        prefix + ["cat-file", "--batch"],
        prefix
        + [
            "pack-objects", "--stdout", "--no-reuse-delta", "--no-reuse-object",
        ],
        prefix + ["index-pack", "--stdin", "--index-version=2"],
        prefix + ["verify-pack", "-v", "{GIT_METADATA_ADAPTER_PACK_INDEX_RELATIVE_PRIVATE}"],
    ]


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
    _GIT_DEVELOPER_ROOTS[binary] = developer
    return binary, actual_hash


def sbpl_literal(path: str, label: str) -> str:
    if (
        not os.path.isabs(path)
        or os.path.normpath(path) != path
        or any(ord(character) < 0x20 or ord(character) > 0x7E or character in ('"', "\\") for character in path)
    ):
        fail(Exit.PREFLIGHT_DRIFT, label + "_SBPL_LITERAL")
    return '(literal "' + path + '")'


def sbpl_subpath(path: str, label: str) -> str:
    sbpl_literal(path, label)
    return '(subpath "' + path + '")'


def git_read_sandbox_profile(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    enumerates_worktree: bool,
) -> bytes:
    if (
        repo_root != boundary.repo_root
        or git_binary not in _GIT_DEVELOPER_ROOTS
        or _GIT_DEVELOPER_ROOTS[git_binary] != boundary.developer_root
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_SANDBOX_BOUNDARY")
    literals = [
        git_binary,
        repo_root,
        "/dev/null",
        boundary.adapter_root,
        boundary.git_dir,
        os.path.join(boundary.git_dir, "HEAD"),
        os.path.join(boundary.git_dir, "index"),
        os.path.join(boundary.git_dir, "config"),
        os.path.join(boundary.git_dir, "packed-refs"),
        os.path.join(boundary.git_dir, "shallow"),
    ]
    subpaths = [
        boundary.developer_root,
        boundary.adapter_root,
    ]
    if enumerates_worktree:
        subpaths.append(repo_root)
    prohibited_literals = [
        os.path.join(repo_root, ".git"),
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
    prohibited_subpaths = sorted({boundary.live_git_dir, boundary.live_common_dir})
    allow_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in literals)
    allow_rules += "\n " + "\n ".join(sbpl_subpath(path, "GIT_SANDBOX") for path in subpaths)
    ancestors: List[str] = []
    for path in literals + subpaths:
        sbpl_literal(path, "GIT_SANDBOX")
        ancestors.append('(path-ancestors "' + path + '")')
    deny_rules = "\n ".join(sbpl_literal(path, "GIT_SANDBOX") for path in prohibited_literals)
    deny_rules += "\n " + "\n ".join(
        sbpl_subpath(path, "GIT_SANDBOX") for path in prohibited_subpaths
    )
    vault_filter = (
        '(regex #"/([.][Oo][Bb][Ss][Ii][Dd][Ii][Aa][Nn]|'
        '[^/]*[Cc][Aa][Nn][Vv][Aa][Ss]-[Vv][Aa][Uu][Ll][Tt][^/]*)(/|$)")'
    )
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        '(deny network*)\n'
        '(allow process-exec ' + sbpl_literal(git_binary, "GIT_SANDBOX") + ')\n'
        '(allow process-fork)\n'
        '(allow signal (target self))\n'
        '(allow file-read* file-test-existence\n ' + allow_rules + '\n)\n'
        '(allow file-read-metadata file-test-existence\n ' + "\n ".join(ancestors) + '\n)\n'
        '(deny file-read* file-test-existence\n ' + deny_rules + '\n)\n'
        '(deny file-read* file-test-existence ' + vault_filter + ')\n'
        '(deny file-write*)\n'
    )
    return profile.encode("ascii", "strict")


def git_hardened_child_argv(
    git_binary: str,
    repo_root: str,
    adapter_git_dir: str,
    arguments: Sequence[str],
) -> List[str]:
    if adapter_git_dir != ".":
        fail(Exit.INTERNAL, "GIT_CHILD_RELATIVE_GIT_DIR")
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
        "--git-dir=" + adapter_git_dir,
        "--work-tree=" + repo_root,
        "--no-pager",
    ] + list(arguments)


def require_git_child_template_match(
    *,
    role: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    git_binary: str,
    repo_root: str,
    adapter_git_dir: str,
    live_objects: Optional[str],
    stdin_bytes: Optional[bytes],
) -> Tuple[str, Tuple[str, ...]]:
    actual = list(argv)
    actual_prefix = git_hardened_child_argv(git_binary, repo_root, adapter_git_dir, ())
    if (
        actual[:len(actual_prefix)] != actual_prefix
        or adapter_git_dir != "."
        or actual.count("--git-dir=.") != 1
        or actual.count("--work-tree=" + repo_root) != 1
        or "-C" in actual
        or any(argument.startswith("core.worktree=") for argument in actual)
    ):
        fail(Exit.TRACE, "GIT_CHILD_ARGV_PREFIX")
    tail = actual[len(actual_prefix):]
    normalized_tail: Optional[List[str]] = None
    templates: List[List[str]]
    expected_environment: Mapping[str, str]
    if role == "git-metadata-adapter-bootstrap":
        templates = git_adapter_bootstrap_argv_templates_v2()
        pack_base = "objects/pack/pack"
        if tail == ["cat-file", "--batch"]:
            normalized_tail = tail
            if not isinstance(stdin_bytes, bytes) or not stdin_bytes:
                fail(Exit.TRACE, "GIT_BOOTSTRAP_STDIN")
        elif tail == ["pack-objects", "--stdout", "--no-reuse-delta", "--no-reuse-object"]:
            normalized_tail = tail
            if not isinstance(stdin_bytes, bytes) or not stdin_bytes:
                fail(Exit.TRACE, "GIT_BOOTSTRAP_STDIN")
        elif tail == ["index-pack", "--stdin", "--index-version=2"]:
            normalized_tail = tail
            if not isinstance(stdin_bytes, bytes) or not stdin_bytes:
                fail(Exit.TRACE, "GIT_BOOTSTRAP_STDIN")
        elif (
            len(tail) == 3
            and tail[:2] == ["verify-pack", "-v"]
            and os.path.dirname(tail[2]) == os.path.dirname(pack_base)
            and re.fullmatch(r"pack-[0-9a-f]{40,64}\.idx", os.path.basename(tail[2])) is not None
        ):
            normalized_tail = tail[:2] + ["{GIT_METADATA_ADAPTER_PACK_INDEX_RELATIVE_PRIVATE}"]
            if stdin_bytes is not None:
                fail(Exit.TRACE, "GIT_BOOTSTRAP_STDIN")
        if normalized_tail is None:
            fail(Exit.TRACE, "GIT_BOOTSTRAP_ARGV")
        needs_bridge = normalized_tail[:1] in (["cat-file"], ["pack-objects"])
        if needs_bridge != (live_objects is not None):
            fail(Exit.TRACE, "GIT_BOOTSTRAP_OBJECT_BRIDGE")
        expected_environment = git_env(live_objects if needs_bridge else None)
    elif role == "git-read-only-evidence":
        templates = git_read_only_argv_templates_v2()
        expected_environment = git_env()
        if live_objects is not None or "GIT_OBJECT_DIRECTORY" in environment:
            fail(Exit.TRACE, "GIT_FINAL_LIVE_OBJECT_BRIDGE")
        if tail in (
            ["rev-parse", "--verify", "HEAD"],
            ["rev-parse", "--verify", "HEAD^{tree}"],
            ["rev-parse", "--show-object-format"],
            ["show-ref"],
            ["ls-tree", "-r", "-t", "-z", "--full-tree", "HEAD^{tree}"],
            [
                "cat-file",
                "--batch-all-objects",
                "--batch-check=%(objectname) %(objecttype) %(objectsize)",
            ],
        ):
            normalized_tail = tail
            if stdin_bytes is not None:
                fail(Exit.TRACE, "GIT_FINAL_STDIN")
        elif tail == ["cat-file", "--batch"]:
            normalized_tail = tail
            if not isinstance(stdin_bytes, bytes) or not stdin_bytes:
                fail(Exit.TRACE, "GIT_FINAL_STDIN")
        elif len(tail) == 15 and tail[:10] == [
            "status", "--porcelain=v2", "-z", "--untracked-files=all", "--", ".",
            ":(exclude).git", ":(exclude).git/**",
            ":(exclude)canvas-vault", ":(exclude)canvas-vault/**",
        ]:
            stage_prefix = ":(exclude).gov01-toolchain-stage-"
            if not tail[10].startswith(stage_prefix):
                fail(Exit.TRACE, "GIT_STATUS_STAGE")
            challenge = tail[10][len(":(exclude).gov01-toolchain-stage-"):]
            stage = ".gov01-toolchain-stage-" + challenge
            envelope_prefix = ":(top,literal,exclude)" + CONTROL_PREFIX + PENDING_ENVELOPE_BASENAME_PREFIX
            envelope_value = tail[14]
            generation_challenge = (
                envelope_value[len(envelope_prefix):-len(".json")]
                if envelope_value.startswith(envelope_prefix) and envelope_value.endswith(".json")
                else ""
            )
            if (
                CHALLENGE_RE.fullmatch(challenge) is None
                or GENERATION_CHALLENGE_RE.fullmatch(generation_challenge) is None
                or tail[11] != ":(exclude)" + stage + "/**"
                or tail[12:14] != [":(exclude)node_modules", ":(exclude)node_modules/**"]
                or stdin_bytes is not None
            ):
                fail(Exit.TRACE, "GIT_STATUS_AUTHORITY")
            normalized_tail = tail[:10] + [
                ":(exclude){STAGE_REPO_RELATIVE}",
                ":(exclude){STAGE_REPO_RELATIVE}/**",
                ":(exclude)node_modules",
                ":(exclude)node_modules/**",
                ":(top,literal,exclude){ENVELOPE_REPO_RELATIVE}",
            ]
        elif (
            len(tail) == 6
            and tail[:3] == ["ls-tree", "-z", "--full-tree"]
            and tail[4] == "--"
            and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", tail[3]) is not None
            and tail[5] in {path for _role, path in PENDING_STATIC_ARTIFACT_SPECS}
            and stdin_bytes is None
        ):
            normalized_tail = [
                "ls-tree", "-z", "--full-tree", "{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}", "--",
                "{PUBLIC_ARTIFACT_REPO_RELATIVE}",
            ]
        elif len(tail) == 2 and tail[0] == "show" and stdin_bytes is None:
            for approved_path in (path for _role, path in PENDING_STATIC_ARTIFACT_SPECS):
                suffix = ":" + approved_path
                if tail[1].endswith(suffix) and re.fullmatch(
                    r"[0-9a-f]{40}|[0-9a-f]{64}",
                    tail[1][:-len(suffix)],
                ) is not None:
                    normalized_tail = [
                        "show",
                        "{GENERATION_AUTHORIZATION_COMMIT_OID_PUBLIC}:{PUBLIC_ARTIFACT_REPO_RELATIVE}",
                    ]
                    break
        if normalized_tail is None:
            fail(Exit.TRACE, "GIT_FINAL_ARGV")
    else:
        fail(Exit.TRACE, "GIT_CHILD_ROLE")
    if dict(environment) != dict(expected_environment):
        fail(Exit.TRACE, "GIT_CHILD_ENVIRONMENT")
    normalized = git_child_argv_template_prefix_v2() + normalized_tail
    matches = sum(1 for template in templates if template == normalized)
    if matches != 1:
        fail(Exit.TRACE, "GIT_CHILD_TEMPLATE_CLOSURE")
    return role, tuple(normalized)


def git_object_bootstrap_sandbox_profile(
    git_binary: str,
    repo_root: str,
    developer_root: str,
    adapter_root: str,
    adapter_git_dir: str,
    live_git_dir: str,
    live_common_dir: str,
    live_objects: str,
    allow_live_objects: bool,
    allow_adapter_writes: bool,
    allowed_live_oids: Sequence[str],
    allowed_pack_paths: Sequence[str],
) -> bytes:
    if (
        _GIT_DEVELOPER_ROOTS.get(git_binary) != developer_root
        or adapter_git_dir != "."
        or live_objects != os.path.join(live_common_dir, "objects")
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_BOOTSTRAP_BOUNDARY")
    read_literals = [
        git_binary, repo_root, "/dev/null", adapter_root, os.path.join(adapter_root, "git"),
    ]
    read_subpaths = [developer_root, adapter_root]
    if allow_live_objects:
        if not allowed_live_oids or any(
            re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
            for oid in allowed_live_oids
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_BOOTSTRAP_OID_SCOPE")
        pack_container = os.path.join(live_objects, "pack")
        expected_pack_paths = tuple(sorted(set(allowed_pack_paths)))
        if any(
            os.path.dirname(path) != pack_container
            or re.fullmatch(
                r"pack-(?:[0-9a-f]{40}|[0-9a-f]{64})\.(?:pack|idx)",
                os.path.basename(path),
            ) is None
            for path in expected_pack_paths
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_BOOTSTRAP_PACK_SCOPE")
        selected_pack_names = {os.path.basename(path) for path in expected_pack_paths}
        if any(
            stem + ".idx" not in selected_pack_names or stem + ".pack" not in selected_pack_names
            for stem in {name.rsplit(".", 1)[0] for name in selected_pack_names}
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_BOOTSTRAP_PACK_PAIR")
        read_literals.extend((pack_container, *expected_pack_paths))
        read_literals.extend(
            os.path.join(live_objects, oid[:2], oid[2:]) for oid in sorted(set(allowed_live_oids))
        )
    elif allowed_live_oids or allowed_pack_paths:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_BOOTSTRAP_OID_SCOPE")
    ancestors = [
        '(path-ancestors "' + path + '")'
        for path in read_literals + read_subpaths
        if sbpl_literal(path, "GIT_OBJECT_BOOTSTRAP")
    ]
    prohibited_literals = {
        os.path.join(repo_root, ".git"),
        os.path.join(live_git_dir, "HEAD"),
        os.path.join(live_git_dir, "index"),
        os.path.join(live_git_dir, "commondir"),
        os.path.join(live_git_dir, "config.worktree"),
        os.path.join(live_git_dir, "gitdir"),
        os.path.join(live_common_dir, "HEAD"),
        os.path.join(live_common_dir, "config"),
        os.path.join(live_common_dir, "packed-refs"),
        os.path.join(live_common_dir, "shallow"),
        os.path.join(live_common_dir, "info", "grafts"),
        os.path.join(live_objects, "info", "alternates"),
        os.path.join(live_objects, "info", "http-alternates"),
    }
    prohibited_subpaths = {
        os.path.join(live_git_dir, "refs"),
        os.path.join(live_common_dir, "refs"),
        os.path.join(live_common_dir, "hooks"),
        os.path.join(live_common_dir, "logs"),
        os.path.join(live_objects, "info"),
    }
    allow_read_rules = "\n ".join(
        [sbpl_literal(path, "GIT_OBJECT_BOOTSTRAP") for path in read_literals]
        + [sbpl_subpath(path, "GIT_OBJECT_BOOTSTRAP") for path in read_subpaths]
    )
    deny_read_rules = "\n ".join(
        [sbpl_literal(path, "GIT_OBJECT_BOOTSTRAP") for path in sorted(prohibited_literals)]
        + [sbpl_subpath(path, "GIT_OBJECT_BOOTSTRAP") for path in sorted(prohibited_subpaths)]
    )
    vault_filter = (
        '(regex #"/([.][Oo][Bb][Ss][Ii][Dd][Ii][Aa][Nn]|'
        '[^/]*[Cc][Aa][Nn][Vv][Aa][Ss]-[Vv][Aa][Uu][Ll][Tt][^/]*)(/|$)")'
    )
    adapter_pack_path = os.path.join(adapter_root, "git", "objects", "pack")
    if allow_adapter_writes:
        write_rule = (
            '(allow file-write* '
            + sbpl_subpath(adapter_pack_path, "GIT_OBJECT_BOOTSTRAP")
            + ')\n'
        )
        # system.sb is imported for the dynamic loader and platform runtime.
        # Do not inherit any of its ambient write grants: the only writable
        # names are strict descendants of this adapter's objects/pack inode.
        # The literal denies also prevent rename/unlink of every directory
        # entry forming that capability path, including the /private/tmp
        # parent and the adapter root itself.
        protected_write_entries = (
            "/private/tmp",
            adapter_root,
            os.path.join(adapter_root, "git"),
            os.path.join(adapter_root, "git", "objects"),
            adapter_pack_path,
        )
        write_deny_rule = (
            '(deny file-write*\n '
            + "\n ".join(
                sbpl_literal(path, "GIT_OBJECT_BOOTSTRAP")
                for path in protected_write_entries
            )
            + '\n (require-not '
            + sbpl_subpath(adapter_pack_path, "GIT_OBJECT_BOOTSTRAP")
            + '))\n'
        )
    else:
        write_rule = ""
        write_deny_rule = '(deny file-write*)\n'
    profile = (
        '(version 1)\n'
        '(deny default)\n'
        '(import "system.sb")\n'
        '(deny network*)\n'
        '(allow process-exec ' + sbpl_literal(git_binary, "GIT_OBJECT_BOOTSTRAP") + ')\n'
        '(allow process-fork)\n'
        '(allow signal (target self))\n'
        '(allow file-read* file-test-existence\n ' + allow_read_rules + '\n)\n'
        '(allow file-read-metadata file-test-existence\n ' + "\n ".join(ancestors) + '\n)\n'
        + write_rule +
        write_deny_rule +
        '(deny file-read* file-test-existence\n ' + deny_read_rules + '\n)\n'
        '(deny file-read* file-test-existence ' + vault_filter + ')\n'
    )
    return profile.encode("ascii", "strict")


def run_git(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    arguments: Sequence[str],
    label: str,
    enumerates_worktree: bool = False,
    authorized_tree_excludes: Sequence[str] = (),
    authorized_exact_file_excludes: Sequence[str] = (),
    allowed_returncodes: Sequence[int] = (0,),
    stdin_bytes: Optional[bytes] = None,
    max_output: int = MAX_GIT_OUTPUT,
) -> bytes:
    verify_git_metadata_adapter(boundary)
    git_adapter_trace_event(boundary, "CHILD_PRECHECK_COMPLETE", "git-child")
    args = list(arguments)
    if enumerates_worktree:
        args.extend(
            [
                "--",
                ".",
                ":(exclude).git",
                ":(exclude).git/**",
                ":(exclude)canvas-vault",
                ":(exclude)canvas-vault/**",
            ]
        )
        for excluded in authorized_tree_excludes:
            validate_relative(excluded, "GIT_AUTHORIZED_EXCLUDE")
            args.extend([":(exclude)" + excluded, ":(exclude)" + excluded + "/**"])
        for excluded in authorized_exact_file_excludes:
            validate_relative(excluded, "GIT_AUTHORIZED_EXACT_FILE_EXCLUDE")
            args.append(":(top,literal,exclude)" + excluded)
    argv = git_hardened_child_argv(git_binary, repo_root, ".", args)
    environment = git_env()
    require_git_child_template_match(
        role="git-read-only-evidence",
        argv=argv,
        environment=environment,
        git_binary=git_binary,
        repo_root=repo_root,
        adapter_git_dir=".",
        live_objects=None,
        stdin_bytes=stdin_bytes,
    )
    git_adapter_trace_event(boundary, "CHILD_EXEC_BEGIN", "git-child")
    try:
        return run_process(
            argv,
            environment,
            max_output,
            label,
            allowed_returncodes=allowed_returncodes,
            sandbox_profile=git_read_sandbox_profile(git_binary, repo_root, boundary, enumerates_worktree),
            stdin_bytes=stdin_bytes,
            working_directory_fd=boundary.git_fd,
        )
    finally:
        verify_git_metadata_adapter(boundary)
        git_adapter_trace_event(boundary, "CHILD_POSTCHECK_COMPLETE", "git-child")


def safe_git_scalar(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    arguments: Sequence[str],
    label: str,
) -> str:
    raw = run_git(git_binary, repo_root, boundary, arguments, label)
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


def observe_runtime_toolchain_v2(
    repo_root: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    require_python_isolation()
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
    observed_entries: List[Dict[str, Any]] = []
    for role in TOOLCHAIN_ROLES:
        actual = actual_hashes.get(role)
        if role != "git-read-only-evidence" and not isinstance(actual, str):
            fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_HASH")
        artifact_kind, digest_profile, execution_authority = TOOLCHAIN_ROLE_PROFILE[role]
        entry = {
            "role": role,
            "logical_id": TOOLCHAIN_LOGICAL_ID_BY_ROLE[role],
            "artifact_kind": artifact_kind,
            "version": expected_tool_version(role),
            "digest_profile": digest_profile,
            "raw_digest_sha256": actual if isinstance(actual, str) else "0" * 64,
            "private_locator_omitted": True,
            "execution_authority": execution_authority,
        }
        observed_entries.append(entry)
    for role in ("xcode-select-resolver", "xcrun-resolver"):
        path = FIXED_TOOL_PATHS[role]
        _AUTHORIZED_EXECUTABLE_HASHES[path] = actual_hashes[role]
    git_binary, git_hash = resolve_clt_git(None)
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
    dynamic_receipt = dynamic_toolchain_receipt(observed_entries)
    return {
        "git_binary": git_binary,
        "pgrep_binary": FIXED_TOOL_PATHS["pgrep-read-only-evidence"],
        "lsof_binary": FIXED_TOOL_PATHS["lsof-read-only-evidence"],
        "entries": observed_entries,
        "toolchain_set_receipt_sha256": receipt,
        "dynamic_closure_receipt_sha256": dynamic_receipt,
        "assurance": "runtime-self-attested-not-pre-exec",
    }


def verify_runtime_toolchain(
    repo_root: str,
    envelope: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
    strict: bool,
) -> Dict[str, Any]:
    observed = observe_runtime_toolchain_v2(repo_root, artifacts)
    frozen = envelope.get("frozen_toolchain")
    if not isinstance(frozen, dict) or not isinstance(frozen.get("entries"), list):
        fail(Exit.CONTRACT, "TOOLCHAIN_SCHEMA")
    frozen_entries = frozen["entries"]
    if len(frozen_entries) != len(observed["entries"]):
        fail(Exit.CONTRACT, "TOOLCHAIN_ROLES")
    for expected, actual in zip(frozen_entries, observed["entries"]):
        if not isinstance(expected, Mapping) or expected.get("role") != actual.get("role"):
            fail(Exit.CONTRACT, "TOOLCHAIN_ROLES")
        validate_tool_identity(expected, str(actual.get("role")))
        if strict and expected != actual:
            fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_DRIFT")
    if strict and not hmac.compare_digest(
        str(frozen.get("toolchain_set_receipt_sha256")),
        observed["toolchain_set_receipt_sha256"],
    ):
        fail(Exit.PREFLIGHT_DRIFT, "TOOLCHAIN_SET_RECEIPT")
    if strict and not hmac.compare_digest(
        str(frozen.get("dynamic_closure_receipt_sha256")),
        observed["dynamic_closure_receipt_sha256"],
    ):
        fail(Exit.PREFLIGHT_DRIFT, "DYNAMIC_TOOLCHAIN_RECEIPT")
    return observed


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


def linked_git_common_anchor(repo_root: str, git_dir: str) -> str:
    """Return this project's exact linked-worktree common-dir anchor."""

    if not os.path.isabs(git_dir) or os.path.normpath(git_dir) != git_dir:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_DIRECTORY_LOCATOR")
    for component in pathlib.PurePath(git_dir).parts:
        folded = component.casefold()
        if (
            not is_nfc(component)
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in component)
            or folded == ".obsidian"
            or "canvas-vault" in folded
        ):
            fail(Exit.PRIVACY, "GIT_CONTROL_PRIVATE_COMPONENT")
    worktree_name = os.path.basename(git_dir)
    worktrees_dir = os.path.dirname(git_dir)
    candidate_common = os.path.dirname(worktrees_dir)
    main_root = os.path.dirname(candidate_common)
    if (
        os.path.basename(worktrees_dir) != "worktrees"
        or os.path.basename(candidate_common).casefold() != ".git"
        or validate_relative(worktree_name, "GIT_WORKTREE_ID") != [worktree_name]
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_ADMIN_ANCHOR")
    try:
        repo_relative = os.path.relpath(repo_root, main_root).replace(os.sep, "/")
        repo_components = validate_relative(repo_relative, "GIT_WORKTREE_REPO")
    except (ContractError, ValueError):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_ADMIN_ANCHOR")
    if repo_components != [".claude", "worktrees", worktree_name]:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_ADMIN_ANCHOR")
    if git_dir != os.path.join(candidate_common, "worktrees", worktree_name):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_CONTROL_ADMIN_ANCHOR")
    return candidate_common


def resolve_git_control_directory(repo_root: str, key: bytes) -> Tuple[str, str, Dict[str, Any]]:
    marker_path = os.path.join(repo_root, ".git")
    marker_meta = assert_no_symlink_components(marker_path, "GIT_CONTROL_MARKER")
    marker_observation: Dict[str, Any]
    if stat.S_ISDIR(marker_meta.st_mode):
        git_dir = marker_path
        expected_common_dir = marker_path
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
        expected_common_dir = linked_git_common_anchor(repo_root, git_dir)
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
        if marker_observation["kind"] == "gitfile":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_REQUIRED")
        common_dir = git_dir
        commondir_observation: Dict[str, Any] = {"state": "ABSENT"}
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_LSTAT")
    else:
        if marker_observation["kind"] != "gitfile":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_UNEXPECTED")
        if not stat.S_ISREG(commondir_meta.st_mode) or stat.S_ISLNK(commondir_meta.st_mode):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_TYPE")
        raw, _ = read_absolute_regular(commondir_path, "GIT_COMMONDIR_FILE", 4096)
        if raw != b"../..\n":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_FORMAT")
        try:
            locator = raw[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_ENCODING")
        if not locator or not is_nfc(locator) or "\x00" in locator or "\\" in locator:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_LOCATOR")
        common_dir = os.path.normpath(locator if os.path.isabs(locator) else os.path.join(git_dir, locator))
        commondir_observation = {"state": "PRESENT", "raw_sha256": sha256(raw), "bytes": len(raw)}
    if common_dir != expected_common_dir:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_COMMONDIR_ADMIN_ANCHOR")
    if marker_observation["kind"] == "gitfile":
        reverse_raw, _ = read_absolute_regular(
            os.path.join(git_dir, "gitdir"),
            "GIT_WORKTREE_GITDIR",
            4096,
        )
        if reverse_raw.count(b"\n") != 1 or not reverse_raw.endswith(b"\n"):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_WORKTREE_GITDIR_FORMAT")
        try:
            reverse_path = reverse_raw[:-1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_WORKTREE_GITDIR_ENCODING")
        if (
            not is_nfc(reverse_path)
            or os.path.normpath(reverse_path) != os.path.join(repo_root, ".git")
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_WORKTREE_GITDIR_BINDING")
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


def inspect_git_control_preflight(
    repo_root: str,
    key: bytes,
) -> Tuple[Dict[str, Any], Tuple[str, str]]:
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
    prohibited_controls = {
        os.path.join(common_dir, "objects", "info", "alternates"),
        os.path.join(common_dir, "objects", "info", "http-alternates"),
        os.path.join(common_dir, "info", "grafts"),
        os.path.join(git_dir, "objects", "info", "alternates"),
        os.path.join(git_dir, "objects", "info", "http-alternates"),
    }
    for candidate in sorted(prohibited_controls):
        try:
            os.lstat(candidate)
        except FileNotFoundError:
            continue
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ALTERNATE_CONTROL_LSTAT")
        fail(Exit.PRIVACY, "GIT_ALTERNATE_CONTROL_PROHIBITED")
    observation["alternate_controls"] = "ABSENT"
    return observation, (git_dir, common_dir)


def git_control_preflight(repo_root: str, key: bytes) -> Dict[str, Any]:
    observation, _private_paths = inspect_git_control_preflight(repo_root, key)
    return observation


GIT_ADAPTER_TRACE_PHASES = {
    "SOURCE_CAPTURE_BEGIN": "source-capture",
    "SOURCE_CAPTURE_COMPLETE": "source-capture",
    "ADAPTER_ROOT_CREATED": "adapter-materialization",
    "ADAPTER_METADATA_FROZEN": "adapter-materialization",
    "SOURCE_BOOTSTRAP_PREVALIDATED": "source-cas",
    "OBJECT_ENUMERATION_COMPLETE": "adapter-materialization",
    "OBJECT_PACK_COMPLETE": "adapter-materialization",
    "OBJECT_PACK_VERIFIED": "adapter-materialization",
    "ADAPTER_OBJECTS_FROZEN": "adapter-materialization",
    "OBJECT_CONTENT_VERIFIED": "adapter-seal",
    "SOURCE_BOOTSTRAP_POSTVALIDATED": "source-cas",
    "ADAPTER_SEALED": "adapter-seal",
    "CHILD_PRECHECK_COMPLETE": "git-child",
    "CHILD_EXEC_BEGIN": "git-child",
    "CHILD_POSTCHECK_COMPLETE": "git-child",
    "SOURCE_FINAL_REVALIDATED": "source-cas",
    "CLEANUP_BEGIN": "adapter-cleanup",
    "CLEANUP_FAILED": "adapter-cleanup",
    "CLEANUP_COMPLETE": "adapter-cleanup",
}


def git_adapter_trace_event(
    target: Any,
    event: str,
    phase: str,
) -> None:
    if GIT_ADAPTER_TRACE_PHASES.get(event) != phase:
        fail(Exit.INTERNAL, "GIT_ADAPTER_TRACE_EVENT")
    trace = target.trace if isinstance(target, GitMetadataAdapter) else target
    if not isinstance(trace, list):
        fail(Exit.INTERNAL, "GIT_ADAPTER_TRACE_TARGET")
    trace.append({"event": event, "phase": phase})


def git_source_metadata(metadata: os.stat_result) -> Dict[str, Any]:
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "owner_uid": metadata.st_uid,
        "group_gid": metadata.st_gid,
        "link_count": metadata.st_nlink,
        "bytes": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "flags": getattr(metadata, "st_flags", 0),
    }


def capture_git_source_regular(
    path: str,
    label: str,
    max_bytes: int,
    required: bool,
) -> Tuple[Optional[bytes], Dict[str, Any]]:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        if required:
            fail(Exit.PREFLIGHT_DRIFT, label + "_MISSING")
        return None, {"state": "ABSENT"}
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_LSTAT")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail(Exit.PREFLIGHT_DRIFT, label + "_TYPE")
    raw, opened = read_absolute_regular(path, label, max_bytes)
    if opened.st_uid != os.getuid() or stat.S_IMODE(opened.st_mode) & 0o022:
        fail(Exit.PREFLIGHT_DRIFT, label + "_POLICY")
    path_metadata = os.stat(path, follow_symlinks=False)
    if git_source_metadata(path_metadata) != git_source_metadata(opened):
        fail(Exit.PREFLIGHT_DRIFT, label + "_PATH_RACE")
    return raw, {
        "state": "PRESENT",
        "metadata": git_source_metadata(opened),
        "raw_sha256": sha256(raw),
        "bytes": len(raw),
    }


def capture_git_source_regular_metadata(
    path: str,
    label: str,
    max_bytes: int,
) -> Dict[str, Any]:
    """Capture stable regular-file identity without reading payload bytes."""
    try:
        before = os.lstat(path)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_LSTAT")
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or before.st_uid != os.getuid()
        or stat.S_IMODE(before.st_mode) & 0o022
        or before.st_nlink != 1
        or before.st_size > max_bytes
    ):
        fail(Exit.PREFLIGHT_DRIFT, label + "_POLICY")
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, label + "_OPEN")
    try:
        assert_no_extended_acl_fd(descriptor, label)
        opened = os.fstat(descriptor)
        after = os.stat(path, follow_symlinks=False)
    finally:
        os.close(descriptor)
    if (
        git_source_metadata(before) != git_source_metadata(opened)
        or git_source_metadata(opened) != git_source_metadata(after)
    ):
        fail(Exit.PREFLIGHT_DRIFT, label + "_RACE")
    return {"state": "PRESENT", "metadata": git_source_metadata(opened)}


def capture_git_source_tree(
    path: str,
    label: str,
    required: bool = False,
) -> Tuple[Dict[str, bytes], Dict[str, Any]]:
    try:
        root_metadata = assert_no_symlink_components(path, label)
    except ContractError as error:
        if not required and error.public_code == label + "_MISSING":
            return {}, {"state": "ABSENT", "directories": [], "files": []}
        raise
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or stat.S_IMODE(root_metadata.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT_DRIFT, label + "_POLICY")
    raw_files: Dict[str, bytes] = {}
    directories: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    total_bytes = 0

    def walk(current_path: str, relative: str) -> None:
        nonlocal total_bytes
        before = assert_no_symlink_components(current_path, label + "_DIRECTORY")
        if (
            not stat.S_ISDIR(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) & 0o022
        ):
            fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_POLICY")
        try:
            entries = list(os.scandir(current_path))
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_SCAN")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            name = entry.name
            if (
                not isinstance(name, str)
                or not is_nfc(name)
                or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in name)
            ):
                fail(Exit.PREFLIGHT_DRIFT, label + "_NAME")
            child_relative = name if not relative else relative + "/" + name
            child_path = os.path.join(current_path, name)
            child_metadata = os.lstat(child_path)
            if stat.S_ISLNK(child_metadata.st_mode):
                fail(Exit.PREFLIGHT_DRIFT, label + "_SYMLINK")
            if stat.S_ISDIR(child_metadata.st_mode):
                walk(child_path, child_relative)
            elif stat.S_ISREG(child_metadata.st_mode):
                raw, observation = capture_git_source_regular(
                    child_path,
                    label + "_FILE",
                    MAX_GIT_CONTROL_BYTES,
                    required=True,
                )
                if raw is None:
                    fail(Exit.INTERNAL, "GIT_SOURCE_TREE_REQUIRED_FILE")
                total_bytes += len(raw)
                if total_bytes > MAX_GIT_OUTPUT:
                    fail(Exit.PREFLIGHT_DRIFT, label + "_SIZE")
                raw_files[child_relative] = raw
                files.append({"relative": child_relative, "observation": observation})
            else:
                fail(Exit.PREFLIGHT_DRIFT, label + "_SPECIAL")
        after = os.stat(current_path, follow_symlinks=False)
        if git_source_metadata(before) != git_source_metadata(after):
            fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_RACE")
        directories.append({"relative": relative, "metadata": git_source_metadata(before)})

    walk(path, "")
    return raw_files, {
        "state": "PRESENT",
        "directories": sorted(directories, key=lambda item: item["relative"]),
        "files": sorted(files, key=lambda item: item["relative"]),
    }


def capture_git_object_store_anchor(path: str) -> Dict[str, Any]:
    root = assert_no_symlink_components(path, "GIT_OBJECT_SOURCE_DIRECTORY")
    if (
        not stat.S_ISDIR(root.st_mode)
        or root.st_uid != os.getuid()
        or stat.S_IMODE(root.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_SOURCE_DIRECTORY_POLICY")
    body = {
        "profile": "live-object-root-anchor-no-container-enumeration-v1",
        "root_anchor": {
            "device": root.st_dev,
            "inode": root.st_ino,
            "mode": root.st_mode,
            "owner_uid": root.st_uid,
            "group_gid": root.st_gid,
            "flags": getattr(root, "st_flags", 0),
        },
        "alternate_controls": "ABSENT",
    }
    return {"fingerprint": sha256(canonical_json(body)), **body}


def capture_git_pack_index_search(path: str) -> Dict[str, Any]:
    def directory_anchor(metadata: os.stat_result) -> Dict[str, Any]:
        return {
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "mode": metadata.st_mode,
            "owner_uid": metadata.st_uid,
            "group_gid": metadata.st_gid,
            "flags": getattr(metadata, "st_flags", 0),
        }

    root = assert_no_symlink_components(path, "GIT_OBJECT_SOURCE_DIRECTORY")
    if (
        not stat.S_ISDIR(root.st_mode)
        or root.st_uid != os.getuid()
        or stat.S_IMODE(root.st_mode) & 0o022
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_SOURCE_DIRECTORY_POLICY")
    pack_path = os.path.join(path, "pack")
    pack_index_records: List[Dict[str, Any]] = []
    pack_index_bytes: Dict[str, bytes] = {}
    pack_index_observations: Dict[str, Dict[str, Any]] = {}
    pack_file_names: List[str] = []
    total_index_bytes = 0
    try:
        pack_before = os.lstat(pack_path)
    except FileNotFoundError:
        pack_state: Dict[str, Any] = {"state": "ABSENT"}
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_LSTAT")
    else:
        if (
            stat.S_ISLNK(pack_before.st_mode)
            or not stat.S_ISDIR(pack_before.st_mode)
            or pack_before.st_uid != os.getuid()
            or stat.S_IMODE(pack_before.st_mode) & 0o022
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_POLICY")
        try:
            entries = list(os.scandir(pack_path))
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_SCAN")
        if len(entries) > MAX_GIT_ADAPTER_ENTRIES:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_LIMIT")
        allowed_pack_name = re.compile(
            r"pack-(?:[0-9a-f]{40}|[0-9a-f]{64})\.(?:pack|idx)"
        )
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            name = entry.name
            if not isinstance(name, str):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_NAME")
            if allowed_pack_name.fullmatch(name) is None:
                # Reverse indexes, bitmaps and unrelated cruft are outside the
                # exact OID bridge.  They are neither opened nor committed.
                continue
            pack_file_names.append(name)
            candidate = os.path.join(pack_path, name)
            if name.endswith(".idx"):
                raw, observation = capture_git_source_regular(
                    candidate,
                    "GIT_OBJECT_PACK_INDEX",
                    MAX_GIT_INDEX_BYTES,
                    required=True,
                )
                if raw is None:
                    fail(Exit.INTERNAL, "GIT_OBJECT_PACK_INDEX_REQUIRED")
                pack_index_bytes[name] = raw
                metadata = observation["metadata"]
                total_index_bytes += len(raw)
                if total_index_bytes > MAX_GIT_INDEX_BYTES:
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_BYTES")
                pack_index_observations[name] = observation
                pack_index_records.append({"name": name, "observation": observation})
        pack_names = set(pack_file_names)
        for name in pack_names:
            stem, suffix = name.rsplit(".", 1)
            peer = stem + (".idx" if suffix == "pack" else ".pack")
            if peer not in pack_names:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_PAIR")
        pack_after = os.stat(pack_path, follow_symlinks=False)
        if git_source_metadata(pack_before) != git_source_metadata(pack_after):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_CONTAINER_RACE")
        pack_state = {
            "state": "PRESENT",
            "directory_anchor": directory_anchor(pack_before),
            "matching_name_count": len(pack_file_names),
            "index_count": len(pack_index_records),
            "index_bytes": total_index_bytes,
            "index_receipt_sha256": sha256(canonical_json(pack_index_records)),
        }
    control = {
        "profile": "pack-index-search-catalog-private-transient-v1",
        "root_anchor": directory_anchor(root),
        "pack_container": pack_state,
        "alternate_controls": "ABSENT",
    }
    return {
        "fingerprint": sha256(canonical_json(control)),
        "pack_entry_count": len(pack_file_names),
        "pack_index_bytes_total": total_index_bytes,
        "pack_file_names": tuple(pack_file_names),
        "pack_index_bytes": pack_index_bytes,
        "pack_index_observations": pack_index_observations,
        "profile": control["profile"],
    }


def parse_git_pack_index_v2(
    raw: bytes,
    oid_length: int,
    index_name: str,
    requested_oids: Sequence[str],
) -> Tuple[str, ...]:
    """Return requested OIDs present in one independently validated pack index."""

    oid_bytes = oid_length // 2
    if (
        oid_length not in (40, 64)
        or re.fullmatch(r"pack-[0-9a-f]{%d}\.idx" % oid_length, index_name) is None
        or any(re.fullmatch(r"[0-9a-f]{%d}" % oid_length, oid) is None for oid in requested_oids)
        or len(raw) < 8 + 256 * 4 + 2 * oid_bytes
        or raw[:4] != b"\xfftOc"
        or int.from_bytes(raw[4:8], "big") != 2
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_FORMAT")
    fanout = tuple(
        int.from_bytes(raw[8 + index * 4:12 + index * 4], "big")
        for index in range(256)
    )
    if any(fanout[index] < fanout[index - 1] for index in range(1, 256)):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_FANOUT")
    object_count = fanout[-1]
    if object_count > MAX_GIT_ADAPTER_ENTRIES:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_COUNT")
    names_start = 8 + 256 * 4
    names_end = names_start + object_count * oid_bytes
    crc_end = names_end + object_count * 4
    offsets_end = crc_end + object_count * 4
    if offsets_end + 2 * oid_bytes > len(raw):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_LENGTH")
    large_offset_indexes: List[int] = []
    for index in range(object_count):
        value = int.from_bytes(raw[crc_end + index * 4:crc_end + (index + 1) * 4], "big")
        if value & 0x80000000:
            large_offset_indexes.append(value & 0x7FFFFFFF)
    if sorted(large_offset_indexes) != list(range(len(large_offset_indexes))):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_LARGE_OFFSET")
    trailer_start = offsets_end + len(large_offset_indexes) * 8
    if trailer_start + 2 * oid_bytes != len(raw):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_LENGTH")
    digest = hashlib.sha1() if oid_length == 40 else hashlib.sha256()
    digest.update(raw[:-oid_bytes])
    if not hmac.compare_digest(digest.digest(), raw[-oid_bytes:]):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_CHECKSUM")
    expected_pack_checksum = index_name[len("pack-"):-len(".idx")]
    if raw[trailer_start:trailer_start + oid_bytes].hex() != expected_pack_checksum:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_PACK_BINDING")

    counts = [0] * 256
    previous = b""
    for index in range(object_count):
        start = names_start + index * oid_bytes
        current = raw[start:start + oid_bytes]
        if index and current <= previous:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_ORDER")
        counts[current[0]] += 1
        previous = current
    cumulative = 0
    for index, count in enumerate(counts):
        cumulative += count
        if fanout[index] != cumulative:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_INDEX_FANOUT")

    matches: List[str] = []
    for oid in sorted(set(requested_oids)):
        raw_oid = bytes.fromhex(oid)
        first = raw_oid[0]
        low = fanout[first - 1] if first else 0
        high = fanout[first]
        while low < high:
            middle = (low + high) // 2
            start = names_start + middle * oid_bytes
            candidate = raw[start:start + oid_bytes]
            if candidate < raw_oid:
                low = middle + 1
            else:
                high = middle
        start = names_start + low * oid_bytes
        if low < fanout[first] and raw[start:start + oid_bytes] == raw_oid:
            matches.append(oid)
    return tuple(matches)


def capture_git_object_dependencies(path: str, object_oids: Sequence[str]) -> Dict[str, Any]:
    if not object_oids or len(set(object_oids)) != len(object_oids):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_OIDS")
    oid_length = len(object_oids[0])
    if oid_length not in (40, 64) or any(
        re.fullmatch(r"[0-9a-f]{%d}" % oid_length, oid) is None
        for oid in object_oids
    ):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_OIDS")
    object_root = capture_git_object_store_anchor(path)
    loose_records: List[Dict[str, Any]] = []
    missing_oids = set(object_oids)
    for oid in sorted(object_oids):
        loose_path = os.path.join(path, oid[:2], oid[2:])
        _raw, observation = capture_git_source_regular(
            loose_path,
            "GIT_OBJECT_DEPENDENCY_LOOSE",
            MAX_GIT_ADAPTER_FILE_BYTES,
            required=False,
        )
        if observation["state"] == "PRESENT":
            missing_oids.remove(oid)
        loose_records.append({"oid": oid, "observation": observation})
    bridge = capture_git_pack_index_search(path) if missing_oids else {
        "pack_index_bytes": {},
        "pack_index_observations": {},
    }
    pack_index_observations = bridge.get("pack_index_observations")
    pack_index_bytes = bridge.get("pack_index_bytes")
    if not isinstance(pack_index_observations, dict) or not isinstance(pack_index_bytes, dict):
        fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_PACK_CAPTURE")
    candidates: Dict[str, List[str]] = {oid: [] for oid in missing_oids}
    for index_name in sorted(pack_index_bytes, key=os.fsencode):
        raw = pack_index_bytes[index_name]
        observation = pack_index_observations.get(index_name)
        if not isinstance(raw, bytes) or not isinstance(observation, dict):
            fail(Exit.INTERNAL, "GIT_OBJECT_DEPENDENCY_PACK_CAPTURE")
        for oid in parse_git_pack_index_v2(raw, oid_length, index_name, tuple(missing_oids)):
            candidates[oid].append(index_name[:-4])
    selected_stems = set()
    for oid in sorted(missing_oids):
        stems = sorted(candidates[oid])
        if not stems:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_DEPENDENCY_MISSING")
        selected_stems.add(stems[0])
    selected_records: List[Dict[str, Any]] = []
    allowed_pack_paths: List[str] = []
    for stem in sorted(selected_stems):
        for suffix in (".idx", ".pack"):
            name = stem + suffix
            if suffix == ".idx":
                observation = pack_index_observations.get(name)
            else:
                observation = capture_git_source_regular_metadata(
                    os.path.join(path, "pack", name),
                    "GIT_OBJECT_DEPENDENCY_PACK",
                    MAX_GIT_ADAPTER_FILE_BYTES,
                )
            if not isinstance(observation, dict):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_DEPENDENCY_PACK_PAIR")
            selected_records.append({"name": name, "observation": observation})
            allowed_pack_paths.append(os.path.join(path, "pack", name))
    body = {
        "profile": GIT_OBJECT_DEPENDENCY_PROFILE_V3,
        "object_root_anchor_fingerprint": object_root["fingerprint"],
        "object_count": len(object_oids),
        "oid_set_sha256": sha256(canonical_json(sorted(object_oids))),
        "loose_dependency_receipt_sha256": sha256(canonical_json(loose_records)),
        "selected_pack_container_count": len(selected_stems),
        "selected_pack_container_receipt_sha256": sha256(canonical_json(selected_records)),
    }
    return {
        "fingerprint": sha256(canonical_json(body)),
        "allowed_pack_paths": tuple(allowed_pack_paths),
        **body,
    }


def parse_git_hooks_path(configs: Sequence[Optional[bytes]]) -> Optional[str]:
    hooks_path: Optional[str] = None
    for raw in configs:
        if raw is None:
            continue
        try:
            text = raw.decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CONFIG_ENCODING")
        section = ""
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ";")):
                continue
            if stripped.startswith("["):
                match = re.fullmatch(
                    r'\[\s*([A-Za-z0-9.-]+)(?:\s+"(?:[^"\\]|\\.)*")?\s*\](?:\s*[#;].*)?',
                    stripped,
                )
                if match is None:
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_CONFIG_SECTION_FORMAT")
                section = match.group(1).casefold()
                continue
            if section != "core":
                continue
            match = re.fullmatch(r"(?i:hookspath)\s*=\s*(.*?)\s*", stripped)
            if match is None:
                continue
            value = match.group(1)
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if (
                not value
                or "\\" in value
                or "\x00" in value
                or not is_nfc(value)
                or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in value)
            ):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_HOOKS_OVERRIDE_FORMAT")
            if hooks_path is not None:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_HOOKS_OVERRIDE_DUPLICATE")
            hooks_path = value
    return hooks_path


def captured_ref_map(capture: Mapping[str, Any]) -> Dict[str, bytes]:
    refs: Dict[str, bytes] = {}
    for prefix, key_name in (("refs", "common_ref_bytes"), ("refs", "worktree_ref_bytes")):
        source = capture.get(key_name)
        if not isinstance(source, dict):
            fail(Exit.INTERNAL, "GIT_CAPTURE_REFS")
        for relative, raw in source.items():
            if not isinstance(relative, str) or not isinstance(raw, bytes):
                fail(Exit.INTERNAL, "GIT_CAPTURE_REF_ENTRY")
            reference = prefix + "/" + relative
            previous = refs.get(reference)
            if previous is not None and previous != raw:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_REF_COLLISION")
            refs[reference] = raw
    packed = capture.get("raw_files", {}).get("packed_refs")
    if packed is not None:
        if not isinstance(packed, bytes):
            fail(Exit.INTERNAL, "GIT_CAPTURE_PACKED_REFS")
        for line in packed.splitlines():
            if not line or line.startswith((b"#", b"^")):
                continue
            fields = line.split(b" ")
            if len(fields) != 2:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_PACKED_REFS_FORMAT")
            try:
                oid = fields[0].decode("ascii", "strict")
                reference = fields[1].decode("ascii", "strict")
            except UnicodeDecodeError:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_PACKED_REFS_ENCODING")
            if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid) is None or not reference.startswith("refs/"):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_PACKED_REFS_VALUE")
            refs.setdefault(reference, (oid + "\n").encode("ascii"))
    return refs


def captured_head_oid(capture: Mapping[str, Any]) -> str:
    raw_files = capture.get("raw_files")
    if not isinstance(raw_files, dict) or not isinstance(raw_files.get("head"), bytes):
        fail(Exit.INTERNAL, "GIT_CAPTURE_HEAD")
    current = raw_files["head"]
    refs = captured_ref_map(capture)
    seen = set()
    for _depth in range(8):
        if current.count(b"\n") != 1 or not current.endswith(b"\n"):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_FORMAT")
        if current.startswith(b"ref: "):
            try:
                reference = current[5:-1].decode("ascii", "strict")
            except UnicodeDecodeError:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_ENCODING")
            if reference in seen or reference not in refs or not reference.startswith("refs/"):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_REF")
            seen.add(reference)
            current = refs[reference]
            continue
        try:
            oid = current[:-1].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_OID")
        if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid) is None:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_OID")
        return oid
    fail(Exit.PREFLIGHT_DRIFT, "GIT_CAPTURE_HEAD_DEPTH")
    raise AssertionError("unreachable")


def capture_git_metadata_source(repo_root: str, key: bytes) -> Dict[str, Any]:
    git_control, (git_dir, common_dir) = inspect_git_control_preflight(repo_root, key)
    specs = (
        ("head", os.path.join(git_dir, "HEAD"), MAX_GIT_CONTROL_BYTES, True),
        ("index", os.path.join(git_dir, "index"), MAX_GIT_INDEX_BYTES, True),
        ("common_config", os.path.join(common_dir, "config"), MAX_GIT_CONTROL_BYTES, True),
        ("worktree_config", os.path.join(git_dir, "config.worktree"), MAX_GIT_CONTROL_BYTES, False),
        ("packed_refs", os.path.join(common_dir, "packed-refs"), MAX_GIT_INDEX_BYTES, False),
        ("shallow", os.path.join(common_dir, "shallow"), MAX_GIT_INDEX_BYTES, False),
        ("info_exclude", os.path.join(common_dir, "info", "exclude"), MAX_GIT_CONTROL_BYTES, False),
    )
    raw_files: Dict[str, Optional[bytes]] = {}
    file_observations: Dict[str, Any] = {}
    for role, path, limit, required in specs:
        raw, observation = capture_git_source_regular(
            path,
            "GIT_SOURCE_" + role.upper(),
            limit,
            required,
        )
        raw_files[role] = raw
        file_observations[role] = observation
    common_ref_bytes, common_refs = capture_git_source_tree(
        os.path.join(common_dir, "refs"),
        "GIT_SOURCE_COMMON_REFS",
        required=False,
    )
    if git_dir == common_dir:
        worktree_ref_bytes: Dict[str, bytes] = {}
        worktree_refs = {"state": "ABSENT", "directories": [], "files": []}
    else:
        worktree_ref_bytes, worktree_refs = capture_git_source_tree(
            os.path.join(git_dir, "refs"),
            "GIT_SOURCE_WORKTREE_REFS",
            required=False,
        )
    objects_path = os.path.join(common_dir, "objects")
    objects = capture_git_object_store_anchor(objects_path)
    hooks_override = parse_git_hooks_path(
        (raw_files["common_config"], raw_files["worktree_config"])
    )
    if hooks_override is None:
        hooks_path = os.path.join(common_dir, "hooks")
        hooks_info = hash_directory_tree_absolute(hooks_path, "GIT_HOOKS")
        hooks_state = "default-git-path"
    else:
        hooks_path = os.path.normpath(
            hooks_override if os.path.isabs(hooks_override) else os.path.join(repo_root, hooks_override)
        )
        if hooks_path == "/dev/null":
            hooks_info = hash_regular_absolute(hooks_path, "GIT_HOOKS_DISABLED", 4096)
            hooks_state = "configured-dev-null"
        elif is_same_or_within(hooks_path, common_dir) or is_same_or_within(hooks_path, repo_root):
            hooks_info = hash_directory_tree_absolute(hooks_path, "GIT_HOOKS")
            hooks_state = "configured-git-contained"
        else:
            fail(Exit.PREFLIGHT_DRIFT, "EXTERNAL_HOOKS_PATH")
    hooks_source = {
        "path_commitment": locator_commitment(key, "git-hooks", hooks_path),
        "state": hooks_state,
        "evidence": hooks_info,
    }
    identity = {
        "git_control": git_control,
        "git_dir": git_source_metadata(assert_no_symlink_components(git_dir, "GIT_SOURCE_GIT_DIR")),
        "common_dir": git_source_metadata(assert_no_symlink_components(common_dir, "GIT_SOURCE_COMMON_DIR")),
        "files": file_observations,
        "common_refs": common_refs,
        "worktree_refs": worktree_refs,
        "objects": objects,
        "hooks": hooks_source,
    }
    capture = {
        "git_dir": git_dir,
        "common_dir": common_dir,
        "git_control": git_control,
        "raw_files": raw_files,
        "common_ref_bytes": common_ref_bytes,
        "worktree_ref_bytes": worktree_ref_bytes,
        "objects_path": objects_path,
        "hooks_path": hooks_path,
        "hooks_state": hooks_state,
        "hooks_info": hooks_info,
        "identity": identity,
        "fingerprint": sha256(canonical_json(identity)),
    }
    capture["head_oid"] = captured_head_oid(capture)
    return capture


def open_git_adapter_directory_at(
    adapter_fd: int,
    components: Sequence[str],
    label: str,
    create: bool,
) -> int:
    current = os.dup(adapter_fd)
    try:
        for component in components:
            if (
                not isinstance(component, str)
                or not component
                or component in (".", "..")
                or "/" in component
                or "\\" in component
                or "\x00" in component
                or not is_nfc(component)
            ):
                fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_NAME")
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=current,
                )
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o700, dir_fd=current)
                next_fd = os.open(
                    component,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=current,
                )
            metadata = os.fstat(next_fd)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) & 0o022
            ):
                os.close(next_fd)
                fail(Exit.PREFLIGHT_DRIFT, label + "_DIRECTORY_POLICY")
            os.close(current)
            current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def mkdir_git_adapter_directory_at(adapter_fd: int, relative: str, label: str) -> None:
    components = validate_relative(relative, label)
    directory_fd = open_git_adapter_directory_at(adapter_fd, components, label, create=True)
    os.close(directory_fd)


def write_git_adapter_file_at(adapter_fd: int, relative: str, raw: bytes, label: str) -> None:
    components = validate_relative(relative, label)
    parent_fd = open_git_adapter_directory_at(adapter_fd, components[:-1], label, create=True)
    try:
        fd = os.open(
            components[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_fd,
        )
    except OSError:
        os.close(parent_fd)
        fail(Exit.PREFLIGHT_DRIFT, label + "_CREATE")
    try:
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(fd, raw[offset:])
            except OSError:
                fail(Exit.PREFLIGHT_DRIFT, label + "_WRITE")
            if written <= 0:
                fail(Exit.PREFLIGHT_DRIFT, label + "_WRITE")
            offset += written
        os.fsync(fd)
        final = os.fstat(fd)
        if final.st_size != len(raw) or final.st_nlink != 1:
            fail(Exit.PREFLIGHT_DRIFT, label + "_FINAL")
    finally:
        os.close(fd)
        os.close(parent_fd)


def hash_git_adapter_file_at(
    adapter_fd: int,
    relative: str,
    label: str,
    max_bytes: int,
) -> Dict[str, Any]:
    components = validate_relative(relative, label)
    parent_fd = open_git_adapter_directory_at(adapter_fd, components[:-1], label, create=False)
    try:
        metadata = os.stat(components[-1], dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            fail(Exit.PREFLIGHT_DRIFT, label + "_TYPE")
        file_fd = os.open(
            components[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        try:
            opened = os.fstat(file_fd)
            if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                fail(Exit.PREFLIGHT_DRIFT, label + "_RACE")
            digest, length = hash_fd(file_fd, "sha256", max_bytes, label)
        finally:
            os.close(file_fd)
    finally:
        os.close(parent_fd)
    return {
        "sha256": digest,
        "bytes": length,
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


def git_adapter_fd_path(fd: int, label: str) -> str:
    command = getattr(fcntl, "F_GETPATH", None)
    if command is None:
        fail(Exit.PREFLIGHT_DRIFT, label + "_IDENTITY_UNAVAILABLE")
    try:
        raw = fcntl.fcntl(fd, command, b"\x00" * 1024)
        return os.fsdecode(raw.split(b"\x00", 1)[0])
    except (OSError, UnicodeError, ValueError):
        fail(Exit.PREFLIGHT_DRIFT, label + "_IDENTITY")
    raise AssertionError("unreachable")


def verify_unsealed_git_adapter_root(
    adapter_root: str,
    adapter_identity: Tuple[int, int],
    adapter_fd: int,
) -> None:
    validate_git_adapter_locator(adapter_root)
    try:
        metadata = os.lstat(adapter_root)
        opened = os.fstat(adapter_fd)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_BUILD_ROOT")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or (metadata.st_dev, metadata.st_ino) != adapter_identity
        or (opened.st_dev, opened.st_ino) != adapter_identity
        or git_adapter_fd_path(adapter_fd, "GIT_ADAPTER_BUILD_ROOT") != adapter_root
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_BUILD_ROOT")


def verify_unsealed_git_adapter_git_directory(
    adapter_root: str,
    adapter_fd: int,
    git_fd: int,
    git_identity: Tuple[int, int],
) -> None:
    try:
        named = os.stat("git", dir_fd=adapter_fd, follow_symlinks=False)
        opened = os.fstat(git_fd)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_BUILD_GIT_DIRECTORY")
    if (
        stat.S_ISLNK(named.st_mode)
        or not stat.S_ISDIR(named.st_mode)
        or named.st_uid != os.getuid()
        or stat.S_IMODE(named.st_mode) != 0o700
        or (named.st_dev, named.st_ino) != git_identity
        or (opened.st_dev, opened.st_ino) != git_identity
        or git_adapter_fd_path(git_fd, "GIT_ADAPTER_BUILD_GIT_DIRECTORY")
        != os.path.join(adapter_root, "git")
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_BUILD_GIT_DIRECTORY")


def assert_git_source_capture_unchanged(
    capture: Mapping[str, Any],
    repo_root: str,
    key: bytes,
    public_code: str,
) -> None:
    recaptured = capture_git_metadata_source(repo_root, key)
    if (
        recaptured["git_dir"] != capture.get("git_dir")
        or recaptured["common_dir"] != capture.get("common_dir")
        or recaptured["fingerprint"] != capture.get("fingerprint")
    ):
        fail(Exit.PREFLIGHT_DRIFT, public_code)


def run_git_object_bootstrap_child(
    *,
    git_binary: str,
    developer_root: str,
    repo_root: str,
    capture: Mapping[str, Any],
    adapter_root: str,
    adapter_git_dir: str,
    adapter_fd: int,
    git_fd: int,
    adapter_identity: Tuple[int, int],
    git_identity: Tuple[int, int],
    arguments: Sequence[str],
    label: str,
    max_output: int,
    allow_live_objects: bool,
    allow_adapter_writes: bool,
    allowed_live_oids: Sequence[str] = (),
    allowed_pack_paths: Sequence[str] = (),
    stdin_bytes: Optional[bytes] = None,
) -> bytes:
    verify_unsealed_git_adapter_root(adapter_root, adapter_identity, adapter_fd)
    verify_unsealed_git_adapter_git_directory(adapter_root, adapter_fd, git_fd, git_identity)
    live_objects = str(capture["objects_path"])
    environment = git_env(live_objects if allow_live_objects else None)
    argv = git_hardened_child_argv(git_binary, repo_root, adapter_git_dir, arguments)
    require_git_child_template_match(
        role="git-metadata-adapter-bootstrap",
        argv=argv,
        environment=environment,
        git_binary=git_binary,
        repo_root=repo_root,
        adapter_git_dir=adapter_git_dir,
        live_objects=live_objects if allow_live_objects else None,
        stdin_bytes=stdin_bytes,
    )
    git_adapter_trace_event(capture["adapter_trace"], "CHILD_PRECHECK_COMPLETE", "git-child")
    git_adapter_trace_event(capture["adapter_trace"], "CHILD_EXEC_BEGIN", "git-child")
    try:
        return run_process(
            argv,
            environment,
            max_output,
            label,
            sandbox_profile=git_object_bootstrap_sandbox_profile(
                git_binary,
                repo_root,
                developer_root,
                adapter_root,
                adapter_git_dir,
                str(capture["git_dir"]),
                str(capture["common_dir"]),
                live_objects,
                allow_live_objects,
                allow_adapter_writes,
                allowed_live_oids,
                allowed_pack_paths,
            ),
            stdin_bytes=stdin_bytes,
            working_directory_fd=git_fd,
        )
    finally:
        verify_unsealed_git_adapter_root(adapter_root, adapter_identity, adapter_fd)
        verify_unsealed_git_adapter_git_directory(adapter_root, adapter_fd, git_fd, git_identity)
        git_adapter_trace_event(capture["adapter_trace"], "CHILD_POSTCHECK_COMPLETE", "git-child")


def parse_git_cat_file_batch_exact(
    raw: bytes,
    expected_types: Mapping[str, str],
    maximum_bytes: int,
    label: str,
) -> Tuple[Dict[str, Tuple[str, bytes]], str]:
    expected_oids = sorted(expected_types)
    if not expected_oids:
        fail(Exit.INTERNAL, label + "_EXPECTATION")
    oid_length = len(expected_oids[0])
    result: Dict[str, Tuple[str, bytes]] = {}
    receipt_rows: List[Dict[str, Any]] = []
    cursor = 0
    content_bytes = 0
    for expected_oid in expected_oids:
        newline = raw.find(b"\n", cursor)
        if newline < 0 or newline - cursor > 256:
            fail(Exit.PREFLIGHT_DRIFT, label + "_HEADER")
        fields = raw[cursor:newline].split(b" ")
        cursor = newline + 1
        if len(fields) != 3:
            fail(Exit.PREFLIGHT_DRIFT, label + "_HEADER")
        try:
            observed_oid = fields[0].decode("ascii", "strict")
            object_type = fields[1].decode("ascii", "strict")
            size_text = fields[2].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, label + "_HEADER")
        if (
            observed_oid != expected_oid
            or object_type != expected_types[expected_oid]
            or re.fullmatch(r"0|[1-9][0-9]*", size_text) is None
        ):
            fail(Exit.PREFLIGHT_DRIFT, label + "_HEADER")
        size = int(size_text, 10)
        content_bytes += size
        end = cursor + size
        if (
            size > MAX_GIT_ADAPTER_FILE_BYTES
            or content_bytes > maximum_bytes
            or end >= len(raw)
            or raw[end:end + 1] != b"\n"
        ):
            fail(Exit.PREFLIGHT_DRIFT, label + "_BODY")
        content = raw[cursor:end]
        cursor = end + 1
        digest = hashlib.sha1() if oid_length == 40 else hashlib.sha256()
        digest.update((object_type + " " + str(size) + "\x00").encode("ascii"))
        digest.update(content)
        if not hmac.compare_digest(digest.hexdigest(), expected_oid):
            fail(Exit.PREFLIGHT_DRIFT, label + "_OID")
        result[expected_oid] = (object_type, content)
        receipt_rows.append({"oid": expected_oid, "type": object_type, "bytes": size})
    if cursor != len(raw) or set(result) != set(expected_types):
        fail(Exit.PREFLIGHT_DRIFT, label + "_SET")
    return result, sha256(canonical_json(receipt_rows))


def parse_git_tree_object_entries(raw: bytes, oid_length: int) -> List[Tuple[str, str, str]]:
    raw_oid_length = oid_length // 2
    cursor = 0
    entries: List[Tuple[str, str, str]] = []
    names = set()
    while cursor < len(raw):
        space = raw.find(b" ", cursor)
        nul = raw.find(b"\x00", space + 1 if space >= 0 else cursor)
        if space < 0 or nul < 0 or nul == space + 1:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_OBJECT_FORMAT")
        try:
            mode = raw[cursor:space].decode("ascii", "strict")
            name = raw[space + 1:nul].decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_OBJECT_ENCODING")
        oid_end = nul + 1 + raw_oid_length
        if oid_end > len(raw):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_OBJECT_OID")
        oid = raw[nul + 1:oid_end].hex()
        if (
            name in names
            or not name
            or "/" in name
            or "\\" in name
            or "\x00" in name
            or not is_nfc(name)
            or any(unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in name)
            or re.fullmatch(r"[0-9a-f]{%d}" % oid_length, oid) is None
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_OBJECT_ENTRY")
        names.add(name)
        if mode == "40000":
            object_type = "tree"
        elif mode in ("100644", "100755", "120000"):
            object_type = "blob"
        else:
            # Includes mode 160000 gitlinks/submodules.
            fail(Exit.PRIVACY, "GIT_TREE_OBJECT_TYPE")
        entries.append((name, object_type, oid if object_type == "tree" else mode + ":" + oid))
        cursor = oid_end
    return entries


def discover_git_object_closure(
    *,
    capture: Mapping[str, Any],
    git_binary: str,
    developer_root: str,
    repo_root: str,
    adapter_root: str,
    adapter_git_dir: str,
    adapter_fd: int,
    git_fd: int,
    adapter_identity: Tuple[int, int],
    git_identity: Tuple[int, int],
) -> Tuple[List[str], Dict[str, str], str, Dict[str, Any]]:
    head_oid = str(capture["head_oid"])
    oid_length = len(head_oid)

    def read_exact(expected_types: Mapping[str, str], label: str) -> Dict[str, Tuple[str, bytes]]:
        dependencies_before = capture_git_object_dependencies(
            str(capture["objects_path"]),
            tuple(sorted(expected_types)),
        )
        request = b"".join(oid.encode("ascii") + b"\n" for oid in sorted(expected_types))
        response = run_git_object_bootstrap_child(
            git_binary=git_binary,
            developer_root=developer_root,
            repo_root=repo_root,
            capture=capture,
            adapter_root=adapter_root,
            adapter_git_dir=adapter_git_dir,
            adapter_fd=adapter_fd,
            git_fd=git_fd,
            adapter_identity=adapter_identity,
            git_identity=git_identity,
            arguments=["cat-file", "--batch"],
            label=label,
            max_output=MAX_GIT_INDEX_BYTES,
            allow_live_objects=True,
            allow_adapter_writes=False,
            allowed_live_oids=tuple(sorted(expected_types)),
            allowed_pack_paths=dependencies_before["allowed_pack_paths"],
            stdin_bytes=request,
        )
        parsed, _receipt = parse_git_cat_file_batch_exact(
            response,
            expected_types,
            MAX_GIT_INDEX_BYTES,
            label,
        )
        dependencies_after = capture_git_object_dependencies(
            str(capture["objects_path"]),
            tuple(sorted(expected_types)),
        )
        if dependencies_after["fingerprint"] != dependencies_before["fingerprint"]:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_OBJECT_DEPENDENCY_DRIFT")
        return parsed

    commit_content = read_exact({head_oid: "commit"}, "GIT_OBJECT_HEAD_COMMIT")[head_oid][1]
    first_line = commit_content.split(b"\n", 1)[0]
    try:
        root_tree_oid = first_line[5:].decode("ascii", "strict") if first_line.startswith(b"tree ") else ""
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ROOT_TREE_FORMAT")
    if re.fullmatch(r"[0-9a-f]{%d}" % oid_length, root_tree_oid) is None:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ROOT_TREE_FORMAT")
    tree_content: Dict[str, bytes] = {}
    pending_contexts: List[Tuple[str, str]] = [(root_tree_oid, "")]
    processed_contexts = set()
    tree_oids = {root_tree_oid}
    approved_paths = {path for _role, path in PENDING_STATIC_ARTIFACT_SPECS}
    if len(PENDING_STATIC_ARTIFACT_SPECS) != 20 or len(approved_paths) != 20:
        fail(Exit.INTERNAL, "GIT_OBJECT_APPROVED_PATH_PROFILE")
    approved_blobs: Dict[str, str] = {}
    observed_paths = set()
    observed_casefold: Dict[str, str] = {}
    while pending_contexts:
        missing = sorted({oid for oid, _prefix in pending_contexts if oid not in tree_content})
        if missing:
            batch = read_exact({oid: "tree" for oid in missing}, "GIT_OBJECT_TREE_BATCH")
            tree_content.update({oid: value[1] for oid, value in batch.items()})
        next_contexts: List[Tuple[str, str]] = []
        for tree_oid, prefix in pending_contexts:
            context = (tree_oid, prefix)
            if context in processed_contexts:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_CONTEXT_DUPLICATE")
            processed_contexts.add(context)
            for name, object_type, encoded_target in parse_git_tree_object_entries(
                tree_content[tree_oid],
                oid_length,
            ):
                path = name if not prefix else prefix + "/" + name
                validate_relative(path, "GIT_OBJECT_ENUMERATION_PATH")
                folded = unicodedata.normalize("NFC", path).casefold()
                if path in observed_paths or (folded in observed_casefold and observed_casefold[folded] != path):
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_PATH_COLLISION")
                observed_paths.add(path)
                observed_casefold[folded] = path
                if object_type == "tree":
                    tree_oids.add(encoded_target)
                    next_contexts.append((encoded_target, path))
                else:
                    mode, blob_oid = encoded_target.split(":", 1)
                    if path in approved_paths:
                        if mode != "100644":
                            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_APPROVED_BLOB_MODE")
                        approved_blobs[path] = blob_oid
                if len(observed_paths) > MAX_GIT_ADAPTER_ENTRIES:
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_LIMIT")
        pending_contexts = next_contexts
    if set(approved_blobs) != approved_paths:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_APPROVED_BLOB_MISSING")
    object_types: Dict[str, str] = {head_oid: "commit"}
    for oid in tree_oids:
        if object_types.setdefault(oid, "tree") != "tree":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_TYPE_COLLISION")
    for oid in approved_blobs.values():
        if object_types.setdefault(oid, "blob") != "blob":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_TYPE_COLLISION")
    object_oids = sorted(object_types)
    manifest = {
        "profile": GIT_METADATA_OBJECT_CLOSURE_PROFILE_V2,
        "object_format": "sha1" if oid_length == 40 else "sha256",
        "object_count": len(object_oids),
        "tree_object_count": len(tree_oids),
        "approved_artifact_blob_count": len(approved_blobs),
        "oid_set_sha256": sha256(canonical_json(object_oids)),
    }
    return object_oids, object_types, root_tree_oid, manifest


def parse_git_ls_tree_object_closure(
    raw: bytes,
    head_oid: str,
    root_tree_oid: str,
) -> Tuple[List[str], Dict[str, str], Dict[str, Any]]:
    oid_length = len(head_oid)
    oid_pattern = re.compile(r"[0-9a-f]{%d}" % oid_length)
    if oid_length not in (40, 64) or oid_pattern.fullmatch(root_tree_oid) is None:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_OID")
    if not raw.endswith(b"\x00") or len(raw) > MAX_GIT_OUTPUT:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_FORMAT")
    approved_paths = {path for _role, path in PENDING_STATIC_ARTIFACT_SPECS}
    if len(PENDING_STATIC_ARTIFACT_SPECS) != 20 or len(approved_paths) != 20:
        fail(Exit.INTERNAL, "GIT_OBJECT_APPROVED_PATH_PROFILE")
    observed_paths = set()
    approved_blobs: Dict[str, str] = {}
    tree_oids = set()
    for raw_record in raw[:-1].split(b"\x00") if raw else ():
        if not raw_record or b"\t" not in raw_record:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_RECORD")
        raw_header, raw_path = raw_record.split(b"\t", 1)
        header_fields = raw_header.split(b" ")
        if len(header_fields) != 3:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_RECORD")
        try:
            mode = header_fields[0].decode("ascii", "strict")
            object_type = header_fields[1].decode("ascii", "strict")
            oid = header_fields[2].decode("ascii", "strict")
            path = raw_path.decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_ENCODING")
        if oid_pattern.fullmatch(oid) is None or len(os.fsencode(path)) > 4096:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_OID")
        validate_relative(path, "GIT_OBJECT_ENUMERATION_PATH")
        if path in observed_paths:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_PATH_DUPLICATE")
        observed_paths.add(path)
        if object_type == "tree":
            if mode != "040000":
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_MODE")
            tree_oids.add(oid)
        elif object_type == "blob":
            if mode not in ("100644", "100755", "120000"):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_MODE")
            if path in approved_paths:
                if mode != "100644":
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_APPROVED_BLOB_MODE")
                approved_blobs[path] = oid
        else:
            # In particular, never fetch a gitlink/submodule commit object.
            fail(Exit.PRIVACY, "GIT_OBJECT_ENUMERATION_TYPE")
        if len(observed_paths) > MAX_GIT_ADAPTER_ENTRIES:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_LIMIT")
    if set(approved_blobs) != approved_paths:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_APPROVED_BLOB_MISSING")
    object_oids = sorted({head_oid, root_tree_oid, *tree_oids, *approved_blobs.values()})
    object_types: Dict[str, str] = {head_oid: "commit", root_tree_oid: "tree"}
    for oid in tree_oids:
        previous = object_types.setdefault(oid, "tree")
        if previous != "tree":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_TYPE_COLLISION")
    for oid in approved_blobs.values():
        previous = object_types.setdefault(oid, "blob")
        if previous != "blob":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_ENUMERATION_TYPE_COLLISION")
    manifest_core = {
        "profile": GIT_METADATA_OBJECT_CLOSURE_PROFILE_V2,
        "object_format": "sha1" if oid_length == 40 else "sha256",
        "object_count": len(object_oids),
        "tree_object_count": len(tree_oids) + (0 if root_tree_oid in tree_oids else 1),
        "approved_artifact_blob_count": len(approved_blobs),
        "oid_set_sha256": sha256(canonical_json(object_oids)),
    }
    return object_oids, object_types, manifest_core


def verify_pack_object_set(raw: bytes, expected_oids: Sequence[str], pack_path: str) -> None:
    oid_length = len(expected_oids[0]) if expected_oids else 0
    oid_pattern = re.compile(r"[0-9a-f]{%d}" % oid_length)
    observed = set()
    saw_ok = False
    try:
        lines = raw.decode("utf-8", "strict").splitlines()
    except UnicodeDecodeError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_VERIFY_ENCODING")
    for line in lines:
        fields = line.split(" ")
        if fields and oid_pattern.fullmatch(fields[0]) is not None:
            if fields[0] in observed or len(fields) not in (5, 7):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_VERIFY_RECORD")
            if fields[1] not in ("commit", "tree", "blob"):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_VERIFY_TYPE")
            observed.add(fields[0])
            continue
        if line == pack_path + ": ok":
            saw_ok = True
            continue
        if re.fullmatch(r"non delta: [0-9]+ objects", line):
            continue
        if re.fullmatch(r"chain length = [0-9]+: [0-9]+ objects?", line):
            continue
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_VERIFY_SUMMARY")
    if not saw_ok or observed != set(expected_oids):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_VERIFY_SET")


def verify_exact_oid_git_pack_stream(
    raw: bytes,
    object_format: str,
    expected_object_count: int,
) -> Dict[str, Any]:
    if object_format == "sha1":
        digest_bytes = 20
        algorithm = hashlib.sha1
    elif object_format == "sha256":
        digest_bytes = 32
        algorithm = hashlib.sha256
    else:
        fail(Exit.INTERNAL, "GIT_OBJECT_PACK_STREAM_FORMAT")
    if (
        not isinstance(raw, bytes)
        or len(raw) < 12 + digest_bytes
        or len(raw) > MAX_GIT_INDEX_BYTES
        or raw[:4] != b"PACK"
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_STREAM_HEADER")
    version = int.from_bytes(raw[4:8], "big")
    object_count = int.from_bytes(raw[8:12], "big")
    if version not in (2, 3) or object_count != expected_object_count or object_count < 1:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_STREAM_HEADER")
    trailer = raw[-digest_bytes:]
    computed = algorithm(raw[:-digest_bytes]).digest()
    if not hmac.compare_digest(computed, trailer):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_STREAM_CHECKSUM")
    receipt = {
        "profile": GIT_METADATA_PACK_IMPORT_PROFILE_V1,
        "object_format": object_format,
        "pack_version": version,
        "object_count": object_count,
        "pack_checksum": trailer.hex(),
        "pack_bytes": len(raw),
        "pack_stream_sha256": sha256(raw),
    }
    receipt["receipt_sha256"] = sha256(canonical_json(receipt))
    return receipt


def materialize_git_object_closure(
    capture: Dict[str, Any],
    repo_root: str,
    key: bytes,
    git_binary: str,
    developer_root: str,
    adapter_root: str,
    adapter_git_dir: str,
    adapter_fd: int,
    git_fd: int,
    adapter_identity: Tuple[int, int],
    git_identity: Tuple[int, int],
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    capture["adapter_trace"] = capture.get("adapter_trace", [])
    assert_git_source_capture_unchanged(capture, repo_root, key, "GIT_ADAPTER_SOURCE_DRIFT")
    git_adapter_trace_event(capture["adapter_trace"], "SOURCE_BOOTSTRAP_PREVALIDATED", "source-cas")
    head_oid = str(capture["head_oid"])
    oid_length = len(head_oid)
    object_oids, object_types, root_tree_oid, manifest = discover_git_object_closure(
        capture=capture,
        git_binary=git_binary,
        developer_root=developer_root,
        repo_root=repo_root,
        adapter_root=adapter_root,
        adapter_git_dir=adapter_git_dir,
        adapter_fd=adapter_fd,
        git_fd=git_fd,
        adapter_identity=adapter_identity,
        git_identity=git_identity,
    )
    dependencies_before = capture_git_object_dependencies(str(capture["objects_path"]), object_oids)
    capture["adapter_root_tree_oid"] = root_tree_oid
    capture["object_dependency_oids"] = tuple(object_oids)
    capture["object_dependency_fingerprint"] = dependencies_before["fingerprint"]
    manifest["source_object_dependency_profile"] = dependencies_before["profile"]
    manifest["source_object_dependency_fingerprint"] = dependencies_before["fingerprint"]
    git_adapter_trace_event(capture["adapter_trace"], "OBJECT_ENUMERATION_COMPLETE", "adapter-materialization")
    if adapter_git_dir != ".":
        fail(Exit.INTERNAL, "GIT_OBJECT_RELATIVE_GIT_DIR")
    try:
        mkdir_git_adapter_directory_at(git_fd, "objects/pack", "GIT_OBJECT_PACK_DIRECTORY")
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_DIRECTORY")
    pack_input = b"".join(oid.encode("ascii") + b"\n" for oid in object_oids)
    pack_stream = run_git_object_bootstrap_child(
        git_binary=git_binary,
        developer_root=developer_root,
        repo_root=repo_root,
        capture=capture,
        adapter_root=adapter_root,
        adapter_git_dir=adapter_git_dir,
        adapter_fd=adapter_fd,
        git_fd=git_fd,
        adapter_identity=adapter_identity,
        git_identity=git_identity,
        arguments=["pack-objects", "--stdout", "--no-reuse-delta", "--no-reuse-object"],
        label="GIT_OBJECT_PACK",
        max_output=MAX_GIT_INDEX_BYTES,
        allow_live_objects=True,
        allow_adapter_writes=False,
        allowed_live_oids=tuple(object_oids),
        allowed_pack_paths=dependencies_before["allowed_pack_paths"],
        stdin_bytes=pack_input,
    )
    object_format = "sha1" if oid_length == 40 else "sha256"
    pack_receipt = verify_exact_oid_git_pack_stream(
        pack_stream,
        object_format,
        len(object_oids),
    )
    pack_name_oid = str(pack_receipt["pack_checksum"])
    dependencies_after_pack = capture_git_object_dependencies(
        str(capture["objects_path"]),
        object_oids,
    )
    if dependencies_after_pack["fingerprint"] != dependencies_before["fingerprint"]:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_OBJECT_DEPENDENCY_DRIFT")
    assert_git_source_capture_unchanged(capture, repo_root, key, "GIT_ADAPTER_SOURCE_DRIFT")
    pack_base = "objects/pack/pack"
    pack_path = pack_base + "-" + pack_name_oid + ".pack"
    index_path = pack_base + "-" + pack_name_oid + ".idx"
    index_result = run_git_object_bootstrap_child(
        git_binary=git_binary,
        developer_root=developer_root,
        repo_root=repo_root,
        capture=capture,
        adapter_root=adapter_root,
        adapter_git_dir=adapter_git_dir,
        adapter_fd=adapter_fd,
        git_fd=git_fd,
        adapter_identity=adapter_identity,
        git_identity=git_identity,
        arguments=["index-pack", "--stdin", "--index-version=2"],
        label="GIT_OBJECT_INDEX_PACK",
        max_output=256,
        allow_live_objects=False,
        allow_adapter_writes=True,
        stdin_bytes=pack_stream,
    )
    expected_index_result = ("pack\t" + pack_name_oid + "\n").encode("ascii")
    if index_result != expected_index_result:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INDEX_PACK_RESULT")
    pack_fd: Optional[int] = None
    try:
        pack_fd = open_git_adapter_directory_at(
            git_fd,
            ("objects", "pack"),
            "GIT_OBJECT_PACK_SCAN",
            create=False,
        )
        names = sorted(entry.name for entry in os.scandir(pack_fd))
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_SCAN")
    finally:
        if pack_fd is not None:
            os.close(pack_fd)
    if names != [os.path.basename(index_path), os.path.basename(pack_path)]:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_PACK_OUTPUT_SET")
    git_adapter_trace_event(capture["adapter_trace"], "OBJECT_PACK_COMPLETE", "adapter-materialization")
    verify_raw = run_git_object_bootstrap_child(
        git_binary=git_binary,
        developer_root=developer_root,
        repo_root=repo_root,
        capture=capture,
        adapter_root=adapter_root,
        adapter_git_dir=adapter_git_dir,
        adapter_fd=adapter_fd,
        git_fd=git_fd,
        adapter_identity=adapter_identity,
        git_identity=git_identity,
        arguments=["verify-pack", "-v", index_path],
        label="GIT_OBJECT_PACK_VERIFY",
        max_output=MAX_GIT_OUTPUT,
        allow_live_objects=False,
        allow_adapter_writes=False,
    )
    verify_pack_object_set(verify_raw, object_oids, pack_path)
    pack_relative = "objects/pack/" + os.path.basename(pack_path)
    index_relative = "objects/pack/" + os.path.basename(index_path)
    pack_evidence = hash_git_adapter_file_at(
        git_fd,
        pack_relative,
        "GIT_OBJECT_PACK_FILE",
        MAX_GIT_ADAPTER_FILE_BYTES,
    )
    index_evidence = hash_git_adapter_file_at(
        git_fd,
        index_relative,
        "GIT_OBJECT_PACK_INDEX",
        MAX_GIT_ADAPTER_FILE_BYTES,
    )
    manifest.update(
        {
            "pack_import_profile": GIT_METADATA_PACK_IMPORT_PROFILE_V1,
            "pack_import_receipt_sha256": pack_receipt["receipt_sha256"],
            "pack_sha256": pack_evidence["sha256"],
            "pack_bytes": pack_evidence["bytes"],
            "index_sha256": index_evidence["sha256"],
            "index_bytes": index_evidence["bytes"],
        }
    )
    git_adapter_trace_event(capture["adapter_trace"], "OBJECT_PACK_VERIFIED", "adapter-materialization")
    dependencies_after = capture_git_object_dependencies(str(capture["objects_path"]), object_oids)
    if dependencies_after["fingerprint"] != dependencies_before["fingerprint"]:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_OBJECT_DEPENDENCY_DRIFT")
    assert_git_source_capture_unchanged(capture, repo_root, key, "GIT_ADAPTER_SOURCE_DRIFT")
    git_adapter_trace_event(capture["adapter_trace"], "SOURCE_BOOTSTRAP_POSTVALIDATED", "source-cas")
    return manifest, object_types


def verify_sealed_git_adapter_object_inventory(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    expected_types: Mapping[str, str],
) -> str:
    raw = run_git(
        git_binary,
        repo_root,
        boundary,
        [
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        ],
        "GIT_OBJECT_INVENTORY",
    )
    if not raw or not raw.endswith(b"\n") or b"\x00" in raw or b"\r" in raw:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_FORMAT")
    expected_oids = set(expected_types)
    oid_length = len(next(iter(expected_oids))) if expected_oids else 0
    observed = set()
    receipt_rows: List[Dict[str, Any]] = []
    total_bytes = 0
    for line in raw.splitlines():
        fields = line.split(b" ")
        if len(fields) != 3:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_RECORD")
        try:
            oid = fields[0].decode("ascii", "strict")
            object_type = fields[1].decode("ascii", "strict")
            size_text = fields[2].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_RECORD")
        if (
            re.fullmatch(r"[0-9a-f]{%d}" % oid_length, oid) is None
            or oid in observed
            or expected_types.get(oid) != object_type
            or re.fullmatch(r"0|[1-9][0-9]*", size_text) is None
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_RECORD")
        size = int(size_text, 10)
        total_bytes += size
        if size > MAX_GIT_ADAPTER_FILE_BYTES or total_bytes > MAX_GIT_INDEX_BYTES:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_LIMIT")
        observed.add(oid)
        receipt_rows.append({"oid": oid, "type": object_type, "bytes": size})
    if observed != expected_oids:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_INVENTORY_SET")
    return sha256(canonical_json(sorted(receipt_rows, key=lambda row: row["oid"])))


def verify_sealed_git_adapter_object_content(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    expected_types: Mapping[str, str],
) -> str:
    expected_oids = sorted(expected_types)
    if not expected_oids:
        fail(Exit.INTERNAL, "GIT_OBJECT_CONTENT_EXPECTATION")
    oid_length = len(expected_oids[0])
    if oid_length not in (40, 64) or any(
        re.fullmatch(r"[0-9a-f]{%d}" % oid_length, oid) is None
        or expected_types.get(oid) not in ("commit", "tree", "blob")
        for oid in expected_oids
    ):
        fail(Exit.INTERNAL, "GIT_OBJECT_CONTENT_EXPECTATION")
    request = b"".join(oid.encode("ascii") + b"\n" for oid in expected_oids)
    response = run_git(
        git_binary,
        repo_root,
        boundary,
        ["cat-file", "--batch"],
        "GIT_OBJECT_CONTENT_RECOMPUTE",
        stdin_bytes=request,
        max_output=MAX_GIT_INDEX_BYTES,
    )
    cursor = 0
    total_content_bytes = 0
    receipt_rows: List[Dict[str, Any]] = []
    for expected_oid in expected_oids:
        newline = response.find(b"\n", cursor)
        if newline < 0 or newline - cursor > 256:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_HEADER")
        header = response[cursor:newline]
        cursor = newline + 1
        fields = header.split(b" ")
        if len(fields) != 3:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_HEADER")
        try:
            observed_oid = fields[0].decode("ascii", "strict")
            object_type = fields[1].decode("ascii", "strict")
            size_text = fields[2].decode("ascii", "strict")
        except UnicodeDecodeError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_HEADER")
        if (
            observed_oid != expected_oid
            or object_type != expected_types[expected_oid]
            or re.fullmatch(r"0|[1-9][0-9]*", size_text) is None
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_HEADER")
        size = int(size_text, 10)
        total_content_bytes += size
        if size > MAX_GIT_ADAPTER_FILE_BYTES or total_content_bytes > MAX_GIT_INDEX_BYTES:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_LIMIT")
        end = cursor + size
        if end >= len(response) or response[end:end + 1] != b"\n":
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_BODY")
        content = response[cursor:end]
        cursor = end + 1
        digest = hashlib.sha1() if oid_length == 40 else hashlib.sha256()
        digest.update((object_type + " " + str(size) + "\x00").encode("ascii"))
        digest.update(content)
        if not hmac.compare_digest(digest.hexdigest(), expected_oid):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_OID")
        receipt_rows.append({"oid": expected_oid, "type": object_type, "bytes": size})
    if cursor != len(response):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_CONTENT_TRAILING")
    git_adapter_trace_event(boundary, "OBJECT_CONTENT_VERIFIED", "adapter-seal")
    return sha256(canonical_json(receipt_rows))


def verify_sealed_git_adapter_tree_selection(
    git_binary: str,
    repo_root: str,
    boundary: GitMetadataAdapter,
    head_oid: str,
    root_tree_oid: str,
    expected_types: Mapping[str, str],
) -> None:
    raw = run_git(
        git_binary,
        repo_root,
        boundary,
        ["ls-tree", "-r", "-t", "-z", "--full-tree", "HEAD^{tree}"],
        "GIT_OBJECT_SEALED_TREE_ENUMERATION",
    )
    observed_oids, observed_types, _manifest = parse_git_ls_tree_object_closure(
        raw,
        head_oid,
        root_tree_oid,
    )
    if observed_oids != sorted(expected_types) or observed_types != dict(expected_types):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_SEALED_TREE_SET")


def copy_captured_refs(capture: Mapping[str, Any], git_fd: int) -> None:
    for reference, raw in sorted(captured_ref_map(capture).items()):
        components = reference.split("/")
        if (
            len(components) < 2
            or components[0] != "refs"
            or any(not component or component in (".", "..") for component in components)
            or any("\\" in component or "\x00" in component or not is_nfc(component) for component in components)
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_REF")
        try:
            parent_fd = open_git_adapter_directory_at(
                git_fd,
                tuple(components[:-1]),
                "GIT_ADAPTER_REF_DIRECTORY",
                create=True,
            )
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_REF_DIRECTORY")
        try:
            try:
                os.stat(components[-1], dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                continue
        finally:
            os.close(parent_fd)
        write_git_adapter_file_at(git_fd, reference, raw, "GIT_ADAPTER_REF")


def adapter_tree_fingerprint(adapter_fd: int, git_fd: int) -> str:
    records: List[Dict[str, Any]] = []
    total_bytes = 0

    def walk(directory_fd: int, relative: str) -> None:
        nonlocal total_bytes
        directory_metadata = os.fstat(directory_fd)
        if not stat.S_ISDIR(directory_metadata.st_mode) or directory_metadata.st_uid != os.getuid():
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_DIRECTORY")
        records.append({
            "relative": relative,
            "kind": "D",
            "metadata": git_source_metadata(directory_metadata),
        })
        if len(records) > MAX_GIT_ADAPTER_ENTRIES:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ENTRY_LIMIT")
        try:
            entries = list(os.scandir(directory_fd))
        except OSError:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SCAN")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            child_relative = entry.name if not relative else relative + "/" + entry.name
            metadata = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode):
                child_fd = os.open(
                    entry.name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_DIRECTORY_RACE")
                    walk(child_fd, child_relative)
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SPECIAL")
            record: Dict[str, Any] = {
                "relative": child_relative,
                "kind": "F",
                "metadata": git_source_metadata(metadata),
            }
            file_fd = os.open(
                entry.name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            try:
                opened = os.fstat(file_fd)
                if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_FILE_RACE")
                total_bytes += opened.st_size
                if total_bytes > MAX_GIT_ADAPTER_TOTAL_BYTES:
                    fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_BYTE_LIMIT")
                record["raw_sha256"] = hash_fd(
                    file_fd,
                    "sha256",
                    MAX_GIT_ADAPTER_FILE_BYTES,
                    "GIT_ADAPTER_CONTENT",
                )[0]
            finally:
                os.close(file_fd)
            records.append(record)
            if len(records) > MAX_GIT_ADAPTER_ENTRIES:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ENTRY_LIMIT")

    try:
        root_metadata = os.fstat(adapter_fd)
        git_metadata = os.fstat(git_fd)
        root_entries = list(os.scandir(adapter_fd))
        named_git = os.stat("git", dir_fd=adapter_fd, follow_symlinks=False)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_SCAN")
    if (
        [entry.name for entry in root_entries] != ["git"]
        or not stat.S_ISDIR(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or stat.S_ISLNK(named_git.st_mode)
        or not stat.S_ISDIR(named_git.st_mode)
        or (named_git.st_dev, named_git.st_ino) != (git_metadata.st_dev, git_metadata.st_ino)
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_TREE")
    records.append({
        "relative": "",
        "kind": "D",
        "metadata": git_source_metadata(root_metadata),
    })
    git_copy = os.dup(git_fd)
    try:
        walk(git_copy, "git")
    finally:
        os.close(git_copy)
    try:
        named_after = os.stat("git", dir_fd=adapter_fd, follow_symlinks=False)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_TREE")
    if (named_after.st_dev, named_after.st_ino) != (git_metadata.st_dev, git_metadata.st_ino):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_TREE")
    return sha256(canonical_json(records))


def seal_git_adapter_tree(adapter_fd: int, git_fd: int) -> None:
    def seal_directory(directory_fd: int) -> None:
        entries = list(os.scandir(directory_fd))
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            metadata = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode):
                child_fd = os.open(
                    entry.name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SEAL_RACE")
                    seal_directory(child_fd)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
                os.chmod(entry.name, 0o400, dir_fd=directory_fd, follow_symlinks=False)
            else:
                fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SEAL_FILE")
        os.fchmod(directory_fd, 0o500)

    try:
        git_metadata = os.fstat(git_fd)
        root_entries = list(os.scandir(adapter_fd))
        named_git = os.stat("git", dir_fd=adapter_fd, follow_symlinks=False)
        if (
            [entry.name for entry in root_entries] != ["git"]
            or stat.S_ISLNK(named_git.st_mode)
            or not stat.S_ISDIR(named_git.st_mode)
            or (named_git.st_dev, named_git.st_ino) != (git_metadata.st_dev, git_metadata.st_ino)
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SEAL_GIT_IDENTITY")
        seal_directory(git_fd)
        named_after = os.stat("git", dir_fd=adapter_fd, follow_symlinks=False)
        if (named_after.st_dev, named_after.st_ino) != (git_metadata.st_dev, git_metadata.st_ino):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SEAL_GIT_IDENTITY")
        os.fchmod(adapter_fd, 0o500)
    except ContractError:
        raise
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_SEAL")


def validate_git_adapter_locator(adapter_root: str) -> None:
    if (
        not isinstance(adapter_root, str)
        or os.path.normpath(adapter_root) != adapter_root
        or os.path.dirname(adapter_root) != "/private/tmp"
        or not os.path.basename(adapter_root).startswith(GIT_ADAPTER_TEMP_PREFIX)
        or len(os.path.basename(adapter_root)) <= len(GIT_ADAPTER_TEMP_PREFIX)
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_LOCATOR")


def claim_git_metadata_adapter_process_scope() -> None:
    """Claim the one cooperative adapter lifecycle owned by this process."""

    global _GIT_METADATA_ADAPTER_SCOPE
    with _GIT_METADATA_ADAPTER_SCOPE_LOCK:
        if _GIT_METADATA_ADAPTER_SCOPE is not None:
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_SCOPE_NON_REENTRANT")
        _GIT_METADATA_ADAPTER_SCOPE = {
            "owner_pid": os.getpid(),
            "owner_uid": os.getuid(),
            "adapter_root": None,
            "adapter_identity": None,
        }


def bind_git_metadata_adapter_process_scope(
    adapter_root: str,
    adapter_identity: Optional[Tuple[int, int]],
) -> None:
    global _GIT_METADATA_ADAPTER_SCOPE
    with _GIT_METADATA_ADAPTER_SCOPE_LOCK:
        scope = _GIT_METADATA_ADAPTER_SCOPE
        if (
            not isinstance(scope, dict)
            or scope.get("owner_pid") != os.getpid()
            or scope.get("owner_uid") != os.getuid()
            or scope.get("adapter_root") not in (None, adapter_root)
            or (
                scope.get("adapter_identity") is not None
                and scope.get("adapter_identity") != adapter_identity
            )
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_SCOPE_OWNERSHIP")
        scope["adapter_root"] = adapter_root
        if adapter_identity is not None:
            scope["adapter_identity"] = tuple(adapter_identity)


def require_git_metadata_adapter_process_scope(
    boundary: GitMetadataAdapter,
) -> None:
    with _GIT_METADATA_ADAPTER_SCOPE_LOCK:
        scope = _GIT_METADATA_ADAPTER_SCOPE
        if (
            boundary.owner_pid != os.getpid()
            or boundary.owner_uid != os.getuid()
            or not isinstance(scope, dict)
            or scope.get("owner_pid") != boundary.owner_pid
            or scope.get("owner_uid") != boundary.owner_uid
            or scope.get("adapter_root") != boundary.adapter_root
            or scope.get("adapter_identity") != boundary.adapter_identity
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_SCOPE_OWNERSHIP")


def release_git_metadata_adapter_process_scope(
    adapter_root: Optional[str],
    adapter_identity: Optional[Tuple[int, int]],
) -> None:
    global _GIT_METADATA_ADAPTER_SCOPE
    with _GIT_METADATA_ADAPTER_SCOPE_LOCK:
        scope = _GIT_METADATA_ADAPTER_SCOPE
        if (
            not isinstance(scope, dict)
            or scope.get("owner_pid") != os.getpid()
            or scope.get("owner_uid") != os.getuid()
            or scope.get("adapter_root") != adapter_root
            or scope.get("adapter_identity") != adapter_identity
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_SCOPE_RELEASE")
        _GIT_METADATA_ADAPTER_SCOPE = None


def git_metadata_adapter_process_scope_residue_count() -> int:
    with _GIT_METADATA_ADAPTER_SCOPE_LOCK:
        return 0 if _GIT_METADATA_ADAPTER_SCOPE is None else 1


def verify_named_git_adapter_cleanup_root(
    parent_fd: int,
    basename: str,
    adapter_identity: Tuple[int, int],
) -> os.stat_result:
    try:
        metadata = os.stat(basename, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_MISSING")
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_IO")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or (metadata.st_dev, metadata.st_ino) != adapter_identity
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_IDENTITY")
    return metadata


def remove_git_adapter_root(
    adapter_root: str,
    adapter_identity: Tuple[int, int],
    trace: List[Dict[str, str]],
    adapter_fd: Optional[int] = None,
) -> None:
    git_adapter_trace_event(trace, "CLEANUP_BEGIN", "adapter-cleanup")
    parent_fd: Optional[int] = None
    root_fd: Optional[int] = None

    def cleanup_fail(public_code: str) -> None:
        fail(Exit.PREFLIGHT_DRIFT, public_code)

    def clear_directory_fd(directory_fd: int, expected_path: str) -> None:
        metadata = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or git_adapter_fd_path(directory_fd, "GIT_ADAPTER_CLEANUP") != expected_path
        ):
            cleanup_fail("GIT_ADAPTER_CLEANUP_ENTRY")
        os.fchmod(directory_fd, 0o700)
        entries = list(os.scandir(directory_fd))
        if len(entries) > MAX_GIT_ADAPTER_ENTRIES:
            cleanup_fail("GIT_ADAPTER_CLEANUP_ENTRY_LIMIT")
        for entry in sorted(entries, key=lambda item: os.fsencode(item.name)):
            name = entry.name
            if (
                not isinstance(name, str)
                or not name
                or name in (".", "..")
                or "/" in name
                or "\x00" in name
            ):
                cleanup_fail("GIT_ADAPTER_CLEANUP_ENTRY")
            child = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISREG(child.st_mode):
                if child.st_uid != os.getuid() or child.st_nlink != 1:
                    cleanup_fail("GIT_ADAPTER_CLEANUP_ENTRY")
                os.unlink(name, dir_fd=directory_fd)
                continue
            if not stat.S_ISDIR(child.st_mode) or stat.S_ISLNK(child.st_mode) or child.st_uid != os.getuid():
                cleanup_fail("GIT_ADAPTER_CLEANUP_ENTRY")
            child_fd = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            try:
                opened = os.fstat(child_fd)
                if (opened.st_dev, opened.st_ino) != (child.st_dev, child.st_ino):
                    cleanup_fail("GIT_ADAPTER_CLEANUP_IDENTITY")
                child_path = os.path.join(expected_path, name)
                clear_directory_fd(child_fd, child_path)
                named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                    cleanup_fail("GIT_ADAPTER_CLEANUP_IDENTITY")
                os.rmdir(name, dir_fd=directory_fd)
                # F_GETPATH remains the original now-absent path after normal
                # APFS removal, but follows a renamed live directory.  Keeping
                # the fd open across rmdir therefore detects final-delete swap.
                if git_adapter_fd_path(child_fd, "GIT_ADAPTER_CLEANUP") != child_path:
                    cleanup_fail("GIT_ADAPTER_CLEANUP_IDENTITY")
            finally:
                os.close(child_fd)
        if list(os.scandir(directory_fd)):
            cleanup_fail("GIT_ADAPTER_CLEANUP_RESIDUE")

    try:
        try:
            validate_git_adapter_locator(adapter_root)
        except ContractError:
            cleanup_fail("GIT_ADAPTER_CLEANUP_LOCATOR")
        basename = os.path.basename(adapter_root)
        parent_fd = os.open(
            "/private/tmp",
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        verify_named_git_adapter_cleanup_root(parent_fd, basename, adapter_identity)
        root_fd = (
            os.dup(adapter_fd)
            if adapter_fd is not None
            else os.open(
                basename,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
        )
        opened_root = os.fstat(root_fd)
        if (
            (opened_root.st_dev, opened_root.st_ino) != adapter_identity
            or git_adapter_fd_path(root_fd, "GIT_ADAPTER_CLEANUP") != adapter_root
        ):
            cleanup_fail("GIT_ADAPTER_CLEANUP_IDENTITY")
        clear_directory_fd(root_fd, adapter_root)
        verify_named_git_adapter_cleanup_root(parent_fd, basename, adapter_identity)
        os.rmdir(basename, dir_fd=parent_fd)
        if git_adapter_fd_path(root_fd, "GIT_ADAPTER_CLEANUP") != adapter_root:
            cleanup_fail("GIT_ADAPTER_CLEANUP_IDENTITY")
        try:
            os.stat(basename, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            cleanup_fail("GIT_ADAPTER_CLEANUP_RESIDUE")
    except ContractError:
        git_adapter_trace_event(trace, "CLEANUP_FAILED", "adapter-cleanup")
        raise
    except OSError:
        git_adapter_trace_event(trace, "CLEANUP_FAILED", "adapter-cleanup")
        cleanup_fail("GIT_ADAPTER_CLEANUP_IO")
    finally:
        if root_fd is not None:
            os.close(root_fd)
        if parent_fd is not None:
            os.close(parent_fd)
    git_adapter_trace_event(trace, "CLEANUP_COMPLETE", "adapter-cleanup")


def create_git_metadata_adapter(
    repo_root: str,
    key: bytes,
    git_binary: str,
) -> Tuple[Dict[str, Any], GitMetadataAdapter]:
    developer_root = _GIT_DEVELOPER_ROOTS.get(git_binary)
    if not isinstance(developer_root, str):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_DEVELOPER_ROOT")
    claim_git_metadata_adapter_process_scope()
    trace: List[Dict[str, str]] = []
    git_adapter_trace_event(trace, "SOURCE_CAPTURE_BEGIN", "source-capture")
    try:
        capture = capture_git_metadata_source(repo_root, key)
    except BaseException:
        release_git_metadata_adapter_process_scope(None, None)
        raise
    git_adapter_trace_event(trace, "SOURCE_CAPTURE_COMPLETE", "source-capture")
    try:
        adapter_root = tempfile.mkdtemp(prefix=GIT_ADAPTER_TEMP_PREFIX, dir="/private/tmp")
    except OSError:
        release_git_metadata_adapter_process_scope(None, None)
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_CREATE")
    bind_git_metadata_adapter_process_scope(adapter_root, None)
    try:
        validate_git_adapter_locator(adapter_root)
        root_metadata = os.lstat(adapter_root)
    except BaseException:
        # The pathname now exists but an exact inode was not established.
        # Never guess at cleanup or clear the registry: this is terminal
        # cleanup uncertainty and process quiescence remains false.
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_IDENTITY_UNAVAILABLE")
    adapter_identity = (root_metadata.st_dev, root_metadata.st_ino)
    bind_git_metadata_adapter_process_scope(adapter_root, adapter_identity)
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or stat.S_ISLNK(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or stat.S_IMODE(root_metadata.st_mode) != 0o700
    ):
        remove_git_adapter_root(adapter_root, adapter_identity, trace)
        release_git_metadata_adapter_process_scope(adapter_root, adapter_identity)
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_POLICY")
    try:
        adapter_fd = os.open(
            adapter_root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError:
        remove_git_adapter_root(adapter_root, adapter_identity, trace)
        release_git_metadata_adapter_process_scope(adapter_root, adapter_identity)
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_ROOT_OPEN")
    git_fd: Optional[int] = None
    try:
        verify_unsealed_git_adapter_root(adapter_root, adapter_identity, adapter_fd)
        git_adapter_trace_event(trace, "ADAPTER_ROOT_CREATED", "adapter-materialization")
        adapter_git_dir = os.path.join(adapter_root, "git")
        mkdir_git_adapter_directory_at(adapter_fd, "git", "GIT_ADAPTER_GIT_DIRECTORY")
        git_fd = open_git_adapter_directory_at(
            adapter_fd,
            ("git",),
            "GIT_ADAPTER_GIT_DIRECTORY",
            create=False,
        )
        git_metadata = os.fstat(git_fd)
        git_identity = (git_metadata.st_dev, git_metadata.st_ino)
        verify_unsealed_git_adapter_git_directory(
            adapter_root,
            adapter_fd,
            git_fd,
            git_identity,
        )
        head_oid = str(capture["head_oid"])
        object_format = "sha1" if len(head_oid) == 40 else "sha256"
        config_lines = [
            "[core]",
            "\trepositoryformatversion = " + ("0" if object_format == "sha1" else "1"),
            "\tbare = false",
            "\tfilemode = true",
            "\tlogallrefupdates = false",
            "\tfsmonitor = false",
            "\tuntrackedCache = false",
            "\tcommitGraph = false",
            "\tmultiPackIndex = false",
            "\thooksPath = /dev/null",
            "\texcludesFile = /dev/null",
            "\tattributesFile = /dev/null",
            "[protocol]",
            "\tallow = never",
            "[submodule]",
            "\trecurse = false",
            "[diff]",
            "\trenames = false",
            "[pack]",
            "\tuseBitmap = false",
            "\twriteReverseIndex = false",
        ]
        if object_format == "sha256":
            config_lines.extend(("[extensions]", "\tobjectFormat = sha256"))
        safe_config = ("\n".join(config_lines) + "\n").encode("ascii")
        write_git_adapter_file_at(git_fd, "config", safe_config, "GIT_ADAPTER_CONFIG")
        raw_files = capture["raw_files"]
        write_git_adapter_file_at(git_fd, "HEAD", raw_files["head"], "GIT_ADAPTER_HEAD")
        write_git_adapter_file_at(git_fd, "index", raw_files["index"], "GIT_ADAPTER_INDEX")
        for role, name in (("packed_refs", "packed-refs"), ("shallow", "shallow")):
            raw = raw_files.get(role)
            if raw is not None:
                write_git_adapter_file_at(
                    git_fd,
                    name,
                    raw,
                    "GIT_ADAPTER_" + role.upper(),
                )
        mkdir_git_adapter_directory_at(git_fd, "info", "GIT_ADAPTER_INFO_DIRECTORY")
        info_exclude = raw_files.get("info_exclude") or b""
        write_git_adapter_file_at(
            git_fd,
            "info/exclude",
            info_exclude,
            "GIT_ADAPTER_INFO_EXCLUDE",
        )
        copy_captured_refs(capture, git_fd)
        verify_unsealed_git_adapter_root(adapter_root, adapter_identity, adapter_fd)
        verify_unsealed_git_adapter_git_directory(adapter_root, adapter_fd, git_fd, git_identity)
        git_adapter_trace_event(trace, "ADAPTER_METADATA_FROZEN", "adapter-materialization")
        capture["adapter_trace"] = trace
        adapter_object_manifest, adapter_object_types = materialize_git_object_closure(
            capture,
            repo_root,
            key,
            git_binary,
            developer_root,
            adapter_root,
            ".",
            adapter_fd,
            git_fd,
            adapter_identity,
            git_identity,
        )
        capture["adapter_object_manifest"] = adapter_object_manifest
        git_adapter_trace_event(trace, "ADAPTER_OBJECTS_FROZEN", "adapter-materialization")
        verify_unsealed_git_adapter_root(adapter_root, adapter_identity, adapter_fd)
        verify_unsealed_git_adapter_git_directory(adapter_root, adapter_fd, git_fd, git_identity)
        seal_git_adapter_tree(adapter_fd, git_fd)
        adapter_fingerprint = adapter_tree_fingerprint(adapter_fd, git_fd)
        git_adapter_trace_event(trace, "ADAPTER_SEALED", "adapter-seal")
        boundary = GitMetadataAdapter(
            developer_root,
            repo_root,
            str(capture["git_dir"]),
            str(capture["common_dir"]),
            adapter_root,
            adapter_git_dir,
            adapter_fd,
            git_fd,
            str(capture["fingerprint"]),
            tuple(capture["object_dependency_oids"]),
            str(capture["object_dependency_fingerprint"]),
            adapter_fingerprint,
            adapter_identity,
            git_identity,
            trace,
        )
        verify_git_metadata_adapter(boundary)
        adapter_object_manifest["object_inventory_verification_profile"] = (
            "sealed-adapter-cat-file-batch-all-exact-set-v1"
        )
        adapter_object_manifest["object_inventory_verification_receipt_sha256"] = (
            verify_sealed_git_adapter_object_inventory(
                git_binary,
                repo_root,
                boundary,
                adapter_object_types,
            )
        )
        adapter_object_manifest["object_content_verification_profile"] = (
            "sealed-adapter-cat-file-batch-parent-oid-recompute-v1"
        )
        adapter_object_manifest["object_content_verification_receipt_sha256"] = (
            verify_sealed_git_adapter_object_content(
                git_binary,
                repo_root,
                boundary,
                adapter_object_types,
            )
        )
        verify_sealed_git_adapter_tree_selection(
            git_binary,
            repo_root,
            boundary,
            str(capture["head_oid"]),
            str(capture["adapter_root_tree_oid"]),
            adapter_object_types,
        )
        return capture, boundary
    except BaseException:
        close_failed = False
        try:
            remove_git_adapter_root(adapter_root, adapter_identity, trace, adapter_fd)
        finally:
            for descriptor in (git_fd, adapter_fd):
                if descriptor is None:
                    continue
                try:
                    os.close(descriptor)
                except OSError:
                    close_failed = True
            if close_failed:
                git_adapter_trace_event(trace, "CLEANUP_FAILED", "adapter-cleanup")
                fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_FD_CLOSE")
        release_git_metadata_adapter_process_scope(adapter_root, adapter_identity)
        raise


def verify_git_metadata_adapter(boundary: GitMetadataAdapter) -> None:
    if boundary.closed:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLOSED")
    require_git_metadata_adapter_process_scope(boundary)
    validate_git_adapter_locator(boundary.adapter_root)
    if (
        boundary.git_dir != os.path.join(boundary.adapter_root, "git")
    ):
        fail(Exit.INTERNAL, "GIT_ADAPTER_LOCATOR")
    try:
        metadata = os.lstat(boundary.adapter_root)
        opened = os.fstat(boundary.adapter_fd)
        named_git = os.stat("git", dir_fd=boundary.adapter_fd, follow_symlinks=False)
        opened_git = os.fstat(boundary.git_fd)
    except OSError:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_DRIFT")
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o500
        or (metadata.st_dev, metadata.st_ino) != boundary.adapter_identity
        or (opened.st_dev, opened.st_ino) != boundary.adapter_identity
        or stat.S_ISLNK(named_git.st_mode)
        or not stat.S_ISDIR(named_git.st_mode)
        or stat.S_IMODE(named_git.st_mode) != 0o500
        or (named_git.st_dev, named_git.st_ino) != boundary.git_identity
        or (opened_git.st_dev, opened_git.st_ino) != boundary.git_identity
        or git_adapter_fd_path(boundary.adapter_fd, "GIT_ADAPTER") != boundary.adapter_root
        or git_adapter_fd_path(boundary.git_fd, "GIT_ADAPTER_GIT_DIRECTORY") != boundary.git_dir
        or adapter_tree_fingerprint(boundary.adapter_fd, boundary.git_fd) != boundary.adapter_fingerprint
    ):
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_DRIFT")


def revalidate_git_metadata_source(boundary: GitMetadataAdapter, key: bytes) -> None:
    require_git_metadata_adapter_process_scope(boundary)
    try:
        current = capture_git_metadata_source(boundary.repo_root, key)
        dependencies = capture_git_object_dependencies(
            os.path.join(boundary.live_common_dir, "objects"),
            boundary.object_dependency_oids,
        )
    except ContractError:
        fail(Exit.GIT_CONTAINMENT, "GIT_ADAPTER_SOURCE_DRIFT")
    if (
        current["git_dir"] != boundary.live_git_dir
        or current["common_dir"] != boundary.live_common_dir
        or current["fingerprint"] != boundary.source_fingerprint
        or dependencies["fingerprint"] != boundary.object_dependency_fingerprint
    ):
        fail(Exit.GIT_CONTAINMENT, "GIT_ADAPTER_SOURCE_DRIFT")
    git_adapter_trace_event(boundary, "SOURCE_FINAL_REVALIDATED", "source-cas")


def cleanup_git_metadata_adapter(boundary: GitMetadataAdapter) -> None:
    if boundary.closed:
        return
    require_git_metadata_adapter_process_scope(boundary)
    remove_git_adapter_root(
        boundary.adapter_root,
        boundary.adapter_identity,
        boundary.trace,
        boundary.adapter_fd,
    )
    close_failed = False
    for field in ("git_fd", "adapter_fd"):
        descriptor = getattr(boundary, field)
        try:
            os.close(descriptor)
        except OSError:
            close_failed = True
        else:
            setattr(boundary, field, -1)
    if close_failed:
        git_adapter_trace_event(boundary, "CLEANUP_FAILED", "adapter-cleanup")
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_FD_CLOSE")
    release_git_metadata_adapter_process_scope(
        boundary.adapter_root,
        boundary.adapter_identity,
    )
    boundary.closed = True


def finalize_git_metadata_adapter(boundary: GitMetadataAdapter, key: bytes) -> Tuple[Dict[str, str], ...]:
    pending: Optional[BaseException] = None
    try:
        verify_git_metadata_adapter(boundary)
        revalidate_git_metadata_source(boundary, key)
    except BaseException as error:
        pending = error
    try:
        cleanup_git_metadata_adapter(boundary)
    except BaseException:
        raise
    if pending is not None:
        raise pending
    return tuple(dict(entry) for entry in boundary.trace)


def git_snapshot(
    repo_root: str,
    key: bytes,
    git_binary: str,
    authorized_tree_excludes: Sequence[str] = (),
    authorized_exact_file_excludes: Sequence[str] = (),
) -> Dict[str, Any]:
    tree_exclusions = tuple(authorized_tree_excludes)
    exact_file_exclusions = tuple(authorized_exact_file_excludes)
    if len(set(tree_exclusions)) != len(tree_exclusions) or len(set(exact_file_exclusions)) != len(exact_file_exclusions):
        fail(Exit.CONTRACT, "GIT_EXCLUSION_DUPLICATE")
    for tree_path in tree_exclusions:
        tree_parts = validate_relative(tree_path, "GIT_TREE_EXCLUSION", forbid_vault=False)
        for exact_path in exact_file_exclusions:
            exact_parts = validate_relative(exact_path, "GIT_EXACT_EXCLUSION", forbid_vault=False)
            shared = min(len(tree_parts), len(exact_parts))
            if tree_parts[:shared] == exact_parts[:shared]:
                # A parent/child overlap silently turns the exact output-file
                # carve-out into a subtree carve-out (or vice versa).  Refuse
                # the ambiguous authority instead of relying on pathspec order.
                fail(Exit.CONTRACT, "GIT_EXCLUSION_CLASS_OVERLAP")
    capture, boundary = create_git_metadata_adapter(repo_root, key, git_binary)
    pending: Optional[BaseException] = None
    fields: Optional[Dict[str, Any]] = None
    try:
        head = safe_git_scalar(
            git_binary,
            repo_root,
            boundary,
            ["rev-parse", "--verify", "HEAD"],
            "GIT_HEAD",
        )
        tree = safe_git_scalar(
            git_binary,
            repo_root,
            boundary,
            ["rev-parse", "--verify", "HEAD^{tree}"],
            "GIT_TREE",
        )
        object_format = safe_git_scalar(
            git_binary,
            repo_root,
            boundary,
            ["rev-parse", "--show-object-format"],
            "GIT_OBJECT_FORMAT",
        )
        if object_format not in ("sha1", "sha256"):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_OBJECT_FORMAT")
        expected_oid_length = 40 if object_format == "sha1" else 64
        if not re.fullmatch(r"[0-9a-f]{%d}" % expected_oid_length, head):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_HEAD_FORMAT")
        if not re.fullmatch(r"[0-9a-f]{%d}" % expected_oid_length, tree):
            fail(Exit.PREFLIGHT_DRIFT, "GIT_TREE_FORMAT")
        status = run_git(
            git_binary,
            repo_root,
            boundary,
            ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
            "GIT_STATUS",
            enumerates_worktree=True,
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
        )
        if VAULT_PREFIX.encode("ascii") in status.lower():
            fail(Exit.PRIVACY, "GIT_STATUS_VAULT_LEAK")
        dirty_manifest = dirty_path_manifest_commitment(repo_root, status, key)
        refs = run_git(git_binary, repo_root, boundary, ["show-ref"], "GIT_REFS")
        file_observations = capture["identity"]["files"]

        def evidence_file(role: str) -> Dict[str, Any]:
            observation = file_observations[role]
            metadata = observation.get("metadata")
            if observation.get("state") != "PRESENT" or not isinstance(metadata, dict):
                fail(Exit.INTERNAL, "GIT_CAPTURE_EVIDENCE_FILE")
            return {
                "sha256": observation["raw_sha256"],
                "bytes": observation["bytes"],
                "device": metadata["device"],
                "inode": metadata["inode"],
            }

        index_path = os.path.join(str(capture["git_dir"]), "index")
        config_path = os.path.join(str(capture["common_dir"]), "config")
        fields = {
            "git_control": capture["git_control"],
            "head": head,
            "tree": tree,
            "object_format": object_format,
            "status_sha256": sha256(status),
            "status_bytes": len(status),
            "dirty_manifest_commitment": dirty_manifest,
            "worktree_tree_exclusions": list(tree_exclusions),
            "worktree_exact_file_exclusions": list(exact_file_exclusions),
            "refs_sha256": sha256(refs),
            "refs_bytes": len(refs),
            "index": evidence_file("index"),
            "config": evidence_file("common_config"),
            "hooks": capture["hooks_info"],
            "index_locator_commitment": locator_commitment(key, "git-index", index_path),
            "config_locator_commitment": locator_commitment(key, "git-config", config_path),
            "hooks_locator_commitment": locator_commitment(key, "git-hooks", str(capture["hooks_path"])),
            "hooks_config_state": capture["hooks_state"],
            "git_binary_sha256": hash_regular_absolute(git_binary, "CLT_GIT")["sha256"],
            "git_metadata_source_commitment": hmac_frame(
                key,
                GIT_METADATA_SOURCE_DOMAIN,
                canonical_json(
                    {
                        "source_fingerprint": capture["fingerprint"],
                        "adapter_object_manifest": capture["adapter_object_manifest"],
                    }
                ),
            ),
        }
    except BaseException as error:
        pending = error
    if pending is None:
        finalize_git_metadata_adapter(boundary, key)
    else:
        try:
            cleanup_git_metadata_adapter(boundary)
        except BaseException:
            raise
        raise pending
    if fields is None:
        fail(Exit.INTERNAL, "GIT_SNAPSHOT_FIELDS")
    if git_metadata_adapter_process_scope_residue_count() != 0:
        fail(Exit.PREFLIGHT_DRIFT, "GIT_ADAPTER_CLEANUP_SCOPE_RESIDUE")
    fields.update(
        {
            "git_metadata_adapter_profile": GIT_METADATA_ADAPTER_PROFILE_V3,
            "git_metadata_adapter_cleanup_state": "removed",
            "git_metadata_adapter_residue_count": 0,
            "live_git_control_child_read_count": 0,
        }
    )
    body = canonical_json(fields)
    fields["commitment"] = hmac_frame(key, GIT_SNAPSHOT_DOMAIN, body)
    return fields


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


def checked_generation_authorization_v2(
    value: Mapping[str, Any],
) -> Dict[str, Any]:
    generation = require_exact_object(
        value,
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_CLAIM_AUTHORIZATION",
    )
    challenge = generation.get("approval_challenge_id")
    if not isinstance(challenge, str) or GENERATION_CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_CHALLENGE")
    expected_approval_path = (
        CONTROL_PREFIX
        + "GOV-01-toolchain-static-envelope-generation-envelope-v1."
        + challenge
        + ".json"
    )
    if (
        generation.get("profile") != "gov01-static-envelope-generation-authority-v1"
        or generation.get("approval_envelope_repo_relative_path") != expected_approval_path
        or generation.get("generated_acquisition_envelope_repo_relative_path")
        != expected_pending_envelope_relative(challenge)
        or generation.get("receipt_domain_profile")
        != "SHA-256(ASCII(CLS/GOV01-STATIC-ENVELOPE-GENERATION-RECEIPT/v1) || NUL || raw-generation-envelope-bytes)"
        or generation.get("commit_transition_profile")
        != "single parent commit changing exactly the generation approval envelope path from ABSENT to the approved canonical raw bytes"
        or generation.get("state") != "approved-single-path-commit"
        or generation.get("generation_claim_required") is not True
        or generation.get("generation_claim_profile") != GENERATION_CLAIM_PROFILE
        or generation.get("generation_claim_record_profile") != GENERATION_CLAIM_RECORD_PROFILE
        or generation.get("generation_claim_retention") != GENERATION_CLAIM_RETENTION
    ):
        fail(Exit.CONTRACT, "GENERATION_CLAIM_AUTHORIZATION_PROFILE")
    for field in ("raw_envelope_sha256", "receipt_digest"):
        require_sha256(generation.get(field), "GENERATION_CLAIM_" + field.upper())
    for field in (
        "authorization_parent_commit_oid",
        "authorization_parent_tree_oid",
        "authorization_commit_oid",
        "authorization_tree_oid",
    ):
        oid = generation.get(field)
        if not isinstance(oid, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid) is None:
            fail(Exit.CONTRACT, "GENERATION_CLAIM_AUTHORIZATION_OID")
    return dict(generation)


def generation_claim_name_v2(generation_authorization: Mapping[str, Any]) -> str:
    generation = checked_generation_authorization_v2(generation_authorization)
    return "generation-claim-" + str(generation["approval_challenge_id"])


def validate_generation_claim_temporal_shape_v2(record: Mapping[str, Any]) -> None:
    challenge = record.get("acquisition_approval_challenge_id")
    if not isinstance(challenge, str) or CHALLENGE_RE.fullmatch(challenge) is None:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_ACQUISITION_CHALLENGE")
    census_at = parse_utc(record.get("census_at_utc"), "GENERATION_CLAIM_CENSUS")
    not_after = parse_utc(record.get("not_after_utc"), "GENERATION_CLAIM_EXPIRY")
    if challenge.split("-")[2] != census_at.strftime("%Y%m%d"):
        fail(Exit.CONTRACT, "GENERATION_CLAIM_CHALLENGE_DATE")
    if not_after <= census_at or not_after - census_at > _datetime.timedelta(hours=24):
        fail(Exit.CONTRACT, "GENERATION_CLAIM_TTL")


def validate_pending_raw_for_generation_claim_v2(
    raw: bytes,
    generation_authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_JSON_BYTES:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_PENDING_RAW")
    envelope = parse_json_bytes(raw, "GENERATION_CLAIM_PENDING_ENVELOPE")
    if not isinstance(envelope, dict) or canonical_json(envelope) != raw:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_PENDING_CANONICAL")
    generation = checked_generation_authorization_v2(generation_authorization)
    if envelope.get("generation_authorization") != generation:
        fail(Exit.CONTRACT, "GENERATION_CLAIM_PENDING_AUTHORIZATION")
    census_at = parse_utc(envelope.get("census_at_utc"), "GENERATION_CLAIM_CENSUS")
    validate_manual_envelope_contract(envelope, now=census_at)
    if has_forbidden_pending_envelope_value(envelope):
        fail(Exit.PRIVACY, "GENERATION_CLAIM_PENDING_PRIVACY")
    expected_path = expected_pending_envelope_relative(generation["approval_challenge_id"])
    preimage = envelope.get("authorization_preimage")
    if (
        not isinstance(preimage, Mapping)
        or preimage.get("envelope_repo_relative_path") != expected_path
    ):
        fail(Exit.CONTRACT, "GENERATION_CLAIM_PENDING_PATH")
    return envelope


def build_generation_claim_record_v2(
    *,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
    key: bytes,
) -> Dict[str, Any]:
    generation = checked_generation_authorization_v2(generation_authorization)
    envelope = validate_pending_raw_for_generation_claim_v2(final_envelope_raw, generation)
    body = {
        "profile": "gov01-static-envelope-generation-claim-v1",
        "generation_authorization_challenge_id": generation["approval_challenge_id"],
        "generation_authorization_envelope_raw_sha256": generation["raw_envelope_sha256"],
        "generation_authorization_receipt_digest": generation["receipt_digest"],
        "generation_authorization_parent_commit_oid": generation["authorization_parent_commit_oid"],
        "generation_authorization_parent_tree_oid": generation["authorization_parent_tree_oid"],
        "generation_authorization_commit_oid": generation["authorization_commit_oid"],
        "generation_authorization_tree_oid": generation["authorization_tree_oid"],
        "acquisition_approval_challenge_id": envelope["approval_challenge_id"],
        "census_at_utc": envelope["census_at_utc"],
        "not_after_utc": envelope["not_after_utc"],
        "final_envelope_repo_relative_path": generation[
            "generated_acquisition_envelope_repo_relative_path"
        ],
        "final_envelope_raw_sha256": sha256(final_envelope_raw),
        "final_envelope_bytes": len(final_envelope_raw),
        "final_envelope_receipt_digest": sha256(
            RECEIPT_DOMAINS["gov-01-toolchain-static-acquisition-envelope-v2"]
            + b"\x00"
            + final_envelope_raw
        ),
        "state": "OUTPUT-IDENTITY-FIXED",
    }
    validate_generation_claim_temporal_shape_v2(body)
    record = dict(body)
    record["record_hmac_sha256"] = hmac_frame(
        key,
        GENERATION_CLAIM_DOMAIN,
        canonical_json(body),
    )
    return record


def validate_generation_claim_record_v2(
    record_value: Mapping[str, Any],
    key: bytes,
    generation_authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    record = require_exact_object(
        record_value,
        GENERATION_CLAIM_FIELDS,
        "GENERATION_CLAIM_RECORD",
    )
    generation = checked_generation_authorization_v2(generation_authorization)
    expected_generation = {
        "generation_authorization_challenge_id": generation["approval_challenge_id"],
        "generation_authorization_envelope_raw_sha256": generation["raw_envelope_sha256"],
        "generation_authorization_receipt_digest": generation["receipt_digest"],
        "generation_authorization_parent_commit_oid": generation["authorization_parent_commit_oid"],
        "generation_authorization_parent_tree_oid": generation["authorization_parent_tree_oid"],
        "generation_authorization_commit_oid": generation["authorization_commit_oid"],
        "generation_authorization_tree_oid": generation["authorization_tree_oid"],
        "final_envelope_repo_relative_path": generation[
            "generated_acquisition_envelope_repo_relative_path"
        ],
    }
    if any(record.get(field) != expected for field, expected in expected_generation.items()):
        fail(Exit.REPLAY, "GENERATION_CLAIM_AUTHORITY_DRIFT")
    if (
        record.get("profile") != "gov01-static-envelope-generation-claim-v1"
        or record.get("state") != "OUTPUT-IDENTITY-FIXED"
        or type(record.get("final_envelope_bytes")) is not int
        or record.get("final_envelope_bytes") <= 0
        or record.get("final_envelope_bytes") > MAX_JSON_BYTES
    ):
        fail(Exit.REPLAY, "GENERATION_CLAIM_RECORD_SHAPE")
    for field in (
        "generation_authorization_envelope_raw_sha256",
        "generation_authorization_receipt_digest",
        "final_envelope_raw_sha256",
        "final_envelope_receipt_digest",
        "record_hmac_sha256",
    ):
        require_sha256(record.get(field), "GENERATION_CLAIM_" + field.upper())
    validate_relative(
        str(record.get("final_envelope_repo_relative_path")),
        "GENERATION_CLAIM_FINAL_PATH",
    )
    validate_generation_claim_temporal_shape_v2(record)
    body = {field: record[field] for field in GENERATION_CLAIM_BODY_FIELDS}
    expected_hmac = hmac_frame(key, GENERATION_CLAIM_DOMAIN, canonical_json(body))
    if not hmac.compare_digest(str(record.get("record_hmac_sha256")), expected_hmac):
        fail(Exit.REPLAY, "GENERATION_CLAIM_HMAC")
    return dict(record)


def verify_generation_claim_container_fds_v2(
    *,
    state_fd: int,
    claims_fd: int,
    expected_uid: int,
    expected_gid: int,
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Revalidate already-open state/claims directories without closing them."""
    if (
        type(state_fd) is not int
        or type(claims_fd) is not int
        or type(expected_uid) is not int
        or type(expected_gid) is not int
        or state_fd < 0
        or claims_fd < 0
        or expected_uid != os.getuid()
    ):
        fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_FD_INPUT")
    try:
        state_meta = os.fstat(state_fd)
        claims_meta = os.fstat(claims_fd)
        named_claims = os.stat("claims", dir_fd=state_fd, follow_symlinks=False)
    except OSError:
        fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_CONTAINER_FSTAT")
    for metadata in (state_meta, claims_meta, named_claims):
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o700
            or metadata.st_uid != expected_uid
            or metadata.st_gid != expected_gid
        ):
            fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_CONTAINER_POLICY")
    state_identity = (state_meta.st_dev, state_meta.st_ino)
    claims_identity = (claims_meta.st_dev, claims_meta.st_ino)
    if (
        state_identity == claims_identity
        or claims_meta.st_dev != state_meta.st_dev
        or (named_claims.st_dev, named_claims.st_ino) != claims_identity
    ):
        fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_CONTAINER_IDENTITY")
    assert_no_extended_acl_fd(state_fd, "GENERATION_CLAIM_STATE")
    assert_no_extended_acl_fd(claims_fd, "GENERATION_CLAIM_CLAIMS")
    return state_identity, claims_identity


def _read_generation_claim_from_claims_fd_v2(
    *,
    claims_fd: int,
    expected_uid: int,
    expected_gid: int,
    key: bytes,
    generation_authorization: Mapping[str, Any],
    expected_claim_identity: Optional[Tuple[int, int]] = None,
) -> Optional[Dict[str, Any]]:
    """Read one complete immutable claim relative to a fixed claims FD."""
    claim_name = generation_claim_name_v2(generation_authorization)
    try:
        claim_meta = os.stat(claim_name, dir_fd=claims_fd, follow_symlinks=False)
    except FileNotFoundError:
        if expected_claim_identity is not None:
            fail(Exit.REPLAY, "GENERATION_CLAIM_CREATED_MISSING")
        return None
    except OSError:
        fail(Exit.REPLAY, "GENERATION_CLAIM_LSTAT")
    claim_identity = (claim_meta.st_dev, claim_meta.st_ino)
    if (
        not stat.S_ISDIR(claim_meta.st_mode)
        or stat.S_ISLNK(claim_meta.st_mode)
        or stat.S_IMODE(claim_meta.st_mode) != 0o700
        or claim_meta.st_uid != expected_uid
        or claim_meta.st_gid != expected_gid
        or (expected_claim_identity is not None and claim_identity != expected_claim_identity)
    ):
        fail(Exit.REPLAY, "GENERATION_CLAIM_DIRECTORY_POLICY")
    claim_fd: Optional[int] = None
    record_fd: Optional[int] = None
    try:
        claim_fd = open_existing_private_container(
            claims_fd,
            claim_name,
            expected_uid=expected_uid,
            expected_gid=expected_gid,
        )
        opened_claim = os.fstat(claim_fd)
        if (opened_claim.st_dev, opened_claim.st_ino) != claim_identity:
            fail(Exit.REPLAY, "GENERATION_CLAIM_DIRECTORY_IDENTITY")
        try:
            children = sorted(os.listdir(claim_fd), key=os.fsencode)
        except OSError:
            fail(Exit.REPLAY, "GENERATION_CLAIM_LIST")
        if children != ["generation-record.json"]:
            fail(Exit.REPLAY, "GENERATION_CLAIM_PARTIAL_OR_UNEXPECTED")
        record_fd, record_meta = open_relative_regular(
            claim_fd,
            "generation-record.json",
            "GENERATION_CLAIM_RECORD",
            MAX_JSON_BYTES,
        )
        record_before = (
            record_meta.st_dev,
            record_meta.st_ino,
            record_meta.st_mode,
            record_meta.st_uid,
            record_meta.st_gid,
            record_meta.st_nlink,
            record_meta.st_size,
            record_meta.st_mtime_ns,
            record_meta.st_ctime_ns,
            getattr(record_meta, "st_flags", 0),
        )
        if (
            stat.S_IMODE(record_meta.st_mode) != 0o600
            or record_meta.st_uid != expected_uid
            or record_meta.st_gid != expected_gid
            or record_meta.st_nlink != 1
            or record_meta.st_size <= 0
        ):
            fail(Exit.REPLAY, "GENERATION_CLAIM_RECORD_POLICY")
        record_raw = read_fd(record_fd, MAX_JSON_BYTES, "GENERATION_CLAIM_RECORD")
        record_after_meta = os.fstat(record_fd)
        record_after = (
            record_after_meta.st_dev,
            record_after_meta.st_ino,
            record_after_meta.st_mode,
            record_after_meta.st_uid,
            record_after_meta.st_gid,
            record_after_meta.st_nlink,
            record_after_meta.st_size,
            record_after_meta.st_mtime_ns,
            record_after_meta.st_ctime_ns,
            getattr(record_after_meta, "st_flags", 0),
        )
        if record_after != record_before or len(record_raw) != record_meta.st_size:
            fail(Exit.REPLAY, "GENERATION_CLAIM_RECORD_READ_RACE")
        try:
            final_children = sorted(os.listdir(claim_fd), key=os.fsencode)
            named_after = os.stat(claim_name, dir_fd=claims_fd, follow_symlinks=False)
        except OSError:
            fail(Exit.REPLAY, "GENERATION_CLAIM_DIRECTORY_REVALIDATE")
        if (
            final_children != ["generation-record.json"]
            or (named_after.st_dev, named_after.st_ino) != claim_identity
            or stat.S_IMODE(named_after.st_mode) != 0o700
            or named_after.st_uid != expected_uid
            or named_after.st_gid != expected_gid
        ):
            fail(Exit.REPLAY, "GENERATION_CLAIM_DIRECTORY_DRIFT")
    finally:
        if record_fd is not None:
            os.close(record_fd)
        if claim_fd is not None:
            os.close(claim_fd)
    record = parse_json_bytes(record_raw, "GENERATION_CLAIM_RECORD")
    if not isinstance(record, dict) or canonical_json(record) != record_raw:
        fail(Exit.REPLAY, "GENERATION_CLAIM_RECORD_CANONICAL")
    return validate_generation_claim_record_v2(record, key, generation_authorization)


def probe_generation_claim_from_verified_fds_v2(
    *,
    state_fd: int,
    claims_fd: int,
    expected_uid: int,
    expected_gid: int,
    key: bytes,
    generation_authorization: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    """Return a trusted complete GEN claim, or None, from fixed caller-owned FDs."""
    if not isinstance(key, bytes) or len(key) != 32:
        fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_KEY")
    verify_generation_claim_container_fds_v2(
        state_fd=state_fd,
        claims_fd=claims_fd,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
    )
    result = _read_generation_claim_from_claims_fd_v2(
        claims_fd=claims_fd,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        key=key,
        generation_authorization=generation_authorization,
    )
    verify_generation_claim_container_fds_v2(
        state_fd=state_fd,
        claims_fd=claims_fd,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
    )
    return result


def probe_generation_claim_v2(
    *,
    runtime_args: GenerationRuntimeArgsV2,
    generation_authorization: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    """Open the receipt-bound private controls, then probe through the FD core."""
    revalidate_generation_runtime_args_v2(runtime_args, generation_authorization)
    verify_control_preparation_projection_v2(runtime_args)
    state_meta = require_owned_directory(runtime_args.state_root, "GENERATION_STATE_ROOT", exact_mode=0o700)
    key = load_hmac_key(runtime_args.key_file, state_meta.st_uid, state_meta.st_gid)
    state_fd = open_directory(runtime_args.state_root, "GENERATION_STATE_ROOT")
    claims_fd: Optional[int] = None
    try:
        opened_state = os.fstat(state_fd)
        if (
            (opened_state.st_dev, opened_state.st_ino, opened_state.st_uid, opened_state.st_gid)
            != (state_meta.st_dev, state_meta.st_ino, state_meta.st_uid, state_meta.st_gid)
            or stat.S_IMODE(opened_state.st_mode) != 0o700
        ):
            fail(Exit.PRE_WORKTREE_CAS, "GENERATION_STATE_ROOT_IDENTITY_DRIFT")
        claims_fd = open_existing_private_container(
            state_fd,
            "claims",
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
        )
        result = probe_generation_claim_from_verified_fds_v2(
            state_fd=state_fd,
            claims_fd=claims_fd,
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
            key=key,
            generation_authorization=generation_authorization,
        )
        verify_open_directory_identity(
            runtime_args.state_root,
            state_fd,
            "GENERATION_STATE_ROOT",
        )
        return result
    finally:
        if claims_fd is not None:
            os.close(claims_fd)
        os.close(state_fd)


def create_generation_claim_from_verified_fds_v2(
    *,
    state_fd: int,
    claims_fd: int,
    expected_uid: int,
    expected_gid: int,
    key: bytes,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
    clock: Callable[[], _datetime.datetime] = utc_now,
) -> Dict[str, Any]:
    """Create, durably sync and semantically reread one claim via fixed FDs.

    Caller-owned FDs remain open.  Any partial claim left by an error is
    retained and is neither repaired nor deleted by this core.
    """
    if not isinstance(key, bytes) or len(key) != 32 or not callable(clock):
        fail(Exit.PRIVATE_STATE, "GENERATION_CLAIM_CORE_INPUT")
    verify_generation_claim_container_fds_v2(
        state_fd=state_fd,
        claims_fd=claims_fd,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
    )
    record = build_generation_claim_record_v2(
        generation_authorization=generation_authorization,
        final_envelope_raw=final_envelope_raw,
        key=key,
    )
    claim_fd: Optional[int] = None
    try:
        claim_fd = mkdir_private_child(
            claims_fd,
            generation_claim_name_v2(generation_authorization),
            expected_uid,
            expected_gid,
            before_create=lambda: assert_deadline_not_expired(record["not_after_utc"], clock),
        )
        claim_meta = os.fstat(claim_fd)
        claim_identity = (claim_meta.st_dev, claim_meta.st_ino)
        try:
            os.fsync(claims_fd)
        except OSError:
            fail(Exit.EVIDENCE, "GENERATION_CLAIM_DIRECTORY_FSYNC")
        write_exclusive(
            claim_fd,
            "generation-record.json",
            canonical_json(record),
            mode=0o600,
        )
        try:
            os.fsync(claim_fd)
            os.fsync(claims_fd)
        except OSError:
            fail(Exit.EVIDENCE, "GENERATION_CLAIM_CONTAINER_FSYNC")
        verify_generation_claim_container_fds_v2(
            state_fd=state_fd,
            claims_fd=claims_fd,
            expected_uid=expected_uid,
            expected_gid=expected_gid,
        )
        observed = _read_generation_claim_from_claims_fd_v2(
            claims_fd=claims_fd,
            expected_uid=expected_uid,
            expected_gid=expected_gid,
            key=key,
            generation_authorization=generation_authorization,
            expected_claim_identity=claim_identity,
        )
        if observed is None or not hmac.compare_digest(canonical_json(observed), canonical_json(record)):
            fail(Exit.REPLAY, "GENERATION_CLAIM_SEMANTIC_REREAD")
        verify_generation_claim_container_fds_v2(
            state_fd=state_fd,
            claims_fd=claims_fd,
            expected_uid=expected_uid,
            expected_gid=expected_gid,
        )
        return observed
    finally:
        if claim_fd is not None:
            os.close(claim_fd)


def create_generation_claim_v2(
    *,
    runtime_args: GenerationRuntimeArgsV2,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
    clock: Callable[[], _datetime.datetime] = utc_now,
) -> Dict[str, Any]:
    """Bind private controls, then consume GEN authority through the FD core."""
    revalidate_generation_runtime_args_v2(runtime_args, generation_authorization)
    verify_control_preparation_projection_v2(runtime_args)
    state_meta = require_owned_directory(runtime_args.state_root, "GENERATION_STATE_ROOT", exact_mode=0o700)
    key = load_hmac_key(runtime_args.key_file, state_meta.st_uid, state_meta.st_gid)
    state_fd = open_directory(runtime_args.state_root, "GENERATION_STATE_ROOT")
    claims_fd: Optional[int] = None
    try:
        opened_state = os.fstat(state_fd)
        if (
            (opened_state.st_dev, opened_state.st_ino, opened_state.st_uid, opened_state.st_gid)
            != (state_meta.st_dev, state_meta.st_ino, state_meta.st_uid, state_meta.st_gid)
            or stat.S_IMODE(opened_state.st_mode) != 0o700
        ):
            fail(Exit.PRE_WORKTREE_CAS, "GENERATION_STATE_ROOT_IDENTITY_DRIFT")
        claims_fd = open_existing_private_container(
            state_fd,
            "claims",
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
        )
        result = create_generation_claim_from_verified_fds_v2(
            state_fd=state_fd,
            claims_fd=claims_fd,
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
            key=key,
            generation_authorization=generation_authorization,
            final_envelope_raw=final_envelope_raw,
            clock=clock,
        )
        verify_open_directory_identity(
            runtime_args.state_root,
            state_fd,
            "GENERATION_STATE_ROOT",
        )
        return result
    finally:
        if claims_fd is not None:
            os.close(claims_fd)
        os.close(state_fd)


def verify_generation_claim_recovery_from_verified_fds_v2(
    *,
    state_fd: int,
    claims_fd: int,
    expected_uid: int,
    expected_gid: int,
    key: bytes,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
) -> Dict[str, Any]:
    """Verify crash recovery against exact raw output via caller-owned FDs."""
    record = probe_generation_claim_from_verified_fds_v2(
        state_fd=state_fd,
        claims_fd=claims_fd,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        key=key,
        generation_authorization=generation_authorization,
    )
    if record is None:
        fail(Exit.REPLAY, "GENERATION_CLAIM_ABSENT")
    envelope = validate_pending_raw_for_generation_claim_v2(
        final_envelope_raw,
        generation_authorization,
    )
    expected = {
        "acquisition_approval_challenge_id": envelope["approval_challenge_id"],
        "census_at_utc": envelope["census_at_utc"],
        "not_after_utc": envelope["not_after_utc"],
        "final_envelope_raw_sha256": sha256(final_envelope_raw),
        "final_envelope_bytes": len(final_envelope_raw),
        "final_envelope_receipt_digest": sha256(
            RECEIPT_DOMAINS["gov-01-toolchain-static-acquisition-envelope-v2"]
            + b"\x00"
            + final_envelope_raw
        ),
    }
    if any(record.get(field) != value for field, value in expected.items()):
        fail(Exit.REPLAY, "GENERATION_CLAIM_RECOVERY_DRIFT")
    return record


def verify_generation_claim_recovery_v2(
    *,
    runtime_args: GenerationRuntimeArgsV2,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
) -> Dict[str, Any]:
    """Bind private controls, then verify recovery through the FD core."""
    revalidate_generation_runtime_args_v2(runtime_args, generation_authorization)
    verify_control_preparation_projection_v2(runtime_args)
    state_meta = require_owned_directory(runtime_args.state_root, "GENERATION_STATE_ROOT", exact_mode=0o700)
    key = load_hmac_key(runtime_args.key_file, state_meta.st_uid, state_meta.st_gid)
    state_fd = open_directory(runtime_args.state_root, "GENERATION_STATE_ROOT")
    claims_fd: Optional[int] = None
    try:
        opened_state = os.fstat(state_fd)
        if (
            (opened_state.st_dev, opened_state.st_ino, opened_state.st_uid, opened_state.st_gid)
            != (state_meta.st_dev, state_meta.st_ino, state_meta.st_uid, state_meta.st_gid)
            or stat.S_IMODE(opened_state.st_mode) != 0o700
        ):
            fail(Exit.PRE_WORKTREE_CAS, "GENERATION_STATE_ROOT_IDENTITY_DRIFT")
        claims_fd = open_existing_private_container(
            state_fd,
            "claims",
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
        )
        result = verify_generation_claim_recovery_from_verified_fds_v2(
            state_fd=state_fd,
            claims_fd=claims_fd,
            expected_uid=state_meta.st_uid,
            expected_gid=state_meta.st_gid,
            key=key,
            generation_authorization=generation_authorization,
            final_envelope_raw=final_envelope_raw,
        )
        verify_open_directory_identity(
            runtime_args.state_root,
            state_fd,
            "GENERATION_STATE_ROOT",
        )
        return result
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
    envelope_relative = validate_locator_boundaries(args)
    current_key = load_hmac_key(args.key_file, expected_owner_uid, expected_group_gid)
    if not hmac.compare_digest(current_key, key):
        fail(Exit.PRE_WORKTREE_CAS, "HMAC_KEY_DRIFT")
    current_envelope, current_raw, current_receipt = load_envelope(args.envelope, receipt_digest)
    if current_raw != envelope_raw or not hmac.compare_digest(current_receipt, receipt_digest):
        fail(Exit.PRE_WORKTREE_CAS, "ENVELOPE_DRIFT")
    if current_envelope.get("approval_challenge_id") != envelope.get("approval_challenge_id"):
        fail(Exit.PRE_WORKTREE_CAS, "ENVELOPE_CHALLENGE_DRIFT")
    validate_envelope_path_binding(args, current_envelope, envelope_relative)
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
        "worktree_tree_exclusions",
        "worktree_exact_file_exclusions",
        "refs_sha256",
        "refs_bytes",
        "index",
        "config",
        "hooks",
        "hooks_config_state",
        "git_binary_sha256",
        "git_metadata_source_commitment",
        "git_metadata_adapter_profile",
        "git_metadata_adapter_cleanup_state",
        "git_metadata_adapter_residue_count",
        "live_git_control_child_read_count",
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
        "product_state_automatic_cleanup_authorized": False,
        "temporary_adapter_cleanup_required": True,
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
    cleanup_uncertain = public_code.startswith("GIT_ADAPTER_CLEANUP_")
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
        GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY,
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": selected_mode == "acquire" or cleanup_uncertain,
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
    cleanup_uncertain = public_code.startswith("GIT_ADAPTER_CLEANUP_")
    recorder.failed(public_code, int(code))
    gate_results = recorder.partial_projection()
    g03_records = [
        record
        for record in gate_results["reached_gates"]
        if record.get("gate_id") == "G03" and record.get("status") == "PASS"
    ]
    toolchain_context: Optional[Dict[str, Any]] = None
    trusted_authority_binding = recorder.authority_binding()
    retry_bound = not cleanup_uncertain and bool(
        isinstance(trusted_authority_binding, Mapping)
        and isinstance(trusted_authority_binding.get("approval_challenge_id"), str)
        and CHALLENGE_RE.fullmatch(trusted_authority_binding["approval_challenge_id"]) is not None
        and isinstance(trusted_authority_binding.get("receipt_digest"), str)
        and SHA256_RE.fullmatch(trusted_authority_binding["receipt_digest"]) is not None
    )
    if trusted_authority_binding is not None:
        # Read-only stdout intentionally carries no approval pair.  A trusted
        # in-process pair is retained only as a non-serialized proof for the
        # conditional same-envelope retry claim.
        if not retry_bound:
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
        retry_bound,
        False,
        (
            PRECLAIM_RETRY_AUTHORITY
            if retry_bound
            else GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else FAIL_CLOSED_REVIEW_AUTHORITY
        ),
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": cleanup_uncertain,
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
    cleanup_uncertain = attempt.adapter_cleanup_state == "residue-or-uncertain"
    preclaim_retry = attempt.claim_state == "not-created" and not cleanup_uncertain
    result["authority"] = authority_projection(
        preclaim_retry,
        False,
        (
            PRECLAIM_RETRY_AUTHORITY
            if preclaim_retry
            else GIT_ADAPTER_CLEANUP_AUTHORITY if cleanup_uncertain else RETAINED_STATE_AUTHORITY
        ),
    )
    result["error"] = public_error_projection(code, public_code)
    result["retention"] = {
        "stage_deleted_or_moved_on_failure": False,
        "automatic_rollback_performed": False,
        "private_state_inspection_required": attempt.claim_state != "not-created" or cleanup_uncertain,
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
    cache_fd: Optional[int],
    repo_fd: Optional[int],
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
        if opened_fd is None:
            continue
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


def public_artifact_entries_v2(
    observations: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    expected_specs = PENDING_STATIC_ARTIFACT_SPECS
    if len(observations) != len(expected_specs) + 1:
        fail(Exit.CONTRACT, "GENERATION_ARTIFACT_COUNT")
    result: List[Dict[str, Any]] = []
    for index, observation in enumerate(observations):
        expected_role, expected_path = (
            expected_specs[index]
            if index < len(expected_specs)
            else (GENERATION_APPROVAL_ROLE, observation.get("path"))
        )
        if observation.get("role") != expected_role or observation.get("path") != expected_path:
            fail(Exit.CONTRACT, "GENERATION_ARTIFACT_ORDER")
        digest = require_sha256(observation.get("sha256"), "GENERATION_ARTIFACT")
        length = observation.get("bytes")
        if type(length) is not int or length <= 0:
            fail(Exit.CONTRACT, "GENERATION_ARTIFACT_BYTES")
        result.append(
            {
                "path": expected_path,
                "role": expected_role,
                "file_kind": "regular",
                "byte_length": length,
                "raw_file_sha256": digest,
            }
        )
    generation_path = result[-1]["path"]
    if not isinstance(generation_path, str) or GENERATION_APPROVAL_PATH_RE.fullmatch(generation_path) is None:
        fail(Exit.CONTRACT, "GENERATION_ARTIFACT_PATH")
    return result


def pending_schema_binding_v2(schema_digest: str) -> Dict[str, Any]:
    require_sha256(schema_digest, "PENDING_SCHEMA")
    return {
        "schema_id": SCHEMA_ID,
        "schema_artifact_path": CONTROL_PREFIX
        + "GOV-01-toolchain-static-acquisition-envelope-v2.schema.json",
        "schema_raw_file_sha256": schema_digest,
        "schema_artifact_role": "pending-envelope-schema",
        "external_validator_profile": "JSON-Schema-draft-2020-12-strict-additionalProperties-false-format-annotation-plus-content-addressed-strict-UTC-calendar-and-duplicate-key-checker",
        "preapproval_external_validation_required": True,
        "runtime_json_schema_execution_allowed": False,
        "runtime_schema_hash_binding_required": True,
        "runtime_manual_critical_field_checks_required": True,
        "runtime_checkpoint": "after raw receipt/challenge/expiry verification and schema artifact hash verification, before any other envelope-controlled read, verifier-source compilation, subprocess or write",
        "schema_digest_must_equal_artifact_entry": True,
        "validation_failure_action": "fail closed before any authorized write or verifier-source compilation",
    }


def collect_generation_observations_v2(
    *,
    runtime_args: GenerationRuntimeArgsV2,
    approval_challenge_id: str,
    census_at_utc: str,
    not_after_utc: str,
    generation_authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    """Collect the one authoritative pending-envelope observation set.

    This function is read-only.  It accepts no pending-envelope skeleton and
    no caller-supplied hash, version, tool identity or private locator.  The
    caller must validate the public GEN receipt and one-file commit before
    invoking it; this function re-derives every locator and revalidates the
    content-addressed GEN artifact before any verifier compilation.
    """
    require_python_isolation()
    require_host()
    envelope_relative = revalidate_generation_runtime_args_v2(
        runtime_args,
        generation_authorization,
    )
    temporal_shell = {
        "approval_challenge_id": approval_challenge_id,
        "census_at_utc": census_at_utc,
        "not_after_utc": not_after_utc,
    }
    validate_envelope_temporal_contract(temporal_shell)
    repo_meta = require_owned_directory(runtime_args.repo_root, "GENERATION_REPO_ROOT")
    state_meta = require_owned_directory(runtime_args.state_root, "GENERATION_STATE_ROOT", exact_mode=0o700)
    require_same_filesystem(repo_meta, state_meta)
    require_owned_directory(runtime_args.cache_root, "GENERATION_CACHE_ROOT")
    observed_predecessor = verify_control_preparation_projection_v2(runtime_args)
    key = load_hmac_key(runtime_args.key_file, state_meta.st_uid, state_meta.st_gid)
    locator_args = argparse.Namespace(**runtime_args._asdict())
    locators = locator_commitments(locator_args, key)
    claim_preimage = verify_claim_preimage(runtime_args.state_root, approval_challenge_id)
    control_identity_body = build_private_control_identity_body(claim_preimage, runtime_args.key_file)
    control_identity = private_control_identity_commitment(key, control_identity_body)
    tree_exclusions = (".gov01-toolchain-stage-" + approval_challenge_id, TARGET_NAME)
    exact_file_exclusions = (envelope_relative,)
    repo_fd = open_directory(runtime_args.repo_root, "GENERATION_REPO_ROOT")
    cache_fd: Optional[int] = None
    try:
        artifacts = observe_pending_artifacts_v2(repo_fd, generation_authorization)
        artifact_entries = public_artifact_entries_v2(artifacts)
        public_predecessor = verify_public_predecessor_sources_v2(repo_fd)
        generation_shell = {"generation_authorization": dict(generation_authorization)}
        generation_envelope = verify_generation_authorization_artifact(repo_fd, generation_shell, artifacts)
        schema_artifact = next(
            entry for entry in artifact_entries if entry["role"] == "pending-envelope-schema"
        )
        schema_shell = {
            "schema_binding": pending_schema_binding_v2(schema_artifact["raw_file_sha256"]),
            "artifacts": artifact_entries,
        }
        schema_observation = verify_bound_schema_artifact(repo_fd, schema_shell)
        schema_bundle = verify_projection_schema_bundle(repo_fd, artifacts, schema_observation)
        control_state = capture_control_state(repo_fd)
        assert_absent_control_paths(repo_fd)
        require_node_modules_absent(runtime_args.repo_root)
        assert_entry_absent(
            repo_fd,
            ".gov01-toolchain-stage-" + approval_challenge_id,
            "GENERATION_STAGE",
        )
        toolchain = observe_runtime_toolchain_v2(runtime_args.repo_root, artifacts)
        git_state = git_snapshot(
            runtime_args.repo_root,
            key,
            toolchain["git_binary"],
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
        )
        if (
            git_state.get("head") != generation_authorization.get("authorization_commit_oid")
            or git_state.get("tree") != generation_authorization.get("authorization_tree_oid")
        ):
            fail(Exit.PREFLIGHT_DRIFT, "GENERATION_AUTHORIZATION_HEAD_DRIFT")
        generation_predecessor = generation_envelope.get("predecessor")
        if (
            not isinstance(generation_predecessor, dict)
            or generation_predecessor.get("static_contract_commit_oid")
            != generation_authorization.get("authorization_parent_commit_oid")
            or generation_predecessor.get("static_contract_tree_oid")
            != generation_authorization.get("authorization_parent_tree_oid")
        ):
            fail(Exit.CONTRACT, "GENERATION_AUTHORIZATION_PARENT_BINDING")
        verify_generation_artifacts_against_micro_and_head_v2(
            runtime_args.repo_root,
            key,
            toolchain["git_binary"],
            artifacts,
            generation_envelope,
            generation_authorization,
        )
        # Only source proven equal to the approved micro and the C2 HEAD blob
        # may be compiled.  Live self-observation alone is not execution authority.
        verifier = load_bound_verifier(repo_fd, artifacts)
        processes = process_census(
            runtime_args.repo_root,
            key,
            toolchain["pgrep_binary"],
            toolchain["lsof_binary"],
        )
        if processes["claude_session_count"] != 0:
            fail(Exit.PREFLIGHT_DRIFT, "ACTIVE_CLAUDE_SESSION")
        lock, lock_raw, _ = read_json_relative(repo_fd, "package-lock.json", "PACKAGE_LOCK")
        if not isinstance(lock, dict):
            fail(Exit.CACHE_LOCK, "LOCK_ROOT")
        selected = selected_lock_entries(lock)
        cache_fd = open_directory(runtime_args.cache_root, "GENERATION_CACHE_ROOT")
        cache_manifest, bins, total_bytes = cache_census(cache_fd, selected)
        try:
            expected = verifier.build_expected(
                runtime_args.repo_root,
                runtime_args.cache_root,
                retain_bytes=False,
            )
        except Exception:
            fail(Exit.ARCHIVE, "STATIC_VERIFIER_BUILD")
        if not isinstance(expected, dict):
            fail(Exit.CHECKER_DRIFT, "STATIC_VERIFIER_RESULT")
        expected_public = verifier.public_summary(expected)
        validate_static_expected_shape(expected_public)
        lock_observation = verify_lock_contract(
            {"lock_closure": {}, "success_contract": {}},
            expected,
            len(selected),
            total_bytes,
            len(bins),
            strict=False,
        )
        artifact_receipt = public_artifact_set_receipt(artifacts)
        preapproval_body = build_private_preapproval_body(
            temporal_shell,
            key,
            locators,
            control_identity,
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
        preapproval = private_preapproval_commitment(key, preapproval_body)
        verify_control_containment(repo_fd, control_state, Exit.PREFLIGHT_DRIFT)
        if (
            observed_predecessor.get("control_preparation_approval_challenge_id")
            != public_predecessor.get("control_preparation_approval_challenge_id")
        ):
            fail(Exit.CONTRACT, "CONTROL_PREPARATION_CHALLENGE_BINDING")
        del cache_manifest
    finally:
        if cache_fd is not None:
            os.close(cache_fd)
        os.close(repo_fd)
    schema_public = dict(schema_observation)
    schema_public.update(schema_bundle)
    return {
        "artifacts": artifact_entries,
        "schema_binding_observation": schema_public,
        "toolchain": {
            "entries": copy.deepcopy(toolchain["entries"]),
            "toolchain_set_receipt_sha256": toolchain["toolchain_set_receipt_sha256"],
            "dynamic_closure_receipt_sha256": toolchain["dynamic_closure_receipt_sha256"],
        },
        "git_snapshot": copy.deepcopy(git_state),
        "process_census": copy.deepcopy(processes),
        "package_lock_raw_sha256": sha256(lock_raw),
        "lock_observation": copy.deepcopy(lock_observation),
        "static_expected": copy.deepcopy(expected_public),
        "hmac_key_id": hmac_key_id(key),
        "authorized_locator_commitments": copy.deepcopy(locators),
        "private_control_identity_commitment": control_identity,
        "public_repo_artifact_set_receipt_sha256": artifact_receipt,
        "private_preapproval_commitment": preapproval,
        "predecessor_projection": copy.deepcopy(observed_predecessor),
        "envelope_repo_relative_path": envelope_relative,
    }


def synchronize_pending_template_git_adapter_v2(template: Dict[str, Any]) -> Dict[str, Any]:
    approval = template["approval_receipt_contract"]
    approval["first_authority_consuming_persistent_write"] = (
        FIRST_AUTHORITY_CONSUMING_PERSISTENT_WRITE_V2
    )
    approval["receipt_before_first_authority_consuming_persistent_write"] = True
    authorization = template["authorization_preimage"]
    authorization["git_snapshot_commitment_profile"] = GIT_SNAPSHOT_COMMITMENT_PROFILE_V2
    authorization["private_preimage_capture"] = (
        "census and post-approval checks may materialize only an identity-bound nonpersistent Git metadata adapter "
        "under /private/tmp; every child fchdir's through a dedicated duplicate of the held adapter Git-directory "
        "FD, closes that child-only FD, and reads the sealed frozen adapter with literal --git-dir=., explicit "
        "--work-tree and zero "
        "live Git-control reads; source and adapter CAS run before/after children, exact cleanup and zero residue are "
        "required before returning; the persistent O_EXCL challenge claim remains the first authority-consuming "
        "persistent write"
    )
    execution = template["execution_plan"]
    execution["allowed_subprocess_executable_roles"] = list(AUTHORIZED_SUBPROCESS_ROLES)
    execution["git_metadata_adapter_bootstrap_sandbox_profile"] = (
        GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V3
    )
    execution["git_metadata_adapter_trust_boundary"] = (
        GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
    )
    execution["git_metadata_adapter_host_assurance"] = (
        GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
    )
    if "GIT_OBJECT_DIRECTORY" not in execution["environment_name_allowlist"]:
        execution["environment_name_allowlist"].append("GIT_OBJECT_DIRECTORY")
    execution["evidence_command_templates"] = [
        entry
        for entry in execution["evidence_command_templates"]
        if not (isinstance(entry, dict) and entry.get("role") == "git-metadata-adapter-bootstrap")
    ]
    git_templates = [
        entry
        for entry in execution["evidence_command_templates"]
        if isinstance(entry, dict) and entry.get("role") == "git-read-only-evidence"
    ]
    if len(git_templates) != 1:
        fail(Exit.INTERNAL, "PENDING_TEMPLATE_GIT_ROLE")
    git_templates[0]["argv_allowlist"] = git_read_only_argv_templates_v2()
    git_templates[0]["read_only"] = True
    bootstrap_environment = list(git_templates[0]["environment_name_allowlist"])
    if "GIT_OBJECT_DIRECTORY" not in bootstrap_environment:
        bootstrap_environment.append("GIT_OBJECT_DIRECTORY")
    bootstrap_template = {
        "argv_allowlist": git_adapter_bootstrap_argv_templates_v2(),
        "environment_name_allowlist": bootstrap_environment,
        "executable": "{RESOLVED_CLT_GIT_PRIVATE}",
        "read_only": False,
        "role": "git-metadata-adapter-bootstrap",
        "shell": False,
        "write_scope": "checkpoint-scoped-private-temp-adapter-only",
    }
    execution["evidence_command_templates"].insert(
        execution["evidence_command_templates"].index(git_templates[0]),
        bootstrap_template,
    )
    execution["phase_order"] = [
        (
            "directly capture live Git metadata, freeze and seal an exact private-temp adapter, run explicit-adapter "
            "Git evidence children with zero live-control reads, revalidate the live source and remove the exact "
            "adapter with zero residue before comparing Git-snapshot and private-preapproval commitments"
            if phase == "read-only-recompute-and-compare-full-Git-snapshot-and-private-preapproval-commitments"
            else phase
        )
        for phase in execution["phase_order"]
    ]
    mutation = template["mutation_scope"]
    mutation["git_metadata_adapter_trust_boundary"] = (
        GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
    )
    mutation["git_metadata_adapter_host_assurance"] = (
        GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
    )
    mutation["git_metadata_adapter_cleanup_guarantee"] = (
        GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
    )
    mutation["allowed_ephemeral_mutations"] = [GIT_ADAPTER_EPHEMERAL_MUTATION_V3] + [
        value
        for value in mutation["allowed_ephemeral_mutations"]
        if value != GIT_ADAPTER_EPHEMERAL_MUTATION_V3
    ]
    mutation["forbidden_mutations"] = [
        (
            "write outside the exact identity-bound /private/tmp Git adapter scratch, exact persistent challenge "
            "claim/ledger, exact stage and exact exclusive target publication"
            if value == "write outside exact persistent challenge claim/ledger, exact stage and exact exclusive target publication"
            else value
        )
        for value in mutation["forbidden_mutations"]
    ]
    failure = template["failure_contract"]
    failure.pop("retry_allowed", None)
    failure["preclaim_retry_allowed"] = True
    failure["postclaim_retry_allowed"] = False
    failure["evidence_action"] = FAILURE_EVIDENCE_ACTION_V2
    failure["git_metadata_adapter_cleanup_guarantee"] = (
        GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
    )
    failure["challenge_state"] = (
        "before the first authority-consuming persistent write no persistent consumption record exists but this "
        "envelope/challenge must be treated as rejected and replaced; after exclusive claim mkdir the persistent "
        "state is consumed-rejected"
    )
    private = template["private_state_authorization"]
    private["first_authority_consuming_persistent_write"] = (
        FIRST_AUTHORITY_CONSUMING_PERSISTENT_WRITE_V2
    )
    private["private_preimage_checks"] = list(PRIVATE_PREIMAGE_CHECKS)
    private["private_write_authority"] = [
        "create, seal and mandatorily remove only the exact dev/inode-bound /private/tmp Git metadata adapter "
        "scratch; cleanup uncertainty or residue is terminal and this scratch never consumes the challenge",
    ] + [
        value
        for value in private["private_write_authority"]
        if not value.startswith("create, seal and mandatorily remove only the exact dev/inode-bound /private/tmp")
    ]
    private["private_read_authority"] = [
        (
            "directly capture live Git control, HEAD, index, refs, config, hooks and object-store evidence into a "
            "path-free keyed source receipt; Git children read only the sealed adapter and source CAS is repeated "
            "before cleanup"
            if value.startswith("read Git control marker/commondir/config/alternate-control state")
            else value
        )
        for value in private["private_read_authority"]
    ]
    private["retention"] = (
        "persistent challenge claim and ledger are retained outside repo and never automatically deleted; failed "
        "stage and any published target are never automatically deleted; the private-temp Git adapter is never "
        "retained intentionally and success requires exact cleanup with residue_count zero"
    )
    template["privacy"]["git_metadata_adapter_trust_boundary"] = (
        GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
    )
    return template


_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON = json.dumps(
    synchronize_pending_template_git_adapter_v2(
        json.loads(_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_BASE_JSON)
    ),
    ensure_ascii=True,
    sort_keys=True,
    separators=(",", ":"),
)


def build_pending_envelope_v2(
    *,
    approval_challenge_id: str,
    census_at_utc: str,
    not_after_utc: str,
    generation_authorization: Mapping[str, Any],
    observations: Mapping[str, Any],
) -> Dict[str, Any]:
    """Pure, deterministic constructor for the v2 pending envelope.

    Entropy and timestamps are explicit so an already-created GEN-keyed output
    can be rebuilt byte-for-byte during crash recovery.  No filesystem,
    subprocess, clock or random source is consulted here.
    """
    validate_envelope_temporal_contract(
        {
            "approval_challenge_id": approval_challenge_id,
            "census_at_utc": census_at_utc,
            "not_after_utc": not_after_utc,
        },
        now=parse_utc(census_at_utc, "CENSUS_AT"),
    )
    generation = require_exact_object(
        generation_authorization,
        GENERATION_AUTHORIZATION_FIELDS,
        "GENERATION_AUTHORIZATION",
    )
    observed = require_exact_object(
        observations,
        (
            "artifacts",
            "schema_binding_observation",
            "toolchain",
            "git_snapshot",
            "process_census",
            "package_lock_raw_sha256",
            "lock_observation",
            "static_expected",
            "hmac_key_id",
            "authorized_locator_commitments",
            "private_control_identity_commitment",
            "public_repo_artifact_set_receipt_sha256",
            "private_preapproval_commitment",
            "predecessor_projection",
            "envelope_repo_relative_path",
        ),
        "GENERATION_OBSERVATIONS",
    )
    artifacts = observed.get("artifacts")
    if not isinstance(artifacts, list):
        fail(Exit.CONTRACT, "GENERATION_ARTIFACTS")
    artifact_observations = [
        {
            "role": entry.get("role"),
            "path": entry.get("path"),
            "bytes": entry.get("byte_length"),
            "sha256": entry.get("raw_file_sha256"),
        }
        for entry in artifacts
        if isinstance(entry, Mapping)
    ]
    if len(artifact_observations) != len(PENDING_STATIC_ARTIFACT_SPECS) + 1:
        fail(Exit.CONTRACT, "GENERATION_ARTIFACTS")
    if public_artifact_entries_v2(artifact_observations) != artifacts:
        fail(Exit.CONTRACT, "GENERATION_ARTIFACT_PROJECTION")
    artifact_by_role = {entry["role"]: entry for entry in artifacts}
    schema_observation = require_exact_object(
        observed.get("schema_binding_observation"),
        ("path", "sha256", "bytes", "schema_count", "schema_bundle_receipt_sha256"),
        "GENERATION_SCHEMA_OBSERVATION",
    )
    pending_schema = artifact_by_role.get("pending-envelope-schema")
    if (
        not isinstance(pending_schema, Mapping)
        or schema_observation.get("path") != pending_schema.get("path")
        or schema_observation.get("sha256") != pending_schema.get("raw_file_sha256")
        or schema_observation.get("bytes") != pending_schema.get("byte_length")
        or schema_observation.get("schema_count") != 3
    ):
        fail(Exit.CONTRACT, "GENERATION_SCHEMA_OBSERVATION")
    require_sha256(schema_observation.get("schema_bundle_receipt_sha256"), "GENERATION_SCHEMA_BUNDLE")
    toolchain = require_exact_object(
        observed.get("toolchain"),
        ("entries", "toolchain_set_receipt_sha256", "dynamic_closure_receipt_sha256"),
        "GENERATION_TOOLCHAIN",
    )
    entries = toolchain.get("entries")
    if not isinstance(entries, list) or len(entries) != len(TOOLCHAIN_ROLES):
        fail(Exit.CONTRACT, "GENERATION_TOOLCHAIN_ENTRIES")
    for index, role in enumerate(TOOLCHAIN_ROLES):
        entry = require_exact_object(
            entries[index],
            (
                "role",
                "logical_id",
                "artifact_kind",
                "version",
                "digest_profile",
                "raw_digest_sha256",
                "private_locator_omitted",
                "execution_authority",
            ),
            "GENERATION_TOOLCHAIN_ENTRY",
        )
        validate_tool_identity(entry, role)
        require_sha256(entry.get("raw_digest_sha256"), "GENERATION_TOOLCHAIN_DIGEST")
    if (
        toolchain.get("toolchain_set_receipt_sha256") != toolchain_set_receipt(entries)
        or toolchain.get("dynamic_closure_receipt_sha256") != dynamic_toolchain_receipt(entries)
    ):
        fail(Exit.CONTRACT, "GENERATION_TOOLCHAIN_RECEIPT")
    git_state = observed.get("git_snapshot")
    if not isinstance(git_state, Mapping):
        fail(Exit.CONTRACT, "GENERATION_GIT_SNAPSHOT")
    expected_output = expected_pending_envelope_relative(generation.get("approval_challenge_id"))
    if (
        observed.get("envelope_repo_relative_path") != expected_output
        or generation.get("generated_acquisition_envelope_repo_relative_path") != expected_output
        or git_state.get("head") != generation.get("authorization_commit_oid")
        or git_state.get("tree") != generation.get("authorization_tree_oid")
        or tuple(git_state.get("worktree_tree_exclusions") or ())
        != (".gov01-toolchain-stage-" + approval_challenge_id, TARGET_NAME)
        or tuple(git_state.get("worktree_exact_file_exclusions") or ()) != (expected_output,)
    ):
        fail(Exit.CONTRACT, "GENERATION_GIT_BINDING")
    for key in ("commitment", "dirty_manifest_commitment", "git_metadata_source_commitment"):
        require_sha256(git_state.get(key), "GENERATION_GIT_" + key.upper())
    if (
        git_state.get("git_metadata_adapter_profile") != GIT_METADATA_ADAPTER_PROFILE_V3
        or git_state.get("git_metadata_adapter_cleanup_state") != "removed"
        or git_state.get("git_metadata_adapter_residue_count") != 0
        or git_state.get("live_git_control_child_read_count") != 0
    ):
        fail(Exit.CONTRACT, "GENERATION_GIT_ADAPTER")
    processes = observed.get("process_census")
    if not isinstance(processes, Mapping) or processes.get("claude_session_count") != 0:
        fail(Exit.CONTRACT, "GENERATION_PROCESS_CENSUS")
    lock_observation = require_exact_object(
        observed.get("lock_observation"),
        LOCK_OBSERVATION_FIELDS,
        "GENERATION_LOCK_OBSERVATION",
    )
    expected_public = validate_static_expected_shape(observed.get("static_expected"))
    if (
        lock_observation.get("host_selected_package_count") != expected_public.get("selected_package_count")
        or lock_observation.get("host_selected_cache_bytes") != expected_public.get("compressed_bytes")
        or lock_observation.get("host_bin_link_count") != expected_public.get("bin_link_count")
        or lock_observation.get("expected_archive_member_count") != expected_public.get("raw_member_count")
        or lock_observation.get("expected_resolved_tree_entry_count")
        != expected_public.get("tree", {}).get("entry_count")
        or lock_observation.get("content_receipt_sha256") != expected_public.get("content_receipt_sha256")
        or lock_observation.get("ustar_closure_sha256") != expected_public.get("ustar_closure_sha256")
        or lock_observation.get("resolution_receipt_sha256")
        != expected_public.get("resolution", {}).get("sha256")
        or lock_observation.get("expected_tree_sha256") != expected_public.get("tree", {}).get("sha256")
    ):
        fail(Exit.CONTRACT, "GENERATION_LOCK_EXPECTED_BINDING")
    predecessor_projection = require_exact_object(
        observed.get("predecessor_projection"),
        (
            "control_preparation_result_raw_sha256",
            "control_preparation_evidence_receipt_sha256",
            "control_preparation_approval_challenge_id",
            "control_preparation_state",
        ),
        "GENERATION_PREDECESSOR_PROJECTION",
    )
    for key in (
        "control_preparation_result_raw_sha256",
        "control_preparation_evidence_receipt_sha256",
    ):
        require_sha256(predecessor_projection.get(key), "GENERATION_PREDECESSOR")
    if (
        not isinstance(predecessor_projection.get("control_preparation_approval_challenge_id"), str)
        or CONTROL_PREPARATION_CHALLENGE_RE.fullmatch(
            predecessor_projection["control_preparation_approval_challenge_id"]
        )
        is None
        or predecessor_projection.get("control_preparation_state")
        != "CONTROL-PREPARED-FULL-TREE-REVALIDATED-PASS"
    ):
        fail(Exit.CONTRACT, "GENERATION_PREDECESSOR_PROFILE")
    artifact_receipt = require_sha256(
        observed.get("public_repo_artifact_set_receipt_sha256"),
        "GENERATION_ARTIFACT_RECEIPT",
    )
    if artifact_receipt != public_artifact_set_receipt(artifact_observations):
        fail(Exit.CONTRACT, "GENERATION_ARTIFACT_RECEIPT")
    package_lock_digest = require_sha256(
        observed.get("package_lock_raw_sha256"),
        "GENERATION_PACKAGE_LOCK",
    )
    package_artifact = artifact_by_role.get("package-lock")
    if not isinstance(package_artifact, Mapping) or package_artifact.get("raw_file_sha256") != package_lock_digest:
        fail(Exit.CONTRACT, "GENERATION_PACKAGE_LOCK_BINDING")
    hmac_id = require_sha256(observed.get("hmac_key_id"), "GENERATION_HMAC_KEY_ID")
    control_identity = require_sha256(
        observed.get("private_control_identity_commitment"),
        "GENERATION_CONTROL_IDENTITY",
    )
    private_preapproval = require_sha256(
        observed.get("private_preapproval_commitment"),
        "GENERATION_PRIVATE_PREAPPROVAL",
    )
    locators = validate_locator_commitment_projection_v2(
        observed.get("authorized_locator_commitments")
    )
    template = synchronize_pending_template_git_adapter_v2(
        json.loads(_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON)
    )
    if not isinstance(template, dict):
        fail(Exit.INTERNAL, "PENDING_TEMPLATE")
    predecessor = {
        "profile": "gov01-static-acquisition-predecessor-chain-v2",
        "first_approval_envelope_raw_sha256": FIRST_APPROVAL_ENVELOPE_RAW_SHA256,
        "first_approval_receipt_digest": FIRST_RECEIPT_DOMAIN_SHA256,
        "bootstrap_patch_raw_sha256": BOOTSTRAP_PATCH_RAW_SHA256,
        "bootstrap_commit_oid": BOOTSTRAP_COMMIT_OID,
        "control_preparation_envelope_raw_sha256": CONTROL_PREPARATION_ENVELOPE_RAW_SHA256,
        "control_preparation_envelope_receipt_digest": CONTROL_PREPARATION_RECEIPT_DIGEST,
        "control_preparation_approval_challenge_id": predecessor_projection[
            "control_preparation_approval_challenge_id"
        ],
        "control_preparation_result_raw_sha256": predecessor_projection[
            "control_preparation_result_raw_sha256"
        ],
        "control_preparation_evidence_receipt_sha256": predecessor_projection[
            "control_preparation_evidence_receipt_sha256"
        ],
        "control_preparation_state": predecessor_projection["control_preparation_state"],
        "generation_authorization_envelope_raw_sha256": generation["raw_envelope_sha256"],
        "generation_authorization_receipt_digest": generation["receipt_digest"],
        "generation_authorization_challenge_id": generation["approval_challenge_id"],
        "generation_authorization_parent_commit_oid": generation["authorization_parent_commit_oid"],
        "generation_authorization_parent_tree_oid": generation["authorization_parent_tree_oid"],
        "generation_authorization_commit_oid": generation["authorization_commit_oid"],
        "generation_authorization_tree_oid": generation["authorization_tree_oid"],
    }
    predecessor["predecessor_chain_receipt_sha256"] = sha256(
        PREDECESSOR_CHAIN_DOMAIN + b"\x00" + canonical_json(predecessor)
    )
    authorization = template["authorization_preimage"]
    authorization.update(
        {
            "head_commit_oid": git_state.get("head"),
            "head_tree_oid": git_state.get("tree"),
            "git_object_format": git_state.get("object_format"),
            "git_snapshot_commitment": git_state.get("commitment"),
            "private_preapproval_commitment": private_preapproval,
            "public_repo_artifact_set_receipt_sha256": artifact_receipt,
            "worktree_state": "clean"
            if git_state.get("status_bytes") == 0
            else "dirty-user-owned-do-not-normalize",
            "target_worktree_claude_sessions": 0,
            "forbidden_process_match_count": 0,
            "envelope_repo_relative_path": expected_output,
        }
    )
    frozen_toolchain = {
        "platform": EXPECTED_PLATFORM,
        "architecture": EXPECTED_ARCH,
        "entries": copy.deepcopy(entries),
        "dynamic_closure_receipt_sha256": toolchain["dynamic_closure_receipt_sha256"],
        "toolchain_set_receipt_profile": "SHA-256(ASCII(CLS/GOV01/STATIC-ACQUISITION-TOOLCHAIN-SET/v2) || NUL || UTF-8-NFC body); body is role-byte-sorted LF-terminated rows of exactly 6 TAB-separated columns: role,logical_id,artifact_kind,version,digest_profile,raw_digest_sha256",
        "toolchain_set_receipt_sha256": toolchain["toolchain_set_receipt_sha256"],
        "private_locator_policy": "resolve realpaths only in private preflight; require exact public digest before execution; never serialize locator in public artifacts",
        "recompute_before_first_non_ledger_acquisition_write": True,
        "drift_action": TOOLCHAIN_DRIFT_ACTION_V2,
    }
    schema_binding = pending_schema_binding_v2(schema_observation["sha256"])
    static_contract = template["static_acquisition_contract"]
    executor_artifact = artifact_by_role.get("static-executor")
    verifier_artifact = artifact_by_role.get("static-verifier")
    if not isinstance(executor_artifact, Mapping) or not isinstance(verifier_artifact, Mapping):
        fail(Exit.CONTRACT, "GENERATION_EXECUTOR_VERIFIER_ARTIFACT")
    static_contract.update(
        {
            "verifier_sha256": verifier_artifact["raw_file_sha256"],
            "executor_sha256": executor_artifact["raw_file_sha256"],
            "stage_repo_relative": ".gov01-toolchain-stage-" + approval_challenge_id,
            "expected": copy.deepcopy(expected_public),
        }
    )
    lock_closure = template["lock_closure"]
    lock_closure.update(copy.deepcopy(dict(lock_observation)))
    execution = template["execution_plan"]
    execution["attempt_policy"] = ATTEMPT_POLICY_V2
    execution["environment_mode"] = ENVIRONMENT_MODE_V2
    execution["git_child_sandbox_profile"] = GIT_CHILD_SANDBOX_PROFILE_V3
    execution["executor_argv_template"] = list(EXECUTOR_ARGV_TEMPLATE_V2)
    execution["executor_argv_template_sha256"] = sha256(
        EXECUTOR_ARGV_TEMPLATE_DOMAIN + b"\x00" + canonical_json(execution["executor_argv_template"])
    )
    execution["evidence_command_templates_sha256"] = sha256(
        EVIDENCE_COMMAND_TEMPLATES_DOMAIN + b"\x00" + canonical_json(execution["evidence_command_templates"])
    )
    private_authorization = template["private_state_authorization"]
    private_authorization.update(
        {
            "hmac_key_id": hmac_id,
            "authorized_locator_commitments": copy.deepcopy(locators),
            "private_control_identity_commitment": control_identity,
        }
    )
    failure_contract = template["failure_contract"]
    failure_contract.pop("retry_allowed", None)
    failure_contract.update(
        {
            "challenge_state": FAILURE_CHALLENGE_POLICY_V2,
            "preclaim_retry_allowed": True,
            "postclaim_retry_allowed": False,
            "new_authority_required": FAILURE_NEW_AUTHORITY_POLICY_V2,
        }
    )
    envelope = {
        "schema_version": "gov-01-toolchain-static-acquisition-envelope-v2",
        "artifact_type": "gov-01-toolchain-acquisition-envelope",
        "artifact_id": "GOV-01-STATIC-ACQUISITION-"
        + census_at_utc[:10].replace("-", "")
        + "-"
        + approval_challenge_id[-16:],
        "plan_id": "PLAN-CLS-PRODUCTIVITY-2026-08-20",
        "state": "pending-user-confirmation",
        "approval_challenge_id": approval_challenge_id,
        "single_use": True,
        "census_at_utc": census_at_utc,
        "not_after_utc": not_after_utc,
        "path_base": "git-repository-root-for-public-paths; private-paths-resolved-only-after-approval",
        "encoding_profile": "UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys",
        "receipt_digest_profile": "SHA-256(ASCII(CLS/GOV01-TOOLCHAIN-STATIC-ACQUISITION-RECEIPT/v2) || one NUL byte || raw-envelope-bytes); digest supplied by the user receipt and stored externally",
        "approval_receipt_contract": template["approval_receipt_contract"],
        "predecessor": predecessor,
        "generation_authorization": copy.deepcopy(dict(generation)),
        "artifacts": copy.deepcopy(artifacts),
        "artifact_path_uniqueness_policy": template["artifact_path_uniqueness_policy"],
        "authorization_preimage": authorization,
        "frozen_toolchain": frozen_toolchain,
        "schema_binding": schema_binding,
        "static_acquisition_contract": static_contract,
        "lock_closure": lock_closure,
        "execution_plan": execution,
        "mutation_scope": template["mutation_scope"],
        "failure_contract": failure_contract,
        "success_contract": template["success_contract"],
        "private_state_authorization": private_authorization,
        "privacy": template["privacy"],
    }
    validate_manual_envelope_contract(envelope, now=parse_utc(census_at_utc, "CENSUS_AT"))
    if has_forbidden_pending_envelope_value(envelope):
        fail(Exit.PRIVACY, "PENDING_BUILDER_PRIVACY")
    return copy.deepcopy(envelope)


def build_census(
    args: argparse.Namespace,
    strict: bool,
    recorder: Optional[GateRecorder] = None,
) -> Dict[str, Any]:
    if recorder is None:
        recorder = GateRecorder()
    require_python_isolation()
    require_host()
    envelope_relative = validate_public_runtime_boundaries_v2(args)
    if args.receipt_digest is None:
        fail(Exit.RECEIPT, "APPROVED_RECEIPT_REQUIRED")
    envelope, envelope_raw, receipt_digest = load_envelope(args.envelope, args.receipt_digest)
    challenge = envelope.get("approval_challenge_id")
    if args.approval_challenge != challenge:
        fail(Exit.RECEIPT, "APPROVAL_CHALLENGE_MISMATCH")
    validate_envelope_path_binding(args, envelope, envelope_relative)
    generation = envelope.get("generation_authorization")
    if (
        not isinstance(generation, Mapping)
        or generation.get("approval_challenge_id") != getattr(args, "generation_challenge", None)
    ):
        fail(Exit.RECEIPT, "GENERATION_CHALLENGE_MISMATCH")
    # The repository is the only locator inspected before G00.  It contains
    # the already receipt-bound public envelope and content-addressed public
    # contract artifacts.  State, cache and key locators remain untouched.
    repo_meta = require_owned_directory(args.repo_root, "REPO_ROOT")
    recorder.bind_run_authority(challenge, receipt_digest)
    stage_name = ".gov01-toolchain-stage-" + str(challenge)
    tree_exclusions = (stage_name, TARGET_NAME)
    exact_file_exclusions = (envelope_relative,)
    repo_fd = open_directory(args.repo_root, "REPO_ROOT")
    cache_fd: Optional[int] = None
    try:
        # Finish every public contract/source check before any state/cache/key
        # metadata or bytes are touched, verifier source is compiled, or child
        # process is started.
        recorder.begin("G00", "schema-contract")
        schema_observation = verify_bound_schema_artifact(repo_fd, envelope)
        validate_manual_envelope_contract(envelope)
        artifacts = verify_artifacts(repo_fd, envelope)
        verify_generation_authorization_artifact(repo_fd, envelope, artifacts)
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
        bind_private_runtime_args_v2(args, generation)
        state_meta = require_owned_directory(args.state_root, "STATE_ROOT", exact_mode=0o700)
        require_same_filesystem(repo_meta, state_meta)
        require_owned_directory(args.cache_root, "CACHE_ROOT")
        key = load_hmac_key(args.key_file)
        generation_claim = verify_generation_claim_recovery_v2(
            runtime_args=GenerationRuntimeArgsV2(
                args.repo_root,
                args.cache_root,
                args.state_root,
                args.key_file,
                args.envelope,
            ),
            generation_authorization=generation,
            final_envelope_raw=envelope_raw,
        )
        if not hmac.compare_digest(
            str(generation_claim["final_envelope_receipt_digest"]),
            receipt_digest,
        ):
            fail(Exit.RECEIPT, "GENERATION_CLAIM_RECEIPT_DRIFT")
        cache_fd = open_directory(args.cache_root, "CACHE_ROOT")
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
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
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
                "authorized_subprocess_role_count": len(AUTHORIZED_SUBPROCESS_ROLES),
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
        if cache_fd is not None:
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
    envelope_relative = validate_public_runtime_boundaries_v2(args)
    if args.receipt_digest is None:
        fail(Exit.RECEIPT, "APPROVED_RECEIPT_REQUIRED")
    envelope, envelope_raw, receipt_digest = load_envelope(args.envelope, args.receipt_digest)
    challenge = envelope.get("approval_challenge_id")
    if args.approval_challenge != challenge:
        fail(Exit.RECEIPT, "APPROVAL_CHALLENGE_MISMATCH")
    validate_envelope_path_binding(args, envelope, envelope_relative)
    generation = envelope.get("generation_authorization")
    if (
        not isinstance(generation, Mapping)
        or generation.get("approval_challenge_id") != getattr(args, "generation_challenge", None)
    ):
        fail(Exit.RECEIPT, "GENERATION_CHALLENGE_MISMATCH")
    # The repository is the only locator inspected before G00.  It contains
    # the already receipt-bound public envelope and content-addressed public
    # contract artifacts.  State, cache and key locators remain untouched.
    repo_meta = require_owned_directory(args.repo_root, "REPO_ROOT")
    preliminary_stage = ".gov01-toolchain-stage-" + str(challenge)
    validate_relative(preliminary_stage, "STATIC_STAGE")
    tree_exclusions = (preliminary_stage, TARGET_NAME)
    exact_file_exclusions = (envelope_relative,)

    repo_fd = open_directory(args.repo_root, "REPO_ROOT")
    cache_fd: Optional[int] = None
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
        # Finish every public contract/source check before any state/cache/key
        # metadata or bytes are touched, verifier source is compiled, or child
        # process is started.
        recorder.begin("G00", "schema-contract")
        schema_observation = verify_bound_schema_artifact(repo_fd, envelope)
        validate_manual_envelope_contract(envelope)
        baseline_artifacts = verify_artifacts(repo_fd, envelope)
        verify_generation_authorization_artifact(repo_fd, envelope, baseline_artifacts)
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
        bind_private_runtime_args_v2(args, generation)
        attempt.set_phase("private-public-boundary")
        state_meta = require_owned_directory(args.state_root, "STATE_ROOT", exact_mode=0o700)
        require_same_filesystem(repo_meta, state_meta)
        require_owned_directory(args.cache_root, "CACHE_ROOT")
        key = load_hmac_key(args.key_file)
        generation_claim = verify_generation_claim_recovery_v2(
            runtime_args=GenerationRuntimeArgsV2(
                args.repo_root,
                args.cache_root,
                args.state_root,
                args.key_file,
                args.envelope,
            ),
            generation_authorization=generation,
            final_envelope_raw=envelope_raw,
        )
        if not hmac.compare_digest(
            str(generation_claim["final_envelope_receipt_digest"]),
            receipt_digest,
        ):
            fail(Exit.RECEIPT, "GENERATION_CLAIM_RECEIPT_DRIFT")
        cache_fd = open_directory(args.cache_root, "CACHE_ROOT")
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
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
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
                "authorized_subprocess_role_count": len(AUTHORIZED_SUBPROCESS_ROLES),
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
                "first_authority_consuming_persistent_write_contract": "exclusive-0700-challenge-mkdir",
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
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
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
            authorized_tree_excludes=tree_exclusions,
            authorized_exact_file_excludes=exact_file_exclusions,
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
        if public_code.startswith("GIT_ADAPTER_CLEANUP_"):
            attempt.adapter_cleanup_uncertain()
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
        child.add_argument("--generation-challenge", required=True)
        child.add_argument("--receipt-digest", required=True)
        child.add_argument("--approval-challenge", required=True)
        if name == "acquire":
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
        bind_public_cli_runtime_args_v2(args)
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
