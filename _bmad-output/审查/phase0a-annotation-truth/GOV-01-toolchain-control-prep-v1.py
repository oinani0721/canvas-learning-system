#!/usr/bin/env python3
"""Receipt-gated GOV-01 control-state preparation.

This program has one deliberately small write surface.  After validating an
exact user receipt, challenge, expiry, envelope, schema, public artifacts and
its own executing bytes, it may create one challenge-named direct child of
/Users/Shared.
The child contains only claims/, hmac.key and a locator-free public receipt.

It never invokes subprocesses, imports networking modules, reads a Vault,
modifies the repository, creates an acquisition challenge claim, or removes a
partial result.  Run only with the frozen CPython interpreter and -I -S -B.
"""

from __future__ import print_function

import argparse
import ctypes
import datetime
import errno
import hashlib
import hmac
import json
import os
import stat
import struct
import sys
import unicodedata


PROFILE_VERSION = "gov-01-toolchain-control-prep-v1"
RECEIPT_DOMAIN = b"CLS/GOV01-TOOLCHAIN-CONTROL-PREP-RECEIPT/v1\0"
PREP_RECEIPT_DOMAIN = b"CLS/GOV01-TOOLCHAIN-CONTROL-PREP-EVIDENCE/v1\0"
CONSUMPTION_CLAIM_DOMAIN = b"CLS/GOV01-TOOLCHAIN-CONTROL-PREP-CONSUMPTION/v1\0"
SCHEMA_RELATIVE_PATH = (
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-control-prep-envelope-v1.schema.json"
)
EXECUTOR_RELATIVE_PATH = (
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-control-prep-v1.py"
)
ENVELOPE_RELATIVE_PATH = (
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-control-prep-envelope-v1.json"
)
GOAL_RELATIVE_PATH = (
    "_bmad-output/审查/2026-08-20-Canvas-Learning-System-"
    "生产力化长期Goal计划书.md"
)
GOV_RELATIVE_PATH = (
    "_bmad-output/审查/phase0a-annotation-truth/"
    "2026-08-20-GOV-01-追踪真相源修复决策稿.md"
)
FIRST_ENVELOPE_RELATIVE_PATH = (
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-first-receipt-envelope-v1.json"
)
TARGET_PARENT = "/Users/Shared"
TARGET_PREFIX = "cls-gov01-toolchain-control-"
CONSUMPTION_CLAIM_PREFIX = "cls-gov01-toolchain-control-consumed-"
CONSUMPTION_CLAIM_SUFFIX = ".claim"
CLAIMS_NAME = "claims"
KEY_NAME = "hmac.key"
PREP_RECEIPT_NAME = "control-prep-receipt.json"
EXPECTED_PYTHON_IMPLEMENTATION = "cpython"
EXPECTED_PYTHON_VERSION = "3.9.6"
EXPECTED_PYTHON_SHA256 = (
    "4b42b1a117605cafc8607b67b0892a609c2cd125012dd56288abeed8c89cdfb1"
)
EXPECTED_SYS_EXECUTABLE = "/Library/Developer/CommandLineTools/usr/bin/python3"
EXPECTED_SYS_EXECUTABLE_LINK_TEXT = "../../Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"
EXPECTED_SYS_EXECUTABLE_REALPATH = (
    "/Library/Developer/CommandLineTools/Library/Frameworks/"
    "Python3.framework/Versions/3.9/bin/python3.9"
)
EXPECTED_SYS_EXECUTABLE_REAL_MODE = 0o755
EXPECTED_EFFECTIVE_UID = 501
EXPECTED_EFFECTIVE_GID = 20
EXPECTED_CREATED_UID = 501
EXPECTED_CREATED_GID = 0
EXPECTED_PARENT_DEVICE = 16777234
EXPECTED_PARENT_INODE = 18434
EXPECTED_PARENT_UID = 0
EXPECTED_PARENT_GID = 0
EXPECTED_PARENT_MODE = 0o1777
PRIOR_FAILED_CHALLENGE = "GOV01-CP-20260820-58610ca0bebc0c442f606e0fe6d96541"
PRIOR_FAILED_ENVELOPE_SHA256 = "9eab068fa58a282c6ed980bf1830ccb6daec88d92cfe343d69fb33e13f7b83fb"
PRIOR_FAILED_RECEIPT_DOMAIN_SHA256 = "4b2be6681fc055d3e5e53573ee3955fe125e844466ff822a89036c36c785a7b0"
PRIOR_FAILED_CLAIM_NAME = CONSUMPTION_CLAIM_PREFIX + PRIOR_FAILED_CHALLENGE + CONSUMPTION_CLAIM_SUFFIX
PRIOR_FAILED_TARGET_NAME = TARGET_PREFIX + PRIOR_FAILED_CHALLENGE
PRIOR_FAILED_CLAIM_DEVICE = 16777234
PRIOR_FAILED_CLAIM_INODE = 19459895
PRIOR_FAILED_CLAIM_MODE = 0o600
PRIOR_FAILED_CLAIM_SIZE = 0
PRIOR_FAILED_CLAIM_NLINK = 1
PRIOR_FAILED_CLAIM_FLAGS = 0
PRIOR_FAILED_CLAIM_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
PROC_PIDTBSDINFO = 3
PROC_PIDVNODEPATHINFO = 9
PROC_UID_ONLY = 4
PROC_BSDINFO_SIZE = 136
CTL_KERN = 1
KERN_PROCARGS2 = 49
MAX_PROCESS_CENSUS_BYTES = 1024 * 1024


class PrepError(Exception):
    def __init__(self, code, reason):
        Exception.__init__(self, reason)
        self.code = code
        self.reason = reason


def fail(code, reason):
    raise PrepError(code, reason)


def reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(11, "duplicate-json-key")
        result[key] = value
    return result


def reject_float(_value):
    fail(11, "json-float-prohibited")


def load_json_bytes(raw, label):
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        fail(11, label + "-encoding-profile")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail(11, label + "-utf8")
    if unicodedata.normalize("NFC", text) != text:
        fail(11, label + "-non-nfc")
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_pairs,
            parse_float=reject_float,
            parse_constant=lambda _x: fail(11, "json-constant-prohibited"),
        )
    except PrepError:
        raise
    except Exception:
        fail(11, label + "-invalid-json")


def canonical_json_bytes(value):
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        fail(11, "canonical-json")
    text = unicodedata.normalize("NFC", text) + "\n"
    return text.encode("utf-8")


def sha256_hex(raw):
    return hashlib.sha256(raw).hexdigest()


def is_sha256(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)


def parse_utc(value, label):
    if not isinstance(value, str) or not value.endswith("Z"):
        fail(12, label + "-format")
    try:
        parsed = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        fail(12, label + "-format")
    return parsed.replace(tzinfo=datetime.timezone.utc)


def require_exact_keys(value, required, label):
    if not isinstance(value, dict) or set(value) != set(required):
        fail(13, label + "-keys")


def validate_component(value, label):
    if not isinstance(value, str) or not value or value in (".", ".."):
        fail(13, label + "-component")
    if "/" in value or "\0" in value or unicodedata.normalize("NFC", value) != value:
        fail(13, label + "-component")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        fail(13, label + "-component")
    return value


def validate_relative_path(value, label):
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        fail(13, label + "-path")
    if unicodedata.normalize("NFC", value) != value:
        fail(13, label + "-path")
    components = value.split("/")
    for component in components:
        validate_component(component, label)
    if components[0] == ".git" or ".git" in components:
        fail(13, label + "-git-path")
    return components


def open_flags(directory=False, write=False, readwrite=False, create=False):
    flags = os.O_RDONLY
    if readwrite:
        flags = os.O_RDWR
    elif write:
        flags = os.O_WRONLY
    if directory and hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if create:
        flags |= os.O_CREAT | os.O_EXCL
    return flags


def read_fd_all(fd, label):
    chunks = []
    while True:
        try:
            chunk = os.read(fd, 1024 * 1024)
        except OSError:
            fail(20, label + "-read")
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def read_absolute_regular_with_identity(path, label):
    try:
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode):
            fail(20, label + "-not-regular")
        fd = os.open(path, open_flags())
    except PrepError:
        raise
    except OSError:
        fail(20, label + "-open")
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            fail(20, label + "-race")
        return read_fd_all(fd, label), (opened.st_dev, opened.st_ino)
    finally:
        os.close(fd)


def read_absolute_regular(path, label):
    raw, _identity = read_absolute_regular_with_identity(path, label)
    return raw


def open_repo_root(repo_root):
    if not isinstance(repo_root, str) or not os.path.isabs(repo_root):
        fail(20, "repo-root-absolute")
    normalized = os.path.normpath(repo_root)
    if normalized != repo_root or os.path.realpath(repo_root) != repo_root:
        fail(20, "repo-root-canonical")
    try:
        info = os.lstat(repo_root)
        if not stat.S_ISDIR(info.st_mode):
            fail(20, "repo-root-not-directory")
        fd = os.open(repo_root, open_flags(directory=True))
    except PrepError:
        raise
    except OSError:
        fail(20, "repo-root-open")
    opened = os.fstat(fd)
    if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        fail(20, "repo-root-race")
    return fd


def read_repo_regular(repo_fd, relative_path, label):
    components = validate_relative_path(relative_path, label)
    current_fd = os.dup(repo_fd)
    try:
        for component in components[:-1]:
            try:
                next_fd = os.open(component, open_flags(directory=True), dir_fd=current_fd)
            except OSError:
                fail(20, label + "-ancestor")
            os.close(current_fd)
            current_fd = next_fd
        try:
            fd = os.open(components[-1], open_flags(), dir_fd=current_fd)
        except OSError:
            fail(20, label + "-open")
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                fail(20, label + "-not-regular")
            return read_fd_all(fd, label)
        finally:
            os.close(fd)
    finally:
        os.close(current_fd)


def artifact_map(envelope):
    artifacts = envelope.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 5:
        fail(13, "artifacts-count")
    result = {}
    paths = set()
    for entry in artifacts:
        require_exact_keys(entry, ["role", "path", "file_kind", "byte_length", "raw_file_sha256"], "artifact")
        role = entry["role"]
        if role in result or entry["file_kind"] != "regular":
            fail(13, "artifact-role")
        validate_relative_path(entry["path"], "artifact")
        if entry["path"] in paths:
            fail(13, "artifact-path-duplicate")
        paths.add(entry["path"])
        if not isinstance(entry["byte_length"], int) or entry["byte_length"] < 1:
            fail(13, "artifact-length")
        if not is_sha256(entry["raw_file_sha256"]):
            fail(13, "artifact-sha256")
        result[role] = entry
    required_roles = {
        "goal", "governance-decision", "first-receipt-predecessor",
        "control-prep-executor", "control-prep-envelope-schema",
    }
    if set(result) != required_roles:
        fail(13, "artifact-role-set")
    expected_paths = {
        "goal": GOAL_RELATIVE_PATH,
        "governance-decision": GOV_RELATIVE_PATH,
        "first-receipt-predecessor": FIRST_ENVELOPE_RELATIVE_PATH,
        "control-prep-executor": EXECUTOR_RELATIVE_PATH,
        "control-prep-envelope-schema": SCHEMA_RELATIVE_PATH,
    }
    for role, expected_path in expected_paths.items():
        if result[role]["path"] != expected_path:
            fail(13, "artifact-path-" + role)
    return result


def validate_artifact_bytes(repo_fd, artifacts):
    for role, entry in artifacts.items():
        raw = read_repo_regular(repo_fd, entry["path"], "artifact-" + role)
        if len(raw) != entry["byte_length"] or not hmac.compare_digest(
            sha256_hex(raw), entry["raw_file_sha256"]
        ):
            fail(16, "artifact-mismatch-" + role)


def validate_self_execution(repo_root, executor_entry, expected_identity=None):
    expected_path = repo_root + "/" + EXECUTOR_RELATIVE_PATH
    candidates = (("executor-file", __file__), ("executor-argv0", sys.argv[0]))
    for label, candidate in candidates:
        if not isinstance(candidate, str):
            fail(16, label + "-type")
        if os.path.abspath(candidate) != expected_path or os.path.realpath(candidate) != expected_path:
            fail(16, label + "-path")
    raw, identity = read_absolute_regular_with_identity(expected_path, "executing-executor")
    if len(raw) != executor_entry["byte_length"] or not hmac.compare_digest(
        sha256_hex(raw), executor_entry["raw_file_sha256"]
    ):
        fail(16, "executing-executor-mismatch")
    if expected_identity is not None and identity != expected_identity:
        fail(16, "executing-executor-identity-drift")
    return identity


def validate_runtime():
    flags = sys.flags
    if not (flags.isolated and flags.no_site and flags.dont_write_bytecode):
        fail(14, "python-flags")
    if sys.implementation.name != EXPECTED_PYTHON_IMPLEMENTATION:
        fail(14, "python-implementation")
    if sys.version.split()[0] != EXPECTED_PYTHON_VERSION:
        fail(14, "python-version")
    if os.geteuid() != EXPECTED_EFFECTIVE_UID or os.getegid() != EXPECTED_EFFECTIVE_GID:
        fail(14, "effective-owner")
    if sys.executable != EXPECTED_SYS_EXECUTABLE:
        fail(14, "python-executable-path")
    try:
        executable_link_info = os.lstat(sys.executable)
        if not stat.S_ISLNK(executable_link_info.st_mode):
            fail(14, "python-executable-not-symlink")
        if executable_link_info.st_uid != 0 or executable_link_info.st_gid != 0:
            fail(14, "python-executable-link-owner")
        if os.readlink(sys.executable) != EXPECTED_SYS_EXECUTABLE_LINK_TEXT:
            fail(14, "python-executable-link-text")
        if os.path.realpath(sys.executable) != EXPECTED_SYS_EXECUTABLE_REALPATH:
            fail(14, "python-executable-realpath")
        executable_real_info = os.lstat(EXPECTED_SYS_EXECUTABLE_REALPATH)
        if (
            not stat.S_ISREG(executable_real_info.st_mode)
            or stat.S_IMODE(executable_real_info.st_mode) != EXPECTED_SYS_EXECUTABLE_REAL_MODE
            or executable_real_info.st_uid != 0
            or executable_real_info.st_gid != 0
        ):
            fail(14, "python-executable-real-metadata")
    except PrepError:
        raise
    except OSError:
        fail(14, "python-executable-binding")
    executable_raw = read_absolute_regular(EXPECTED_SYS_EXECUTABLE_REALPATH, "python-executable-real")
    if not hmac.compare_digest(sha256_hex(executable_raw), EXPECTED_PYTHON_SHA256):
        fail(14, "python-binary")


def require_same_uid_process_gone(pid, label):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        fail(14, label)
    fail(14, label)


def parse_macos_procargs(raw):
    if len(raw) < 5:
        fail(14, "process-census-args-format")
    argc = struct.unpack_from("=i", raw, 0)[0]
    if argc <= 0 or argc > 4096:
        fail(14, "process-census-argc")
    cursor = 4
    executable_end = raw.find(b"\0", cursor)
    if executable_end < cursor:
        fail(14, "process-census-executable")
    executable = raw[cursor:executable_end]
    cursor = executable_end + 1
    while cursor < len(raw) and raw[cursor] == 0:
        cursor += 1
    arguments = []
    while len(arguments) < argc:
        if cursor >= len(raw):
            fail(14, "process-census-argv-count")
        argument_end = raw.find(b"\0", cursor)
        if argument_end < cursor:
            fail(14, "process-census-argv-termination")
        arguments.append(raw[cursor:argument_end])
        cursor = argument_end + 1
    return executable, arguments


def is_claude_launcher_token(token):
    lowered = token.lower()
    for component in lowered.split(b"/"):
        if component == b"claude" or component.startswith(b"claude-"):
            return True
    return False


def target_worktree_claude_session_count(repo_root):
    if sys.platform != "darwin":
        fail(14, "process-census-platform")
    try:
        libsystem = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        libsystem.proc_listpids.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        libsystem.proc_listpids.restype = ctypes.c_int
        libsystem.proc_pidinfo.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        libsystem.proc_pidinfo.restype = ctypes.c_int
        libsystem.sysctl.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        libsystem.sysctl.restype = ctypes.c_int
    except Exception:
        fail(14, "process-census-api")

    requested_bytes = libsystem.proc_listpids(
        PROC_UID_ONLY,
        EXPECTED_EFFECTIVE_UID,
        None,
        0,
    )
    if requested_bytes <= 0 or requested_bytes > 4 * 1024 * 1024:
        fail(14, "process-census-size")
    pid_capacity = max(1, (requested_bytes * 2 + ctypes.sizeof(ctypes.c_int) - 1) // ctypes.sizeof(ctypes.c_int))
    pids = (ctypes.c_int * pid_capacity)()
    returned_bytes = libsystem.proc_listpids(
        PROC_UID_ONLY,
        EXPECTED_EFFECTIVE_UID,
        pids,
        ctypes.sizeof(pids),
    )
    if (
        returned_bytes <= 0
        or returned_bytes >= ctypes.sizeof(pids)
        or returned_bytes % ctypes.sizeof(ctypes.c_int) != 0
    ):
        fail(14, "process-census-list")
    returned = returned_bytes // ctypes.sizeof(ctypes.c_int)

    repo_bytes = repo_root.encode("utf-8")
    active = 0
    for pid in pids[:returned]:
        if pid <= 0 or pid == os.getpid():
            continue

        bsd_buffer = ctypes.create_string_buffer(PROC_BSDINFO_SIZE)
        bsd_length = libsystem.proc_pidinfo(
            pid,
            PROC_PIDTBSDINFO,
            0,
            bsd_buffer,
            len(bsd_buffer),
        )
        if bsd_length != PROC_BSDINFO_SIZE:
            if require_same_uid_process_gone(pid, "process-census-bsdinfo"):
                continue
        bsd_raw = bsd_buffer.raw[:bsd_length]
        reported_pid = struct.unpack_from("=I", bsd_raw, 12)[0]
        effective_uid = struct.unpack_from("=I", bsd_raw, 20)[0]
        real_uid = struct.unpack_from("=I", bsd_raw, 28)[0]
        if reported_pid != pid:
            fail(14, "process-census-pid-identity")
        if EXPECTED_EFFECTIVE_UID not in (effective_uid, real_uid):
            fail(14, "process-census-uid-filter")
        bsd_command = bsd_raw[48:64].rstrip(b"\0")
        bsd_name = bsd_raw[64:96].rstrip(b"\0")
        start_tvsec = struct.unpack_from("=Q", bsd_raw, 120)[0]
        start_tvusec = struct.unpack_from("=Q", bsd_raw, 128)[0]
        process_generation = (
            reported_pid,
            effective_uid,
            real_uid,
            start_tvsec,
            start_tvusec,
            bsd_command,
            bsd_name,
        )

        vnode_buffer = ctypes.create_string_buffer(4096)
        vnode_length = libsystem.proc_pidinfo(
            pid,
            PROC_PIDVNODEPATHINFO,
            0,
            vnode_buffer,
            len(vnode_buffer),
        )
        if vnode_length <= 0:
            if require_same_uid_process_gone(pid, "process-census-vnode"):
                continue
        associated = repo_bytes in vnode_buffer.raw[:vnode_length]

        mib = (ctypes.c_int * 3)(CTL_KERN, KERN_PROCARGS2, pid)
        args_size = ctypes.c_size_t(0)
        if libsystem.sysctl(mib, 3, None, ctypes.byref(args_size), None, 0) != 0:
            if require_same_uid_process_gone(pid, "process-census-args-size"):
                continue
        if args_size.value <= 0 or args_size.value > MAX_PROCESS_CENSUS_BYTES:
            fail(14, "process-census-args-limit")
        args_buffer = ctypes.create_string_buffer(args_size.value)
        if libsystem.sysctl(mib, 3, args_buffer, ctypes.byref(args_size), None, 0) != 0:
            if require_same_uid_process_gone(pid, "process-census-args"):
                continue
        executable, arguments = parse_macos_procargs(
            args_buffer.raw[:args_size.value]
        )

        # Bind vnode/argv evidence to the same process generation.  A PID may
        # exit and be reused between proc_listpids(), proc_pidinfo(), and
        # sysctl(KERN_PROCARGS2); mixing those generations could hide Claude.
        bsd_after_buffer = ctypes.create_string_buffer(PROC_BSDINFO_SIZE)
        bsd_after_length = libsystem.proc_pidinfo(
            pid,
            PROC_PIDTBSDINFO,
            0,
            bsd_after_buffer,
            len(bsd_after_buffer),
        )
        if bsd_after_length != PROC_BSDINFO_SIZE:
            if require_same_uid_process_gone(pid, "process-census-bsdinfo-after"):
                continue
        bsd_after = bsd_after_buffer.raw[:bsd_after_length]
        process_generation_after = (
            struct.unpack_from("=I", bsd_after, 12)[0],
            struct.unpack_from("=I", bsd_after, 20)[0],
            struct.unpack_from("=I", bsd_after, 28)[0],
            struct.unpack_from("=Q", bsd_after, 120)[0],
            struct.unpack_from("=Q", bsd_after, 128)[0],
            bsd_after[48:64].rstrip(b"\0"),
            bsd_after[64:96].rstrip(b"\0"),
        )
        if process_generation_after != process_generation:
            fail(14, "process-census-generation-drift")

        if any(repo_bytes in argument for argument in arguments):
            associated = True
        launcher_tokens = [bsd_command, bsd_name, executable] + arguments[:4]
        is_claude = any(is_claude_launcher_token(token) for token in launcher_tokens)
        if associated and is_claude:
            active += 1
    return active


def validate_envelope(repo_root, repo_fd, envelope_raw, receipt_digest, approval_challenge, now):
    calculated_receipt = sha256_hex(RECEIPT_DOMAIN + envelope_raw)
    if not is_sha256(receipt_digest) or not hmac.compare_digest(calculated_receipt, receipt_digest):
        fail(15, "receipt-digest")
    envelope = load_json_bytes(envelope_raw, "envelope")
    top_keys = [
        "schema_version", "artifact_type", "artifact_id", "plan_id", "state",
        "approval_challenge_id", "single_use", "census_at_utc", "not_after_utc",
        "encoding_profile", "receipt_digest_profile", "predecessor", "artifacts",
        "schema_binding", "runtime_contract", "target", "action_sequence",
        "authorization_scope", "failure_contract", "success_contract", "privacy",
    ]
    require_exact_keys(envelope, top_keys, "envelope")
    expected_scalars = {
        "schema_version": "gov-01-toolchain-control-prep-envelope-v1",
        "artifact_type": "gov-01-toolchain-control-prep-envelope",
        "artifact_id": "GOV-01-TOOLCHAIN-CONTROL-PREP-2026-08-20-08",
        "plan_id": "PLAN-CLS-PRODUCTIVITY-2026-08-20",
        "state": "pending-user-confirmation",
        "single_use": True,
        "encoding_profile": "UTF-8-NFC-LF-no-BOM-no-duplicate-json-keys",
        "receipt_digest_profile": "SHA-256(ASCII(CLS/GOV01-TOOLCHAIN-CONTROL-PREP-RECEIPT/v1) || one NUL byte || raw-envelope-bytes); digest supplied by user and stored externally",
    }
    for key, expected in expected_scalars.items():
        if envelope.get(key) != expected:
            fail(13, "envelope-" + key)

    predecessor = envelope["predecessor"]
    expected_predecessor = {
        "first_envelope_raw_sha256": "0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410",
        "first_receipt_domain_sha256": "c89e7195e67b60a26117469e2b212fb508c0a5a64cac5d25a59a257f73b55740",
        "bootstrap_patch_raw_sha256": "d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa",
        "bootstrap_containment_state": "independently-verified-pass",
        "prior_execution_ceiling": "control-prep-attempt-consumed-stop-before-target-create",
        "failed_control_prep_attempt": {
            "prior_envelope_raw_sha256": PRIOR_FAILED_ENVELOPE_SHA256,
            "prior_receipt_domain_sha256": PRIOR_FAILED_RECEIPT_DOMAIN_SHA256,
            "approval_challenge_id": PRIOR_FAILED_CHALLENGE,
            "terminal_state": "ATTEMPT-CONSUMED-STOP",
            "observed_stop_reason": "durable-claim-owner",
            "durable_claim": {
                "absolute_path": TARGET_PARENT + "/" + PRIOR_FAILED_CLAIM_NAME,
                "object_kind": "regular",
                "device": PRIOR_FAILED_CLAIM_DEVICE,
                "inode": PRIOR_FAILED_CLAIM_INODE,
                "uid": EXPECTED_CREATED_UID,
                "gid": EXPECTED_CREATED_GID,
                "mode": "0600",
                "byte_length": PRIOR_FAILED_CLAIM_SIZE,
                "link_count": PRIOR_FAILED_CLAIM_NLINK,
                "flags": PRIOR_FAILED_CLAIM_FLAGS,
                "raw_file_sha256": PRIOR_FAILED_CLAIM_SHA256,
            },
            "target": {
                "absolute_path": TARGET_PARENT + "/" + PRIOR_FAILED_TARGET_NAME,
                "state": "ABSENT",
            },
            "retention_contract": "the prior empty durable claim is terminal failure evidence; it must remain path-to-inode and metadata exact; deletion mutation cleanup or challenge reuse is evidence tampering and never authorized",
        },
    }
    if predecessor != expected_predecessor:
        fail(13, "predecessor")
    challenge = validate_component(envelope["approval_challenge_id"], "challenge")
    challenge_prefix = "GOV01-CP-20260820-"
    challenge_suffix = challenge[len(challenge_prefix):]
    if (
        not challenge.startswith(challenge_prefix)
        or len(challenge) != 50
        or len(challenge_suffix) != 32
        or any(character not in "0123456789abcdef" for character in challenge_suffix)
    ):
        fail(13, "challenge-shape")
    if hmac.compare_digest(challenge, PRIOR_FAILED_CHALLENGE):
        fail(13, "challenge-reuses-prior-consumed-attempt")
    if not hmac.compare_digest(challenge, approval_challenge):
        fail(15, "approval-challenge")
    census_at = parse_utc(envelope["census_at_utc"], "census-at")
    not_after = parse_utc(envelope["not_after_utc"], "not-after")
    if not census_at <= now < not_after:
        fail(15, "approval-expired")

    artifacts = artifact_map(envelope)
    validate_artifact_bytes(repo_fd, artifacts)
    if artifacts["control-prep-executor"]["path"] != EXECUTOR_RELATIVE_PATH:
        fail(16, "executor-path")
    if artifacts["control-prep-envelope-schema"]["path"] != SCHEMA_RELATIVE_PATH:
        fail(16, "schema-path")
    self_identity = validate_self_execution(
        repo_root,
        artifacts["control-prep-executor"],
    )

    binding = envelope["schema_binding"]
    require_exact_keys(binding, ["schema_id", "path", "raw_file_sha256", "external_validation_required"], "schema-binding")
    schema_entry = artifacts["control-prep-envelope-schema"]
    if binding != {
        "schema_id": "urn:canvas-learning-system:gov-01:toolchain-control-prep-envelope:v1",
        "path": SCHEMA_RELATIVE_PATH,
        "raw_file_sha256": schema_entry["raw_file_sha256"],
        "external_validation_required": True,
    }:
        fail(16, "schema-binding")

    runtime = envelope["runtime_contract"]
    expected_runtime = {
        "implementation": EXPECTED_PYTHON_IMPLEMENTATION,
        "version": EXPECTED_PYTHON_VERSION,
        "binary_sha256": EXPECTED_PYTHON_SHA256,
        "effective_executable_path": EXPECTED_SYS_EXECUTABLE,
        "effective_executable_link_text": EXPECTED_SYS_EXECUTABLE_LINK_TEXT,
        "effective_executable_realpath": EXPECTED_SYS_EXECUTABLE_REALPATH,
        "effective_executable_realpath_mode": "0755",
        "effective_executable_owner": {"uid": 0, "gid": 0},
        "required_flags": ["-I", "-S", "-B"],
        "stdlib_only": True,
        "effective_uid": EXPECTED_EFFECTIVE_UID,
        "effective_gid": EXPECTED_EFFECTIVE_GID,
        "executing_source_binding": "__file__ and argv[0] resolve to the exact approved repo artifact; raw bytes and inode are rechecked immediately before first write",
        "target_worktree_claude_session_census": "stdlib ctypes libSystem proc_listpids(PROC_UID_ONLY=current euid) proc_pidinfo(PROC_PIDTBSDINFO and PROC_PIDVNODEPATHINFO) and sysctl(KERN_PROCARGS2); every UID-filtered process is inspected before native Node or Bun Claude classification; PID start-time UID and BSD command/name generation is re-read after vnode/argv and must match; disappeared PID is skipped only after kill(0) confirms ESRCH; no subprocess; immediately before first write; uninspectable live same-UID process associated Claude process or generation drift stops",
        "required_active_target_worktree_claude_session_count": 0,
        "key_generator": "exactly one os.urandom(32) call after exclusive hmac.key creation; no fallback or caller-supplied entropy",
        "shell_allowed": False,
        "subprocess_allowed": False,
        "network_allowed": False,
    }
    if runtime != expected_runtime:
        fail(13, "runtime-contract")

    target_name = TARGET_PREFIX + challenge
    claim_name = CONSUMPTION_CLAIM_PREFIX + challenge + CONSUMPTION_CLAIM_SUFFIX
    expected_target = {
        "parent": TARGET_PARENT,
        "parent_identity": {
            "object_kind": "directory",
            "realpath": TARGET_PARENT,
            "device": EXPECTED_PARENT_DEVICE,
            "inode": EXPECTED_PARENT_INODE,
            "uid": EXPECTED_PARENT_UID,
            "gid": EXPECTED_PARENT_GID,
            "mode": "1777",
        },
        "direct_child_name": target_name,
        "absolute_path": TARGET_PARENT + "/" + target_name,
        "preimage": "ABSENT",
        "durable_claim_direct_child_name": claim_name,
        "durable_claim_absolute_path": TARGET_PARENT + "/" + claim_name,
        "durable_claim_preimage": "ABSENT",
        "durable_claim_mode": "0600",
        "root_mode": "0700",
        "claims_mode": "0700",
        "key_mode": "0600",
        "receipt_mode": "0600",
        "expected_created_owner": {
            "uid": EXPECTED_CREATED_UID,
            "gid": EXPECTED_CREATED_GID,
            "scope": "new durable claim target root and every descendant",
        },
        "durability_contract": "a separate durable sibling claim is the single-use record; target deletion cannot enable replay; executor never deletes either object; claim deletion is evidence tampering and never authorizes challenge reuse",
    }
    if envelope["target"] != expected_target:
        fail(13, "target-contract")
    expected_actions = [
        "read-only revalidate exact envelope artifact closure executing source identity pinned /Users/Shared parent retained prior failed-claim evidence and zero target-worktree Claude sessions",
        "recheck UTC expiry immediately before the first authorized write",
        "create exact durable consumption claim sibling mode 0600 owner uid501 gid0 with O_CREAT|O_EXCL|O_NOFOLLOW and fsync it and /Users/Shared; EEXIST is terminal",
        "mkdir exact target direct child under /Users/Shared mode 0700 owner uid501 gid0 with dir_fd and fail on EEXIST after consumption",
        "mkdir exact claims direct child mode 0700 owner uid501 gid0 with dir_fd and fail on EEXIST",
        "create exact hmac.key mode 0600 owner uid501 gid0 with O_CREAT|O_EXCL|O_NOFOLLOW then call os.urandom(32) exactly once and write exactly 32 bytes",
        "create exact locator-free non-authoritative control-prep evidence candidate mode 0600 owner uid501 gid0 with O_CREAT|O_EXCL|O_NOFOLLOW",
        "fsync each created file and directory and the /Users/Shared parent after its direct child creation",
        "recheck pinned parent and exact root claims key receipt FD-to-path inode owner group mode bytes lengths and child sets before CONTROL-PREPARED stdout",
    ]
    if envelope["action_sequence"] != expected_actions:
        fail(13, "action-sequence")

    scope = envelope["authorization_scope"]
    required_prohibited = {
        "private preimage sidecar creation", "acquisition challenge claim creation",
        "stage or node_modules creation", "repository or Git mutation", "subprocess execution",
        "network access", "Node npm npx or OpenSpec execution", "Vault read or enumeration",
        "Graphiti access", "cleanup deletion overwrite retry or repair",
    }
    expected_scope = {
        "first_authorized_write": "exclusive openat of the exact durable 0600 consumption claim sibling under identity-pinned /Users/Shared; O_CREAT O_EXCL O_NOFOLLOW; EEXIST is terminal consumed-replay-or-tampering",
        "allowed_created_objects": [
            expected_target["durable_claim_absolute_path"],
            expected_target["absolute_path"],
            expected_target["absolute_path"] + "/claims",
            expected_target["absolute_path"] + "/hmac.key",
            expected_target["absolute_path"] + "/control-prep-receipt.json",
        ],
        "maximum_state": "CONTROL-PREPARED",
        "single_use_semantics": "read-only preflight may rerun before expiry while both claim and target are absent; successful exclusive claim creation consumes the challenge permanently; target deletion cannot enable replay; claim EEXIST or observed deletion is terminal and the challenge is never reused",
        "host_sandbox_write_gate": "separate user-approved host sandbox escalation is required for the exact /Users/Shared claim and target siblings; envelope approval does not bypass the host sandbox",
        "expiry_semantics": "UTC expiry must pass on envelope load and again immediately before the first authorized write; after durable consumption the same attempt may finish but never restart",
        "same_uid_threat_boundary": "the current macOS user is inside the trusted computing base; active malicious same-UID filesystem or process tampering is not an OS-isolation guarantee; every detected drift stops",
        "repository_write_count": 0,
        "prohibited_actions": envelope["authorization_scope"].get("prohibited_actions"),
    }
    if scope != expected_scope:
        fail(13, "authorization-scope")
    prohibited = scope["prohibited_actions"]
    if not isinstance(prohibited, list) or set(prohibited) != required_prohibited:
        fail(13, "prohibited-actions")

    expected_failure = {
        "pre_claim_failure": "STOP with zero write; the same exact read-only preflight may rerun only before expiry while both claim and target remain absent",
        "claim_eexist": "STOP as terminal consumed-replay-or-tampering; perform no target write or mutation",
        "post_claim_failure": "STOP and retain the durable claim plus any exact partial target and children; any receipt candidate is non-authoritative and never independently claims CONTROL-PREPARED",
        "target_eexist_after_claim": "STOP with durable claim retained and no target child write or mutation",
        "prior_failed_attempt_retention": "the prior challenge is permanently consumed; its exact empty durable claim must remain as predecessor failure evidence and its absent target must remain absent; deletion mutation cleanup retry or challenge reuse is never authorized",
        "cleanup_authorized": False,
        "retry_policy": "after claim creation the challenge is permanently consumed; target deletion cannot permit reuse; claim deletion is evidence tampering; any new write attempt requires a new envelope challenge and user approval",
    }
    if envelope["failure_contract"] != expected_failure:
        fail(13, "failure-contract")
    expected_success = {
        "maximum_state": "CONTROL-PREPARED",
        "created_object_count": 5,
        "stdout_projection": {"state": "CONTROL-PREPARED"},
        "secret_or_locator_stdout_count": 0,
        "success_evidence_rule": "CONTROL-PREPARED is emitted only after retained predecessor failure evidence and final FD-to-path inode metadata content child-set and fsync checks; on-disk receipt remains a non-authoritative candidate requiring full-tree verification",
        "threat_model_ceiling": "personal local tool only; parent sticky root-owned identity and all observable path inode metadata content and session drift are fail-closed, but no claim of isolation from an actively malicious process running as the same macOS user",
        "next_required_authorization": "new toolchain-acquisition envelope binding this control-preparation predecessor and a fresh acquisition challenge",
    }
    if envelope["success_contract"] != expected_success:
        fail(13, "success-contract")
    expected_privacy = {
        "key_publication_allowed": False,
        "locator_stdout_allowed": False,
        "prep_receipt_locator_free": True,
        "private_preimage_capture_allowed": False,
        "public_generic_target_locator_allowed": True,
        "repository_write_count": 0,
        "vault_read_count": 0,
        "graphiti_call_count": 0,
        "network_call_count": 0,
    }
    if envelope["privacy"] != expected_privacy:
        fail(13, "privacy-contract")
    return envelope, target_name, claim_name, calculated_receipt, artifacts, self_identity, census_at, not_after


def check_absent_at(parent_fd, name, label):
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        if error.errno == errno.ENOENT:
            return
        fail(21, label + "-preimage-check")
    fail(21, label + "-exists-consumed-replay-or-tampering")


def verify_prior_failure_evidence(parent_fd):
    claim_fd = None
    try:
        path_info = os.stat(
            PRIOR_FAILED_CLAIM_NAME,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        claim_fd = os.open(
            PRIOR_FAILED_CLAIM_NAME,
            open_flags(),
            dir_fd=parent_fd,
        )
        opened = os.fstat(claim_fd)
        expected_identity = (
            PRIOR_FAILED_CLAIM_DEVICE,
            PRIOR_FAILED_CLAIM_INODE,
        )
        for info in (path_info, opened):
            if not stat.S_ISREG(info.st_mode):
                fail(21, "prior-failure-claim-kind")
            if object_identity(info) != expected_identity:
                fail(21, "prior-failure-claim-identity")
            if stat.S_IMODE(info.st_mode) != PRIOR_FAILED_CLAIM_MODE:
                fail(21, "prior-failure-claim-mode")
            if info.st_uid != EXPECTED_CREATED_UID or info.st_gid != EXPECTED_CREATED_GID:
                fail(21, "prior-failure-claim-owner")
            if (
                info.st_size != PRIOR_FAILED_CLAIM_SIZE
                or info.st_nlink != PRIOR_FAILED_CLAIM_NLINK
                or getattr(info, "st_flags", 0) != PRIOR_FAILED_CLAIM_FLAGS
            ):
                fail(21, "prior-failure-claim-metadata")
        if object_identity(path_info) != object_identity(opened):
            fail(21, "prior-failure-claim-path-identity")
        raw = read_fd_all(claim_fd, "prior-failure-claim")
        if (
            raw != b""
            or not hmac.compare_digest(
                sha256_hex(raw),
                PRIOR_FAILED_CLAIM_SHA256,
            )
        ):
            fail(21, "prior-failure-claim-content")
    except PrepError:
        raise
    except OSError:
        fail(21, "prior-failure-claim-open")
    finally:
        if claim_fd is not None:
            os.close(claim_fd)
    check_absent_at(parent_fd, PRIOR_FAILED_TARGET_NAME, "prior-failure-target")


def object_identity(info):
    return info.st_dev, info.st_ino


def verify_parent_directory(fd, path_info):
    opened = os.fstat(fd)
    expected_identity = (EXPECTED_PARENT_DEVICE, EXPECTED_PARENT_INODE)
    for info in (path_info, opened):
        if not stat.S_ISDIR(info.st_mode):
            fail(21, "target-parent-not-directory")
        if stat.S_IMODE(info.st_mode) != EXPECTED_PARENT_MODE:
            fail(21, "target-parent-mode")
        if info.st_uid != EXPECTED_PARENT_UID or info.st_gid != EXPECTED_PARENT_GID:
            fail(21, "target-parent-owner")
        if object_identity(info) != expected_identity:
            fail(21, "target-parent-identity")
        if getattr(info, "st_flags", 0) != 0:
            fail(21, "target-parent-flags")
    if object_identity(path_info) != object_identity(opened):
        fail(21, "target-parent-race")


def verify_parent_path(fd):
    try:
        path_info = os.lstat(TARGET_PARENT)
    except OSError:
        fail(21, "target-parent-final-lstat")
    verify_parent_directory(fd, path_info)


def verify_created_directory(fd, expected_mode, label):
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != expected_mode:
        fail(22, label + "-mode")
    if info.st_uid != EXPECTED_CREATED_UID or info.st_gid != EXPECTED_CREATED_GID:
        fail(22, label + "-owner")
    if getattr(info, "st_flags", 0) != 0:
        fail(22, label + "-flags")
    return object_identity(info)


def verify_created_file(fd, expected_mode, label):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != expected_mode:
        fail(23, label + "-mode")
    if info.st_uid != EXPECTED_CREATED_UID or info.st_gid != EXPECTED_CREATED_GID:
        fail(23, label + "-owner")
    if getattr(info, "st_flags", 0) != 0 or info.st_nlink != 1:
        fail(23, label + "-metadata")
    return object_identity(info)


def verify_path_matches_fd(parent_fd, name, fd, expected_kind, expected_mode, label):
    try:
        path_info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        opened = os.fstat(fd)
    except OSError:
        fail(25, label + "-final-stat")
    if object_identity(path_info) != object_identity(opened):
        fail(25, label + "-path-identity")
    if expected_kind == "directory":
        verify_created_directory(fd, expected_mode, label)
        if not stat.S_ISDIR(path_info.st_mode):
            fail(25, label + "-path-kind")
    elif expected_kind == "regular":
        verify_created_file(fd, expected_mode, label)
        if not stat.S_ISREG(path_info.st_mode):
            fail(25, label + "-path-kind")
    else:
        fail(25, label + "-expected-kind")


def verify_directory_final(parent_fd, name, fd, expected_mode, expected_names, label):
    verify_path_matches_fd(parent_fd, name, fd, "directory", expected_mode, label)
    try:
        actual_names = set(os.listdir(fd))
    except OSError:
        fail(25, label + "-list")
    if actual_names != set(expected_names):
        fail(25, label + "-children")


def verify_file_final(parent_fd, name, fd, expected_mode, expected_raw, label):
    verify_path_matches_fd(parent_fd, name, fd, "regular", expected_mode, label)
    info = os.fstat(fd)
    if info.st_size != len(expected_raw):
        fail(25, label + "-length")
    try:
        os.lseek(fd, 0, os.SEEK_SET)
    except OSError:
        fail(25, label + "-seek")
    actual_raw = read_fd_all(fd, label + "-final")
    if not hmac.compare_digest(actual_raw, expected_raw):
        fail(25, label + "-content")


def write_all(fd, raw, label):
    offset = 0
    while offset < len(raw):
        try:
            written = os.write(fd, raw[offset:])
        except OSError:
            fail(23, label + "-write")
        if written <= 0:
            fail(23, label + "-short-write")
        offset += written


def create_exclusive_file(parent_fd, name, mode, raw, label, eexist_reason=None):
    fd = None
    try:
        fd = os.open(name, open_flags(readwrite=True, create=True), mode, dir_fd=parent_fd)
    except OSError as error:
        if error.errno == errno.EEXIST and eexist_reason is not None:
            fail(24, eexist_reason)
        fail(23, label + "-create")
    try:
        os.fchmod(fd, mode)
        verify_created_file(fd, mode, label)
        write_all(fd, raw, label)
        os.fsync(fd)
        return fd
    except PrepError:
        os.close(fd)
        raise
    except OSError:
        os.close(fd)
        fail(23, label + "-fsync")


def execute_prepare(
    repo_root,
    repo_fd,
    envelope,
    envelope_raw,
    artifacts,
    self_identity,
    target_name,
    claim_name,
    challenge,
    approved_receipt_digest,
    envelope_raw_sha256,
    census_at,
    not_after,
):
    previous_umask = os.umask(0o077)
    parent_fd = None
    root_fd = None
    claims_fd = None
    claim_fd = None
    key_fd = None
    receipt_fd = None
    root_created = False
    claim_created = False
    try:
        if os.path.realpath(TARGET_PARENT) != TARGET_PARENT:
            fail(21, "target-parent-canonical")
        parent_info = os.lstat(TARGET_PARENT)
        parent_fd = os.open(TARGET_PARENT, open_flags(directory=True))
    except PrepError:
        os.umask(previous_umask)
        raise
    except OSError:
        os.umask(previous_umask)
        fail(21, "target-parent-open")
    try:
        verify_parent_directory(parent_fd, parent_info)
        verify_prior_failure_evidence(parent_fd)
        check_absent_at(parent_fd, claim_name, "durable-claim")
        check_absent_at(parent_fd, target_name, "target")

        # Recompute every approved byte and the executing source identity while
        # all actions are still read-only.
        current_envelope_raw = read_repo_regular(repo_fd, ENVELOPE_RELATIVE_PATH, "envelope-prewrite")
        if not hmac.compare_digest(current_envelope_raw, envelope_raw):
            fail(16, "envelope-prewrite-drift")
        validate_artifact_bytes(repo_fd, artifacts)
        validate_self_execution(
            repo_root,
            artifacts["control-prep-executor"],
            expected_identity=self_identity,
        )
        verify_parent_path(parent_fd)
        if target_worktree_claude_session_count(repo_root) != 0:
            fail(14, "active-target-worktree-claude-session")
        verify_prior_failure_evidence(parent_fd)
        check_absent_at(parent_fd, claim_name, "durable-claim")
        check_absent_at(parent_fd, target_name, "target")

        claim_body = {
            "schema_version": "gov-01-toolchain-control-prep-consumption-v1",
            "state": "ATTEMPT-CONSUMED",
            "approval_challenge_id": challenge,
            "approved_receipt_digest": approved_receipt_digest,
            "envelope_raw_sha256": envelope_raw_sha256,
            "target_direct_child_name": target_name,
            "expected_created_owner": {
                "uid": EXPECTED_CREATED_UID,
                "gid": EXPECTED_CREATED_GID,
            },
            "deletion_policy": "deletion-is-evidence-tampering-and-never-authorizes-challenge-reuse",
        }
        claim_core = canonical_json_bytes(claim_body)
        claim_evidence = dict(claim_body)
        claim_evidence["evidence_sha256"] = sha256_hex(CONSUMPTION_CLAIM_DOMAIN + claim_core)
        claim_raw = canonical_json_bytes(claim_evidence)

        # Expiry is re-evaluated immediately before the first authorized write.
        write_now = datetime.datetime.now(datetime.timezone.utc)
        if not census_at <= write_now < not_after:
            fail(15, "approval-expired-prewrite")

        # FIRST AND ONLY INITIAL WRITE: an atomic durable sibling claim.
        claim_fd = create_exclusive_file(
            parent_fd,
            claim_name,
            0o600,
            claim_raw,
            "durable-claim",
            eexist_reason="durable-claim-exists-consumed-replay-or-tampering",
        )
        claim_created = True
        os.fsync(parent_fd)
        verify_file_final(parent_fd, claim_name, claim_fd, 0o600, claim_raw, "durable-claim")
        verify_prior_failure_evidence(parent_fd)

        # The challenge is now consumed.  All later failures retain the claim.
        check_absent_at(parent_fd, target_name, "target-after-claim")
        try:
            os.mkdir(target_name, 0o700, dir_fd=parent_fd)
            root_created = True
            root_path_info = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False)
            root_fd = os.open(target_name, open_flags(directory=True), dir_fd=parent_fd)
        except OSError as error:
            if error.errno == errno.EEXIST:
                fail(24, "target-exists-consumed-replay-or-tampering")
            fail(24, "target-root-create")
        try:
            os.fchmod(root_fd, 0o700)
        except OSError:
            fail(24, "target-root-chmod")
        if object_identity(root_path_info) != object_identity(os.fstat(root_fd)):
            fail(24, "target-root-open-race")
        verify_created_directory(root_fd, 0o700, "target-root")
        os.fsync(parent_fd)

        try:
            os.mkdir(CLAIMS_NAME, 0o700, dir_fd=root_fd)
            claims_path_info = os.stat(CLAIMS_NAME, dir_fd=root_fd, follow_symlinks=False)
            claims_fd = os.open(CLAIMS_NAME, open_flags(directory=True), dir_fd=root_fd)
        except OSError:
            fail(24, "claims-create")
        try:
            os.fchmod(claims_fd, 0o700)
        except OSError:
            fail(24, "claims-chmod")
        if object_identity(claims_path_info) != object_identity(os.fstat(claims_fd)):
            fail(24, "claims-open-race")
        verify_created_directory(claims_fd, 0o700, "claims")
        os.fsync(claims_fd)
        os.fsync(root_fd)

        # The file is claimed before entropy is requested.  A crash leaves a
        # terminal partial state, never a reusable challenge.
        try:
            key_fd = os.open(KEY_NAME, open_flags(readwrite=True, create=True), 0o600, dir_fd=root_fd)
        except OSError:
            fail(24, "key-create")
        try:
            os.fchmod(key_fd, 0o600)
            verify_created_file(key_fd, 0o600, "key")
            key_bytes = os.urandom(32)
            if not isinstance(key_bytes, bytes) or len(key_bytes) != 32:
                fail(24, "key-generator")
            write_all(key_fd, key_bytes, "key")
            os.fsync(key_fd)
        except PrepError:
            raise
        except OSError:
            fail(24, "key-fsync")
        os.fsync(root_fd)

        # Validate every pre-receipt object before creating the evidence
        # candidate.  The candidate never independently asserts success.
        verify_parent_path(parent_fd)
        verify_prior_failure_evidence(parent_fd)
        verify_file_final(parent_fd, claim_name, claim_fd, 0o600, claim_raw, "durable-claim-pre-receipt")
        verify_directory_final(
            parent_fd,
            target_name,
            root_fd,
            0o700,
            [CLAIMS_NAME, KEY_NAME],
            "target-root-pre-receipt",
        )
        verify_directory_final(root_fd, CLAIMS_NAME, claims_fd, 0o700, [], "claims-pre-receipt")
        verify_file_final(root_fd, KEY_NAME, key_fd, 0o600, key_bytes, "key-pre-receipt")

        receipt_body = {
            "schema_version": "gov-01-toolchain-control-prep-evidence-v1",
            "evidence_state": "CONTROL-PREPARED-CANDIDATE",
            "derived_state_if_full_tree_verifies": "CONTROL-PREPARED",
            "candidate_is_independently_authoritative": False,
            "approval_challenge_id": challenge,
            "approved_receipt_digest": approved_receipt_digest,
            "envelope_raw_sha256": envelope_raw_sha256,
            "created_objects": [
                {
                    "kind": "regular",
                    "name": "durable-consumption-claim-sibling",
                    "mode": "0600",
                    "uid": EXPECTED_CREATED_UID,
                    "gid": EXPECTED_CREATED_GID,
                    "byte_length": len(claim_raw),
                },
                {
                    "kind": "directory",
                    "name": "root",
                    "mode": "0700",
                    "uid": EXPECTED_CREATED_UID,
                    "gid": EXPECTED_CREATED_GID,
                },
                {
                    "kind": "directory",
                    "name": CLAIMS_NAME,
                    "mode": "0700",
                    "uid": EXPECTED_CREATED_UID,
                    "gid": EXPECTED_CREATED_GID,
                },
                {
                    "kind": "regular",
                    "name": KEY_NAME,
                    "mode": "0600",
                    "uid": EXPECTED_CREATED_UID,
                    "gid": EXPECTED_CREATED_GID,
                    "byte_length": 32,
                },
                {
                    "kind": "regular",
                    "name": PREP_RECEIPT_NAME,
                    "mode": "0600",
                    "uid": EXPECTED_CREATED_UID,
                    "gid": EXPECTED_CREATED_GID,
                },
            ],
            "retained_predecessor_failure": {
                "approval_challenge_id": PRIOR_FAILED_CHALLENGE,
                "prior_envelope_raw_sha256": PRIOR_FAILED_ENVELOPE_SHA256,
                "prior_receipt_domain_sha256": PRIOR_FAILED_RECEIPT_DOMAIN_SHA256,
                "terminal_state": "ATTEMPT-CONSUMED-STOP",
                "observed_stop_reason": "durable-claim-owner",
                "failure_evidence_verified": True,
            },
            "single_use_state": "CONSUMED-BY-DURABLE-SIBLING-CLAIM",
            "durable_claim_raw_sha256": sha256_hex(claim_raw),
            "deletion_policy": "deletion-is-evidence-tampering-and-never-authorizes-challenge-reuse",
            "acquisition_challenge_claim_state": "ABSENT",
            "private_preimage_sidecar_state": "ABSENT",
            "maximum_state": "CONTROL-PREPARED",
        }
        receipt_core = canonical_json_bytes(receipt_body)
        evidence = dict(receipt_body)
        evidence["evidence_sha256"] = sha256_hex(PREP_RECEIPT_DOMAIN + receipt_core)
        receipt_raw = canonical_json_bytes(evidence)
        receipt_fd = create_exclusive_file(
            root_fd,
            PREP_RECEIPT_NAME,
            0o600,
            receipt_raw,
            "prep-receipt",
        )
        os.fsync(root_fd)

        # A success claim is emitted only after every public path still names
        # the inode opened by this process and every final byte is exact.
        verify_parent_path(parent_fd)
        verify_prior_failure_evidence(parent_fd)
        verify_file_final(parent_fd, claim_name, claim_fd, 0o600, claim_raw, "durable-claim-final")
        verify_directory_final(
            parent_fd,
            target_name,
            root_fd,
            0o700,
            [CLAIMS_NAME, KEY_NAME, PREP_RECEIPT_NAME],
            "target-root",
        )
        verify_directory_final(root_fd, CLAIMS_NAME, claims_fd, 0o700, [], "claims")
        verify_file_final(root_fd, KEY_NAME, key_fd, 0o600, key_bytes, "key")
        verify_file_final(
            root_fd,
            PREP_RECEIPT_NAME,
            receipt_fd,
            0o600,
            receipt_raw,
            "prep-receipt",
        )
        os.fsync(key_fd)
        os.fsync(receipt_fd)
        os.fsync(claim_fd)
        os.fsync(claims_fd)
        os.fsync(root_fd)
        os.fsync(parent_fd)
    except PrepError:
        # A partial root is intentionally retained.  No cleanup is authorized.
        raise
    except OSError:
        fail(24 if claim_created or root_created else 21, "filesystem-operation")
    finally:
        if claim_fd is not None:
            os.close(claim_fd)
        if receipt_fd is not None:
            os.close(receipt_fd)
        if key_fd is not None:
            os.close(key_fd)
        if claims_fd is not None:
            os.close(claims_fd)
        if root_fd is not None:
            os.close(root_fd)
        if parent_fd is not None:
            os.close(parent_fd)
        os.umask(previous_umask)


def build_parser():
    parser = argparse.ArgumentParser(description="Receipt-gated GOV-01 control-state preparation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="create the exact receipt-authorized control root")
    prepare.add_argument("--repo-root", required=True)
    prepare.add_argument("--envelope", required=True)
    prepare.add_argument("--receipt-digest", required=True)
    prepare.add_argument("--approval-challenge", required=True)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        validate_runtime()
        repo_fd = open_repo_root(args.repo_root)
        try:
            expected_envelope_path = args.repo_root + "/" + ENVELOPE_RELATIVE_PATH
            if args.envelope != expected_envelope_path:
                fail(20, "envelope-path")
            envelope_raw = read_repo_regular(repo_fd, ENVELOPE_RELATIVE_PATH, "envelope")
            (
                envelope,
                target_name,
                claim_name,
                calculated_receipt,
                artifacts,
                self_identity,
                census_at,
                not_after,
            ) = validate_envelope(
                args.repo_root,
                repo_fd,
                envelope_raw,
                args.receipt_digest,
                args.approval_challenge,
                datetime.datetime.now(datetime.timezone.utc),
            )
            execute_prepare(
                args.repo_root,
                repo_fd,
                envelope,
                envelope_raw,
                artifacts,
                self_identity,
                target_name,
                claim_name,
                envelope["approval_challenge_id"],
                calculated_receipt,
                sha256_hex(envelope_raw),
                census_at,
                not_after,
            )
        finally:
            os.close(repo_fd)
        print(json.dumps({"state": "CONTROL-PREPARED"}, sort_keys=True, separators=(",", ":")))
        return 0
    except PrepError as error:
        print(json.dumps({"state": "STOP", "reason": error.reason}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return error.code
    except Exception:
        print('{"reason":"unexpected-failure","state":"STOP"}', file=sys.stderr)
        return 70


if __name__ == "__main__":
    sys.exit(main())
