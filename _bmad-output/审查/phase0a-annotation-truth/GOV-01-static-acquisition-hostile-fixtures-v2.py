#!/usr/bin/env python3
import argparse
import ast
import base64
import copy
import contextlib
import datetime
import gzip
import hashlib
import hmac
import itertools
import json
import io
import os
import pathlib
import platform
import pwd
import runpy
import stat
import subprocess
import sys
import tempfile
import types

from jsonschema import Draft202012Validator, ValidationError


ROOT = pathlib.Path(__file__).resolve().parent
ACQ_PATH = ROOT / "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-v2.py"
VERIFIER_PATH = ROOT / "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-verifier-v2.py"
PHASE_ROOT = ROOT / "_bmad-output/审查/phase0a-annotation-truth"
ENVELOPE_SCHEMA_PATH = PHASE_ROOT / "GOV-01-toolchain-static-acquisition-envelope-v2.schema.json"
PRIVATE_SCHEMA_PATH = PHASE_ROOT / "GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json"
PUBLIC_SCHEMA_PATH = PHASE_ROOT / "GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json"


def configure_repo_paths(requested_root=None):
    global ROOT
    global ACQ_PATH
    global VERIFIER_PATH
    global PHASE_ROOT
    global ENVELOPE_SCHEMA_PATH
    global PRIVATE_SCHEMA_PATH
    global PUBLIC_SCHEMA_PATH

    try:
        if requested_root is None:
            source_path = pathlib.Path(__file__).resolve(strict=True)
            candidate = source_path.parents[3]
        else:
            candidate = pathlib.Path(requested_root).resolve(strict=True)
        phase_root = candidate / "_bmad-output/审查/phase0a-annotation-truth"
        paths = {
            "acquisition": phase_root / "GOV-01-toolchain-static-acquisition-v2.py",
            "verifier": phase_root / "GOV-01-toolchain-static-verifier-v2.py",
            "envelope": phase_root / "GOV-01-toolchain-static-acquisition-envelope-v2.schema.json",
            "private": phase_root / "GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json",
            "public": phase_root / "GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json",
        }
        if not stat.S_ISDIR(candidate.stat().st_mode):
            raise ValueError("not-directory")
        for path in paths.values():
            path_stat = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(path_stat.st_mode):
                raise ValueError("artifact-not-regular")
    except (IndexError, OSError, RuntimeError, ValueError):
        raise ValueError("fixture-repo-root-contract") from None

    ROOT = candidate
    PHASE_ROOT = phase_root
    ACQ_PATH = paths["acquisition"]
    VERIFIER_PATH = paths["verifier"]
    ENVELOPE_SCHEMA_PATH = paths["envelope"]
    PRIVATE_SCHEMA_PATH = paths["private"]
    PUBLIC_SCHEMA_PATH = paths["public"]


def synthetic_private_locator(*parts):
    return os.sep + os.path.join("Users", *parts)


class PrivacySafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, self.prog + ": error: fixture-arguments-invalid\n")


def fixture_argument_parser():
    parser = PrivacySafeArgumentParser(
        prog="gov01-static-acquisition-hostile-fixtures-v2",
        description="Offline hostile fixtures for the GOV-01 static acquisition contract",
    )
    parser.add_argument(
        "--repo-root",
        metavar="PATH",
        help="explicit repository root for a copied fixture; defaults to the source-file ancestry",
    )
    return parser


def expect_error(label, function, expected_reason=None):
    try:
        function()
    except Exception as error:
        reason = getattr(error, "reason", getattr(error, "public_code", ""))
        if expected_reason is not None and reason != expected_reason:
            raise AssertionError("%s wrong error: %s" % (label, reason))
        return reason
    raise AssertionError(label + " unexpectedly passed")


def expect_schema_error(label, validator, instance):
    try:
        validator.validate(instance)
    except ValidationError:
        return
    raise AssertionError(label + " unexpectedly passed schema")


def load_json_no_duplicates(path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AssertionError("duplicate JSON key in schema")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def verify_local_refs(schema):
    definitions = schema.get("$defs", {})

    def walk(value):
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                name = reference.split("/", 2)[2]
                if name not in definitions:
                    raise AssertionError("unresolved local ref " + reference)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


def octal_field(value, width):
    encoded = ("%0*o" % (width - 1, value)).encode("ascii") + b"\0"
    if len(encoded) != width:
        raise AssertionError("octal fixture overflow")
    return encoded


def ustar_member(name, payload=b"", mode=0o644, typeflag=b"0"):
    header = bytearray(512)
    encoded_name = name.encode("ascii")
    header[0 : len(encoded_name)] = encoded_name
    header[100:108] = octal_field(mode, 8)
    header[108:116] = octal_field(0, 8)
    header[116:124] = octal_field(0, 8)
    header[124:136] = octal_field(len(payload), 12)
    header[136:148] = octal_field(0, 12)
    header[148:156] = b"        "
    header[156:157] = typeflag
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    checksum = sum(header)
    header[148:156] = ("%06o" % checksum).encode("ascii") + b"\0 "
    padding = b"\0" * ((512 - (len(payload) % 512)) % 512)
    return bytes(header) + payload + padding


def package_archive(extra_members=(), eoa_blocks=2, package_manifest=None):
    if package_manifest is None:
        package_manifest = {"name": "fixture", "version": "1.0.0"}
    package_json = json.dumps(package_manifest, separators=(",", ":")).encode()
    raw = ustar_member("package/", b"", 0o755, b"5")
    raw += ustar_member("package/package.json", package_json)
    for member in extra_members:
        raw += member
    raw += b"\0" * 512 * eoa_blocks
    return gzip.compress(raw, mtime=0)


def mutate_first_ustar_header(compressed, offset, replacement):
    raw = bytearray(gzip.decompress(compressed))
    raw[offset : offset + len(replacement)] = replacement
    raw[148:156] = b"        "
    checksum = sum(raw[:512])
    raw[148:156] = ("%06o" % checksum).encode("ascii") + b"\0 "
    return gzip.compress(bytes(raw), mtime=0)


def write_bytes(path, data, mode=0o600):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
    finally:
        os.close(fd)


def rewrite_json(path, value):
    output_fd = os.open(str(path), os.O_WRONLY | os.O_TRUNC)
    try:
        os.write(output_fd, json.dumps(value, separators=(",", ":")).encode())
    finally:
        os.close(output_fd)


def rewrite_bytes(path, data):
    output_fd = os.open(str(path), os.O_WRONLY | os.O_TRUNC)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(output_fd, data[offset:])
    finally:
        os.close(output_fd)


def rewrite_canonical_json(path, value):
    raw = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    output_fd = os.open(str(path), os.O_WRONLY | os.O_TRUNC)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(output_fd, raw[offset:])
    finally:
        os.close(output_fd)


def run_checked(argv, cwd):
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
    )
    if completed.returncode != 0:
        raise AssertionError("fixture setup command failed")


def sbpl_top_level_forms(profile):
    """Return balanced top-level SBPL forms without interpreting the policy."""

    forms = []
    start = None
    depth = 0
    quoted = False
    escaped = False
    for index, character in enumerate(profile):
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "(":
            if depth == 0:
                start = index
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise AssertionError("unbalanced sandbox profile")
            if depth == 0:
                if start is None:
                    raise AssertionError("sandbox profile form start missing")
                forms.append(profile[start : index + 1])
                start = None
    if quoted or depth != 0 or start is not None:
        raise AssertionError("unterminated sandbox profile")
    return forms


def exercise_claim_fault(acquisition, fault_name):
    with tempfile.TemporaryDirectory(prefix="gov01-claim-fault-", dir="/private/tmp") as temporary:
        state_root = pathlib.Path(temporary) / "state"
        state_root.mkdir(mode=0o700)
        claims = state_root / "claims"
        claims.mkdir(mode=0o700)
        owner_uid = os.stat(state_root, follow_symlinks=False).st_uid
        group_gid = os.stat(state_root, follow_symlinks=False).st_gid
        if os.stat(claims, follow_symlinks=False).st_gid != group_gid:
            raise AssertionError("claim fixture group inheritance drift")
        challenge = "GOV01-SA-20260820-" + hashlib.sha256(fault_name.encode()).hexdigest()
        receipt = "b" * 64
        preimage = acquisition["verify_claim_preimage"](
            str(state_root), challenge, expected_uid=owner_uid, expected_gid=group_gid
        )
        attempt = acquisition["AttemptState"]()
        module_os = acquisition["os"]
        original_open = module_os.open
        original_fstat = module_os.fstat
        original_fsync = module_os.fsync
        original_write = module_os.write
        captured = {}

        def fault_open(path, flags, mode=0o777, *, dir_fd=None):
            if fault_name == "post-mkdir-open" and path == challenge:
                raise OSError("fixture")
            if fault_name == "ledger-create" and path == "ledger.jsonl":
                raise OSError("fixture")
            fd = original_open(path, flags, mode, dir_fd=dir_fd)
            if path == "claims":
                captured["claims_fd"] = fd
            elif path == challenge:
                captured["claim_fd"] = fd
            elif path == "ledger.jsonl":
                captured["ledger_fd"] = fd
            return fd

        def fault_fstat(fd):
            observed = original_fstat(fd)
            if fault_name == "post-mkdir-policy" and fd == captured.get("claim_fd"):
                return types.SimpleNamespace(
                    st_uid=observed.st_uid,
                    st_gid=observed.st_gid + 1,
                    st_mode=observed.st_mode,
                )
            return observed

        def fault_fsync(fd):
            if fault_name == "claims-directory-fsync" and fd == captured.get("claims_fd") and (claims / challenge).exists():
                raise OSError("fixture")
            if fault_name == "ledger-directory-fsync" and fd == captured.get("claim_fd") and "ledger_fd" in captured:
                raise OSError("fixture")
            return original_fsync(fd)

        def fault_write(fd, data):
            if fault_name == "first-ledger-write" and fd == captured.get("ledger_fd"):
                raise OSError("fixture")
            return original_write(fd, data)

        module_os.open = fault_open
        module_os.fstat = fault_fstat
        module_os.fsync = fault_fsync
        module_os.write = fault_write
        try:
            reason = expect_error(
                fault_name,
                lambda: acquisition["create_permanent_claim"](
                    str(state_root), b"k" * 32, challenge, receipt, preimage,
                    owner_uid, group_gid, "2099-01-01T00:00:00Z", attempt=attempt,
                ),
            )
        finally:
            module_os.open = original_open
            module_os.fstat = original_fstat
            module_os.fsync = original_fsync
            module_os.write = original_write
        expected_reasons = {
            "post-mkdir-open": "PRIVATE_CHILD_OPEN",
            "post-mkdir-policy": "PRIVATE_CHILD_POLICY",
            "claims-directory-fsync": "CLAIM_DIRECTORY_FSYNC",
            "ledger-create": "LEDGER_CREATE",
            "first-ledger-write": "LEDGER_WRITE",
            "ledger-directory-fsync": "LEDGER_DIRECTORY_FSYNC",
        }
        if reason != expected_reasons[fault_name]:
            raise AssertionError("%s wrong reason %r" % (fault_name, reason))
        if not (claims / challenge).is_dir():
            raise AssertionError(fault_name + " did not retain permanent claim")
        projection = attempt.failure_projection()
        assert projection["challenge_state"] == "claimed-consumed"
        assert projection["claim_state"] == "created-0700"
        assert projection["ledger_terminal_state"] == "absent-partial-or-semantic-invalid"
        assert not (state_root / (".gov01-toolchain-stage-" + challenge)).exists()


TREE_SHA256 = "777dc62b5a2094903c2047cb30bc63eccf34543c3d4466be30b6ae4789d391a2"


def ledger_event_data(event, promoted=False):
    zero = "0" * 64
    values = {
        "receipt-consumed": {"authority": "single-use-consumed-before-stage-write"},
        "preflight-frozen": {
            "envelope_raw_sha256": "1" * 64,
            "artifact_manifest_commitment": "2" * 64,
            "git_commitment": "3" * 64,
            "cache_manifest_commitment": "4" * 64,
            "selected_package_count": 167,
            "compressed_bytes": 13916529,
            "payload_bytes": 55954126,
            "tree_sha256": TREE_SHA256,
            "network_attempt_count": 0,
            "lifecycle_execution_count": 0,
            "installed_code_execution_count": 0,
        },
        "stage-materialized": {
            "file_count": 4099,
            "directory_count": 554,
            "symlink_count": 12,
            "tree_sha256": TREE_SHA256,
            "incomplete_marker_present": True,
        },
        "pre-promotion-cas-pass": {
            "artifact_manifest_unchanged": True,
            "git_unchanged": True,
            "cache_unchanged": True,
            "claude_sessions": 0,
            "target_absent": True,
            "incomplete_marker_present": True,
        },
        "stage-promoted": {
            "tree_sha256": TREE_SHA256,
            "incomplete_marker_present": False,
            "root_mode": "0755",
            "rename_profile": "renameatx_np-RENAME_EXCL",
        },
        "static-attestation-complete": {
            "state": "static-attested-unexecuted",
            "tree_sha256": TREE_SHA256,
            "selected_package_count": 167,
            "network_attempt_count": 0,
            "lifecycle_execution_count": 0,
            "installed_code_execution_count": 0,
            "openspec_execution_allowed": False,
            "openspec_scaffold_allowed": False,
        },
        "attempt-failed": {
            "public_code": "FIXTURE_FAILURE",
            "promoted": promoted,
            "stage_deleted_or_moved_on_failure": False,
            "automatic_rollback_performed": False,
        },
    }
    del zero
    return copy.deepcopy(values[event])


def build_ledger(acquisition, events, key, challenge, receipt, times=None, previous_override=None):
    previous = "0" * 64
    records = []
    for sequence, item in enumerate(events):
        if isinstance(item, tuple):
            event, promoted = item
        else:
            event, promoted = item, False
        at_utc = times[sequence] if times is not None else "2026-08-20T00:%02d:00Z" % sequence
        previous_value = previous_override.get(sequence, previous) if previous_override else previous
        base = {
            "schema_version": "gov01-static-acquisition-ledger-event-v2",
            "sequence": sequence,
            "at_utc": at_utc,
            "challenge": challenge,
            "receipt_digest": receipt,
            "event": event,
            "previous_hmac_sha256": previous_value,
            "data": ledger_event_data(event, promoted),
        }
        mac = acquisition["hmac_frame"](
            key,
            acquisition["LEDGER_DOMAIN"],
            acquisition["canonical_json"](base),
        )
        record = dict(base)
        record["hmac_sha256"] = mac
        records.append(record)
        previous = mac
    raw = b"".join(acquisition["canonical_json"](record) for record in records)
    return raw, records, previous


def private_projection(acquisition, report, executor_sha256, executor_bytes):
    return acquisition["build_private_ledger_projection"](
        report,
        executor_sha256,
        executor_bytes,
    )


def frozen_static_expected(zero):
    return {
        "profile_version": "gov-01-toolchain-static-verifier-v2",
        "package_json_sha256": "bd5c4e933e2dcbf7f2019bec9fec555b5b1adff1c4a6e5c36ea4415ff9a711fe",
        "package_lock_sha256": "c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea",
        "lockfile_version": 3,
        "lock_package_count": 176,
        "selected_package_count": 167,
        "excluded_platform_package_count": 9,
        "compressed_bytes": 13916529,
        "tar_stream_bytes": 59361280,
        "payload_bytes": 55954126,
        "raw_member_count": 4117,
        "raw_regular_count": 4099,
        "raw_directory_count": 18,
        "bin_link_count": 12,
        "lifecycle_field_count": 11,
        "content_receipt_body_bytes": 49665,
        "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
        "ustar_closure_body_bytes": 41470,
        "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
        "resolution": {
            "row_count": 256,
            "body_bytes": 26629,
            "sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
            "required_missing": 0,
            "allowed_missing": 10,
        },
        "tree": {
            "entry_count": 4665,
            "file_count": 4099,
            "directory_count": 554,
            "symlink_count": 12,
            "body_bytes": 539842,
            "sha256": TREE_SHA256,
        },
    }


def frozen_lock_observation():
    return {
        "host_selected_package_count": 167,
        "host_selected_cache_bytes": 13916529,
        "host_bin_link_count": 12,
        "expected_archive_member_count": 4117,
        "expected_resolved_tree_entry_count": 4665,
        "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b",
        "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb",
        "resolution_receipt_sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
        "expected_tree_sha256": TREE_SHA256,
    }


def synthetic_gate_evidence(gate_id):
    zero = "0" * 64
    values = {
        "G00": {"schema_sha256": zero, "schema_bytes": 1, "schema_count": 3, "schema_bundle_receipt_sha256": zero, "manual_critical_contract_passed": True},
        "G01": {
            "challenge_claim_created": True,
            "ledger_receipt_consumed_recorded": True,
            "first_authority_consuming_persistent_write_contract": "exclusive-0700-challenge-mkdir",
        },
        "G02": {"authorized_locator_commitment_count": 5, "private_control_identity_commitment": zero, "private_locator_public_count": 0, "private_vault_read_count": 0},
        "G03": {"toolchain_role_count": 9, "toolchain_set_receipt_sha256": zero, "dynamic_closure_receipt_sha256": zero, "assurance": "runtime-self-attested-not-pre-exec", "pre_exec_launcher_attested": False},
        "G04": {"authorized_subprocess_role_count": 6, "shell_allowed": False, "network_capable_child_authorized": False, "authorized_network_call_site_invocation_count": 0, "runtime_network_syscall_observation_available": False, "assurance": "static-structural-self-attestation-not-syscall-observation"},
        "G05": {"selected_package_count": 167, "compressed_bytes": 13916529, "content_receipt_sha256": "ade2bf32961a18ba9365b1aef1df3456471622759cbf56890ecfbdd40e92a60b"},
        "G06": {"raw_member_count": 4117, "ustar_closure_sha256": "bd9a30d26415f06e20dc61c551e34fface39c376b5f761518bb69cca72efe9bb"},
        "G07": {"parser": "custom-fixed-512-byte-ustar", "gzip_stream_count": 1, "required_zero_eoa_blocks": 2},
        "G08": {"accepted_member_types": ["regular-file", "directory"], "raw_regular_count": 4099, "raw_directory_count": 18, "generated_symlink_count": 12, "bundled_node_modules_allowed": False},
        "G09": {"compressed_bytes": 13916529, "payload_bytes": 55954126, "tar_stream_bytes": 59361280, "limits_enforced_by_frozen_verifier": True},
        "G10": {"protected_control_count": 3, "absent_alternate_control_count": 6},
        "G11": {"target_absent": True, "stage_absent": True},
        "G12": {"candidate_count": 0, "target_worktree_claude_sessions": 0, "pgrep_sha256": zero, "candidate_lsof_sha256": zero},
        "G13": {"same_filesystem": True, "stage_root_mode": "0700", "incomplete_marker_present": True, "stage_entry_write_scope_exact": True},
        "G14": {"entry_count": 4665, "file_count": 4099, "directory_count": 554, "symlink_count": 12, "expected_tree_sha256": TREE_SHA256},
        "G15": {"profile": "package-lock-path-closure-not-semver-proof", "row_count": 256, "required_missing": 0, "allowed_missing": 10, "resolution_receipt_sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0"},
        "G16": {"tree_sha256": TREE_SHA256, "entry_count": 4665, "incomplete_marker_excluded_from_tree": True, "double_stable_fingerprint_required_before_publication": True},
        "G17": {"authorized_payload_execution_call_site_invocation_count": 0, "authorized_lifecycle_execution_call_site_invocation_count": 0, "authorized_installed_code_call_site_invocation_count": 0, "authorized_node_npm_npx_call_site_invocation_count": 0, "runtime_exec_syscall_observation_available": False, "assurance": "static-structural-self-attestation-not-syscall-observation"},
        "G18": {"publish_syscall": "renameatx_np", "publish_flag": "RENAME_EXCL", "publish_attempt_count": 1, "target_parent_fsynced": True, "overwrite_allowed": False},
        "G19": {"protected_control_count": 3, "protected_controls_unchanged": True, "absent_alternate_control_count": 6},
        "G20": {"public_artifacts_unchanged": True, "toolchain_unchanged": True, "git_snapshot_unchanged": True, "cache_closure_unchanged": True, "protected_controls_unchanged": True, "stage_path_absent_after_publication": True, "outside_scope_mutation_count": 0, "assurance": "targeted-content-and-metadata-CAS-not-machine-wide-audit"},
        "G21": {"tree_sha256": TREE_SHA256, "entry_count": 4665, "file_count": 4099, "directory_count": 554, "symlink_count": 12, "double_stable_fingerprint_passed": True},
        "G22": {"candidate_count": 0, "target_worktree_claude_sessions": 0, "pgrep_sha256": zero, "candidate_lsof_sha256": zero},
        "G23": {"checker_interface": "gov01-ledger-semantic-checker-v2", "record_count": 6, "terminal_kind": "success", "ledger_head_hmac_sha256": zero, "canonical_jsonl_and_hmac_chain_valid": True, "private_projection_schema_version": "gov-01-toolchain-static-acquisition-private-evidence-v2"},
        "G24": {"private_locator_public_count": 0, "private_vault_read_count": 0, "raw_command_output_public_count": 0, "projection_preflight_passed": True},
    }
    return copy.deepcopy(values[gate_id])


READ_ONLY_EXECUTION_ORDER = (
    "G00", "G02", "G10", "G03", "G11", "G12", "G04",
    "G05", "G06", "G07", "G08", "G09", "G14", "G15",
)
ACQUIRE_EXECUTION_ORDER = (
    "G00", "G02", "G10", "G03", "G12", "G04", "G11",
    "G05", "G06", "G07", "G08", "G09", "G14", "G15",
    "G01", "G13", "G16", "G17", "G18", "G21", "G19", "G20",
    "G22", "G23", "G24",
)


def synthetic_tool_hashes(acquisition):
    zero = "0" * 64
    result = {role: zero for role in acquisition["TOOLCHAIN_ROLES"]}
    result["static-executor"] = hashlib.sha256(ACQ_PATH.read_bytes()).hexdigest()
    result["static-verifier"] = hashlib.sha256(VERIFIER_PATH.read_bytes()).hexdigest()
    return result


def synthetic_locator_commitments():
    zero = "0" * 64
    labels = {
        "repo_root": "repo-root",
        "cache_root": "npm-cache",
        "state_root": "state-root",
        "key_file": "hmac-key",
        "envelope": "envelope",
    }
    return {
        name: {"label": label, "commitment": zero}
        for name, label in labels.items()
    }


def record_synthetic_pass(acquisition, recorder, gate_id, evidence):
    zero = "0" * 64
    if gate_id == "G00":
        recorder.passed_with_authority(
            gate_id,
            evidence,
            "schema",
            {
                "path": "_bmad-output/审查/phase0a-annotation-truth/pending.schema.json",
                "sha256": evidence["schema_sha256"],
                "bytes": evidence["schema_bytes"],
                "schema_count": evidence["schema_count"],
                "schema_bundle_receipt_sha256": evidence["schema_bundle_receipt_sha256"],
            }
        )
    elif gate_id == "G02":
        recorder.passed_with_authority(
            gate_id,
            evidence,
            "private",
            {
                "private_control_identity_commitment": evidence["private_control_identity_commitment"],
                "hmac_key_id": zero,
                "authorized_locator_commitments": synthetic_locator_commitments(),
            },
        )
    elif gate_id == "G03":
        recorder.passed_with_authority(gate_id, evidence, "toolchain", evidence)
    else:
        recorder.passed(gate_id, evidence)


def recorder_with_prefix(acquisition, order, length, failure_code=None, evidence_overrides=None, failure_exit=11):
    recorder = acquisition["GateRecorder"]()
    if tuple(order) == ACQUIRE_EXECUTION_ORDER or (
        tuple(order) == READ_ONLY_EXECUTION_ORDER and length > 0
    ):
        recorder.bind_run_authority(
            "GOV01-SA-20260820-" + ("f" * 64),
            "e" * 64,
        )
    overrides = evidence_overrides or {}
    for index, gate_id in enumerate(order[:length]):
        recorder.begin(gate_id, acquisition["GATE_PHASE_BY_ID"][gate_id])
        if failure_code is not None and index == length - 1:
            recorder.failed(failure_code, failure_exit)
        else:
            evidence = synthetic_gate_evidence(gate_id)
            evidence.update(copy.deepcopy(overrides.get(gate_id, {})))
            record_synthetic_pass(acquisition, recorder, gate_id, evidence)
    return recorder


def refresh_gate_receipts(acquisition, result, validate=True):
    projection = result["gate_results"]
    for record in projection["reached_gates"]:
        body = dict(record)
        body.pop("receipt_sha256", None)
        record["receipt_sha256"] = acquisition["sha256"](
            acquisition["GATE_DOMAIN"] + b"\x00" + acquisition["canonical_json"](body)
        )
    if projection["complete"]:
        receipt_body = {
            "schema_version": "gov01-static-acquisition-gate-set-v2",
            "gate_receipts": [
                {"gate_id": record["gate_id"], "receipt_sha256": record["receipt_sha256"]}
                for record in projection["reached_gates"]
            ],
        }
        projection["gate_set_receipt_sha256"] = acquisition["sha256"](
            acquisition["GATE_SET_DOMAIN"] + b"\x00" + acquisition["canonical_json"](receipt_body)
        )
    if validate:
        acquisition["validate_gate_projection"](projection)


def public_authority_binding(result):
    context = result.get("attestation", result.get("observation"))
    if not isinstance(context, dict):
        raise AssertionError("public authority binding requires success context")
    tool_context = context.get("toolchain", context)
    zero = "0" * 64
    labels = {
        "repo_root": "repo-root",
        "cache_root": "npm-cache",
        "state_root": "state-root",
        "key_file": "hmac-key",
        "envelope": "envelope",
    }
    package_lock_raw = (
        context["package_lock_raw_sha256"]
        if "package_lock_raw_sha256" in context
        else context["source_and_receipts"]["static_expected"]["package_lock_sha256"]
    )
    return {
        "approval_challenge_id": result["approval_challenge_id"],
        "receipt_digest": result["receipt_digest"],
        "schema_binding_observation": context["schema_binding_observation"],
        "toolchain_hashes": tool_context.get("hashes", context.get("toolchain_hashes")),
        "public_repo_artifact_set_receipt_sha256": context["public_repo_artifact_set_receipt_sha256"],
        "git_snapshot_commitment": context["git_snapshot_commitment"],
        "private_preapproval_commitment": context["private_preapproval_commitment"],
        "private_control_identity_commitment": context["private_control_identity_commitment"],
        "hmac_key_id": context.get("hmac_key_id", zero),
        "authorized_locator_commitments": context.get(
            "authorized_locator_commitments",
            {name: {"label": label, "commitment": zero} for name, label in labels.items()},
        ),
        "package_lock_raw_sha256": package_lock_raw,
        "toolchain_set_receipt_sha256": tool_context["toolchain_set_receipt_sha256"],
        "dynamic_closure_receipt_sha256": tool_context["dynamic_closure_receipt_sha256"],
    }


def recorder_authority_binding_for_result(acquisition, result):
    """Build the success sidecar through the production monotonic recorder API."""

    context = result.get("attestation", result.get("observation"))
    manual = public_authority_binding(result)
    recorder = acquisition["GateRecorder"]()
    recorder.bind_run_authority(result["approval_challenge_id"], result["receipt_digest"])
    for gate_id in ("G00", "G02", "G03"):
        matching = [
            record
            for record in result["gate_results"]["reached_gates"]
            if record["gate_id"] == gate_id
        ]
        if len(matching) != 1 or matching[0]["status"] != "PASS":
            raise AssertionError("missing authority gate " + gate_id)
        recorder.begin(gate_id, acquisition["GATE_PHASE_BY_ID"][gate_id])
        evidence = copy.deepcopy(matching[0]["evidence"])
        if gate_id == "G00":
            authority_value = context["schema_binding_observation"]
            authority_kind = "schema"
        elif gate_id == "G02":
            authority_value = {
                "private_control_identity_commitment": context["private_control_identity_commitment"],
                "hmac_key_id": manual["hmac_key_id"],
                "authorized_locator_commitments": manual["authorized_locator_commitments"],
            }
            authority_kind = "private"
        else:
            authority_value = {
                "toolchain_set_receipt_sha256": manual["toolchain_set_receipt_sha256"],
                "dynamic_closure_receipt_sha256": manual["dynamic_closure_receipt_sha256"],
            }
            authority_kind = "toolchain"
        recorder.passed_with_authority(
            gate_id,
            evidence,
            authority_kind,
            authority_value,
        )
    additions = {
        name: manual[name]
        for name in (
            "toolchain_hashes",
            "public_repo_artifact_set_receipt_sha256",
            "git_snapshot_commitment",
            "private_preapproval_commitment",
            "package_lock_raw_sha256",
        )
    }
    return acquisition["completed_public_authority_binding"](recorder, additions)


def validate_public_contract(acquisition, validator, result, authority_binding=None):
    validator.validate(result)
    acquisition["validate_public_result_projection"](result, authority_binding)


def run_main_handler(acquisition, mode, handler):
    """Exercise the production handler -> main -> emit -> process-exit chain."""

    class FixtureParser:
        def parse_args(self, argv):
            del argv
            return argparse.Namespace(
                mode=mode,
                handler=handler,
                generation_challenge="GOV01-GEN-20260820-" + ("c" * 64),
                receipt_digest="e" * 64,
                approval_challenge="GOV01-SA-20260820-" + ("f" * 64),
            )

    executor_globals = acquisition["main"].__globals__
    original_parser = executor_globals["parser"]
    executor_globals["parser"] = lambda: FixtureParser()
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            return_code = acquisition["main"]([])
    finally:
        executor_globals["parser"] = original_parser
    serialized = json.loads(output.getvalue())
    expected_exit = 0 if serialized.get("ok") is True else serialized["error"]["exit"]
    if return_code != expected_exit:
        raise AssertionError(
            "stdout/process exit divergence: stdout=%r process=%r" % (expected_exit, return_code)
        )
    return return_code, serialized


def synthetic_success(acquisition, ledger_head=None):
    zero = "0" * 64
    if ledger_head is None:
        ledger_head = zero
    challenge = "GOV01-SA-20260820-" + ("a" * 64)
    tool_hashes = synthetic_tool_hashes(acquisition)
    recorder = acquisition["GateRecorder"]()
    recorder.bind_run_authority(challenge, zero)
    for gate_id, _scope in acquisition["GATE_SCOPES"]:
        recorder.begin(gate_id, acquisition["GATE_PHASE_BY_ID"][gate_id])
        evidence = synthetic_gate_evidence(gate_id)
        if gate_id == "G23":
            evidence["ledger_head_hmac_sha256"] = ledger_head
        record_synthetic_pass(acquisition, recorder, gate_id, evidence)
    gates = recorder.complete_projection()
    acquisition["validate_gate_projection"](gates)
    terminal = acquisition["AttemptState"]()
    terminal.claim_created()
    terminal.stage_created()
    terminal.target_promoted()
    terminal.terminal_success_recorded()
    schema_observation = {
        "path": "_bmad-output/审查/phase0a-annotation-truth/pending.schema.json",
        "sha256": zero,
        "bytes": 1,
        "schema_count": 3,
        "schema_bundle_receipt_sha256": zero,
    }
    lock_observation = frozen_lock_observation()
    static_expected = frozen_static_expected(zero)
    toolchain = {
        "assurance": "runtime-self-attested-not-pre-exec",
        "pre_exec_launcher_attested": False,
        "toolchain_set_receipt_sha256": zero,
        "dynamic_closure_receipt_sha256": zero,
        "hashes": tool_hashes,
    }
    result = acquisition["base_public_result"](
        True,
        "acquire",
        "static-attestation-complete",
        "static-attested-unexecuted",
        terminal.projection(),
        gates,
        {"toolchain_set_receipt_sha256": zero, "dynamic_closure_receipt_sha256": zero},
    )
    result["approval_challenge_id"] = challenge
    result["receipt_digest"] = zero
    result["authority"] = acquisition["authority_projection"](
        False,
        True,
        "new runtime-use envelope binding this final tree and a fresh single-use challenge",
    )
    result["attestation"] = {
        "schema_version": "gov01-static-acquisition-success-attestation-v2",
        "approval_challenge_id": challenge,
        "receipt_digest": zero,
        "schema_binding_observation": schema_observation,
        "public_repo_artifact_set_receipt_sha256": zero,
        "git_snapshot_commitment": zero,
        "private_preapproval_commitment": zero,
        "private_control_identity_commitment": zero,
        "toolchain": toolchain,
        "source_and_receipts": {"lock_closure_observed": lock_observation, "static_expected": static_expected},
        "publication": {
            "publish_syscall": "renameatx_np",
            "publish_flag": "RENAME_EXCL",
            "tree_sha256": TREE_SHA256,
            "private_ledger_head_hmac_sha256": ledger_head,
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
    return result


def synthetic_read_only(acquisition, mode="census"):
    zero = "0" * 64
    challenge = "GOV01-SA-20260820-" + ("b" * 64)
    state = "read-only-preapproval-census" if mode == "census" else "preconditions-reverified-read-only"
    recorder = recorder_with_prefix(acquisition, READ_ONLY_EXECUTION_ORDER, len(READ_ONLY_EXECUTION_ORDER))
    tool_hashes = synthetic_tool_hashes(acquisition)
    schema_observation = {
        "path": "_bmad-output/审查/phase0a-annotation-truth/pending.schema.json",
        "sha256": zero,
        "bytes": 1,
        "schema_count": 3,
        "schema_bundle_receipt_sha256": zero,
    }
    result = acquisition["base_public_result"](
        True,
        mode,
        state + "-complete",
        state,
        acquisition["read_only_terminal_state"](),
        recorder.partial_projection(),
        {"toolchain_set_receipt_sha256": zero, "dynamic_closure_receipt_sha256": zero},
    )
    result["approval_challenge_id"] = challenge
    result["receipt_digest"] = zero
    result["authority"] = acquisition["authority_projection"](
        True,
        False,
        "exact user-approved acquisition receipt and challenge required before any mutation",
    )
    labels = {
        "repo_root": "repo-root",
        "cache_root": "npm-cache",
        "state_root": "state-root",
        "key_file": "hmac-key",
        "envelope": "envelope",
    }
    result["observation"] = {
        "selected_packages": 167,
        "selected_cache_bytes": 13916529,
        "bin_links": 12,
        "claude_sessions": 0,
        "hmac_key_id": zero,
        "authorized_locator_commitments": {
            name: {"label": label, "commitment": zero} for name, label in labels.items()
        },
        "private_control_identity_commitment": zero,
        "schema_binding_observation": schema_observation,
        "public_repo_artifact_set_receipt_sha256": zero,
        "git_snapshot_commitment": zero,
        "toolchain_set_receipt_sha256": zero,
        "dynamic_closure_receipt_sha256": zero,
        "toolchain_hashes": tool_hashes,
        "package_lock_raw_sha256": "c6e190741427b99ff132d6504b2a782d75c418d6ae93066769ac422bff6b7cea",
        "lock_closure_observed": frozen_lock_observation(),
        "static_expected": frozen_static_expected(zero),
        "private_preapproval_commitment": zero,
    }
    return result


def synthesize_schema_instance(schema):
    """Deterministic redacted satisfiability witness; never an approval envelope."""

    def merge(left, right):
        result = copy.deepcopy(left)
        for key, value in right.items():
            if key == "properties":
                result.setdefault(key, {})
                for name, child in value.items():
                    result[key][name] = merge(result[key].get(name, {}), child)
            elif key == "required":
                result[key] = list(dict.fromkeys(result.get(key, []) + value))
            elif key == "allOf":
                result.setdefault(key, [])
                result[key] += copy.deepcopy(value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    def dereference(value):
        if "$ref" not in value:
            return value
        reference = value["$ref"]
        if not reference.startswith("#/$defs/"):
            raise AssertionError("nonlocal ref in synthetic schema")
        base = schema["$defs"][reference.split("/", 2)[2]]
        return merge(base, {key: item for key, item in value.items() if key != "$ref"})

    def flatten(value):
        value = dereference(value)
        result = {key: copy.deepcopy(item) for key, item in value.items() if key != "allOf"}
        for child in value.get("allOf", []):
            if "if" in child or "contains" in child:
                continue
            result = merge(result, flatten(child))
        return result

    def string_value(value):
        pattern = value.get("pattern", "")
        if value.get("format") == "date-time" or ("T" in pattern and "Z" in pattern):
            return "2026-08-20T00:00:00Z"
        if "GOV01-GEN" in pattern:
            return "GOV01-GEN-20260820-" + ("b" * 64)
        if "GOV01-CP" in pattern:
            return "GOV01-CP-20260820-" + ("c" * 32)
        if "GOV01-SA" in pattern:
            return "GOV01-SA-20260820-" + ("a" * 64)
        if "[0-9a-f]{64}" in pattern:
            return "0" * 64
        if "[0-9a-f]{40}" in pattern:
            return "0" * 40
        if "^[A-Za-z0-9]" in pattern:
            return "fixture-id"
        if "^(?!/)" in pattern:
            return "fixture/path.json"
        if "^[A-Za-z_]" in pattern:
            return "FIXTURE"
        if "^[A-Z]" in pattern:
            return "FIXTURE"
        return "fixture"

    def synthesize(value):
        flattened = flatten(value)
        if "const" in flattened:
            return copy.deepcopy(flattened["const"])
        if "enum" in flattened:
            return copy.deepcopy(flattened["enum"][0])
        if "oneOf" in flattened:
            base = {key: item for key, item in flattened.items() if key != "oneOf"}
            return synthesize(merge(base, flattened["oneOf"][0]))
        kind = flattened.get("type")
        if isinstance(kind, list):
            kind = next(item for item in kind if item != "null")
        if kind == "object" or "properties" in flattened or "required" in flattened:
            properties = flattened.get("properties", {})
            result = {
                name: synthesize(properties.get(name, {}))
                for name in flattened.get("required", [])
            }
            for condition in dereference(value).get("allOf", []):
                if "if" not in condition or not Draft202012Validator(condition["if"]).is_valid(result):
                    continue
                overlay = flatten(condition.get("then", {}))
                for name, child in overlay.get("properties", {}).items():
                    if name in result:
                        result[name] = synthesize(child)
                for name in overlay.get("required", []):
                    result[name] = synthesize(overlay.get("properties", {}).get(name, {}))
            return result
        if kind == "array" or "items" in flattened or "prefixItems" in flattened:
            item_schema = flattened.get("items", {}) if isinstance(flattened.get("items", {}), dict) else {}
            result = [synthesize(item) for item in flattened.get("prefixItems", [])]
            for condition in dereference(value).get("allOf", []):
                if "contains" in condition:
                    result.append(synthesize(merge(item_schema, condition["contains"])))
            while len(result) < flattened.get("minItems", 0):
                candidate = synthesize(item_schema)
                if candidate in result and isinstance(candidate, dict):
                    candidate = dict(candidate)
                    candidate["logical_id"] = "fixture-%d" % len(result)
                result.append(candidate)
            return result[: flattened.get("maxItems", len(result))]
        if kind == "string" or "pattern" in flattened:
            return string_value(flattened)
        if kind == "integer":
            return flattened.get("minimum", 0)
        if kind == "number":
            return flattened.get("minimum", 0)
        if kind == "boolean":
            return False
        if kind == "null":
            return None
        return {}

    instance = synthesize(schema)
    challenge = instance["approval_challenge_id"]
    instance["census_at_utc"] = "2026-08-20T00:00:00Z"
    instance["not_after_utc"] = "2026-08-20T01:00:00Z"
    instance["static_acquisition_contract"]["stage_repo_relative"] = ".gov01-toolchain-stage-" + challenge
    generation_challenge = "GOV01-GEN-20260820-" + ("b" * 64)
    generation_micro_path = (
        "_bmad-output/审查/phase0a-annotation-truth/"
        "GOV-01-toolchain-static-envelope-generation-envelope-v1." + generation_challenge + ".json"
    )
    generated_pending_path = (
        "_bmad-output/审查/phase0a-annotation-truth/"
        "GOV-01-toolchain-static-acquisition-pending-" + generation_challenge + ".json"
    )
    instance["generation_authorization"].update(
        {
            "approval_challenge_id": generation_challenge,
            "approval_envelope_repo_relative_path": generation_micro_path,
            "generated_acquisition_envelope_repo_relative_path": generated_pending_path,
            "authorization_commit_oid": "0" * 64,
            "authorization_tree_oid": "0" * 64,
        }
    )
    instance["authorization_preimage"]["envelope_repo_relative_path"] = (
        generated_pending_path
    )
    instance["authorization_preimage"]["git_object_format"] = "sha256"
    instance["authorization_preimage"]["head_commit_oid"] = "0" * 64
    instance["authorization_preimage"]["head_tree_oid"] = "0" * 64
    role_paths = {
        "goal": "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md",
        "governance-decision": "_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md",
        "pending-envelope-schema": "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-envelope-v2.schema.json",
        "private-evidence-schema": "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-private-evidence-v2.schema.json",
        "public-attestation-schema": "_bmad-output/审查/phase0a-annotation-truth/GOV-01-toolchain-static-acquisition-public-attestation-v2.schema.json",
        "package-manifest": "package.json",
        "package-lock": "package-lock.json",
        "gitignore": ".gitignore",
        "generation-approval-envelope": generation_micro_path,
    }
    for artifact in instance["artifacts"]:
        if artifact["role"] in role_paths:
            artifact["path"] = role_paths[artifact["role"]]
        if artifact["role"] == "generation-approval-envelope":
            artifact["raw_file_sha256"] = instance["generation_authorization"]["raw_envelope_sha256"]
    predecessor_artifact_hashes = {
        "first-receipt-envelope": "0b73b83e1dbd92dd0a4684a83438dafc7afae6a6fde42b4130d776d7ee246410",
        "bootstrap-patch": "d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa",
        "control-prep-envelope": "ef424f80672568076d750ae0f6d662ebfdae242fdea8fcda2b37f39e6406945b",
    }
    for artifact in instance["artifacts"]:
        if artifact["role"] in predecessor_artifact_hashes:
            artifact["raw_file_sha256"] = predecessor_artifact_hashes[artifact["role"]]
    generation = instance["generation_authorization"]
    instance["predecessor"].update(
        {
            "generation_authorization_envelope_raw_sha256": generation["raw_envelope_sha256"],
            "generation_authorization_receipt_digest": generation["receipt_digest"],
            "generation_authorization_challenge_id": generation["approval_challenge_id"],
            "generation_authorization_parent_commit_oid": generation["authorization_parent_commit_oid"],
            "generation_authorization_parent_tree_oid": generation["authorization_parent_tree_oid"],
            "generation_authorization_commit_oid": generation["authorization_commit_oid"],
            "generation_authorization_tree_oid": generation["authorization_tree_oid"],
        }
    )
    predecessor_body = {
        key: value
        for key, value in instance["predecessor"].items()
        if key != "predecessor_chain_receipt_sha256"
    }
    predecessor_raw = json.dumps(
        predecessor_body,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    instance["predecessor"]["predecessor_chain_receipt_sha256"] = hashlib.sha256(
        b"CLS/GOV01/STATIC-ACQUISITION-PREDECESSOR-CHAIN/v2\x00" + predecessor_raw
    ).hexdigest()
    for entry in instance["frozen_toolchain"]["entries"]:
        if entry["role"] in ("python-interpreter", "python-stdlib-tree"):
            entry["version"] = platform.python_version()
    pending_artifact = next(
        artifact for artifact in instance["artifacts"] if artifact["role"] == "pending-envelope-schema"
    )
    instance["schema_binding"]["schema_artifact_path"] = pending_artifact["path"]
    instance["schema_binding"]["schema_raw_file_sha256"] = pending_artifact["raw_file_sha256"]
    execution = instance["execution_plan"]

    def contract_receipt(domain, value):
        canonical = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        return hashlib.sha256(domain + b"\x00" + canonical).hexdigest()

    execution["executor_argv_template_sha256"] = contract_receipt(
        b"CLS/GOV01/EXECUTOR-ARGV-TEMPLATE/v2",
        execution["executor_argv_template"],
    )
    execution["evidence_command_templates_sha256"] = contract_receipt(
        b"CLS/GOV01/EVIDENCE-COMMAND-TEMPLATES/v2",
        execution["evidence_command_templates"],
    )
    return instance


def build_real_pending_envelope_from_synthetic_observations(acquisition, schema_witness):
    """Reproject a schema witness through the production pending-envelope builder."""
    artifacts = copy.deepcopy(schema_witness["artifacts"])
    artifact_by_role = {entry["role"]: entry for entry in artifacts}
    artifact_observations = [
        {
            "role": entry["role"],
            "path": entry["path"],
            "bytes": entry["byte_length"],
            "sha256": entry["raw_file_sha256"],
        }
        for entry in artifacts
    ]
    tool_entries = copy.deepcopy(schema_witness["frozen_toolchain"]["entries"])
    generation = schema_witness["generation_authorization"]
    preimage = schema_witness["authorization_preimage"]
    challenge = schema_witness["approval_challenge_id"]
    output_path = generation["generated_acquisition_envelope_repo_relative_path"]
    lock_closure = schema_witness["lock_closure"]
    observations = {
        "artifacts": artifacts,
        "schema_binding_observation": {
            "path": artifact_by_role["pending-envelope-schema"]["path"],
            "sha256": artifact_by_role["pending-envelope-schema"]["raw_file_sha256"],
            "bytes": artifact_by_role["pending-envelope-schema"]["byte_length"],
            "schema_count": 3,
            "schema_bundle_receipt_sha256": "0" * 64,
        },
        "toolchain": {
            "entries": tool_entries,
            "toolchain_set_receipt_sha256": acquisition["toolchain_set_receipt"](tool_entries),
            "dynamic_closure_receipt_sha256": acquisition["dynamic_toolchain_receipt"](tool_entries),
        },
        "git_snapshot": {
            "head": generation["authorization_commit_oid"],
            "tree": generation["authorization_tree_oid"],
            "object_format": preimage["git_object_format"],
            "commitment": preimage["git_snapshot_commitment"],
            "dirty_manifest_commitment": "0" * 64,
            "git_metadata_source_commitment": "0" * 64,
            "git_metadata_adapter_profile": acquisition["GIT_METADATA_ADAPTER_PROFILE_V5"],
            "git_metadata_adapter_cleanup_state": "removed",
            "git_metadata_adapter_residue_count": 0,
            "live_git_control_child_read_count": 0,
            "index_gitlink_profile": acquisition["GIT_INDEX_GITLINK_PROFILE_V1"],
            "index_gitlink_count": 1,
            "worktree_tree_exclusions": (
                acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"],
                ".gov01-toolchain-stage-" + challenge,
                acquisition["TARGET_NAME"],
            ),
            "worktree_exact_file_exclusions": (output_path,),
            "status_bytes": 0,
        },
        "process_census": {
            "claude_session_count": preimage["target_worktree_claude_sessions"],
        },
        "package_lock_raw_sha256": artifact_by_role["package-lock"]["raw_file_sha256"],
        "lock_observation": {
            key: lock_closure[key] for key in acquisition["LOCK_OBSERVATION_FIELDS"]
        },
        "static_expected": schema_witness["static_acquisition_contract"]["expected"],
        "hmac_key_id": schema_witness["private_state_authorization"]["hmac_key_id"],
        "authorized_locator_commitments": schema_witness["private_state_authorization"][
            "authorized_locator_commitments"
        ],
        "private_control_identity_commitment": schema_witness["private_state_authorization"][
            "private_control_identity_commitment"
        ],
        "public_repo_artifact_set_receipt_sha256": acquisition["public_artifact_set_receipt"](
            artifact_observations
        ),
        "private_preapproval_commitment": preimage["private_preapproval_commitment"],
        "predecessor_projection": {
            key: schema_witness["predecessor"][key]
            for key in (
                "control_preparation_result_raw_sha256",
                "control_preparation_evidence_receipt_sha256",
                "control_preparation_approval_challenge_id",
                "control_preparation_state",
            )
        },
        "envelope_repo_relative_path": output_path,
    }
    candidate = acquisition["build_pending_envelope_v2"](
        approval_challenge_id=challenge,
        census_at_utc=schema_witness["census_at_utc"],
        not_after_utc=schema_witness["not_after_utc"],
        generation_authorization=generation,
        observations=observations,
    )
    if candidate == schema_witness:
        raise AssertionError("production builder was bypassed by the synthetic witness")
    return candidate


def json_pointer(path):
    return "#" if not path else "#/" + "/".join(
        str(component).replace("~", "~0").replace("/", "~1") for component in path
    )


def iter_bool_int_scalar_paths(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_bool_int_scalar_paths(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_bool_int_scalar_paths(child, path + (index,))
    elif type(value) in (bool, int):
        yield path, value


def iter_leaf_paths(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_leaf_paths(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_leaf_paths(child, path + (index,))
    else:
        yield path, value


def value_at_path(value, path):
    current = value
    for component in path:
        current = current[component]
    return current


def replace_at_path(value, path, replacement):
    current = value
    for component in path[:-1]:
        current = current[component]
    current[path[-1]] = replacement


def pending_dynamic_none_overlay_coverage(acquisition, candidate):
    template = json.loads(acquisition["_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON"])
    none_paths = sorted(
        path for path, value in iter_leaf_paths(template) if value is None
    )
    overlay_rows = []
    dynamic_scalar_rows = []
    unclassified = []
    expected_lock_structure = acquisition["pending_lock_observation_expected_structure"](
        candidate["static_acquisition_contract"]["expected"]
    )
    if frozenset(expected_lock_structure) != acquisition["LOCK_OBSERVATION_FIELDS"]:
        raise AssertionError("lock observation expected projection is incomplete")
    for path in none_paths:
        actual = value_at_path(candidate, path)
        overlay_rows.append(
            {"path": json_pointer(path), "actual_container_or_scalar_type": type(actual).__name__}
        )
        for suffix, scalar in iter_bool_int_scalar_paths(actual):
            full_path = path + suffix
            if path == ("static_acquisition_contract", "expected"):
                coverage = "validated-static-expected-structure"
            elif (
                len(path) == 2
                and path[0] == "lock_closure"
                and path[1] in expected_lock_structure
            ):
                coverage = "lock-observation-expected-structure-projection"
            elif path in (
                ("authorization_preimage", "forbidden_process_match_count"),
                ("authorization_preimage", "target_worktree_claude_sessions"),
            ):
                coverage = "authorization-preimage-exact-zero-consumer"
            else:
                coverage = "unclassified"
                unclassified.append(json_pointer(full_path))
            dynamic_scalar_rows.append(
                {
                    "path": json_pointer(full_path),
                    "type": "boolean" if type(scalar) is bool else "integer",
                    "coverage": coverage,
                }
            )
    if unclassified:
        raise AssertionError("unclassified dynamic bool/int overlay: " + ",".join(unclassified))
    overlay_paths = [row["path"] for row in overlay_rows]
    dynamic_paths = [row["path"] for row in dynamic_scalar_rows]
    return {
        "template_none_overlay_count": len(overlay_rows),
        "template_none_overlay_paths": overlay_paths,
        "template_none_overlay_path_set_sha256": acquisition["sha256"](
            b"CLS/GOV01/PENDING-TEMPLATE-NONE-OVERLAY-PATH-SET/v1\x00"
            + acquisition["canonical_json"](overlay_paths)
        ),
        "bool_int_leaf_count": len(dynamic_scalar_rows),
        "bool_int_leaf_paths": dynamic_scalar_rows,
        "bool_int_leaf_path_set_sha256": acquisition["sha256"](
            b"CLS/GOV01/PENDING-DYNAMIC-BOOL-INT-PATH-SET/v1\x00"
            + acquisition["canonical_json"](dynamic_paths)
        ),
        "classified_bool_int_leaf_count": len(dynamic_scalar_rows),
        "unclassified_bool_int_leaf_paths": unclassified,
    }


def pending_builder_bool_int_scalar_type_parity(acquisition, validator, candidate, witness_now):
    validator.validate(candidate)
    acquisition["validate_manual_envelope_contract"](candidate, now=witness_now)
    scalar_rows = sorted(iter_bool_int_scalar_paths(candidate), key=lambda item: json_pointer(item[0]))
    typed_paths = [
        {
            "path": json_pointer(path),
            "type": "boolean" if type(value) is bool else "integer",
        }
        for path, value in scalar_rows
    ]
    schema_rejection_count = 0
    manual_rejection_count = 0
    for path, value in scalar_rows:
        hostile = copy.deepcopy(candidate)
        replacement = int(value) if type(value) is bool else bool(value)
        replace_at_path(hostile, path, replacement)
        schema_rejected = not validator.is_valid(hostile)
        try:
            acquisition["validate_manual_envelope_contract"](hostile, now=witness_now)
        except acquisition["ContractError"]:
            manual_rejected = True
        else:
            manual_rejected = False
        schema_rejection_count += int(schema_rejected)
        manual_rejection_count += int(manual_rejected)
        if schema_rejected != manual_rejected:
            raise AssertionError("schema/manual scalar-type difference at " + json_pointer(path))
        if not schema_rejected:
            raise AssertionError("bool/int scalar mutation unexpectedly accepted at " + json_pointer(path))
    template = json.loads(acquisition["_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON"])
    template_typed_paths = {
        json_pointer(path): type(value)
        for path, value in iter_bool_int_scalar_paths(template)
    }
    candidate_types = {json_pointer(path): type(value) for path, value in scalar_rows}
    if any(candidate_types.get(path) is not kind for path, kind in template_typed_paths.items()):
        raise AssertionError("synchronized template bool/int coverage drift")
    dynamic_coverage = pending_dynamic_none_overlay_coverage(acquisition, candidate)
    builder_only_count = len(typed_paths) - len(template_typed_paths) - dynamic_coverage["bool_int_leaf_count"]
    if (
        len(typed_paths) != 145
        or sum(row["type"] == "boolean" for row in typed_paths) != 66
        or sum(row["type"] == "integer" for row in typed_paths) != 79
        or len(template_typed_paths) != 82
        or dynamic_coverage["template_none_overlay_count"] != 29
        or dynamic_coverage["bool_int_leaf_count"] != 30
        or builder_only_count != 33
    ):
        raise AssertionError("pending builder bool/int frozen coverage count drift")
    return {
        "builder": "build_pending_envelope_v2",
        "production_builder_baseline_differs_from_schema_witness": True,
        "mutation_count": len(typed_paths),
        "bool_path_count": sum(row["type"] == "boolean" for row in typed_paths),
        "int_path_count": sum(row["type"] == "integer" for row in typed_paths),
        "integer_zero_or_one_baseline_count": sum(
            type(value) is int and value in (0, 1) for _, value in scalar_rows
        ),
        "schema_rejection_count": schema_rejection_count,
        "manual_rejection_count": manual_rejection_count,
        "typed_paths": typed_paths,
        "typed_path_set_sha256": acquisition["sha256"](
            b"CLS/GOV01/PENDING-BOOL-INT-SCALAR-PATH-SET/v1\x00"
            + acquisition["canonical_json"](typed_paths)
        ),
        "coverage_partition": {
            "synchronized_template_bool_int_leaf_count": len(template_typed_paths),
            "dynamic_none_overlay_bool_int_leaf_count": dynamic_coverage["bool_int_leaf_count"],
            "builder_structure_bool_int_leaf_count": builder_only_count,
        },
        "dynamic_none_overlay_coverage": dynamic_coverage,
    }


def validate_public_result_branch_schema_equivalence(
    acquisition,
    public_schema,
    public_validator,
    fixture_error,
    challenge,
    receipt,
    toolchain,
    failure_reports_by_count,
    success_report,
):
    """Keep schema-only and production-checker consumers on the same branches."""

    fields = (
        "challenge_state",
        "claim_state",
        "stage_state",
        "publication_state",
        "ledger_terminal_state",
        "target_disposition",
    )
    terminal_schema = public_schema["$defs"]["actualTerminalState"]
    terminal_validator = Draft202012Validator(terminal_schema)
    domains = tuple(tuple(terminal_schema["properties"][name]["enum"]) for name in fields)
    terminal_tuples = tuple(
        values
        for values in itertools.product(*domains)
        if terminal_validator.is_valid(dict(zip(fields, values)))
    )
    assert len(terminal_tuples) == 5724
    authority_values = tuple(
        public_schema["$defs"]["actualAuthority"]["properties"]["next_required_authority"]["allOf"][1]["enum"]
    )
    assert len(authority_values) == 6

    def checker_accepts(candidate, authority_binding=None):
        try:
            acquisition["validate_public_result_projection"](candidate, authority_binding)
        except acquisition["ContractError"]:
            return False
        return True

    def assert_schema_and_checker_reject(label, candidate, authority_binding=None):
        if public_validator.is_valid(candidate):
            raise AssertionError(label + " unexpectedly passed schema")
        if checker_accepts(candidate, authority_binding):
            raise AssertionError(label + " unexpectedly passed whole checker")

    entry_contract = public_schema["$defs"]["actualEntryAndReadOnlyFailureContract"]

    def branch_validator(index):
        definitions = dict(public_schema["$defs"])
        definitions["fixtureSelectedBranch"] = entry_contract["oneOf"][index]
        return Draft202012Validator(
            {
                "$schema": public_schema["$schema"],
                "$ref": "#/$defs/fixtureSelectedBranch",
                "$defs": definitions,
            }
        )

    generic = {
        mode: acquisition["generic_public_failure"](fixture_error, mode)
        for mode in ("unknown", "census", "verify", "acquire")
    }
    privacy = acquisition["privacy_rejection_result"]()
    read_only_failures = {}
    for mode in ("census", "verify"):
        recorder = recorder_with_prefix(
            acquisition,
            READ_ONLY_EXECUTION_ORDER,
            7,
            failure_code="FIXTURE_FAILURE",
        )
        read_only_failures[mode] = acquisition["read_only_failure_result"](
            fixture_error,
            mode,
            recorder,
        )

    branch_cases = (
        ("unknown-entry", 0, generic["unknown"], None),
        ("census-entry", 2, generic["census"], None),
        ("census-read-only", 3, read_only_failures["census"], read_only_failures["census"].authority_binding),
        ("verify-entry", 4, generic["verify"], None),
        ("verify-read-only", 5, read_only_failures["verify"], read_only_failures["verify"].authority_binding),
        ("acquire-entry", 6, generic["acquire"], None),
    )
    quotient_count = len(terminal_tuples) * 2 * len(authority_values)
    assert quotient_count == 68688
    for label, index, baseline, authority_binding in branch_cases:
        public_validator.validate(baseline)
        acquisition["validate_public_result_projection"](baseline, authority_binding)
        expected_key = (
            tuple(baseline["terminal_state"][name] for name in fields),
            baseline["retention"]["private_state_inspection_required"],
            baseline["authority"]["next_required_authority"],
        )
        schema_keys = set()
        checker_keys = set()
        selected_validator = branch_validator(index)
        for values in terminal_tuples:
            for inspection in (False, True):
                for next_authority in authority_values:
                    candidate = dict(baseline)
                    candidate["terminal_state"] = dict(zip(fields, values))
                    candidate["retention"] = dict(baseline["retention"])
                    candidate["retention"]["private_state_inspection_required"] = inspection
                    candidate["authority"] = dict(baseline["authority"])
                    candidate["authority"]["next_required_authority"] = next_authority
                    key = (values, inspection, next_authority)
                    if selected_validator.is_valid(candidate):
                        schema_keys.add(key)
                    if checker_accepts(candidate, authority_binding):
                        checker_keys.add(key)
        assert schema_keys == checker_keys == {expected_key}, (
            label,
            sorted(schema_keys - checker_keys)[:1],
            sorted(checker_keys - schema_keys)[:1],
        )

    # Privacy is a distinct fail-closed branch.  Exhaust its five independent
    # structural axes rather than sampling the old schema-only gap:
    # 5,724 terminals x 2 inspection values x 6 authorities x 2 runtime
    # shapes x 3 ledger shapes = 412,128.  Exactly the production privacy
    # projection is accepted by both authorities.
    failure_ledger = acquisition["ledger_public_evidence"](failure_reports_by_count[2])
    success_ledger = acquisition["ledger_public_evidence"](success_report)
    privacy_validator = branch_validator(1)
    privacy_domain_count = 0
    privacy_accept_count = 0
    expected_privacy_key = (
        tuple(privacy["terminal_state"][name] for name in fields),
        True,
        "new explicit user approval after private-state inspection",
        False,
        "absent",
    )
    for values in terminal_tuples:
        for inspection in (False, True):
            for next_authority in authority_values:
                for runtime_extended in (False, True):
                    for ledger_label, ledger_value in (
                        ("absent", None),
                        ("failure", failure_ledger),
                        ("success", success_ledger),
                    ):
                        privacy_domain_count += 1
                        candidate = copy.copy(privacy)
                        candidate["terminal_state"] = dict(zip(fields, values))
                        candidate["retention"] = dict(privacy["retention"])
                        candidate["retention"]["private_state_inspection_required"] = inspection
                        candidate["authority"] = dict(privacy["authority"])
                        candidate["authority"]["next_required_authority"] = next_authority
                        candidate["runtime_assurance"] = dict(privacy["runtime_assurance"])
                        if runtime_extended:
                            candidate["runtime_assurance"]["toolchain_set_receipt_sha256"] = "0" * 64
                            candidate["runtime_assurance"]["dynamic_closure_receipt_sha256"] = "0" * 64
                        if ledger_value is None:
                            candidate.pop("ledger_evidence", None)
                        else:
                            candidate["ledger_evidence"] = ledger_value
                        key = (values, inspection, next_authority, runtime_extended, ledger_label)
                        schema_ok = privacy_validator.is_valid(candidate)
                        checker_ok = checker_accepts(candidate)
                        if schema_ok != checker_ok:
                            raise AssertionError(("privacy branch schema/whole difference", key, schema_ok, checker_ok))
                        if schema_ok:
                            assert key == expected_privacy_key
                            privacy_accept_count += 1
    assert privacy_domain_count == 412128
    assert privacy_accept_count == 1

    # Every reachable read-only failure prefix can end in FAIL or in a PASS
    # followed by an asynchronous exception before the next gate begins.
    for mode in ("census", "verify"):
        for length in range(len(READ_ONLY_EXECUTION_ORDER) + 1):
            failure_codes = (None,) if length == 0 else (None, "FIXTURE_FAILURE")
            for failure_code in failure_codes:
                recorder = recorder_with_prefix(
                    acquisition,
                    READ_ONLY_EXECUTION_ORDER,
                    length,
                    failure_code=failure_code,
                )
                result = acquisition["read_only_failure_result"](
                    fixture_error,
                    mode,
                    recorder,
                )
                validate_public_contract(acquisition, public_validator, result)

        # Receipt binding precedes G00.  An asynchronous failure in that
        # zero-gate window is retryable, while a pre-receipt zero-gate failure
        # above remains non-retryable.
        bound_zero = acquisition["GateRecorder"]()
        bound_zero.bind_run_authority(
            "GOV01-SA-20260820-" + ("f" * 64),
            "e" * 64,
        )
        bound_zero_result = acquisition["read_only_failure_result"](
            fixture_error,
            mode,
            bound_zero,
        )
        validate_public_contract(acquisition, public_validator, bound_zero_result)
        assert bound_zero_result["authority"]["retry_authorized"] is True
        stripped_bound_zero = dict(bound_zero_result)
        if checker_accepts(stripped_bound_zero):
            raise AssertionError("read-only retry passed without trusted receipt sidecar")

    wrong_read_only_trace = copy.deepcopy(read_only_failures["census"])
    wrong_read_only_trace["gate_results"] = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        7,
        failure_code="FIXTURE_FAILURE",
    ).partial_projection()
    assert_schema_and_checker_reject("read-only acquire-order trace", wrong_read_only_trace)

    nonzero_gates = recorder_with_prefix(
        acquisition,
        READ_ONLY_EXECUTION_ORDER,
        1,
        failure_code="FIXTURE_FAILURE",
    ).partial_projection()
    for label, baseline in (
        ("unknown-entry", generic["unknown"]),
        ("census-entry", generic["census"]),
        ("verify-entry", generic["verify"]),
        ("acquire-entry", generic["acquire"]),
        ("privacy", privacy),
    ):
        mutations = []
        candidate = copy.deepcopy(baseline)
        candidate["phase"] = "public-projection" if label != "privacy" else "entry-fail-closed"
        mutations.append(("phase", candidate))
        candidate = copy.deepcopy(baseline)
        candidate["gate_results"] = copy.deepcopy(nonzero_gates)
        mutations.append(("gates", candidate))
        candidate = copy.deepcopy(baseline)
        candidate["runtime_assurance"]["toolchain_set_receipt_sha256"] = "0" * 64
        candidate["runtime_assurance"]["dynamic_closure_receipt_sha256"] = "0" * 64
        mutations.append(("runtime", candidate))
        candidate = copy.deepcopy(baseline)
        candidate["ledger_evidence"] = copy.deepcopy(failure_ledger)
        mutations.append(("ledger", candidate))
        candidate = copy.deepcopy(baseline)
        candidate["approval_challenge_id"] = challenge
        candidate["receipt_digest"] = receipt
        mutations.append(("approval", candidate))
        for mutation, candidate in mutations:
            assert_schema_and_checker_reject(label + " " + mutation, candidate)

    privacy_with_approval = copy.deepcopy(privacy)
    privacy_with_approval["approval_challenge_id"] = challenge
    privacy_with_approval["receipt_digest"] = receipt
    assert_schema_and_checker_reject(
        "privacy approval with matching hidden authority",
        privacy_with_approval,
        {"approval_challenge_id": challenge, "receipt_digest": receipt},
    )

    # G03 receipt presence is exactly equivalent to a reached PASS receipt.
    pre_g03_read_only = acquisition["read_only_failure_result"](
        fixture_error,
        "census",
        recorder_with_prefix(acquisition, READ_ONLY_EXECUTION_ORDER, 3, failure_code="FIXTURE_FAILURE"),
    )
    injected = copy.deepcopy(pre_g03_read_only)
    injected["runtime_assurance"]["toolchain_set_receipt_sha256"] = "0" * 64
    injected["runtime_assurance"]["dynamic_closure_receipt_sha256"] = "0" * 64
    assert_schema_and_checker_reject("read-only pre-G03 runtime injection", injected)
    removed = copy.deepcopy(read_only_failures["census"])
    removed["runtime_assurance"].pop("toolchain_set_receipt_sha256")
    removed["runtime_assurance"].pop("dynamic_closure_receipt_sha256")
    assert_schema_and_checker_reject("read-only post-G03 runtime removal", removed)

    pre_g03_attempt = acquisition["AttemptState"]()
    pre_g03_attempt.set_phase("control-root-before")
    pre_g03_acquire = acquisition["acquire_failure_result"](
        fixture_error,
        pre_g03_attempt,
        recorder_with_prefix(acquisition, ACQUIRE_EXECUTION_ORDER, 3, failure_code="FIXTURE_FAILURE"),
        challenge,
        receipt,
        None,
        None,
    )
    injected = copy.deepcopy(pre_g03_acquire)
    injected["runtime_assurance"]["toolchain_set_receipt_sha256"] = "0" * 64
    injected["runtime_assurance"]["dynamic_closure_receipt_sha256"] = "0" * 64
    assert_schema_and_checker_reject("acquire pre-G03 runtime injection", injected)
    post_g03_attempt = acquisition["AttemptState"]()
    post_g03_attempt.set_phase("process-census-before")
    post_g03_acquire = acquisition["acquire_failure_result"](
        fixture_error,
        post_g03_attempt,
        recorder_with_prefix(acquisition, ACQUIRE_EXECUTION_ORDER, 6, failure_code="FIXTURE_FAILURE"),
        challenge,
        receipt,
        toolchain,
        None,
    )
    removed = copy.deepcopy(post_g03_acquire)
    removed["runtime_assurance"].pop("toolchain_set_receipt_sha256")
    removed["runtime_assurance"].pop("dynamic_closure_receipt_sha256")
    assert_schema_and_checker_reject("acquire post-G03 runtime removal", removed)

    # Success/result-finalization branches use the same exact runtime and
    # authority contract rather than relying on the in-process checker alone.
    for mode in ("census", "verify"):
        result = synthetic_read_only(acquisition, mode)
        binding = recorder_authority_binding_for_result(acquisition, result)
        validate_public_contract(acquisition, public_validator, result, binding)
        mutations = []
        candidate = copy.deepcopy(result)
        candidate["phase"] = "read-only-fail-closed"
        mutations.append(("phase", candidate))
        candidate = copy.deepcopy(result)
        candidate["state"] = (
            "preconditions-reverified-read-only"
            if mode == "census"
            else "read-only-preapproval-census"
        )
        mutations.append(("state", candidate))
        candidate = copy.deepcopy(result)
        candidate["terminal_state"]["challenge_state"] = "preclaim-pending"
        mutations.append(("terminal", candidate))
        candidate = copy.deepcopy(result)
        candidate["authority"]["next_required_authority"] = "new explicit user approval after fail-closed evidence review"
        mutations.append(("authority", candidate))
        candidate = copy.deepcopy(result)
        candidate["gate_results"] = recorder_with_prefix(acquisition, READ_ONLY_EXECUTION_ORDER, 0).partial_projection()
        mutations.append(("gates", candidate))
        candidate = copy.deepcopy(result)
        candidate["runtime_assurance"].pop("toolchain_set_receipt_sha256")
        candidate["runtime_assurance"].pop("dynamic_closure_receipt_sha256")
        mutations.append(("runtime", candidate))
        for mutation, candidate in mutations:
            assert_schema_and_checker_reject(mode + " success " + mutation, candidate, binding)

    acquire_success = synthetic_success(acquisition, success_report["head_hmac_sha256"])
    acquire_binding = recorder_authority_binding_for_result(acquisition, acquire_success)
    validate_public_contract(acquisition, public_validator, acquire_success, acquire_binding)
    candidate = copy.deepcopy(acquire_success)
    candidate["phase"] = "ledger-terminal-success"
    assert_schema_and_checker_reject("acquire success phase", candidate, acquire_binding)
    candidate = copy.deepcopy(acquire_success)
    candidate["authority"]["next_required_authority"] = "new explicit user approval after fail-closed evidence review"
    assert_schema_and_checker_reject("acquire success authority", candidate, acquire_binding)
    candidate = copy.deepcopy(acquire_success)
    candidate["runtime_assurance"].pop("toolchain_set_receipt_sha256")
    candidate["runtime_assurance"].pop("dynamic_closure_receipt_sha256")
    assert_schema_and_checker_reject("acquire success runtime", candidate, acquire_binding)

    complete_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        25,
        evidence_overrides={"G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}},
    )
    complete_attempt = acquisition["AttemptState"]()
    for action in (
        "claim_created",
        "stage_created",
        "stage_marker_removed",
        "target_promoted",
        "terminal_success_recorded",
    ):
        getattr(complete_attempt, action)()
    complete_attempt.set_phase("static-attestation-complete")
    finalization = acquisition["resource_finalization_failure_result"](
        complete_attempt,
        complete_recorder,
        challenge,
        receipt,
        toolchain,
        success_report,
    )
    validate_public_contract(acquisition, public_validator, finalization)
    candidate = copy.deepcopy(finalization)
    candidate["runtime_assurance"].pop("toolchain_set_receipt_sha256")
    candidate["runtime_assurance"].pop("dynamic_closure_receipt_sha256")
    assert_schema_and_checker_reject("resource finalization runtime", candidate)


def validate_public_failure_state_schema_equivalence(
    acquisition,
    public_schema,
    public_validator,
    fixture_error,
    challenge,
    receipt,
    toolchain,
    failure_reports_by_count,
    success_report,
):
    """Exhaust the finite acquisition-failure terminal domain.

    The full public schema is expensive because every gate receipt has a
    discriminated evidence schema.  This test therefore validates the exact
    content-addressed trace/reachability definitions in a reduced resolver,
    enumerates the production whole-result checker over the same domain, and
    replays every accepted intersection member through both full authorities.
    """

    fields = (
        "challenge_state",
        "claim_state",
        "stage_state",
        "publication_state",
        "ledger_terminal_state",
        "target_disposition",
    )
    terminal_schema = public_schema["$defs"]["actualTerminalState"]
    terminal_validator = Draft202012Validator(terminal_schema)
    domains = tuple(tuple(terminal_schema["properties"][name]["enum"]) for name in fields)
    raw_terminal_count = 1
    for domain in domains:
        raw_terminal_count *= len(domain)
    assert raw_terminal_count == 61236
    terminal_tuples = tuple(
        values
        for values in itertools.product(*domains)
        if terminal_validator.is_valid(dict(zip(fields, values)))
    )
    assert len(terminal_tuples) == 5724

    reachability_names = (
        "actualAcquireFailureReachability",
        "actualTerminalRecoveryU32",
        "actualTerminalRecoveryU28",
        "actualTerminalRecoveryS47",
        "actualTerminalRecoveryP40",
        "actualTerminalRecoveryL40",
        "actualFailurePreclaimAuthority",
        "actualFailureClaimedInvalidAuthority",
        "actualFailureLedgerAuthority",
        "actualSuccessLedgerAuthority",
    )
    reachability_validator = Draft202012Validator(
        {
            "$schema": public_schema["$schema"],
            "$ref": "#/$defs/actualAcquireFailureReachability",
            "$defs": {
                name: public_schema["$defs"][name]
                for name in reachability_names
            },
        }
    )
    trace_validator = Draft202012Validator(
        {
            "$schema": public_schema["$schema"],
            "$ref": "#/$defs/actualAcquireFailureTrace",
            "$defs": {
                "actualAcquireFailureTrace": public_schema["$defs"]["actualAcquireFailureTrace"]
            },
        }
    )
    resource_validator = Draft202012Validator(
        public_schema["$defs"]["actualTerminalRecoveryR1"]
    )

    def make_attempt(recipe, phase):
        attempt = acquisition["AttemptState"]()
        for action in recipe.split(",") if recipe else ():
            getattr(attempt, action)()
        attempt.set_phase(phase)
        return attempt

    specs = (
        (1, "schema-contract", 1, "FAIL", None, ""),
        (2, "process-census-before", 6, "FAIL", None, ""),
        (3, "persistent-claim", 14, "PASS", None, ""),
        (4, "persistent-claim", 15, "FAIL", 2, "claim_directory_created,terminal_failure_recorded"),
        (5, "stage-materialization", 15, "PASS", 3, "claim_created,terminal_failure_recorded"),
        (6, "stage-materialization", 16, "FAIL", 3, "claim_created,stage_directory_created,terminal_failure_recorded"),
        (7, "stage-tree-attestation", 17, "FAIL", 4, "claim_created,stage_created,terminal_failure_recorded"),
        (8, "stage-tree-attestation", 18, "FAIL", 4, "claim_created,stage_created,terminal_failure_recorded"),
        (9, "pre-promotion-cas", 18, "PASS", 4, "claim_created,stage_created,terminal_failure_recorded"),
        (10, "sealed-marker-removed", 19, "FAIL", 5, "claim_created,stage_created,stage_marker_removed,terminal_failure_recorded"),
        (11, "rename-succeeded-attestation-incomplete", 20, "FAIL", 6, "claim_created,stage_created,stage_marker_removed,target_promoted,terminal_failure_recorded"),
        (12, "post-promotion-containment", 20, "PASS", 6, "claim_created,stage_created,stage_marker_removed,target_promoted,terminal_failure_recorded"),
        (13, "ledger-terminal-success", 24, "FAIL", "success", "claim_created,stage_created,stage_marker_removed,target_promoted,terminal_success_publication_failed"),
        (14, "static-attestation-complete", 25, "FAIL", "success", "claim_created,stage_created,stage_marker_removed,target_promoted,terminal_success_publication_failed"),
    )
    contexts = []
    for ident, phase, prefix, last_status, ledger_value, recipe in specs:
        evidence_overrides = None
        if ident == 14:
            evidence_overrides = {
                "G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}
            }
        recorder = recorder_with_prefix(
            acquisition,
            ACQUIRE_EXECUTION_ORDER,
            prefix,
            failure_code=("FIXTURE_FAILURE" if last_status == "FAIL" else None),
            failure_exit=int(acquisition["Exit"].CONTRACT),
            evidence_overrides=evidence_overrides,
        )
        ledger_report = (
            success_report
            if ledger_value == "success"
            else failure_reports_by_count[ledger_value]
            if isinstance(ledger_value, int)
            else None
        )
        baseline = acquisition["acquire_failure_result"](
            fixture_error,
            make_attempt(recipe, phase),
            recorder,
            challenge,
            receipt,
            toolchain if prefix >= 4 else None,
            ledger_report,
        )
        contexts.append((ident, baseline, False))

    complete_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        25,
        evidence_overrides={
            "G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}
        },
    )
    complete_attempt = make_attempt(
        "claim_created,stage_created,stage_marker_removed,target_promoted,terminal_success_recorded",
        "static-attestation-complete",
    )
    contexts.append(
        (
            15,
            acquisition["resource_finalization_failure_result"](
                complete_attempt,
                complete_recorder,
                challenge,
                receipt,
                toolchain,
                success_report,
            ),
            True,
        )
    )

    expected_counts = (32, 32, 32, 32, 32, 32, 28, 28, 28, 47, 40, 40, 40, 40, 1)
    accepted_total = 0
    for ident, baseline, complete in contexts:
        public_validator.validate(baseline)
        acquisition["validate_public_result_projection"](baseline)
        if complete:
            schema_set = {
                values
                for values in terminal_tuples
                if resource_validator.is_valid(dict(zip(fields, values)))
            }
        else:
            trace_validator.validate(baseline)
            schema_set = set()
            for values in terminal_tuples:
                baseline["terminal_state"] = dict(zip(fields, values))
                if reachability_validator.is_valid(baseline):
                    schema_set.add(values)

        checker_set = set()
        for values in terminal_tuples:
            baseline["terminal_state"] = dict(zip(fields, values))
            try:
                acquisition["validate_public_result_projection"](baseline)
            except acquisition["ContractError"]:
                pass
            else:
                checker_set.add(values)
        assert schema_set == checker_set, (
            ident,
            sorted(schema_set - checker_set)[:3],
            sorted(checker_set - schema_set)[:3],
        )
        assert len(schema_set) == expected_counts[ident - 1]

        for values in schema_set:
            baseline["terminal_state"] = dict(zip(fields, values))
            public_validator.validate(baseline)
            acquisition["validate_public_result_projection"](baseline)
            accepted_total += 1
        rejected = next(values for values in terminal_tuples if values not in schema_set)
        baseline["terminal_state"] = dict(zip(fields, rejected))
        assert not public_validator.is_valid(baseline)

    assert len(contexts) == 15
    assert raw_terminal_count * len(contexts) == 918540
    assert accepted_total == 484


def run_process_stderr_boundary_fixtures(acquisition, report):
    """Use a real child to prove bounded stderr is rejected without disclosure."""

    python_binary = os.path.realpath(sys.executable)
    previous_hash = acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].get(python_binary)
    acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][python_binary] = acquisition[
        "hash_regular_absolute"
    ](python_binary, "PROCESS_STDERR_FIXTURE_PYTHON")["sha256"]
    environment = acquisition["git_env"]()
    private_diagnostic = synthetic_private_locator(
        "FixtureSecret",
        "stderr-must-not-be-public",
    ).encode("utf-8")

    def child(source):
        return [python_binary, "-I", "-S", "-B", "-c", source]

    try:
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            diagnostic_reason = expect_error(
                "rc-zero child diagnostic",
                lambda: acquisition["run_process"](
                    child("import os;os.write(2,%r)" % private_diagnostic),
                    environment,
                    4096,
                    "PROCESS_STDERR_FIXTURE",
                ),
                "PROCESS_STDERR_FIXTURE_STDERR",
            )
            large_reason = expect_error(
                "bounded large child diagnostic",
                lambda: acquisition["run_process"](
                    child(
                        "import os;os.write(2,b'x'*%d)"
                        % (acquisition["MAX_PROCESS_STDERR_BYTES"] + 17)
                    ),
                    environment,
                    4096,
                    "PROCESS_STDERR_BOUND_FIXTURE",
                ),
                "PROCESS_STDERR_BOUND_FIXTURE_STDERR",
            )
            nonzero_reason = expect_error(
                "nonzero clean child",
                lambda: acquisition["run_process"](
                    child("raise SystemExit(7)"),
                    environment,
                    4096,
                    "PROCESS_NONZERO_FIXTURE",
                ),
                "PROCESS_NONZERO_FIXTURE_RESULT",
            )
            assert acquisition["run_process"](
                child("raise SystemExit(7)"),
                environment,
                4096,
                "PROCESS_ALLOWED_NONZERO_FIXTURE",
                allowed_returncodes=(7,),
            ) == b""
        public_capture = captured_stdout.getvalue() + captured_stderr.getvalue()
        assert public_capture == ""
        for reason in (diagnostic_reason, large_reason, nonzero_reason):
            assert private_diagnostic.decode("utf-8") not in reason
    finally:
        if previous_hash is None:
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].pop(python_binary, None)
        else:
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][python_binary] = previous_hash
    report["process_bounded_stderr_rc0_diagnostic_and_nonzero_clean"] = "PASS"
    report["process_stderr_private_bytes_not_disclosed"] = "PASS"


def run_captured_ref_observation_fixtures(acquisition, report):
    """Exercise frozen ref parsing and the exact read-only argv without live Git state."""

    oid_head = "1" * 40
    oid_loose = "2" * 40
    oid_packed = "3" * 40
    oid_packed_shadowed = "4" * 40
    oid_override = "5" * 40
    oid_worktree = "6" * 40
    oid_peeled = "7" * 40

    def captured(head=None, loose=None, worktree=None, packed=None, linked=False):
        return {
            "linked_worktree": linked,
            "raw_files": {
                "head": head if head is not None else b"ref: refs/heads/main\n",
                "packed_refs": packed,
            },
            "common_ref_bytes": loose if loose is not None else {
                "heads/main": (oid_head + "\n").encode("ascii"),
            },
            "worktree_ref_bytes": worktree if worktree is not None else {},
        }

    oid_worktree_override = "8" * 40
    oid_common_hidden = "9" * 40
    oid_packed_hidden = "a" * 40
    valid = captured(
        loose={
            "heads/main": (oid_head + "\n").encode("ascii"),
            "aliases/main": b"ref: refs/heads/main\n",
            "foo": (oid_loose + "\n").encode("ascii"),
            "stash": (oid_head + "\n").encode("ascii"),
            "bisect/override": (oid_common_hidden + "\n").encode("ascii"),
            "worktree/common-hidden": (oid_common_hidden + "\n").encode("ascii"),
            "tags/loose-unmaterialized": (oid_loose + "\n").encode("ascii"),
            "tags/override": (oid_override + "\n").encode("ascii"),
        },
        worktree={
            "bisect/override": (oid_worktree_override + "\n").encode("ascii"),
            "worktree/current": (oid_worktree + "\n").encode("ascii"),
        },
        packed=(
            b"# pack-refs with: peeled fully-peeled sorted\n"
            + (oid_packed_shadowed + " refs/bisect/override\n").encode("ascii")
            + (oid_packed_hidden + " refs/rewritten/packed-hidden\n").encode("ascii")
            + (oid_packed_shadowed + " refs/tags/override\n").encode("ascii")
            + (oid_packed + " refs/tags/packed-unmaterialized\n").encode("ascii")
            + ("^" + oid_peeled + "\n").encode("ascii")
            + (oid_packed + " refs/worktree/common-hidden\n").encode("ascii")
        ),
        linked=True,
    )
    state = acquisition["parse_captured_git_ref_state"](valid)
    expected_by_ref = {
        "refs/aliases/main": oid_head,
        "refs/bisect/override": oid_worktree_override,
        "refs/foo": oid_loose,
        "refs/heads/main": oid_head,
        "refs/rewritten/packed-hidden": oid_packed_hidden,
        "refs/stash": oid_head,
        "refs/tags/loose-unmaterialized": oid_loose,
        "refs/tags/override": oid_override,
        "refs/tags/packed-unmaterialized": oid_packed,
        "refs/worktree/common-hidden": oid_packed,
        "refs/worktree/current": oid_worktree,
    }
    assert state["head_oid"] == oid_head
    assert state["oid_length"] == 40
    assert state["profile"] == acquisition["GIT_REF_OBSERVATION_PROFILE_V1"]
    assert state["linked_worktree"] is True
    assert dict((refname, oid) for oid, refname in state["canonical_refs"]) == expected_by_ref
    assert state["effective_ref_raw"]["refs/tags/override"] == (
        oid_override + "\n"
    ).encode("ascii")
    canonical_output = b"".join(
        (oid + " " + refname + "\n").encode("ascii")
        for oid, refname in state["canonical_refs"]
    )
    assert acquisition["parse_git_for_each_ref_output"](
        canonical_output,
        40,
    ) == state["canonical_refs"]
    oid_sha256 = "a" * 64
    detached_sha256 = captured(
        head=(oid_sha256 + "\n").encode("ascii"),
        loose={"tags/sha256": (oid_sha256 + "\n").encode("ascii")},
    )
    detached_sha256_state = acquisition["parse_captured_git_ref_state"](detached_sha256)
    assert detached_sha256_state["head_oid"] == oid_sha256
    assert detached_sha256_state["oid_length"] == 64
    assert detached_sha256_state["canonical_refs"] == (
        (oid_sha256, "refs/tags/sha256"),
    )

    broken = captured(
        loose={
            "heads/main": (oid_head + "\n").encode("ascii"),
            "aliases/broken": b"ref: refs/heads/missing\n",
        }
    )
    expect_error(
        "captured broken symref",
        lambda: acquisition["parse_captured_git_ref_state"](broken),
        "GIT_CAPTURE_REF_RESOLUTION_MISSING",
    )
    cycle = captured(
        loose={
            "heads/main": (oid_head + "\n").encode("ascii"),
            "aliases/one": b"ref: refs/aliases/two\n",
            "aliases/two": b"ref: refs/aliases/one\n",
        }
    )
    expect_error(
        "captured symref cycle",
        lambda: acquisition["parse_captured_git_ref_state"](cycle),
        "GIT_CAPTURE_REF_RESOLUTION_CYCLE",
    )
    invalid_worktree_namespace = captured(
        loose={"heads/main": (oid_head + "\n").encode("ascii")},
        worktree={"heads/forbidden": (oid_head + "\n").encode("ascii")},
        linked=True,
    )
    expect_error(
        "captured linked worktree ref outside namespace",
        lambda: acquisition["parse_captured_git_ref_state"](invalid_worktree_namespace),
        "GIT_CAPTURE_WORKTREE_REF_NAMESPACE",
    )
    positive_depth_refs = {"heads/main": (oid_head + "\n").encode("ascii")}
    for index in range(acquisition["MAX_CAPTURED_REF_SYMREF_DEPTH"] - 1):
        target = (
            "refs/aliases/positive-%02d" % (index + 1)
            if index + 1 < acquisition["MAX_CAPTURED_REF_SYMREF_DEPTH"] - 1
            else "refs/heads/main"
        )
        positive_depth_refs["aliases/positive-%02d" % index] = (
            "ref: " + target + "\n"
        ).encode("ascii")
    positive_depth = captured(
        head=b"ref: refs/aliases/positive-00\n",
        loose=positive_depth_refs,
    )
    assert acquisition["parse_captured_git_ref_state"](positive_depth)["head_oid"] == oid_head
    depth_refs = {"heads/main": (oid_head + "\n").encode("ascii")}
    for index in range(acquisition["MAX_CAPTURED_REF_SYMREF_DEPTH"]):
        target = (
            "refs/aliases/depth-%02d" % (index + 1)
            if index + 1 < acquisition["MAX_CAPTURED_REF_SYMREF_DEPTH"]
            else "refs/heads/main"
        )
        depth_refs["aliases/depth-%02d" % index] = ("ref: " + target + "\n").encode("ascii")
    depth = captured(
        head=b"ref: refs/aliases/depth-00\n",
        loose=depth_refs,
    )
    expect_error(
        "captured symref depth",
        lambda: acquisition["parse_captured_git_ref_state"](depth),
        "GIT_CAPTURE_HEAD_REF_DEPTH",
    )

    malformed_states = (
        captured(head=(("0" * 40) + "\n").encode("ascii")),
        captured(loose={"heads/main": (("A" * 40) + "\n").encode("ascii")}),
        captured(loose={"heads/main": (oid_head + "\nextra\n").encode("ascii")}),
        captured(loose={"bad..name/value": (oid_head + "\n").encode("ascii")}),
        captured(
            loose={
                "heads/main": (oid_head + "\n").encode("ascii"),
                "tags/zero": (("0" * 40) + "\n").encode("ascii"),
            }
        ),
        captured(
            packed=(("8" * 64) + " refs/tags/mixed-width\n").encode("ascii"),
        ),
    )
    for index, hostile in enumerate(malformed_states):
        expect_error(
            "captured malformed or mixed ref %d" % index,
            lambda value=hostile: acquisition["parse_captured_git_ref_state"](value),
        )

    hostile_packed = (
        ("^" + oid_peeled + "\n").encode("ascii"),
        ("# unrelated comment\n" + oid_packed + " refs/tags/one\n").encode("ascii"),
        (
            "# pack-refs with: sorted unknown\n"
            + oid_packed + " refs/tags/one\n"
        ).encode("ascii"),
        (
            "# pack-refs with: sorted\n"
            + oid_packed + " refs/tags/two\n"
            + oid_peeled + " refs/tags/one\n"
        ).encode("ascii"),
        (
            oid_packed + " refs/tags/one\n"
            + oid_peeled + " refs/tags/one\n"
        ).encode("ascii"),
        (("0" * 40) + " refs/tags/zero\n").encode("ascii"),
        (
            oid_packed + " refs/tags/one\n"
            "^" + oid_peeled + "\n"
            "^" + ("8" * 40) + "\n"
        ).encode("ascii"),
        (
            oid_packed + " refs/tags/one\n"
            "# intervening comment\n"
            "^" + oid_peeled + "\n"
        ).encode("ascii"),
        (oid_packed + " refs/tags/one\n^" + ("0" * 40) + "\n").encode("ascii"),
        (oid_packed + " refs/tags/one\n^" + ("8" * 64) + "\n").encode("ascii"),
        (oid_packed + " refs/tags/one").encode("ascii"),
    )
    for index, packed in enumerate(hostile_packed):
        expect_error(
            "captured hostile packed peeled %d" % index,
            lambda value=packed: acquisition["parse_captured_git_ref_state"](
                captured(packed=value)
            ),
        )

    hostile_outputs = (
        canonical_output[:-1],
        canonical_output + canonical_output.splitlines(keepends=True)[0],
        canonical_output.replace((oid_head + " ").encode("ascii"), (("0" * 40) + " ").encode("ascii"), 1),
        (("8" * 64) + " refs/heads/main\n").encode("ascii"),
        (oid_head + "  refs/heads/main\n").encode("ascii"),
        b"not-ascii-\xff refs/heads/main\n",
    )
    for index, output in enumerate(hostile_outputs):
        expect_error(
            "for-each-ref hostile output %d" % index,
            lambda value=output: acquisition["parse_git_for_each_ref_output"](value, 40),
        )

    original_entry_limit = acquisition["MAX_GIT_ADAPTER_ENTRIES"]
    try:
        acquisition["MAX_GIT_ADAPTER_ENTRIES"] = 3
        expect_error(
            "captured effective ref count bound",
            lambda: acquisition["parse_captured_git_ref_state"](
                captured(
                    loose={
                        "heads/main": (oid_head + "\n").encode("ascii"),
                        "foo": (oid_head + "\n").encode("ascii"),
                        "stash": (oid_head + "\n").encode("ascii"),
                        "tags/fourth": (oid_head + "\n").encode("ascii"),
                    }
                )
            ),
            "GIT_CAPTURE_REF_LIMIT",
        )
    finally:
        acquisition["MAX_GIT_ADAPTER_ENTRIES"] = original_entry_limit

    with tempfile.TemporaryDirectory(
        prefix="gov01-ref-tree-count-",
        dir="/private/tmp",
    ) as ref_tree_temporary:
        ref_tree = pathlib.Path(ref_tree_temporary)
        nested = ref_tree / "nested"
        nested.mkdir(mode=0o700)
        write_bytes(ref_tree / "root-ref", (oid_head + "\n").encode("ascii"), 0o600)
        write_bytes(nested / "child-ref", (oid_head + "\n").encode("ascii"), 0o600)
        _raw_tree, tree_observation = acquisition["capture_git_source_tree"](
            str(ref_tree),
            "GIT_SOURCE_REF_COUNT_FIXTURE",
            required=True,
        )
        assert tree_observation["entry_count"] == 4
        assert tree_observation["directory_count"] == 2
        assert tree_observation["file_count"] == 2
        try:
            acquisition["MAX_GIT_ADAPTER_ENTRIES"] = 3
            expect_error(
                "captured ref tree entry and directory bound",
                lambda: acquisition["capture_git_source_tree"](
                    str(ref_tree),
                    "GIT_SOURCE_REF_COUNT_FIXTURE",
                    required=True,
                ),
                "GIT_SOURCE_REF_COUNT_FIXTURE_ENTRY_LIMIT",
            )
        finally:
            acquisition["MAX_GIT_ADAPTER_ENTRIES"] = original_entry_limit

    git_binary = "/fixture/git"
    repo_root = "/fixture/repo"
    exact_tail = [
        "for-each-ref",
        "--sort=refname",
        "--format=%(objectname) %(refname)",
        "refs",
    ]
    exact_argv = acquisition["git_hardened_child_argv"](
        git_binary,
        repo_root,
        ".",
        exact_tail,
    )
    receipt = acquisition["require_git_child_template_match"](
        role="git-read-only-evidence",
        argv=exact_argv,
        environment=acquisition["git_env"](),
        git_binary=git_binary,
        repo_root=repo_root,
        adapter_git_dir=".",
        live_objects=None,
        stdin_bytes=None,
    )
    assert receipt == (
        "git-read-only-evidence",
        tuple(acquisition["git_child_argv_template_prefix_v2"]() + exact_tail),
    )
    for hostile_tail in (exact_tail[:-1], exact_tail + ["refs/heads"]):
        expect_error(
            "for-each-ref argv insertion or deletion",
            lambda value=hostile_tail: acquisition["require_git_child_template_match"](
                role="git-read-only-evidence",
                argv=acquisition["git_hardened_child_argv"](
                    git_binary,
                    repo_root,
                    ".",
                    value,
                ),
                environment=acquisition["git_env"](),
                git_binary=git_binary,
                repo_root=repo_root,
                adapter_git_dir=".",
                live_objects=None,
                stdin_bytes=None,
            ),
            "GIT_FINAL_ARGV",
        )
    read_templates = acquisition["git_read_only_argv_templates_v2"]()
    assert sum(
        template[-4:] == exact_tail for template in read_templates
    ) == 1
    assert all("show" + "-ref" not in template for template in read_templates)
    report["captured_ref_strict_resolution_and_output_equality"] = "PASS"
    report["captured_ref_entry_directory_and_effective_count_bounds"] = "PASS"
    report["for_each_ref_exact_argv_insertion_deletion"] = "PASS"


def run_verify_pack_parser_fixtures(acquisition, report):
    """Exercise the strict verify-pack grammar without touching live Git state."""

    def replace_once(raw, old, new):
        if raw.count(old) != 1:
            raise AssertionError("verify-pack fixture replacement is not unique")
        return raw.replace(old, new, 1)

    def object_ids(oid_length):
        return {
            "commit": "1" * oid_length,
            "tree": "2" * oid_length,
            "base": "3" * oid_length,
            "delta_one": "4" * oid_length,
            "delta_two": "5" * oid_length,
        }

    def record(oid, object_type, size, packed_size, offset, depth=None, base=None):
        padding = " " if object_type == "commit" else "   "
        line = "%s %s%s%s %s %s" % (
            oid,
            object_type,
            padding,
            size,
            packed_size,
            offset,
        )
        if depth is not None or base is not None:
            if depth is None or base is None:
                raise AssertionError("incomplete verify-pack delta fixture")
            line += " %s %s" % (depth, base)
        return line

    def positive_fixture(oid_length):
        oids = object_ids(oid_length)
        pack_name = "a" * oid_length
        pack_path = "objects/pack/pack-%s.pack" % pack_name
        expected_types = {
            oids["commit"]: "commit",
            oids["tree"]: "tree",
            oids["base"]: "blob",
            oids["delta_one"]: "blob",
            oids["delta_two"]: "blob",
        }
        records = [
            record(oids["commit"], "commit", "241", "160", "12"),
            record(oids["tree"], "tree", "107", "98", "172"),
            record(oids["base"], "blob", "131072", "81200", "270"),
            record(
                oids["delta_one"],
                "blob",
                "131072",
                "37",
                "81470",
                "1",
                oids["base"],
            ),
            record(
                oids["delta_two"],
                "blob",
                "131072",
                "41",
                "81507",
                "2",
                oids["delta_one"],
            ),
        ]
        lines = records + [
            "non delta: 3 objects",
            "chain length = 1: 1 object",
            "chain length = 2: 1 object",
            pack_path + ": ok",
        ]
        return ("\n".join(lines) + "\n").encode("ascii"), expected_types, pack_path, oids, records

    positives = {}
    for oid_length, object_format in ((40, "sha1"), (64, "sha256")):
        raw, expected_types, pack_path, oids, records = positive_fixture(oid_length)
        acquisition["verify_pack_object_set"](raw, expected_types, pack_path)
        positives[object_format] = (raw, expected_types, pack_path, oids, records)

    raw, expected_types, pack_path, oids, records = positives["sha1"]
    newline = b"\n"
    commit_line = records[0].encode("ascii")
    tree_line = records[1].encode("ascii")
    base_line = records[2].encode("ascii")
    delta_one_line = records[3].encode("ascii")
    delta_two_line = records[4].encode("ascii")
    non_delta = b"non delta: 3 objects"
    chain_one = b"chain length = 1: 1 object"
    chain_two = b"chain length = 2: 1 object"
    ok_line = (pack_path + ": ok").encode("ascii")

    hostile_raw = [
        ("leading record space", b" " + raw),
        ("trailing record space", replace_once(raw, commit_line + newline, commit_line + b" " + newline)),
        ("commit padding widened", replace_once(raw, b" commit ", b" commit  ")),
        ("tree padding narrowed", replace_once(raw, b" tree   ", b" tree  ")),
        (
            "record tab",
            replace_once(
                raw,
                oids["base"].encode("ascii") + b" blob   131072",
                oids["base"].encode("ascii") + b" blob\t  131072",
            ),
        ),
        ("record CRLF", raw.replace(newline, b"\r\n")),
        ("UTF-8 BOM", b"\xef\xbb\xbf" + raw),
        ("embedded NUL", replace_once(raw, commit_line + newline, commit_line + b"\x00" + newline)),
        ("missing final LF", raw[:-1]),
        ("blank line", replace_once(raw, non_delta + newline, newline + non_delta + newline)),
        ("invalid UTF-8", b"\xff" + raw),
        ("numeric leading zero", replace_once(raw, b"commit 241", b"commit 0241")),
        ("numeric plus sign", replace_once(raw, b"commit 241", b"commit +241")),
        ("numeric negative", replace_once(raw, b"commit 241", b"commit -241")),
        ("numeric nondigit", replace_once(raw, b"commit 241", b"commit 24x")),
        ("numeric unbounded", replace_once(raw, b"commit 241", b"commit " + (b"9" * 80))),
        ("packed size zero", replace_once(raw, b"241 160 12", b"241 0 12")),
        ("physical offset gap", replace_once(raw, b"107 98 172", b"107 98 173")),
        (
            "delta depth zero",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 0 " + oids["base"].encode("ascii"),
            ),
        ),
        ("OID uppercase", replace_once(raw, oids["commit"].encode("ascii"), ("A" * 40).encode("ascii"))),
        ("OID short", replace_once(raw, oids["commit"].encode("ascii"), oids["commit"][:-1].encode("ascii"))),
        ("unexpected OID", replace_once(raw, oids["commit"].encode("ascii"), ("6" * 40).encode("ascii"))),
        ("unknown type", replace_once(raw, b"commit 241", b"tag    241")),
        (
            "incomplete delta fields",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 1",
            ),
        ),
        (
            "base OID lexical",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 1 " + (b"g" * 40),
            ),
        ),
        (
            "missing delta base",
            replace_once(
                raw,
                oids["base"].encode("ascii") + newline,
                ("6" * 40).encode("ascii") + newline,
            ),
        ),
        (
            "self delta base",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 1 " + oids["delta_one"].encode("ascii"),
            ),
        ),
        (
            "wrong-type delta base",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 1 " + oids["tree"].encode("ascii"),
            ),
        ),
        (
            "wrong delta depth",
            replace_once(
                raw,
                b" 1 " + oids["base"].encode("ascii"),
                b" 2 " + oids["base"].encode("ascii"),
            ),
        ),
        (
            "skipped delta ancestor",
            replace_once(
                raw,
                b" 2 " + oids["delta_one"].encode("ascii"),
                b" 2 " + oids["base"].encode("ascii"),
            ),
        ),
        ("non-delta count", replace_once(raw, non_delta, b"non delta: 4 objects")),
        ("non-delta plural", replace_once(raw, non_delta, b"non delta: 3 object")),
        ("missing non-delta", replace_once(raw, non_delta + newline, b"")),
        ("duplicate non-delta", replace_once(raw, non_delta + newline, non_delta + newline + non_delta + newline)),
        ("non-delta after chain", replace_once(raw, non_delta + newline + chain_one, chain_one + newline + non_delta)),
        ("chain count", replace_once(raw, chain_one, b"chain length = 1: 2 objects")),
        ("chain singular", replace_once(raw, chain_one, b"chain length = 1: 1 objects")),
        ("missing chain", replace_once(raw, chain_one + newline, b"")),
        ("duplicate chain", replace_once(raw, chain_one + newline, chain_one + newline + chain_one + newline)),
        ("chain order", replace_once(raw, chain_one + newline + chain_two, chain_two + newline + chain_one)),
        ("unexpected chain depth", replace_once(raw, chain_two, b"chain length = 3: 1 object")),
        ("wrong ok path", replace_once(raw, ok_line, b"objects/pack/pack-" + (b"b" * 40) + b".pack: ok")),
        ("missing ok", replace_once(raw, ok_line + newline, b"")),
        ("duplicate ok", replace_once(raw, ok_line + newline, ok_line + newline + ok_line + newline)),
        ("ok before summaries", replace_once(raw, non_delta + newline, ok_line + newline + non_delta + newline)),
        ("trailing summary text", raw + b"unexpected\n"),
        ("duplicate record", replace_once(raw, tree_line + newline, tree_line + newline + tree_line + newline)),
    ]
    hostile_code_groups = {
        "GIT_OBJECT_PACK_VERIFY_ENCODING": (
            "record CRLF",
            "UTF-8 BOM",
            "embedded NUL",
            "missing final LF",
            "blank line",
            "invalid UTF-8",
        ),
        "GIT_OBJECT_PACK_VERIFY_RECORD": (
            "leading record space",
            "trailing record space",
            "commit padding widened",
            "tree padding narrowed",
            "OID uppercase",
            "OID short",
            "duplicate record",
            "incomplete delta fields",
            "physical offset gap",
        ),
        "GIT_OBJECT_PACK_VERIFY_TYPE": (
            "record tab",
            "unknown type",
        ),
        "GIT_OBJECT_PACK_VERIFY_NUMERIC": (
            "numeric leading zero",
            "numeric plus sign",
            "numeric negative",
            "numeric nondigit",
            "numeric unbounded",
            "packed size zero",
            "delta depth zero",
        ),
        "GIT_OBJECT_PACK_VERIFY_SET": ("unexpected OID",),
        "GIT_OBJECT_PACK_VERIFY_BASE": (
            "missing delta base",
            "base OID lexical",
            "self delta base",
            "wrong-type delta base",
        ),
        "GIT_OBJECT_PACK_VERIFY_GRAPH": (
            "wrong delta depth",
            "skipped delta ancestor",
        ),
        "GIT_OBJECT_PACK_VERIFY_SUMMARY": (
            "non-delta count",
            "non-delta plural",
            "missing non-delta",
            "duplicate non-delta",
            "non-delta after chain",
            "chain count",
            "chain singular",
            "missing chain",
            "duplicate chain",
            "chain order",
            "unexpected chain depth",
            "wrong ok path",
            "missing ok",
            "duplicate ok",
            "ok before summaries",
            "trailing summary text",
        ),
    }
    hostile_codes = {
        label: code
        for code, labels in hostile_code_groups.items()
        for label in labels
    }
    if set(hostile_codes) != {label for label, _raw in hostile_raw}:
        raise AssertionError("verify-pack hostile error-code partition is not exact")
    for label, hostile in hostile_raw:
        expect_error(
            "verify-pack " + label,
            lambda value=hostile: acquisition["verify_pack_object_set"](
                value,
                expected_types,
                pack_path,
            ),
            hostile_codes[label],
        )

    mismatched_types = dict(expected_types)
    mismatched_types[oids["base"]] = "tree"
    expect_error(
        "verify-pack expected type equality",
        lambda: acquisition["verify_pack_object_set"](raw, mismatched_types, pack_path),
        "GIT_OBJECT_PACK_VERIFY_TYPE",
    )
    different_expected = dict(expected_types)
    different_expected.pop(oids["delta_two"])
    different_expected["6" * 40] = "blob"
    expect_error(
        "verify-pack expected set equality",
        lambda: acquisition["verify_pack_object_set"](
            raw,
            different_expected,
            pack_path,
        ),
        "GIT_OBJECT_PACK_VERIFY_SET",
    )

    cycle_records = [
        records[0],
        records[1],
        records[2],
        record(
            oids["delta_one"],
            "blob",
            "131072",
            "37",
            "81470",
            "1",
            oids["delta_two"],
        ),
        record(
            oids["delta_two"],
            "blob",
            "131072",
            "41",
            "81507",
            "1",
            oids["delta_one"],
        ),
    ]
    cycle_raw = (
        "\n".join(
            cycle_records
            + [
                "non delta: 3 objects",
                "chain length = 1: 2 objects",
                pack_path + ": ok",
            ]
        )
        + "\n"
    ).encode("ascii")
    expect_error(
        "verify-pack delta cycle",
        lambda: acquisition["verify_pack_object_set"](cycle_raw, expected_types, pack_path),
        "GIT_OBJECT_PACK_VERIFY_GRAPH",
    )

    report["verify_pack_sha1_sha256_fixed_padding_delta_graph"] = "PASS"
    report["verify_pack_hostile_record_numeric_oid_type_base_summary_matrix"] = {
        "case_count": len(hostile_raw) + 3,
        "result": "PASS",
    }

    # Exercise the real Apple Git formatter with deliberately similar blobs so
    # at least one native OFS/REF delta record is fed to the production parser.
    git_binary = "/Library/Developer/CommandLineTools/usr/bin/git"
    if platform.system() != "Darwin" or not os.path.isfile(git_binary):
        raise AssertionError("Apple Git verify-pack fixture unavailable")
    with tempfile.TemporaryDirectory(
        prefix="gov01-verify-pack-native-",
        dir="/private/tmp",
    ) as temporary:
        repo = pathlib.Path(temporary) / "repo"
        repo.mkdir(mode=0o700)

        def git_capture(*arguments):
            completed = subprocess.run(
                [git_binary] + list(arguments),
                cwd=str(repo),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                env={
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                    "LC_ALL": "C",
                    "LANG": "C",
                },
            )
            if completed.returncode != 0:
                raise AssertionError("native verify-pack fixture Git command failed")
            return completed.stdout

        run_checked([git_binary, "init", "-q"], repo)
        run_checked([git_binary, "config", "user.name", "fixture"], repo)
        run_checked([git_binary, "config", "user.email", "fixture@example.invalid"], repo)
        common = b"".join(
            hashlib.sha256(("block-%05d" % index).encode("ascii")).digest()
            for index in range(4096)
        )
        for index in range(16):
            body = bytearray(common)
            for mutation in range(8):
                offset = ((index + 1) * 7919 + mutation * 104729) % (len(body) - 32)
                body[offset : offset + 32] = hashlib.sha256(
                    ("variant-%02d-%02d" % (index, mutation)).encode("ascii")
                ).digest()
            write_bytes(repo / ("similar-%02d.bin" % index), bytes(body), 0o600)
        run_checked([git_binary, "add", "--all"], repo)
        run_checked([git_binary, "commit", "-q", "-m", "native verify-pack fixture"], repo)
        run_checked(
            [git_binary, "repack", "-a", "-d", "-f", "--window=250", "--depth=50"],
            repo,
        )
        pack_root = repo / ".git/objects/pack"
        index_paths = sorted(pack_root.glob("pack-*.idx"))
        pack_paths = sorted(pack_root.glob("pack-*.pack"))
        if len(index_paths) != 1 or len(pack_paths) != 1:
            raise AssertionError("native verify-pack fixture pack set is not exact")
        index_relative = os.path.relpath(index_paths[0], repo)
        pack_relative = os.path.relpath(pack_paths[0], repo)
        native_raw = git_capture("verify-pack", "-v", index_relative)
        object_rows = git_capture(
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype)",
        )
        native_types = {}
        for row in object_rows.decode("ascii", "strict").splitlines():
            fields = row.split(" ")
            if (
                len(fields) != 2
                or len(fields[0]) != 40
                or any(character not in "0123456789abcdef" for character in fields[0])
                or fields[1] not in ("commit", "tree", "blob")
                or fields[0] in native_types
            ):
                raise AssertionError("native verify-pack independent object inventory malformed")
            native_types[fields[0]] = fields[1]
        native_lines = native_raw.decode("ascii", "strict").splitlines()
        native_delta_count = sum(
            1
            for line in native_lines
            if len(line.split()) == 7
            and len(line.split()[0]) == 40
            and line.split()[1] in ("commit", "tree", "blob")
        )
        if native_delta_count < 1:
            raise AssertionError("native Apple Git did not produce a delta record")
        if not any(
            (" tree   " in line or " blob   " in line)
            for line in native_lines
            if len(line.split()) in (5, 7)
        ):
            raise AssertionError("native Apple Git fixed-width padding was not observed")
        acquisition["verify_pack_object_set"](native_raw, native_types, pack_relative)
        report["verify_pack_native_apple_git_delta_and_padding"] = {
            "delta_record_minimum": 1,
            "result": "PASS",
        }


def run_git_metadata_adapter_hostile_fixtures(acquisition, report):
    """Run only synthetic Git-adapter tests; never call census/verify/acquire."""

    prefix = acquisition["GIT_ADAPTER_TEMP_PREFIX"]

    def adapter_roots():
        return {str(path) for path in pathlib.Path("/private/tmp").glob(prefix + "*")}

    # This probe is deliberately first.  Nested Codex sandbox refusal is a
    # structured non-PASS mode; an elevated run executes the matrix below with
    # the production inner sandbox enabled.
    true_binary = "/usr/bin/true"
    old_true = acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].get(true_binary)
    acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][true_binary] = acquisition[
        "hash_regular_absolute"
    ](true_binary, "ADAPTER_SANDBOX_PROBE")["sha256"]
    try:
        try:
            acquisition["run_process"](
                [true_binary], acquisition["git_env"](), 4096, "ADAPTER_SANDBOX_PROBE",
                sandbox_profile=(
                    b"(version 1)\n"
                    b"(deny default)\n"
                    b"(import \"system.sb\")\n"
                    b"(deny network*)\n"
                    b"(allow process-exec (literal \"/usr/bin/true\"))\n"
                    b"(allow process-fork)\n"
                    b"(allow signal (target self))\n"
                    b"(allow file-read* file-test-existence (literal \"/usr/bin/true\"))\n"
                ),
            )
        except acquisition["ContractError"] as error:
            if error.public_code != "ADAPTER_SANDBOX_PROBE_SANDBOX_INIT":
                raise
            sandbox_mode = "nested-host-sandbox-refused-second-sandbox-fail-closed"
        else:
            sandbox_mode = "host-sandbox-enforced-positive"
    finally:
        if old_true is None:
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].pop(true_binary, None)
        else:
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][true_binary] = old_true
    report["git_metadata_adapter_inner_sandbox_matrix"] = sandbox_mode

    if sandbox_mode != "host-sandbox-enforced-positive":
        report["git_metadata_adapter_private_tmp_write_sandbox_capability"] = sandbox_mode
    else:
        # A real native child executes each syscall.  This is not a profile
        # string inspection: success means the kernel sandbox returned
        # EPERM/EACCES and the parent independently observed no mutation.
        with tempfile.TemporaryDirectory(
            prefix="gov01-adapter-sandbox-probe-", dir="/private/tmp"
        ) as probe_temporary:
            probe_root = pathlib.Path(probe_temporary)
            probe_developer_root = probe_root / "developer"
            probe_developer_root.mkdir(mode=0o700)
            probe_source = probe_developer_root / "probe.c"
            probe_binary = probe_developer_root / "probe"
            write_bytes(
                probe_source,
                b"""#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int denied(int result) {
  if (result == -1 && (errno == EPERM || errno == EACCES)) return 0;
  return result == 0 ? 40 : 41;
}
int main(int argc, char **argv) {
  if (argc < 3) return 50;
  if (strcmp(argv[1], "touch-ok") == 0) {
    int fd = open(argv[2], O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0 || close(fd) != 0) return 51;
    return 0;
  }
  errno = 0;
  if (strcmp(argv[1], "mkdir-denied") == 0)
    return denied(mkdir(argv[2], 0700));
  if (strcmp(argv[1], "rmdir-denied") == 0)
    return denied(rmdir(argv[2]));
  if (strcmp(argv[1], "rename-denied") == 0 && argc == 4)
    return denied(rename(argv[2], argv[3]));
  errno = 0;
  if (strcmp(argv[1], "existence-absent") == 0) {
    int result = access(argv[2], F_OK);
    return result == -1 && errno == ENOENT ? 0 : 53;
  }
  if (strcmp(argv[1], "existence-present") == 0)
    return access(argv[2], F_OK) == 0 ? 0 : 54;
  if (strcmp(argv[1], "existence-denied") == 0)
    return denied(access(argv[2], F_OK));
  if (strcmp(argv[1], "metadata-denied") == 0) {
    struct stat metadata;
    return denied(lstat(argv[2], &metadata));
  }
  if (strcmp(argv[1], "read-zero-bytes") == 0) {
    unsigned char byte = 0;
    int fd = open(argv[2], O_RDONLY);
    if (fd == -1) return denied(fd);
    errno = 0;
    ssize_t count = read(fd, &byte, 1);
    int read_errno = errno;
    if (close(fd) != 0) return 55;
    if (count == -1 && (read_errno == EPERM || read_errno == EACCES)) return 0;
    return 56;
  }
  if (strcmp(argv[1], "read-one-byte") == 0) {
    unsigned char byte = 0;
    int fd = open(argv[2], O_RDONLY);
    if (fd == -1) return 57;
    ssize_t count = read(fd, &byte, 1);
    if (close(fd) != 0) return 58;
    return count == 1 ? 0 : 59;
  }
  return 52;
}
""",
                0o600,
            )
            compiled = subprocess.run(
                [
                    "/usr/bin/clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-Os", str(probe_source), "-o", str(probe_binary),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
            )
            if compiled.returncode != 0:
                raise AssertionError("native sandbox write probe compilation failed")
            os.chmod(probe_binary, 0o500)
            adapter_root = pathlib.Path(
                tempfile.mkdtemp(prefix=prefix, dir="/private/tmp")
            )
            empty_adapter_root = pathlib.Path(
                tempfile.mkdtemp(prefix=prefix, dir="/private/tmp")
            )
            sibling = pathlib.Path(str(adapter_root) + ".sibling")
            moved = pathlib.Path(str(adapter_root) + ".moved")
            adapter_git = adapter_root / "git"
            adapter_pack = adapter_git / "objects/pack"
            adapter_pack.mkdir(parents=True, mode=0o700)
            probe_repo = probe_root / "repo"
            live_git = probe_root / "live-git"
            live_common = probe_root / "live-common"
            live_objects = live_common / "objects"
            for directory in (probe_repo, live_git, live_objects):
                directory.mkdir(parents=True, mode=0o700)
            probe_path = str(probe_binary)
            old_probe_hash = acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].get(probe_path)
            old_probe_developer = acquisition["_GIT_DEVELOPER_ROOTS"].get(probe_path)
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][probe_path] = acquisition[
                "hash_regular_absolute"
            ](probe_path, "ADAPTER_SANDBOX_WRITE_PROBE")["sha256"]
            acquisition["_GIT_DEVELOPER_ROOTS"][probe_path] = str(probe_developer_root)
            git_fd = os.open(adapter_git, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                write_profile = acquisition["git_object_bootstrap_sandbox_profile"](
                    probe_path,
                    str(probe_repo),
                    str(probe_developer_root),
                    str(adapter_root),
                    ".",
                    str(live_git),
                    str(live_common),
                    str(live_objects),
                    False,
                    True,
                    (),
                    (),
                )
                allowed_file = adapter_pack / "allowed"
                acquisition["run_process"](
                    [probe_path, "touch-ok", str(allowed_file)],
                    acquisition["git_env"](),
                    4096,
                    "ADAPTER_SANDBOX_WRITE_ALLOWED",
                    sandbox_profile=write_profile,
                    working_directory_fd=git_fd,
                )
                assert allowed_file.is_file()
                acquisition["run_process"](
                    [probe_path, "mkdir-denied", str(sibling)],
                    acquisition["git_env"](),
                    4096,
                    "ADAPTER_SANDBOX_PARENT_CREATE",
                    sandbox_profile=write_profile,
                    working_directory_fd=git_fd,
                )
                acquisition["run_process"](
                    [probe_path, "rename-denied", str(adapter_root), str(moved)],
                    acquisition["git_env"](),
                    4096,
                    "ADAPTER_SANDBOX_ROOT_RENAME",
                    sandbox_profile=write_profile,
                    working_directory_fd=git_fd,
                )
                empty_profile = acquisition["git_object_bootstrap_sandbox_profile"](
                    probe_path,
                    str(probe_repo),
                    str(probe_developer_root),
                    str(empty_adapter_root),
                    ".",
                    str(live_git),
                    str(live_common),
                    str(live_objects),
                    False,
                    True,
                    (),
                    (),
                )
                acquisition["run_process"](
                    [probe_path, "rmdir-denied", str(empty_adapter_root)],
                    acquisition["git_env"](),
                    4096,
                    "ADAPTER_SANDBOX_ROOT_UNLINK",
                    sandbox_profile=empty_profile,
                    working_directory_fd=git_fd,
                )
                assert (
                    not sibling.exists()
                    and not moved.exists()
                    and adapter_root.is_dir()
                    and empty_adapter_root.is_dir()
                )

                # A2 grants one post-deny existence probe for exactly the
                # prevalidated-absent common object-store alternates path.  It
                # never grants metadata or data reads, including when a race
                # replaces that pathname with a regular file, hard link or
                # symlink to an otherwise readable object.
                object_info = live_objects / "info"
                object_info.mkdir(mode=0o700)
                selected_oid = "a" * 40
                selected_loose = live_objects / selected_oid[:2] / selected_oid[2:]
                selected_loose.parent.mkdir(mode=0o700)
                selected_loose_raw = b"separately allowed object bytes\n"
                write_bytes(selected_loose, selected_loose_raw, 0o600)
                selected_loose_link_count = selected_loose.stat().st_nlink
                alternates = object_info / "alternates"
                http_alternates = object_info / "http-alternates"
                object_sentinel = object_info / "sentinel"
                grafts = live_common / "info/grafts"
                grafts.parent.mkdir(mode=0o700)
                write_bytes(http_alternates, b"https://invalid.example/objects\n", 0o600)
                write_bytes(object_sentinel, b"must remain unread\n", 0o600)
                write_bytes(grafts, b"0 0\n", 0o600)
                bridge_profile = acquisition["git_object_bootstrap_sandbox_profile"](
                    probe_path,
                    str(probe_repo),
                    str(probe_developer_root),
                    str(adapter_root),
                    ".",
                    str(live_git),
                    str(live_common),
                    str(live_objects),
                    True,
                    False,
                    (selected_oid,),
                    (),
                )
                bridge_profile_text = bridge_profile.decode("ascii")
                bridge_forms = sbpl_top_level_forms(bridge_profile_text)
                alternates_literal = '(literal "' + str(alternates) + '")'
                alternates_allow_forms = [
                    form
                    for form in bridge_forms
                    if form.lstrip().startswith("(allow ") and alternates_literal in form
                ]
                assert len(alternates_allow_forms) == 1
                assert " ".join(alternates_allow_forms[0].split()) == (
                    "(allow file-test-existence " + alternates_literal + ")"
                )
                alternate_form_index = bridge_forms.index(alternates_allow_forms[0])
                alternates_denies = [
                    index
                    for index, form in enumerate(bridge_forms)
                    if form.lstrip().startswith("(deny ") and alternates_literal in form
                ]
                object_info_subpath = '(subpath "' + str(object_info) + '")'
                object_info_denies = [
                    index
                    for index, form in enumerate(bridge_forms)
                    if form.lstrip().startswith("(deny ") and object_info_subpath in form
                ]
                assert alternates_denies and max(alternates_denies) < alternate_form_index
                assert object_info_denies and max(object_info_denies) < alternate_form_index
                for denied_path in (http_alternates, grafts, object_sentinel):
                    quoted_path = '"' + str(denied_path) + '"'
                    assert not any(
                        form.lstrip().startswith("(allow ") and quoted_path in form
                        for form in bridge_forms
                    )

                def native_probe(command, path, profile, label):
                    acquisition["run_process"](
                        [probe_path, command, str(path)],
                        acquisition["git_env"](),
                        4096,
                        label,
                        sandbox_profile=profile,
                        working_directory_fd=git_fd,
                    )

                native_probe(
                    "existence-absent",
                    alternates,
                    bridge_profile,
                    "ADAPTER_SANDBOX_ALTERNATES_ABSENT",
                )
                native_probe(
                    "read-one-byte",
                    selected_loose,
                    bridge_profile,
                    "ADAPTER_SANDBOX_SELECTED_OBJECT_POSITIVE_CONTROL",
                )
                for denied_path, label in (
                    (http_alternates, "HTTP_ALTERNATES"),
                    (grafts, "GRAFTS"),
                    (object_sentinel, "OBJECT_INFO_SENTINEL"),
                ):
                    native_probe(
                        "existence-denied",
                        denied_path,
                        bridge_profile,
                        "ADAPTER_SANDBOX_" + label + "_EXISTENCE",
                    )
                    native_probe(
                        "metadata-denied",
                        denied_path,
                        bridge_profile,
                        "ADAPTER_SANDBOX_" + label + "_METADATA",
                    )
                    native_probe(
                        "read-zero-bytes",
                        denied_path,
                        bridge_profile,
                        "ADAPTER_SANDBOX_" + label + "_READ",
                    )

                for kind in ("regular", "hardlink", "symlink"):
                    if kind == "regular":
                        write_bytes(alternates, b"hostile regular bytes\n", 0o600)
                    elif kind == "hardlink":
                        os.link(selected_loose, alternates)
                    else:
                        os.symlink(str(selected_loose), str(alternates))
                    try:
                        native_probe(
                            "existence-denied" if kind == "symlink" else "existence-present",
                            alternates,
                            bridge_profile,
                            "ADAPTER_SANDBOX_ALTERNATES_" + kind.upper() + "_EXISTENCE",
                        )
                        native_probe(
                            "metadata-denied",
                            alternates,
                            bridge_profile,
                            "ADAPTER_SANDBOX_ALTERNATES_" + kind.upper() + "_METADATA",
                        )
                        native_probe(
                            "read-zero-bytes",
                            alternates,
                            bridge_profile,
                            "ADAPTER_SANDBOX_ALTERNATES_" + kind.upper() + "_READ",
                        )
                    finally:
                        alternates.unlink()
                assert selected_loose.read_bytes() == selected_loose_raw
                assert selected_loose.stat().st_nlink == selected_loose_link_count

                # Bridge-free children receive no alternates exception at all.
                bridge_free_profile = acquisition["git_object_bootstrap_sandbox_profile"](
                    probe_path,
                    str(probe_repo),
                    str(probe_developer_root),
                    str(adapter_root),
                    ".",
                    str(live_git),
                    str(live_common),
                    str(live_objects),
                    False,
                    False,
                    (),
                    (),
                )
                bridge_free_forms = sbpl_top_level_forms(bridge_free_profile.decode("ascii"))
                assert not any(
                    form.lstrip().startswith("(allow ") and alternates_literal in form
                    for form in bridge_free_forms
                )
                assert any(
                    form.lstrip().startswith("(deny ") and alternates_literal in form
                    for form in bridge_free_forms
                )
                native_probe(
                    "existence-denied",
                    alternates,
                    bridge_free_profile,
                    "ADAPTER_SANDBOX_BRIDGE_FREE_ALTERNATES",
                )

                # The permission follows the linked-worktree common object
                # store, never a per-worktree object path or an environment
                # override.
                linked_wrong_alternates = live_git / "objects/info/alternates"
                linked_wrong_alternates.parent.mkdir(parents=True, mode=0o700)
                write_bytes(linked_wrong_alternates, b"wrong object root\n", 0o600)
                linked_wrong_literal = '(literal "' + str(linked_wrong_alternates) + '")'
                assert not any(
                    form.lstrip().startswith("(allow ") and linked_wrong_literal in form
                    for form in bridge_forms
                )
                assert any(
                    form.lstrip().startswith("(deny ") and linked_wrong_literal in form
                    for form in bridge_forms
                )
                native_probe(
                    "existence-denied",
                    linked_wrong_alternates,
                    bridge_profile,
                    "ADAPTER_SANDBOX_LINKED_WRONG_ALTERNATES_EXISTENCE",
                )
                native_probe(
                    "read-zero-bytes",
                    linked_wrong_alternates,
                    bridge_profile,
                    "ADAPTER_SANDBOX_LINKED_WRONG_ALTERNATES_READ",
                )
                assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in acquisition["git_env"]()
                assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in acquisition["git_env"](
                    str(live_objects)
                )
            finally:
                os.close(git_fd)
                if old_probe_hash is None:
                    acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].pop(probe_path, None)
                else:
                    acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][probe_path] = old_probe_hash
                if old_probe_developer is None:
                    acquisition["_GIT_DEVELOPER_ROOTS"].pop(probe_path, None)
                else:
                    acquisition["_GIT_DEVELOPER_ROOTS"][probe_path] = old_probe_developer
                if moved.exists() and not adapter_root.exists():
                    os.rename(moved, adapter_root)
                if sibling.exists():
                    os.rmdir(sibling)
                if empty_adapter_root.exists():
                    os.rmdir(empty_adapter_root)
                allowed_file = adapter_pack / "allowed"
                if allowed_file.exists():
                    allowed_file.unlink()
                for directory in (adapter_pack, adapter_git / "objects", adapter_git, adapter_root):
                    if directory.exists():
                        os.rmdir(directory)
            report["git_metadata_adapter_private_tmp_write_sandbox_capability"] = "PASS"
            report["git_metadata_adapter_alternates_existence_only_profile_order"] = "PASS"
            report["git_metadata_adapter_alternates_native_zero_byte_matrix"] = "PASS"
            report["git_metadata_adapter_bridge_free_and_linked_object_scope"] = "PASS"

    executor_source = ACQ_PATH.read_text(encoding="utf-8")
    executor_tree = ast.parse(executor_source)
    for retired_field in (
        '"automatic_cleanup_authorized"',
        '"automatic_cleanup_allowed"',
        '"first_authorized_write"',
        '"receipt_before_any_authorized_write"',
        '"first_authorized_write_contract"',
    ):
        assert retired_field not in executor_source
    for current_field in (
        '"product_state_automatic_cleanup_authorized"',
        '"temporary_adapter_cleanup_required"',
        '"retained_product_state_automatic_cleanup_allowed"',
        '"first_authority_consuming_persistent_write"',
        '"receipt_before_first_authority_consuming_persistent_write"',
        '"first_authority_consuming_persistent_write_contract"',
    ):
        assert current_field in executor_source
    public_authority = acquisition["authority_projection"](False, False, "fixture-authority")
    assert public_authority == {
        "retry_authorized": False,
        "public_success_attestation_allowed": False,
        "product_state_automatic_cleanup_authorized": False,
        "temporary_adapter_cleanup_required": True,
        "openspec_execution_allowed": False,
        "openspec_scaffold_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "next_required_authority": "fixture-authority",
    }
    embedded = json.loads(acquisition["_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON"])
    synchronized_once = acquisition["synchronize_pending_template_git_adapter_v2"](
        copy.deepcopy(embedded)
    )
    synchronized_twice = acquisition["synchronize_pending_template_git_adapter_v2"](
        copy.deepcopy(synchronized_once)
    )
    assert embedded == synchronized_once == synchronized_twice
    bootstrap_profile_contract = acquisition[
        "GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V4"
    ]
    assert embedded["execution_plan"][
        "git_metadata_adapter_bootstrap_sandbox_profile"
    ] == bootstrap_profile_contract
    assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in embedded["execution_plan"][
        "environment_name_allowlist"
    ]
    assert all(
        "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in entry["environment_name_allowlist"]
        for entry in embedded["execution_plan"]["evidence_command_templates"]
    )
    assert synchronized_twice["mutation_scope"]["allowed_ephemeral_mutations"][0] == acquisition[
        "GIT_ADAPTER_EPHEMERAL_MUTATION_V3"
    ]
    assert sum(
        value.startswith(
            "before each Git child sequence create one unpredictable exact 0700 /private/tmp/"
        )
        for value in synchronized_twice["mutation_scope"]["allowed_ephemeral_mutations"]
    ) == 1
    stale_template = copy.deepcopy(embedded)
    stale_template["execution_plan"][
        "git_metadata_adapter_bootstrap_sandbox_profile"
    ] = "retired-bootstrap-sandbox-profile-v3"
    stale_template["mutation_scope"]["allowed_ephemeral_mutations"].insert(
        0,
        "before each Git child sequence create one unpredictable exact 0700 /private/tmp/"
        "retired-dead-branch",
    )
    stale_synchronized = acquisition["synchronize_pending_template_git_adapter_v2"](
        stale_template
    )
    assert stale_synchronized["execution_plan"][
        "git_metadata_adapter_bootstrap_sandbox_profile"
    ] == bootstrap_profile_contract
    assert stale_synchronized == acquisition[
        "synchronize_pending_template_git_adapter_v2"
    ](copy.deepcopy(stale_synchronized))
    assert sum(
        value.startswith(
            "before each Git child sequence create one unpredictable exact 0700 /private/tmp/"
        )
        for value in stale_synchronized["mutation_scope"]["allowed_ephemeral_mutations"]
    ) == 1
    bootstrap_profile_assignments = [
        node
        for node in executor_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V4"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    assert len(bootstrap_profile_assignments) == 1
    assert bootstrap_profile_assignments[0].value.value == bootstrap_profile_contract
    assert "GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V3" not in executor_source
    trust_boundary = acquisition["GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1"]
    host_assurance = acquisition["GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1"]
    cleanup_guarantee = acquisition["GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1"]
    assert trust_boundary == (
        "the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate "
        "other UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has "
        "exactly one owning process and compliant same-UID product processes never mutate another invocation's "
        "root; non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and "
        "out-of-process access to the 0600 private HMAC key are outside the supported threat model"
    )
    assert host_assurance == (
        "every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the "
        "private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact "
        "adapter entry, root and descendants for that invocation, while /private/tmp and sibling entries remain "
        "ambient host namespace; every product invocation creates one fresh unique adapter root; the process-wide "
        "non-reentrant scope and registry forbid interleaved adapter ownership within one process and do not claim "
        "cross-process exclusion"
    )
    assert cleanup_guarantee == (
        "under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable "
        "pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, "
        "post-removal absence, and zero pathname and registry residue; any observed root or Git identity drift, "
        "missing authorized pathname, cleanup error, or residue is terminal and quiescence must fail; preservation "
        "against a non-cooperating same-UID replacement at the final pathname-deletion linearization point is "
        "outside the supported guarantee"
    )
    assert embedded["execution_plan"]["git_metadata_adapter_trust_boundary"] == trust_boundary
    assert embedded["execution_plan"]["git_metadata_adapter_host_assurance"] == host_assurance
    assert embedded["mutation_scope"]["git_metadata_adapter_trust_boundary"] == trust_boundary
    assert embedded["mutation_scope"]["git_metadata_adapter_host_assurance"] == host_assurance
    assert embedded["mutation_scope"]["git_metadata_adapter_cleanup_guarantee"] == cleanup_guarantee
    assert embedded["failure_contract"]["git_metadata_adapter_cleanup_guarantee"] == cleanup_guarantee
    assert embedded["privacy"]["git_metadata_adapter_trust_boundary"] == trust_boundary
    runtime_assurance = acquisition["runtime_assurance_projection"]()
    assert runtime_assurance["git_metadata_adapter_trust_boundary"] == trust_boundary
    assert runtime_assurance["git_metadata_adapter_host_assurance"] == host_assurance
    assert set(embedded["approval_receipt_contract"]) == {
        "required_user_reference",
        "receipt_must_match_raw_envelope_bytes",
        "challenge_must_match",
        "receipt_before_first_authority_consuming_persistent_write",
        "first_authority_consuming_persistent_write",
        "authority_is_exact",
        "authority_expansion_allowed",
    }
    assert "first_authority_consuming_persistent_write" in embedded["private_state_authorization"]
    assert "_GIT_READ_BOUNDARIES" not in {
        node.id for node in ast.walk(executor_tree) if isinstance(node, ast.Name)
    }
    assert not any(
        "/dev/fd" in node.value
        for node in ast.walk(executor_tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    process_node = next(
        node for node in executor_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_process"
    )
    process_text = ast.unparse(process_node)
    assert "os.dup(working_directory_fd)" in process_text
    assert "stderr=subprocess.PIPE" in process_text
    assert "stderr=subprocess.DEVNULL" not in process_text
    assert "MAX_PROCESS_STDERR_BYTES" in process_text
    assert "label + '_STDERR'" in process_text
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == "drain_process_pipe"
        for node in process_node.body
    )
    child_boundary_node = next(
        node for node in process_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "initialize_child_boundary"
    )
    child_calls = [
        ast.unparse(node.func)
        for node in ast.walk(child_boundary_node)
        if isinstance(node, ast.Call)
    ]
    assert child_calls.index("os.fchdir") < child_calls.index("sandbox_library.sandbox_init")
    assert child_calls.index("os.close") < child_calls.index("sandbox_library.sandbox_init")
    for node in ast.walk(executor_tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("run_git", "safe_git_scalar")
        ):
            assert len(node.args) >= 3
            assert isinstance(node.args[2], ast.Name) and node.args[2].id == "boundary"
    templates = (
        acquisition["git_read_only_argv_templates_v2"]()
        + acquisition["git_adapter_bootstrap_argv_templates_v2"]()
    )
    assert all(template.count("--git-dir=.") == 1 and "-C" not in template for template in templates)
    report["git_metadata_adapter_ast_fd_and_template_boundary"] = "PASS"
    report["git_metadata_adapter_bootstrap_v4_raw_template_idempotence"] = "PASS"

    roots_before = adapter_roots()
    with tempfile.TemporaryDirectory(prefix="gov01-git-adapter-fixture-", dir="/private/tmp") as temporary:
        temporary_path = pathlib.Path(temporary)
        repo = temporary_path / "repo"
        repo.mkdir(mode=0o700)
        git_binary = "/Library/Developer/CommandLineTools/usr/bin/git"

        def git_output(*arguments):
            completed = subprocess.run(
                [git_binary] + list(arguments), cwd=str(repo), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
            )
            if completed.returncode != 0:
                raise AssertionError("adapter fixture Git setup failed")
            return completed.stdout

        run_checked([git_binary, "init", "-q"], repo)
        run_checked([git_binary, "config", "user.name", "fixture"], repo)
        run_checked([git_binary, "config", "user.email", "fixture@example.invalid"], repo)
        for index, (_role, relative) in enumerate(acquisition["PENDING_STATIC_ARTIFACT_SPECS"]):
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            write_bytes(target, ("approved-%02d\n" % index).encode("ascii"), 0o600)
        unrelated = repo / "unrelated/tracked-body.txt"
        unrelated.parent.mkdir(parents=True)
        write_bytes(unrelated, b"unrelated tracked body\n", 0o600)
        run_checked([git_binary, "add", "--all"], repo)
        run_checked(
            [
                git_binary,
                "update-index",
                "--add",
                "--cacheinfo",
                "160000," + ("1" * 40) + "," + acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"],
            ],
            repo,
        )
        run_checked([git_binary, "commit", "-q", "-m", "adapter fixture"], repo)
        head_oid = git_output("rev-parse", "HEAD").strip().decode("ascii")
        head_ref = git_output("symbolic-ref", "HEAD").strip().decode("ascii")
        unrelated_oid = git_output("rev-parse", "HEAD:unrelated/tracked-body.txt").strip().decode("ascii")
        loose_unmaterialized_oid = "2" * len(head_oid)
        packed_unmaterialized_oid = "3" * len(head_oid)
        packed_shadowed_oid = "4" * len(head_oid)
        loose_override_oid = "5" * len(head_oid)
        packed_peeled_oid = "6" * len(head_oid)
        hostile_ref_root = repo / ".git/refs/gov01"
        hostile_ref_root.mkdir(parents=True, mode=0o700)
        write_bytes(
            hostile_ref_root / "loose-unmaterialized",
            (loose_unmaterialized_oid + "\n").encode("ascii"),
            0o600,
        )
        write_bytes(
            hostile_ref_root / "override",
            (loose_override_oid + "\n").encode("ascii"),
            0o600,
        )
        write_bytes(
            hostile_ref_root / "symalias",
            ("ref: " + head_ref + "\n").encode("ascii"),
            0o600,
        )
        write_bytes(
            repo / ".git/packed-refs",
            (
                "# pack-refs with: peeled fully-peeled sorted\n"
                + packed_shadowed_oid + " refs/gov01/override\n"
                + packed_unmaterialized_oid + " refs/gov01/packed-unmaterialized\n"
                + "^" + packed_peeled_oid + "\n"
            ).encode("ascii"),
            0o600,
        )
        key = b"g" * 32
        challenge = "GOV01-SA-20260821-" + ("a" * 64)
        generation = "GOV01-GEN-20260821-" + ("b" * 64)
        stage = ".gov01-toolchain-stage-" + challenge
        envelope_relative = (
            acquisition["CONTROL_PREFIX"] + acquisition["PENDING_ENVELOPE_BASENAME_PREFIX"]
            + generation + ".json"
        )
        old_hash = acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].get(git_binary)
        old_developer = acquisition["_GIT_DEVELOPER_ROOTS"].get(git_binary)
        acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][git_binary] = acquisition[
            "hash_regular_absolute"
        ](git_binary, "ADAPTER_FIXTURE_GIT")["sha256"]
        acquisition["_GIT_DEVELOPER_ROOTS"][git_binary] = str(pathlib.Path(git_binary).parents[2])
        original_read_profile = acquisition["git_read_sandbox_profile"]
        original_bootstrap_profile = acquisition["git_object_bootstrap_sandbox_profile"]
        if sandbox_mode != "host-sandbox-enforced-positive":
            acquisition["git_read_sandbox_profile"] = lambda *_args, **_kwargs: None
            acquisition["git_object_bootstrap_sandbox_profile"] = lambda *_args, **_kwargs: None

        def create_adapter():
            return acquisition["create_git_metadata_adapter"](str(repo), key, git_binary)

        def cleanup(boundary):
            if boundary is not None and not boundary.closed:
                acquisition["cleanup_git_metadata_adapter"](boundary)

        try:
            # Every already-present alternates shape is rejected by the
            # parent lstat preflight before a child or adapter root exists.
            # This also proves the existence-only child permission is not a
            # substitute for the parent absence gate.
            live_alternates = repo / ".git/objects/info/alternates"
            live_alternates.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            hostile_alternates_source = temporary_path / "hostile-alternates-source"
            write_bytes(hostile_alternates_source, b"hostile alternate store\n", 0o600)
            source_link_count = hostile_alternates_source.stat().st_nlink
            for kind in ("regular", "hardlink", "symlink"):
                if kind == "regular":
                    write_bytes(live_alternates, b"hostile regular store\n", 0o600)
                elif kind == "hardlink":
                    os.link(hostile_alternates_source, live_alternates)
                else:
                    os.symlink(str(hostile_alternates_source), str(live_alternates))
                roots_before_present_control = adapter_roots()
                child_starts = []
                original_run_process_for_control = acquisition["run_process"]

                def record_present_control_child(*args, **kwargs):
                    child_starts.append((args, kwargs))
                    return original_run_process_for_control(*args, **kwargs)

                acquisition["run_process"] = record_present_control_child
                try:
                    expect_error(
                        "adapter present alternates preflight " + kind,
                        create_adapter,
                        "GIT_ALTERNATE_CONTROL_PROHIBITED",
                    )
                finally:
                    acquisition["run_process"] = original_run_process_for_control
                    live_alternates.unlink()
                assert child_starts == []
                assert adapter_roots() == roots_before_present_control
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
                assert hostile_alternates_source.stat().st_nlink == source_link_count
            hostile_alternates_source.unlink()
            report["git_metadata_adapter_present_alternates_preflight_zero_child_root"] = "PASS"

            if sandbox_mode == "host-sandbox-enforced-positive":
                # Inject the same control only after capture and scratch
                # creation, immediately before the first production
                # live-object bootstrap child.  The A2 profile exposes
                # existence only: Apple Git's byte read is denied, strict
                # stderr/result handling aborts, and create removes the exact
                # scratch root without registry residue.
                original_bootstrap_for_race = acquisition[
                    "run_git_object_bootstrap_child"
                ]
                race_calls = []

                def inject_post_preflight_alternates(**kwargs):
                    if kwargs.get("allow_live_objects") is True and not race_calls:
                        write_bytes(live_alternates, b"post-preflight hostile store\n", 0o600)
                        race_calls.append(tuple(kwargs.get("arguments", ())))
                    return original_bootstrap_for_race(**kwargs)

                roots_before_race = adapter_roots()
                acquisition[
                    "run_git_object_bootstrap_child"
                ] = inject_post_preflight_alternates
                try:
                    race_reason = expect_error(
                        "adapter post-preflight alternates race",
                        create_adapter,
                    )
                    assert race_calls and race_reason in (
                        "GIT_OBJECT_HEAD_COMMIT_STDERR",
                        "GIT_OBJECT_HEAD_COMMIT_RESULT",
                        "GIT_ADAPTER_SOURCE_DRIFT",
                    )
                finally:
                    acquisition[
                        "run_git_object_bootstrap_child"
                    ] = original_bootstrap_for_race
                    if os.path.lexists(live_alternates):
                        live_alternates.unlink()
                assert adapter_roots() == roots_before_race
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
                assert not os.path.lexists(live_alternates)
                report["git_metadata_adapter_post_preflight_alternates_race_fail_closed"] = "PASS"
            else:
                report[
                    "git_metadata_adapter_post_preflight_alternates_race_fail_closed"
                ] = sandbox_mode

            roots_before_ref_capture_overflow = adapter_roots()
            original_entry_limit = acquisition["MAX_GIT_ADAPTER_ENTRIES"]
            try:
                acquisition["MAX_GIT_ADAPTER_ENTRIES"] = 1
                expect_error(
                    "adapter ref capture overflow before scratch",
                    create_adapter,
                    "GIT_SOURCE_COMMON_REFS_ENTRY_LIMIT",
                )
            finally:
                acquisition["MAX_GIT_ADAPTER_ENTRIES"] = original_entry_limit
            assert adapter_roots() == roots_before_ref_capture_overflow
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
            report["git_metadata_adapter_ref_capture_overflow_zero_scratch"] = "PASS"

            invocations = []
            template_hits = []
            original_run_process = acquisition["run_process"]
            original_template_match = acquisition["require_git_child_template_match"]

            def recording_run_process(argv, *args, **kwargs):
                invocations.append((list(argv), dict(kwargs)))
                return original_run_process(argv, *args, **kwargs)

            def recording_template_match(**kwargs):
                receipt = original_template_match(**kwargs)
                template_hits.append(receipt)
                return receipt

            acquisition["run_process"] = recording_run_process
            acquisition["require_git_child_template_match"] = recording_template_match
            boundary = None
            try:
                capture, boundary = create_adapter()
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 1
                roots_during_scope = adapter_roots()
                expect_error(
                    "adapter process scope non-reentrant",
                    create_adapter,
                    "GIT_ADAPTER_CLEANUP_SCOPE_NON_REENTRANT",
                )
                assert adapter_roots() == roots_during_scope
                final_profile = original_read_profile(
                    git_binary, str(repo), boundary, False
                ).decode("ascii")
                bootstrap_read_profile = original_bootstrap_profile(
                    git_binary,
                    str(repo),
                    boundary.developer_root,
                    boundary.adapter_root,
                    ".",
                    boundary.live_git_dir,
                    boundary.live_common_dir,
                    os.path.join(boundary.live_common_dir, "objects"),
                    False,
                    False,
                    (),
                    (),
                ).decode("ascii")
                bootstrap_write_profile = original_bootstrap_profile(
                    git_binary,
                    str(repo),
                    boundary.developer_root,
                    boundary.adapter_root,
                    ".",
                    boundary.live_git_dir,
                    boundary.live_common_dir,
                    os.path.join(boundary.live_common_dir, "objects"),
                    False,
                    True,
                    (),
                    (),
                ).decode("ascii")
                adapter_pack_path = os.path.join(
                    boundary.adapter_root, "git", "objects", "pack"
                )
                assert "(deny file-write*)" in final_profile
                assert "(deny file-write*)" in bootstrap_read_profile
                live_alternates_literal = '(literal "' + os.path.join(
                    boundary.live_common_dir,
                    "objects",
                    "info",
                    "alternates",
                ) + '")'
                final_profile_forms = sbpl_top_level_forms(final_profile)
                assert not any(
                    form.lstrip().startswith("(allow ") and live_alternates_literal in form
                    for form in final_profile_forms
                )
                assert any(
                    form.lstrip().startswith("(deny ") and live_alternates_literal in form
                    for form in final_profile_forms
                )
                assert '(literal "/private/tmp")' in bootstrap_write_profile
                assert '(literal "' + boundary.adapter_root + '")' in bootstrap_write_profile
                assert '(subpath "' + adapter_pack_path + '")' in bootstrap_write_profile
                assert (
                    '(require-not (subpath "' + adapter_pack_path + '"))'
                    in bootstrap_write_profile
                )
                manifest = capture["adapter_object_manifest"]
                adapter_index_raw = pathlib.Path(boundary.git_dir, "index").read_bytes()
                adapter_index_observation = acquisition["parse_captured_git_index"](
                    adapter_index_raw,
                    len(capture["head_oid"]),
                )
                assert adapter_index_observation["index_extension_count"] == 0
                assert adapter_index_observation["index_root_tree_oid"] == capture[
                    "index_tree_observation"
                ]["index_root_tree_oid"]
                assert manifest["approved_artifact_blob_count"] == len(
                    acquisition["PENDING_STATIC_ARTIFACT_SPECS"]
                )
                assert manifest["object_count"] < 100
                captured_refs = {
                    refname: oid for oid, refname in capture["canonical_refs"]
                }
                assert captured_refs["refs/gov01/loose-unmaterialized"] == loose_unmaterialized_oid
                assert captured_refs["refs/gov01/packed-unmaterialized"] == packed_unmaterialized_oid
                assert captured_refs["refs/gov01/override"] == loose_override_oid
                assert captured_refs["refs/gov01/symalias"] == head_oid
                assert {
                    loose_unmaterialized_oid,
                    packed_unmaterialized_oid,
                    packed_shadowed_oid,
                    loose_override_oid,
                    packed_peeled_oid,
                }.isdisjoint(boundary.object_dependency_oids)
                missing = acquisition["run_git"](
                    git_binary, str(repo), boundary, ["cat-file", "--batch"],
                    "ADAPTER_UNRELATED", stdin_bytes=(unrelated_oid + "\n").encode("ascii"),
                )
                assert missing == (unrelated_oid + " missing\n").encode("ascii")
                for arguments, label in (
                    (["rev-parse", "--verify", "HEAD"], "ADAPTER_HEAD"),
                    (["rev-parse", "--verify", "HEAD^{tree}"], "ADAPTER_TREE"),
                    (["rev-parse", "--show-object-format"], "ADAPTER_FORMAT"),
                ):
                    acquisition["safe_git_scalar"](git_binary, str(repo), boundary, arguments, label)
                for dirty_arguments, dirty_label in (
                    (["diff-files", "--ignore-submodules=all", "--name-only", "-z"], "ADAPTER_DIFF_FILES"),
                    (["ls-files", "--others", "--exclude-standard", "-z"], "ADAPTER_LS_FILES_OTHERS"),
                ):
                    acquisition["run_git"](
                        git_binary, str(repo), boundary, dirty_arguments,
                        dirty_label, enumerates_worktree=True,
                        authorized_tree_excludes=(stage, "node_modules"),
                        authorized_exact_file_excludes=(envelope_relative,),
                    )
                refs_output = acquisition["run_git"](
                    git_binary,
                    str(repo),
                    boundary,
                    [
                        "for-each-ref",
                        "--sort=refname",
                        "--format=%(objectname) %(refname)",
                        "refs",
                    ],
                    "ADAPTER_FOR_EACH_REF",
                )
                assert acquisition["parse_git_for_each_ref_output"](
                    refs_output,
                    len(head_oid),
                ) == capture["canonical_refs"]
                artifact_path = acquisition["PENDING_STATIC_ARTIFACT_SPECS"][0][1]
                acquisition["run_git"](
                    git_binary, str(repo), boundary,
                    ["ls-tree", "-z", "--full-tree", head_oid, "--", artifact_path],
                    "ADAPTER_ARTIFACT_TREE",
                )
                acquisition["run_git"](
                    git_binary, str(repo), boundary, ["show", head_oid + ":" + artifact_path],
                    "ADAPTER_ARTIFACT_SHOW",
                )
                adapter_root = boundary.adapter_root
                acquisition["finalize_git_metadata_adapter"](boundary, key)
                assert boundary.closed and not os.path.lexists(adapter_root)
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
            finally:
                acquisition["run_process"] = original_run_process
                acquisition["require_git_child_template_match"] = original_template_match
                cleanup(boundary)
            prefix_length = len(acquisition["git_hardened_child_argv"](git_binary, str(repo), ".", ()))
            tails = [tuple(argv[prefix_length:]) for argv, _kwargs in invocations if argv[0] == git_binary]
            assert {tail[0] for tail in tails} >= {
                "rev-parse", "cat-file", "ls-tree", "diff-files", "ls-files",
                "for-each-ref", "show", "pack-objects", "index-pack", "verify-pack",
            }
            assert sum(tail[0] == "for-each-ref" for tail in tails) == 1
            assert sum(tail[0] == "show" + "-ref" for tail in tails) == 0
            all_child_stdin = b"".join(
                kwargs.get("stdin_bytes") or b""
                for argv, kwargs in invocations
                if argv[0] == git_binary
            )
            for unmaterialized_oid in (
                loose_unmaterialized_oid,
                packed_unmaterialized_oid,
                packed_shadowed_oid,
                loose_override_oid,
                packed_peeled_oid,
            ):
                assert unmaterialized_oid.encode("ascii") not in all_child_stdin
            assert all(
                kwargs.get("working_directory_fd") is not None
                for argv, kwargs in invocations if argv[0] == git_binary
            )
            expected_template_hits = {
                ("git-read-only-evidence", tuple(template))
                for template in acquisition["git_read_only_argv_templates_v2"]()
            } | {
                ("git-metadata-adapter-bootstrap", tuple(template))
                for template in acquisition["git_adapter_bootstrap_argv_templates_v2"]()
            }
            assert set(template_hits) == expected_template_hits
            report["git_metadata_adapter_private_tmp_write_profile_closure"] = "PASS"
            snapshot = acquisition["git_snapshot"](
                str(repo), key, git_binary,
                authorized_tree_excludes=(stage, "node_modules"),
                authorized_exact_file_excludes=(envelope_relative,),
            )
            assert snapshot["git_metadata_adapter_profile"] == acquisition["GIT_METADATA_ADAPTER_PROFILE_V5"]
            assert snapshot["git_metadata_adapter_cleanup_state"] == "removed"
            assert snapshot["git_metadata_adapter_residue_count"] == 0
            assert snapshot["live_git_control_child_read_count"] == 0
            assert snapshot["index_gitlink_profile"] == acquisition["GIT_INDEX_GITLINK_PROFILE_V1"]
            assert snapshot["index_gitlink_count"] == 1
            assert snapshot["worktree_tree_exclusions"] == [
                acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"],
                stage,
                "node_modules",
            ]
            assert len(snapshot["git_metadata_source_commitment"]) == 64
            expected_refs_bytes = b"".join(
                (captured_refs[refname] + " " + refname + "\n").encode("ascii")
                for refname in sorted(captured_refs)
            )
            assert snapshot["refs_sha256"] == hashlib.sha256(expected_refs_bytes).hexdigest()
            assert snapshot["refs_bytes"] == len(expected_refs_bytes)
            report["git_metadata_adapter_exact_oid_runtime_and_snapshot"] = "PASS"
            report["git_metadata_adapter_unmaterialized_ref_tips_no_expansion"] = "PASS"

            original_run_git_for_ref_mismatch = acquisition["run_git"]

            def omit_one_frozen_ref(*args, **kwargs):
                output = original_run_git_for_ref_mismatch(*args, **kwargs)
                arguments = args[3] if len(args) > 3 else kwargs.get("arguments")
                if arguments == [
                    "for-each-ref",
                    "--sort=refname",
                    "--format=%(objectname) %(refname)",
                    "refs",
                ]:
                    lines = output.splitlines(keepends=True)
                    assert len(lines) > 1
                    return b"".join(lines[:-1])
                return output

            roots_before_ref_mismatch = adapter_roots()
            acquisition["run_git"] = omit_one_frozen_ref
            try:
                expect_error(
                    "adapter for-each-ref value mismatch",
                    lambda: acquisition["git_snapshot"](
                        str(repo), key, git_binary,
                        authorized_tree_excludes=(stage, "node_modules"),
                        authorized_exact_file_excludes=(envelope_relative,),
                    ),
                    "GIT_FOR_EACH_REF_VALUE_MISMATCH",
                )
            finally:
                acquisition["run_git"] = original_run_git_for_ref_mismatch
            assert adapter_roots() == roots_before_ref_mismatch
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
            report["git_metadata_adapter_ref_value_mismatch_zero_residue"] = "PASS"

            # Both adapter-root and Git-subdirectory construction remain on
            # their held inodes across rename/replacement barriers.
            original_mkdir = acquisition["mkdir_git_adapter_directory_at"]
            root_barrier = []

            def root_swap_mkdir(directory_fd, relative, label):
                if not root_barrier:
                    original_path = acquisition["git_adapter_fd_path"](directory_fd, "ROOT_SWAP")
                    moved = original_path + ".moved"
                    os.rename(original_path, moved)
                    os.mkdir(original_path, 0o700)
                    original_mkdir(directory_fd, relative, label)
                    root_barrier.append((os.listdir(original_path), os.path.isdir(os.path.join(moved, relative))))
                    os.rmdir(original_path)
                    os.rename(moved, original_path)
                    return
                return original_mkdir(directory_fd, relative, label)

            acquisition["mkdir_git_adapter_directory_at"] = root_swap_mkdir
            boundary = None
            try:
                _capture, boundary = create_adapter()
                assert root_barrier == [([], True)]
            finally:
                acquisition["mkdir_git_adapter_directory_at"] = original_mkdir
                cleanup(boundary)

            original_write = acquisition["write_git_adapter_file_at"]
            git_barrier = []

            def git_swap_write(directory_fd, relative, raw, label):
                if not git_barrier:
                    git_path = acquisition["git_adapter_fd_path"](directory_fd, "GIT_SWAP")
                    retained = os.path.join(os.path.dirname(git_path), "git-retained")
                    os.rename(git_path, retained)
                    os.mkdir(git_path, 0o700)
                    original_write(directory_fd, relative, raw, label)
                    git_barrier.append((os.listdir(git_path), os.path.exists(os.path.join(retained, relative))))
                    os.rmdir(git_path)
                    os.rename(retained, git_path)
                    return
                return original_write(directory_fd, relative, raw, label)

            acquisition["write_git_adapter_file_at"] = git_swap_write
            boundary = None
            try:
                _capture, boundary = create_adapter()
                assert git_barrier == [([], True)]
            finally:
                acquisition["write_git_adapter_file_at"] = original_write
                cleanup(boundary)
            report["git_metadata_adapter_root_and_git_build_swap"] = "PASS"

            # Child fchdir(git_fd) never follows a replacement Git directory;
            # postcheck still rejects the rename seam.
            _capture, boundary = create_adapter()
            original_run_process = acquisition["run_process"]
            child_observation = []

            def child_git_swap(argv, *args, **kwargs):
                os.chmod(boundary.adapter_root, 0o700)
                retained = os.path.join(boundary.adapter_root, "git-retained")
                os.rename(boundary.git_dir, retained)
                os.mkdir(boundary.git_dir, 0o500)
                try:
                    output = original_run_process(argv, *args, **kwargs)
                    child_observation.append((output, os.listdir(boundary.git_dir)))
                    return output
                finally:
                    os.rmdir(boundary.git_dir)
                    os.rename(retained, boundary.git_dir)
                    os.chmod(boundary.adapter_root, 0o500)

            acquisition["run_process"] = child_git_swap
            try:
                child_swap_reason = expect_error(
                    "adapter child Git-directory swap",
                    lambda: acquisition["safe_git_scalar"](
                        git_binary, str(repo), boundary,
                        ["rev-parse", "--verify", "HEAD"], "ADAPTER_CHILD_SWAP",
                    ),
                )
                assert child_swap_reason in ("GIT_ADAPTER_DRIFT", "ADAPTER_CHILD_SWAP_RESULT")
                if child_swap_reason == "GIT_ADAPTER_DRIFT":
                    assert child_observation == [((head_oid + "\n").encode("ascii"), [])]
                else:
                    assert child_observation == []
            finally:
                acquisition["run_process"] = original_run_process
                cleanup(boundary)
            report["git_metadata_adapter_child_git_swap_fail_closed"] = "PASS"

            # Config/index/ref/object drift is caught before any child starts.
            for kind in ("config", "index", "ref", "object"):
                capture, boundary = create_adapter()
                if kind in ("config", "index"):
                    target = pathlib.Path(boundary.git_dir) / kind
                elif kind == "ref":
                    ref_name = capture["raw_files"]["head"][5:-1].decode("ascii")
                    target = pathlib.Path(boundary.git_dir) / ref_name
                else:
                    packs = sorted((pathlib.Path(boundary.git_dir) / "objects/pack").glob("*.pack"))
                    assert len(packs) == 1
                    target = packs[0]
                os.chmod(target, 0o600)
                with target.open("ab") as stream:
                    stream.write(b"tamper")
                starts = []
                original_run_process = acquisition["run_process"]
                acquisition["run_process"] = lambda *_args, **_kwargs: starts.append(True) or b""
                try:
                    expect_error(
                        "adapter pre-child " + kind + " tamper",
                        lambda: acquisition["safe_git_scalar"](
                            git_binary, str(repo), boundary,
                            ["rev-parse", "--verify", "HEAD"], "ADAPTER_TAMPER",
                        ),
                        "GIT_ADAPTER_DRIFT",
                    )
                    assert starts == []
                finally:
                    acquisition["run_process"] = original_run_process
                    cleanup(boundary)
            report["git_metadata_adapter_tamper_pre_child_stop"] = "PASS"

            # Deleting a live exact object cannot affect the sealed child, but
            # exact dependency CAS detects it.
            capture, boundary = create_adapter()
            loose = pathlib.Path(capture["objects_path"]) / head_oid[:2] / head_oid[2:]
            held = loose.with_name(loose.name + ".fixture-held")
            assert loose.is_file()
            os.rename(loose, held)
            try:
                assert acquisition["safe_git_scalar"](
                    git_binary, str(repo), boundary,
                    ["rev-parse", "--verify", "HEAD"], "ADAPTER_LIVE_OBJECT_DELETE",
                ) == head_oid
                expect_error(
                    "adapter live object deletion CAS",
                    lambda: acquisition["revalidate_git_metadata_source"](boundary, key),
                    "GIT_ADAPTER_SOURCE_DRIFT",
                )
            finally:
                os.rename(held, loose)
                cleanup(boundary)
            report["git_metadata_adapter_live_object_delete_frozen"] = "PASS"

            # Root swap and injected final-rmdir failure both retain explicit
            # uncertainty; neither marks the boundary closed or touches a
            # replacement.  Restoring authority permits exact cleanup.
            _capture, boundary = create_adapter()
            moved = boundary.adapter_root + ".moved"
            os.rename(boundary.adapter_root, moved)
            os.mkdir(boundary.adapter_root, 0o700)
            marker = pathlib.Path(boundary.adapter_root) / "replacement-marker"
            write_bytes(marker, b"untouched", 0o600)
            expect_error(
                "adapter cleanup root swap",
                lambda: acquisition["cleanup_git_metadata_adapter"](boundary),
                "GIT_ADAPTER_CLEANUP_IDENTITY",
            )
            assert not boundary.closed and marker.read_bytes() == b"untouched"
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 1
            expect_error(
                "adapter cleanup root drift rejects quiescent reuse",
                create_adapter,
                "GIT_ADAPTER_CLEANUP_SCOPE_NON_REENTRANT",
            )
            marker.unlink()
            os.rmdir(boundary.adapter_root)
            os.rename(moved, boundary.adapter_root)
            acquisition["cleanup_git_metadata_adapter"](boundary)
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0

            _capture, boundary = create_adapter()
            original_named_root_check = acquisition["verify_named_git_adapter_cleanup_root"]
            final_delete_swap = []

            def swap_before_final_root_delete(parent_fd, basename, expected_identity):
                if not final_delete_swap:
                    final_delete_swap.append("initial-check")
                    return original_named_root_check(parent_fd, basename, expected_identity)
                if len(final_delete_swap) == 1:
                    retained = boundary.adapter_root + ".pre-rmdir-retained"
                    os.rename(boundary.adapter_root, retained)
                    os.mkdir(boundary.adapter_root, 0o700)
                    replacement_marker = pathlib.Path(boundary.adapter_root) / "replacement-marker"
                    write_bytes(replacement_marker, b"must remain untouched", 0o600)
                    final_delete_swap.append((retained, replacement_marker))
                return original_named_root_check(parent_fd, basename, expected_identity)

            acquisition["verify_named_git_adapter_cleanup_root"] = swap_before_final_root_delete
            try:
                expect_error(
                    "adapter cleanup pre-final-rmdir root swap",
                    lambda: acquisition["cleanup_git_metadata_adapter"](boundary),
                    "GIT_ADAPTER_CLEANUP_IDENTITY",
                )
                retained, replacement_marker = final_delete_swap[1]
                assert not boundary.closed and replacement_marker.read_bytes() == b"must remain untouched"
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 1
            finally:
                acquisition["verify_named_git_adapter_cleanup_root"] = original_named_root_check
            replacement_marker.unlink()
            os.rmdir(boundary.adapter_root)
            os.rename(retained, boundary.adapter_root)
            acquisition["cleanup_git_metadata_adapter"](boundary)
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0

            # Deterministic witness for the final pathname-rmdir gap.  The
            # replacement must be empty so a weak stat(name)->rmdir(name)
            # implementation can actually delete it.  Its dev/ino pair is the
            # identity sentinel: a strict implementation must leave that exact
            # directory present and report cleanup uncertainty.  Darwin has no
            # public identity-conditioned directory unlink primitive.  Under
            # the selected A contract, a non-cooperating same-UID replacement
            # is out of model; this remains a supporting capability
            # characterization and can never be counted as a safety PASS.
            _capture, boundary = create_adapter()
            original_rmdir = acquisition["os"].rmdir
            final_rmdir_gap = {}

            def swap_at_final_root_rmdir(path, *args, **kwargs):
                if (
                    path == os.path.basename(boundary.adapter_root)
                    and kwargs.get("dir_fd") is not None
                    and not final_rmdir_gap
                ):
                    retained_root = boundary.adapter_root + ".final-rmdir-retained"
                    os.rename(boundary.adapter_root, retained_root)
                    os.mkdir(boundary.adapter_root, 0o700)
                    replacement = os.stat(boundary.adapter_root, follow_symlinks=False)
                    final_rmdir_gap.update(
                        retained_root=retained_root,
                        replacement_identity=(replacement.st_dev, replacement.st_ino),
                    )
                return original_rmdir(path, *args, **kwargs)

            acquisition["os"].rmdir = swap_at_final_root_rmdir
            try:
                expect_error(
                    "adapter cleanup final-rmdir replacement witness",
                    lambda: acquisition["cleanup_git_metadata_adapter"](boundary),
                    "GIT_ADAPTER_CLEANUP_IDENTITY",
                )
                assert not boundary.closed and final_rmdir_gap
                retained_metadata = os.stat(
                    final_rmdir_gap["retained_root"], follow_symlinks=False
                )
                assert (retained_metadata.st_dev, retained_metadata.st_ino) == boundary.adapter_identity
                try:
                    replacement_after = os.stat(boundary.adapter_root, follow_symlinks=False)
                except FileNotFoundError:
                    replacement_untouched = False
                else:
                    replacement_untouched = (
                        replacement_after.st_dev,
                        replacement_after.st_ino,
                    ) == final_rmdir_gap["replacement_identity"]
            finally:
                acquisition["os"].rmdir = original_rmdir
            if replacement_untouched:
                report["git_metadata_adapter_final_rmdir_identity_safety"] = (
                    "OUT-OF-MODEL-capability-characterization-replacement-preserved"
                )
                os.rmdir(boundary.adapter_root)
            else:
                report["git_metadata_adapter_final_rmdir_identity_safety"] = (
                    "OUT-OF-MODEL-observed-pathname-rmdir-deleted-same-UID-replacement"
                )
            os.rename(final_rmdir_gap["retained_root"], boundary.adapter_root)
            acquisition["cleanup_git_metadata_adapter"](boundary)

            missing_reason = expect_error(
                "adapter cleanup initially missing",
                lambda: acquisition["remove_git_adapter_root"](
                    "/private/tmp/" + prefix + "definitely-missing-fixture", (1, 1), []
                ),
            )
            assert missing_reason.startswith("GIT_ADAPTER_CLEANUP_")

            _capture, boundary = create_adapter()
            original_rmdir = acquisition["os"].rmdir
            cleanup_fault = []

            def fail_root_rmdir(path, *args, **kwargs):
                if path == os.path.basename(boundary.adapter_root) and not cleanup_fault:
                    cleanup_fault.append(path)
                    raise OSError("fixture cleanup fault")
                return original_rmdir(path, *args, **kwargs)

            acquisition["os"].rmdir = fail_root_rmdir
            try:
                expect_error(
                    "adapter cleanup final rmdir fault",
                    lambda: acquisition["cleanup_git_metadata_adapter"](boundary),
                    "GIT_ADAPTER_CLEANUP_IO",
                )
                assert not boundary.closed and cleanup_fault
                assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 1
                expect_error(
                    "adapter cleanup residue rejects reentrant scope",
                    create_adapter,
                    "GIT_ADAPTER_CLEANUP_SCOPE_NON_REENTRANT",
                )
            finally:
                acquisition["os"].rmdir = original_rmdir
            acquisition["cleanup_git_metadata_adapter"](boundary)
            assert acquisition["git_metadata_adapter_process_scope_residue_count"]() == 0
            cleanup_error = acquisition["ContractError"](
                acquisition["Exit"].PREFLIGHT_DRIFT,
                "GIT_ADAPTER_CLEANUP_IO",
            )
            for public_mode in ("unknown", "census", "verify", "acquire"):
                public_failure = acquisition["generic_public_failure"](
                    cleanup_error,
                    public_mode,
                )
                assert public_failure["authority"] == acquisition["authority_projection"](
                    False,
                    False,
                    acquisition["GIT_ADAPTER_CLEANUP_AUTHORITY"],
                )
                assert public_failure["retention"]["private_state_inspection_required"] is True
            cleanup_attempt = acquisition["AttemptState"]()
            cleanup_attempt.set_phase("schema-contract")
            cleanup_attempt.adapter_cleanup_uncertain()
            cleanup_recorder = acquisition["GateRecorder"]()
            cleanup_recorder.bind_run_authority(challenge, "c" * 64)
            cleanup_recorder.begin("G00", "schema-contract")
            cleanup_recorder.failed("GIT_ADAPTER_CLEANUP_IO", int(acquisition["Exit"].PREFLIGHT_DRIFT))
            acquire_cleanup_failure = acquisition["acquire_failure_result"](
                cleanup_error,
                cleanup_attempt,
                cleanup_recorder,
                challenge,
                "c" * 64,
                None,
                None,
            )
            assert acquire_cleanup_failure["authority"] == acquisition["authority_projection"](
                False,
                False,
                acquisition["GIT_ADAPTER_CLEANUP_AUTHORITY"],
            )
            assert acquire_cleanup_failure["retention"]["private_state_inspection_required"] is True
            report["git_metadata_adapter_cleanup_swap_missing_fault"] = "PASS"

            # Drift injected after pack-objects and pack-index metadata drift
            # both abort create and leave the adapter-root set unchanged.
            config_path = repo / ".git/config"
            original_config = config_path.read_bytes()
            original_bootstrap = acquisition["run_git_object_bootstrap_child"]
            source_drift = []

            def inject_source_drift(**kwargs):
                output = original_bootstrap(**kwargs)
                if kwargs.get("arguments", [None])[0] == "pack-objects" and not source_drift:
                    rewrite_bytes(config_path, original_config + b"# source drift\n")
                    source_drift.append(True)
                return output

            roots_at_drift = adapter_roots()
            acquisition["run_git_object_bootstrap_child"] = inject_source_drift
            try:
                expect_error("adapter source drift during copy", create_adapter, "GIT_ADAPTER_SOURCE_DRIFT")
            finally:
                acquisition["run_git_object_bootstrap_child"] = original_bootstrap
                rewrite_bytes(config_path, original_config)
            assert source_drift and adapter_roots() == roots_at_drift

            for fixture_ref_name in ("loose-unmaterialized", "override", "symalias"):
                (hostile_ref_root / fixture_ref_name).unlink()
            hostile_ref_root.rmdir()
            (repo / ".git/packed-refs").unlink()
            run_checked([git_binary, "-c", "repack.writeBitmaps=false", "repack", "-ad"], repo)
            dangling_source = temporary_path / "unreachable-object-source"
            write_bytes(dangling_source, b"unreachable object body must never enter adapter\n", 0o600)
            dangling_oid = git_output("hash-object", "-w", str(dangling_source)).strip().decode("ascii")
            dangling_pack = subprocess.run(
                [git_binary, "pack-objects", str(repo / ".git/objects/pack/pack")],
                cwd=str(repo),
                input=(dangling_oid + "\n").encode("ascii"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
            )
            assert dangling_pack.returncode == 0
            dangling_pack_oid = dangling_pack.stdout.strip().decode("ascii")
            dangling_pack_names = {
                "pack-" + dangling_pack_oid + ".idx",
                "pack-" + dangling_pack_oid + ".pack",
            }
            dangling_loose = repo / ".git/objects" / dangling_oid[:2] / dangling_oid[2:]
            dangling_loose.unlink()
            pack_indexes = sorted((repo / ".git/objects/pack").glob("*.idx"))
            assert len(pack_indexes) >= 2
            selected_head_dependency = acquisition["capture_git_object_dependencies"](
                str(repo / ".git/objects"),
                (head_oid,),
            )
            selected_pack_index = next(
                pathlib.Path(path)
                for path in selected_head_dependency["allowed_pack_paths"]
                if path.endswith(".idx")
            )
            corrupted_index = bytearray(selected_pack_index.read_bytes())
            corrupted_index[-1] ^= 1
            expect_error(
                "adapter pack index independent checksum",
                lambda: acquisition["parse_git_pack_index_v2"](
                    bytes(corrupted_index),
                    len(head_oid),
                    selected_pack_index.name,
                    (head_oid,),
                ),
                "GIT_OBJECT_PACK_INDEX_CHECKSUM",
            )
            original_bootstrap = acquisition["run_git_object_bootstrap_child"]
            corrupted_pack_stream = []

            def inject_corrupted_pack_stream(**kwargs):
                output = original_bootstrap(**kwargs)
                if kwargs.get("arguments", [None])[0] == "pack-objects" and not corrupted_pack_stream:
                    corrupted = bytearray(output)
                    corrupted[-1] ^= 1
                    corrupted_pack_stream.append(True)
                    return bytes(corrupted)
                return output

            roots_at_pack_corruption = adapter_roots()
            acquisition["run_git_object_bootstrap_child"] = inject_corrupted_pack_stream
            try:
                expect_error(
                    "adapter streamed pack independent checksum",
                    create_adapter,
                    "GIT_OBJECT_PACK_STREAM_CHECKSUM",
                )
            finally:
                acquisition["run_git_object_bootstrap_child"] = original_bootstrap
            assert corrupted_pack_stream and adapter_roots() == roots_at_pack_corruption

            pack_drift = []

            def inject_pack_drift(**kwargs):
                output = original_bootstrap(**kwargs)
                if kwargs.get("arguments", [None])[0] == "pack-objects" and not pack_drift:
                    selected_metadata = selected_pack_index.stat()
                    os.utime(
                        selected_pack_index,
                        ns=(selected_metadata.st_atime_ns, selected_metadata.st_mtime_ns + 1_000_000_000),
                    )
                    pack_drift.append(True)
                return output

            roots_at_pack_drift = adapter_roots()
            acquisition["run_git_object_bootstrap_child"] = inject_pack_drift
            try:
                expect_error(
                    "adapter pack index drift during copy",
                    create_adapter,
                    "GIT_ADAPTER_OBJECT_DEPENDENCY_DRIFT",
                )
            finally:
                acquisition["run_git_object_bootstrap_child"] = original_bootstrap
            assert pack_drift and adapter_roots() == roots_at_pack_drift
            selected_pack_file = selected_pack_index.with_suffix(".pack")
            assert selected_pack_file.is_file()
            pack_body_drift = []

            def inject_pack_body_drift(**kwargs):
                output = original_bootstrap(**kwargs)
                if kwargs.get("arguments", [None])[0] == "pack-objects" and not pack_body_drift:
                    selected_metadata = selected_pack_file.stat()
                    os.utime(
                        selected_pack_file,
                        ns=(selected_metadata.st_atime_ns, selected_metadata.st_mtime_ns + 1_000_000_000),
                    )
                    pack_body_drift.append(True)
                return output

            roots_at_pack_body_drift = adapter_roots()
            acquisition["run_git_object_bootstrap_child"] = inject_pack_body_drift
            try:
                expect_error(
                    "adapter selected pack drift during copy",
                    create_adapter,
                    "GIT_ADAPTER_OBJECT_DEPENDENCY_DRIFT",
                )
            finally:
                acquisition["run_git_object_bootstrap_child"] = original_bootstrap
            assert pack_body_drift and adapter_roots() == roots_at_pack_body_drift
            _capture, boundary = create_adapter()
            try:
                dependency = acquisition["capture_git_object_dependencies"](
                    str(repo / ".git/objects"),
                    boundary.object_dependency_oids,
                )
                allowed_names = {pathlib.Path(path).name for path in dependency["allowed_pack_paths"]}
                assert allowed_names and allowed_names.isdisjoint(dangling_pack_names)
                assert dangling_oid not in boundary.object_dependency_oids
            finally:
                cleanup(boundary)
            report["git_metadata_adapter_source_and_pack_copy_drift"] = "PASS"

            # Linked-worktree anchor/reverse binding is captured directly;
            # no discovery child participates.
            linked = repo / ".claude/worktrees/adapter-linked"
            linked.parent.mkdir(parents=True, mode=0o700)
            run_checked([git_binary, "worktree", "add", "-q", "-b", "adapter-linked", str(linked)], repo)
            marker_raw = (linked / ".git").read_text(encoding="utf-8")
            linked_git_dir = pathlib.Path(marker_raw[len("gitdir: "):].strip())
            linked_override_oid = "b" * len(head_oid)
            common_hidden_oid = "c" * len(head_oid)
            linked_unique_oid = "d" * len(head_oid)
            packed_overlay_base_oid = "e" * len(head_oid)
            packed_only_oid = "f" * len(head_oid)
            common_git_dir = repo / ".git"
            write_bytes(
                common_git_dir / "packed-refs",
                (
                    "# pack-refs with: peeled fully-peeled sorted\n"
                    + packed_overlay_base_oid + " refs/bisect/override\n"
                    + packed_only_oid + " refs/rewritten/packed-only\n"
                    + packed_overlay_base_oid + " refs/worktree/common-with-packed\n"
                ).encode("ascii"),
                0o600,
            )
            linked_ref_values = {
                "bisect/override": linked_override_oid,
                "worktree/current": linked_unique_oid,
                "rewritten/current": linked_unique_oid,
            }
            common_ref_values = {
                "foo": head_oid,
                "stash": head_oid,
                "bisect/override": common_hidden_oid,
                "worktree/common-with-packed": common_hidden_oid,
                "worktree/common-hidden": common_hidden_oid,
                "rewritten/common-hidden": common_hidden_oid,
            }
            for relative, oid in common_ref_values.items():
                target = common_git_dir / "refs" / relative
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                write_bytes(target, (oid + "\n").encode("ascii"), 0o600)
            for relative, oid in linked_ref_values.items():
                target = linked_git_dir / "refs" / relative
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                write_bytes(target, (oid + "\n").encode("ascii"), 0o600)
            linked_live_bootstrap_profiles = []
            original_run_process_for_linked = acquisition["run_process"]

            def record_linked_bootstrap_profile(argv, *args, **kwargs):
                environment = args[0] if args else kwargs.get("environment", {})
                if "GIT_OBJECT_DIRECTORY" in environment:
                    linked_live_bootstrap_profiles.append(kwargs.get("sandbox_profile"))
                return original_run_process_for_linked(argv, *args, **kwargs)

            acquisition["run_process"] = record_linked_bootstrap_profile
            try:
                linked_capture, linked_boundary = acquisition["create_git_metadata_adapter"](
                    str(linked), key, git_binary
                )
            finally:
                acquisition["run_process"] = original_run_process_for_linked
            assert linked_live_bootstrap_profiles
            linked_common_alternates_literal = '(literal "' + str(
                common_git_dir / "objects/info/alternates"
            ) + '")'
            linked_wrong_alternates_literal = '(literal "' + str(
                linked_git_dir / "objects/info/alternates"
            ) + '")'
            if sandbox_mode == "host-sandbox-enforced-positive":
                for raw_profile in linked_live_bootstrap_profiles:
                    assert isinstance(raw_profile, bytes)
                    linked_profile_forms = sbpl_top_level_forms(raw_profile.decode("ascii"))
                    assert sum(
                        form.lstrip().startswith("(allow ")
                        and linked_common_alternates_literal in form
                        for form in linked_profile_forms
                    ) == 1
                    assert not any(
                        form.lstrip().startswith("(allow ")
                        and linked_wrong_alternates_literal in form
                        for form in linked_profile_forms
                    )
            else:
                assert all(raw_profile is None for raw_profile in linked_live_bootstrap_profiles)
            assert linked_capture["git_control"]["marker"]["kind"] == "gitfile"
            assert linked_capture["linked_worktree"] is True
            linked_canonical = {
                refname: oid for oid, refname in linked_capture["canonical_refs"]
            }
            assert linked_canonical["refs/foo"] == head_oid
            assert linked_canonical["refs/stash"] == head_oid
            assert linked_canonical["refs/bisect/override"] == linked_override_oid
            assert linked_canonical["refs/rewritten/packed-only"] == packed_only_oid
            assert (
                linked_canonical["refs/worktree/common-with-packed"]
                == packed_overlay_base_oid
            )
            assert linked_canonical["refs/worktree/current"] == linked_unique_oid
            assert linked_canonical["refs/rewritten/current"] == linked_unique_oid
            assert "refs/worktree/common-hidden" not in linked_canonical
            assert "refs/rewritten/common-hidden" not in linked_canonical
            linked_refs_output = acquisition["run_git"](
                git_binary,
                str(linked),
                linked_boundary,
                [
                    "for-each-ref",
                    "--sort=refname",
                    "--format=%(objectname) %(refname)",
                    "refs",
                ],
                "ADAPTER_LINKED_FOR_EACH_REF",
            )
            assert acquisition["parse_git_for_each_ref_output"](
                linked_refs_output,
                len(head_oid),
            ) == linked_capture["canonical_refs"]
            acquisition["cleanup_git_metadata_adapter"](linked_boundary)
            invalid_linked_ref = linked_git_dir / "refs/heads/outside-namespace"
            invalid_linked_ref.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            write_bytes(invalid_linked_ref, (head_oid + "\n").encode("ascii"), 0o600)
            roots_before_invalid_linked_ref = adapter_roots()
            try:
                expect_error(
                    "adapter linked ref outside per-worktree namespaces",
                    lambda: acquisition["create_git_metadata_adapter"](
                        str(linked), key, git_binary
                    ),
                    "GIT_CAPTURE_WORKTREE_REF_NAMESPACE",
                )
            finally:
                invalid_linked_ref.unlink()
                invalid_linked_ref.parent.rmdir()
            assert adapter_roots() == roots_before_invalid_linked_ref
            reverse = linked_git_dir / "gitdir"
            reverse_raw = reverse.read_bytes()
            rewrite_bytes(reverse, b"/private/tmp/unrelated/.git\n")
            try:
                expect_error(
                    "adapter linked reverse pointer",
                    lambda: acquisition["capture_git_metadata_source"](str(linked), key),
                    "GIT_WORKTREE_GITDIR_BINDING",
                )
            finally:
                rewrite_bytes(reverse, reverse_raw)
            report["git_metadata_adapter_linked_anchor_reverse"] = "PASS"
            report["git_metadata_adapter_linked_ref_namespace_semantics"] = "PASS"

            # Hostile live controls and HEAD/index/ref drift occur only after
            # capture.  The final child returns the frozen HEAD; recapture/CAS
            # stops before a success result.
            capture, boundary = create_adapter()
            live_git = pathlib.Path(capture["git_dir"])
            common_git = pathlib.Path(capture["common_dir"])
            head_path = live_git / "HEAD"
            index_path = live_git / "index"
            common_config = common_git / "config"
            head_raw = head_path.read_bytes()
            index_raw = index_path.read_bytes()
            config_raw = common_config.read_bytes()
            ref_name = head_raw[5:-1].decode("ascii")
            ref_path = common_git / ref_name
            ref_raw = ref_path.read_bytes()
            worktree_config = live_git / "config.worktree"
            alternates = common_git / "objects/info/alternates"
            alternates.parent.mkdir(parents=True, exist_ok=True)
            include_file = temporary_path / "hostile-include.cfg"
            write_bytes(include_file, b"[core]\n\tbare = true\n", 0o600)
            rewrite_bytes(
                common_config,
                config_raw + ("[include]\n\tpath = %s\n" % include_file).encode("utf-8"),
            )
            rewrite_bytes(head_path, (head_oid + "\n").encode("ascii"))
            rewrite_bytes(index_path, index_raw + b"index-drift")
            rewrite_bytes(ref_path, (("0" * len(head_oid)) + "\n").encode("ascii"))
            write_bytes(worktree_config, b"[core]\n\tbare = true\n", 0o600)
            write_bytes(alternates, b"/private/tmp/hostile-object-store\n", 0o600)
            try:
                assert acquisition["safe_git_scalar"](
                    git_binary, str(repo), boundary,
                    ["rev-parse", "--verify", "HEAD"], "ADAPTER_FROZEN_AFTER_DRIFT",
                ) == head_oid
                reason = expect_error(
                    "adapter hostile live controls final CAS",
                    lambda: acquisition["revalidate_git_metadata_source"](boundary, key),
                )
                assert reason.startswith("GIT_")
            finally:
                rewrite_bytes(common_config, config_raw)
                rewrite_bytes(head_path, head_raw)
                rewrite_bytes(index_path, index_raw)
                rewrite_bytes(ref_path, ref_raw)
                worktree_config.unlink()
                alternates.unlink()
                cleanup(boundary)
            report["git_metadata_adapter_hostile_live_control_drift"] = "PASS"

            expect_error(
                "adapter tree gitlink",
                lambda: acquisition["select_required_git_tree_entries"](
                    b"160000 submodule\x00" + (b"\x01" * 20),
                    40,
                    {b"submodule": None},
                ),
                "GIT_OBJECT_APPROVED_BLOB_MODE",
            )
            for private_path in (".obsidian/sentinel", "prefix-canvas-vault-secret/sentinel"):
                expect_error(
                    "adapter private path " + private_path,
                    lambda value=private_path: acquisition["validate_relative"](
                        value, "GIT_OBJECT_ENUMERATION_PATH"
                    ),
                    "GIT_OBJECT_ENUMERATION_PATH_VAULT",
                )
            report["git_metadata_adapter_gitlink_and_private_path_rejection"] = "PASS"
        finally:
            acquisition["git_read_sandbox_profile"] = original_read_profile
            acquisition["git_object_bootstrap_sandbox_profile"] = original_bootstrap_profile
            if old_hash is None:
                acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].pop(git_binary, None)
            else:
                acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][git_binary] = old_hash
            if old_developer is None:
                acquisition["_GIT_DEVELOPER_ROOTS"].pop(git_binary, None)
            else:
                acquisition["_GIT_DEVELOPER_ROOTS"][git_binary] = old_developer
    assert adapter_roots() == roots_before
    report["git_metadata_adapter_private_tmp_residue_set_unchanged"] = "PASS"


def run_partial_git_boundary_fixtures(acquisition, report):
    oid_bytes = 20
    oid_length = oid_bytes * 2

    def index_bytes(entries, *, version=2, extension=None, include_gitlink=True):
        materialized_entries = list(entries)
        if (
            include_gitlink
            and not any(path == acquisition["OPAQUE_INDEX_GITLINK_RAW"] for path, _mode, _oid in materialized_entries)
        ):
            materialized_entries.append(
                (acquisition["OPAQUE_INDEX_GITLINK_RAW"], 0o160000, b"g" * oid_bytes)
            )
        body = bytearray(
            b"DIRC" + version.to_bytes(4, "big") + len(materialized_entries).to_bytes(4, "big")
        )
        for path, mode, oid in sorted(materialized_entries, key=lambda entry: entry[0]):
            fixed = bytearray(40 + oid_bytes + 2)
            fixed[24:28] = mode.to_bytes(4, "big")
            fixed[40:40 + oid_bytes] = oid
            fixed[40 + oid_bytes:42 + oid_bytes] = len(path).to_bytes(2, "big")
            entry = fixed + path + b"\x00"
            entry.extend(b"\x00" * ((-len(entry)) % 8))
            body.extend(entry)
        if extension is not None:
            signature, payload = extension
            body.extend(signature + len(payload).to_bytes(4, "big") + payload)
        return bytes(body) + hashlib.sha1(body).digest()

    specs = acquisition["PENDING_STATIC_ARTIFACT_SPECS"]
    entries = []
    for index, (_role, path) in enumerate(specs, 1):
        entries.append((path.encode("utf-8"), 0o100644, hashlib.sha1(str(index).encode("ascii")).digest()))
    raw_index = index_bytes(entries, extension=(b"TEST", b"opaque-extension"))
    observation = acquisition["parse_captured_git_index"](raw_index, oid_length)
    assert observation["index_version"] == 2
    assert observation["index_entry_count"] == 21
    assert observation["index_gitlink_count"] == 1
    assert observation["index_gitlink_profile"] == acquisition["GIT_INDEX_GITLINK_PROFILE_V1"]
    assert observation["index_extension_count"] == 1
    assert len(observation["index_root_tree_oid"]) == oid_length
    sanitized = observation["sanitized_index_bytes"]
    sanitized_observation = acquisition["parse_captured_git_index"](sanitized, oid_length)
    assert sanitized_observation["index_extension_count"] == 0
    assert sanitized_observation["index_root_tree_oid"] == observation["index_root_tree_oid"]
    assert sanitized_observation["adapter_index_bytes"] == len(sanitized)
    eoie_observation = acquisition["parse_captured_git_index"](
        index_bytes(entries, extension=(b"EOIE", b"opaque-offset-cache")),
        oid_length,
    )
    assert eoie_observation["index_extension_count"] == 1
    assert acquisition["parse_captured_git_index"](
        eoie_observation["sanitized_index_bytes"], oid_length
    )["index_extension_count"] == 0
    gitlink_oid = b"g" * oid_bytes
    gitlink_child_content = b"160000 obsidian-sample-plugin\x00" + gitlink_oid
    gitlink_child_oid = hashlib.sha1(
        b"tree " + str(len(gitlink_child_content)).encode("ascii") + b"\x00" + gitlink_child_content
    ).digest()
    one_blob = b"\x01" * oid_bytes
    child_content = b"100644 b\x00" + one_blob
    child_oid = hashlib.sha1(
        b"tree " + str(len(child_content)).encode("ascii") + b"\x00" + child_content
    ).digest()
    root_records = [
        (b"_reference/", b"40000 _reference\x00" + gitlink_child_oid),
        (b"a/", b"40000 a\x00" + child_oid),
    ]
    root_content = b"".join(record for _key, record in sorted(root_records))
    expected_root = hashlib.sha1(
        b"tree " + str(len(root_content)).encode("ascii") + b"\x00" + root_content
    ).hexdigest()
    one_observation = acquisition["parse_captured_git_index"](
        index_bytes([(b"a/b", 0o100644, one_blob)]),
        oid_length,
    )
    assert one_observation["index_root_tree_oid"] == expected_root
    gitlink_root_content = b"40000 _reference\x00" + gitlink_child_oid
    gitlink_expected_root = hashlib.sha1(
        b"tree " + str(len(gitlink_root_content)).encode("ascii") + b"\x00" + gitlink_root_content
    ).hexdigest()
    gitlink_observation = acquisition["parse_captured_git_index"](
        index_bytes(
            [(acquisition["OPAQUE_INDEX_GITLINK_RAW"], 0o160000, gitlink_oid)]
        ),
        oid_length,
    )
    assert gitlink_observation["index_root_tree_oid"] == gitlink_expected_root
    assert acquisition["parse_captured_git_index"](
        gitlink_observation["sanitized_index_bytes"], oid_length
    )["index_root_tree_oid"] == gitlink_expected_root
    corrupted = bytearray(raw_index)
    corrupted[-1] ^= 1
    expect_error(
        "captured index checksum",
        lambda: acquisition["parse_captured_git_index"](bytes(corrupted), oid_length),
        "GIT_INDEX_CHECKSUM",
    )
    expect_error(
        "captured index v4",
        lambda: acquisition["parse_captured_git_index"](index_bytes(entries, version=4), oid_length),
        "GIT_INDEX_VERSION",
    )
    expect_error(
        "captured index required extension",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes(entries, extension=(b"link", b"shared-index")), oid_length
        ),
        "GIT_INDEX_EXTENSION",
    )
    expect_error(
        "captured index extra unrelated gitlink",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes([(b"submodule", 0o160000, b"g" * oid_bytes)]), oid_length
        ),
        "GIT_INDEX_GITLINK_SET",
    )
    expect_error(
        "captured index approved path gitlink",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes([(specs[0][1].encode("utf-8"), 0o160000, b"r" * oid_bytes)]),
            oid_length,
        ),
        "GIT_INDEX_GITLINK_SET",
    )
    expect_error(
        "captured index zero gitlink",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes(entries, include_gitlink=False), oid_length
        ),
        "GIT_INDEX_GITLINK_SET",
    )
    expect_error(
        "captured index exact gitlink mode replacement",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes(
                [(acquisition["OPAQUE_INDEX_GITLINK_RAW"], 0o100644, b"m" * oid_bytes)]
            ),
            oid_length,
        ),
        "GIT_INDEX_GITLINK_SET",
    )
    expect_error(
        "captured index dot-git component",
        lambda: acquisition["parse_captured_git_index"](
            index_bytes([(b"safe/.GIT/config", 0o100644, b"d" * oid_bytes)]), oid_length
        ),
        "GIT_INDEX_PATH",
    )
    assumed_path = b"assumed.txt"
    assumed_index = bytearray(
        index_bytes(
            [(assumed_path, 0o100644, b"a" * oid_bytes)],
            include_gitlink=False,
        )
    )
    flags_offset = 12 + 40 + oid_bytes
    assumed_index[flags_offset:flags_offset + 2] = (
        0x8000 | len(assumed_path)
    ).to_bytes(2, "big")
    assumed_index[-oid_bytes:] = hashlib.sha1(assumed_index[:-oid_bytes]).digest()
    expect_error(
        "captured index assume unchanged",
        lambda: acquisition["parse_captured_git_index"](bytes(assumed_index), oid_length),
        "GIT_INDEX_ASSUME_UNCHANGED",
    )

    wanted_oid = b"w" * oid_bytes
    sibling_oid = b"s" * oid_bytes
    records = [
        (b"wanted\x00", b"100644 wanted\x00" + wanted_oid),
        (b"\xff-private\x00", b"100644 \xff-private\x00" + sibling_oid),
    ]
    tree_raw = b"".join(record for _key, record in sorted(records, key=lambda item: item[0]))
    selected = acquisition["select_required_git_tree_entries"](
        tree_raw,
        oid_length,
        {b"wanted": None},
    )
    assert selected == {b"wanted": ("blob", wanted_oid.hex(), "100644")}
    duplicate_name_raw = (
        b"100644 foo\x00" + wanted_oid
        + b"40000 foo\x00" + sibling_oid
    )
    expect_error(
        "tree same-name file-directory duplicate",
        lambda: acquisition["select_required_git_tree_entries"](
            duplicate_name_raw,
            oid_length,
            {},
        ),
        "GIT_TREE_OBJECT_NAME_DUPLICATE",
    )

    closure_root = {}
    closure_entries = entries + [
        (acquisition["OPAQUE_INDEX_GITLINK_RAW"], 0o160000, gitlink_oid)
    ]
    for path_raw, mode, oid_raw in closure_entries:
        node = closure_root
        components = path_raw.split(b"/")
        for component in components[:-1]:
            node = node.setdefault(component, {})
        node[components[-1]] = (format(mode, "o").encode("ascii"), oid_raw)
    synthetic_objects = {}
    synthetic_tree_paths = {}

    def seal_tree(node, prefix=()):
        records = []
        for name, value in node.items():
            if isinstance(value, dict):
                mode_raw = b"40000"
                child_oid_hex = seal_tree(value, prefix + (name,))
                child_oid_raw = bytes.fromhex(child_oid_hex)
            else:
                mode_raw, child_oid_raw = value
            order_key = name + (b"/" if mode_raw == b"40000" else b"\x00")
            records.append((order_key, mode_raw + b" " + name + b"\x00" + child_oid_raw))
        content = b"".join(record for _key, record in sorted(records, key=lambda item: item[0]))
        oid_hex = acquisition["git_object_oid"]("tree", content, oid_length)
        synthetic_objects[oid_hex] = ("tree", content)
        synthetic_tree_paths[prefix] = oid_hex
        return oid_hex

    closure_root_oid = seal_tree(closure_root)
    closure_index_observation = acquisition["parse_captured_git_index"](
        index_bytes(closure_entries), oid_length
    )
    assert closure_index_observation["index_root_tree_oid"] == closure_root_oid
    commit_content = ("tree " + closure_root_oid + "\n\nfixture\n").encode("ascii")
    closure_head_oid = acquisition["git_object_oid"]("commit", commit_content, oid_length)
    synthetic_objects[closure_head_oid] = ("commit", commit_content)
    requested_oids = []
    original_dependencies = acquisition["capture_git_object_dependencies"]
    original_bootstrap_child = acquisition["run_git_object_bootstrap_child"]

    def synthetic_dependencies(_objects_path, expected_oids):
        return {
            "fingerprint": hashlib.sha256(b"\x00".join(oid.encode("ascii") for oid in expected_oids)).hexdigest(),
            "allowed_pack_paths": (),
        }

    def synthetic_bootstrap_child(**kwargs):
        requested = tuple(
            line.decode("ascii") for line in kwargs["stdin_bytes"].splitlines()
        )
        assert requested == tuple(sorted(kwargs["allowed_live_oids"]))
        requested_oids.extend(requested)
        response = bytearray()
        for oid_hex in requested:
            object_type, content = synthetic_objects[oid_hex]
            response.extend(
                (oid_hex + " " + object_type + " " + str(len(content)) + "\n").encode("ascii")
            )
            response.extend(content + b"\n")
        return bytes(response)

    acquisition["capture_git_object_dependencies"] = synthetic_dependencies
    acquisition["run_git_object_bootstrap_child"] = synthetic_bootstrap_child
    try:
        closure_oids, closure_types, observed_root_oid, closure_manifest = acquisition[
            "discover_git_object_closure"
        ](
            capture={
                "head_oid": closure_head_oid,
                "objects_path": "/fixture/objects",
                "index_tree_observation": closure_index_observation,
            },
            git_binary="/fixture/git",
            developer_root="/fixture/developer",
            repo_root="/fixture/repo",
            adapter_root="/private/tmp/fixture-adapter",
            adapter_git_dir=".",
            adapter_fd=91,
            git_fd=92,
            adapter_identity=(1, 2),
            git_identity=(1, 3),
        )
    finally:
        acquisition["capture_git_object_dependencies"] = original_dependencies
        acquisition["run_git_object_bootstrap_child"] = original_bootstrap_child
    opaque_reference_tree_oid = synthetic_tree_paths[(b"_reference",)]
    opaque_gitlink_oid = gitlink_oid.hex()
    assert observed_root_oid == closure_root_oid
    assert opaque_reference_tree_oid not in requested_oids
    assert opaque_gitlink_oid not in requested_oids
    assert opaque_reference_tree_oid not in closure_oids
    assert opaque_gitlink_oid not in closure_oids
    assert opaque_reference_tree_oid not in closure_types
    assert opaque_gitlink_oid not in closure_types
    assert "opaque-gitlink-omitted" in closure_manifest["profile"]

    original_create_adapter = acquisition["create_git_metadata_adapter"]
    original_open_directory = acquisition["open_directory"]
    create_adapter_calls = []
    open_directory_calls = []
    acquisition["create_git_metadata_adapter"] = lambda *_args, **_kwargs: (
        create_adapter_calls.append("unexpected-adapter-create")
    )
    acquisition["open_directory"] = lambda *_args, **_kwargs: (
        open_directory_calls.append("unexpected-open")
    )
    try:
        for reserved_overlap in (
            "_reference",
            acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"] + "/descendant",
        ):
            expect_error(
                "opaque gitlink exclusion overlap " + reserved_overlap,
                lambda value=reserved_overlap: acquisition["git_snapshot"](
                    "/fixture/repo",
                    b"k" * 32,
                    "/fixture/git",
                    authorized_tree_excludes=(value,),
                ),
                "GIT_EXCLUSION_RESERVED_GITLINK",
            )
    finally:
        acquisition["create_git_metadata_adapter"] = original_create_adapter
        acquisition["open_directory"] = original_open_directory
    assert create_adapter_calls == [] and open_directory_calls == []

    challenge = "GOV01-SA-20260820-" + ("a" * 64)
    generation_challenge = "GOV01-GEN-20260820-" + ("b" * 64)
    stage = ".gov01-toolchain-stage-" + challenge
    pending = (
        acquisition["CONTROL_PREFIX"]
        + acquisition["PENDING_ENVELOPE_BASENAME_PREFIX"]
        + generation_challenge
        + ".json"
    )
    dirty_suffix = [
            "--", ".", ":(exclude).git", ":(exclude).git/**",
            ":(exclude)canvas-vault", ":(exclude)canvas-vault/**",
            ":(exclude)" + acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"],
            ":(exclude)" + acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"] + "/**",
            ":(exclude)" + stage, ":(exclude)" + stage + "/**",
            ":(exclude)node_modules", ":(exclude)node_modules/**",
            ":(top,literal,exclude)" + pending,
    ]
    diff_arguments = ["diff-files", "--ignore-submodules=all", "--name-only", "-z"] + dirty_suffix
    ls_arguments = ["ls-files", "--others", "--exclude-standard", "-z"] + dirty_suffix
    for arguments in (diff_arguments, ls_arguments):
        argv = acquisition["git_hardened_child_argv"](
            "/fixture/git", "/fixture/repo", ".", arguments
        )
        role, normalized = acquisition["require_git_child_template_match"](
            role="git-read-only-evidence",
            argv=argv,
            environment=acquisition["git_env"](),
            git_binary="/fixture/git",
            repo_root="/fixture/repo",
            adapter_git_dir=".",
            live_objects=None,
            stdin_bytes=None,
        )
        assert role == "git-read-only-evidence" and normalized

    for label, malformed_arguments in (
        ("diff-files trailing argument", diff_arguments + ["--unexpected-extra"]),
        ("ls-files truncated argument", ls_arguments[:-1]),
        ("diff-files missing ignore-submodules", ["diff-files", "--name-only", "-z"] + dirty_suffix),
        (
            "ls-files unsupported ignore-submodules insertion",
            ["ls-files", "--ignore-submodules=all", "--others", "--exclude-standard", "-z"]
            + dirty_suffix,
        ),
        (
            "diff-files missing opaque gitlink exclusions",
            [
                value for value in diff_arguments
                if acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"] not in value
            ],
        ),
    ):
        malformed_argv = acquisition["git_hardened_child_argv"](
            "/fixture/git", "/fixture/repo", ".", malformed_arguments
        )
        expect_error(
            label,
            lambda value=malformed_argv: acquisition["require_git_child_template_match"](
                role="git-read-only-evidence",
                argv=value,
                environment=acquisition["git_env"](),
                git_binary="/fixture/git",
                repo_root="/fixture/repo",
                adapter_git_dir=".",
                live_objects=None,
                stdin_bytes=None,
            ),
            "GIT_FINAL_ARGV",
        )

    boundary = acquisition["GitMetadataAdapter"](
        "/fixture/developer", "/fixture/repo", "/fixture/live-git", "/fixture/live-common",
        "/private/tmp/gov01-git-adapter-fixture", "/private/tmp/gov01-git-adapter-fixture/git",
        91, 92, "1" * 64, ("a" * oid_length,), "2" * 64, "3" * 64,
        (1, 2), (1, 3), [],
    )
    old_developer = acquisition["_GIT_DEVELOPER_ROOTS"].get("/fixture/git")
    acquisition["_GIT_DEVELOPER_ROOTS"]["/fixture/git"] = "/fixture/developer"
    try:
        profile = acquisition["git_read_sandbox_profile"](
            "/fixture/git",
            "/fixture/repo",
            boundary,
            True,
            (stage, "node_modules"),
            (pending,),
        ).decode("utf-8")
    finally:
        if old_developer is None:
            acquisition["_GIT_DEVELOPER_ROOTS"].pop("/fixture/git", None)
        else:
            acquisition["_GIT_DEVELOPER_ROOTS"]["/fixture/git"] = old_developer
    assert '(literal "/fixture/repo/' + pending + '")' in profile
    assert '(subpath "/fixture/repo/' + stage + '")' in profile
    assert '(subpath "/fixture/repo/node_modules")' in profile
    opaque_gitlink_absolute = "/fixture/repo/" + acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"]
    deny_block = profile.split('(deny file-read* file-test-existence\n ', 1)[1].split('\n)\n', 1)[0]
    assert '(literal "' + opaque_gitlink_absolute + '")' in deny_block
    assert '(subpath "' + opaque_gitlink_absolute + '")' in deny_block

    original_dirty_builder = acquisition["dirty_path_manifest_commitment"]
    parent_read_count = []
    acquisition["dirty_path_manifest_commitment"] = lambda *_args, **_kwargs: (
        parent_read_count.append("unexpected-open-or-hash") or "0" * 64
    )
    try:
        for forged, expected_reason in (
            (stage + "/sentinel", "GIT_DIRTY_EXCLUDED_PATH"),
            ("node_modules/sentinel", "GIT_DIRTY_EXCLUDED_PATH"),
            (pending, "GIT_DIRTY_EXCLUDED_PATH"),
            (acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"], "GIT_DIRTY_EXCLUDED_PATH"),
            (
                acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"] + "/.git/config",
                "GIT_DIRTY_PROHIBITED_PATH",
            ),
            (
                acquisition["OPAQUE_INDEX_GITLINK_RELATIVE"] + "/content.md",
                "GIT_DIRTY_EXCLUDED_PATH",
            ),
        ):
            expect_error(
                "forged excluded dirty path",
                lambda value=forged: acquisition["dirty_index_worktree_manifest_commitment"](
                    "/fixture/repo",
                    value.encode("utf-8") + b"\x00",
                    b"",
                    b"k" * 32,
                    (stage, "node_modules"),
                    (pending,),
                ),
                expected_reason,
            )
    finally:
        acquisition["dirty_path_manifest_commitment"] = original_dirty_builder
    assert parent_read_count == []

    with tempfile.TemporaryDirectory(prefix="gov01-dirty-sanitized-index-", dir="/private/tmp") as temporary:
        repo = pathlib.Path(temporary)
        sentinel = repo / "tracked.txt"
        sentinel.write_bytes(b"one")
        first = acquisition["dirty_index_worktree_manifest_commitment"](
            str(repo), b"tracked.txt\x00", b"", b"k" * 32,
            (stage, "node_modules"), (pending,),
        )
        sentinel.write_bytes(b"two")
        second = acquisition["dirty_index_worktree_manifest_commitment"](
            str(repo), b"tracked.txt\x00", b"", b"k" * 32,
            (stage, "node_modules"), (pending,),
        )
        assert first != second

    source_text = ACQ_PATH.read_text(encoding="utf-8")
    for stale in (
        '"ls-tree","-r","-t","-z","--full-tree"',
        '"status","--porcelain=v2"',
        '"diff-files","--name-only","-z"',
        "git-diff-files-plus-ls-files-others-exact-top-literal-envelope-file-exclusion-v2",
        "worktree tree exclusions are exactly the challenge stage and node_modules",
        "captured-index-v2-v3-stage0-strict-framing-bottom-up-root-tree-oid-v2",
        "checkpoint-scoped-private-temp-sanitized-exact-oid-identity-bound-git-fd-metadata-adapter-v3",
        "checkpoint-scoped-private-temp-sanitized-required-path-ancestor-exact-oid-index-root-proven-"
        "identity-bound-git-fd-metadata-adapter-v4",
        "nonrecursive ls-files",
        "plus-nonrecursive-ls-files",
        "all current tree OIDs",
        "every current-tree tree OID",
        "nonexcluded porcelain-v2 path",
    ):
        assert stale not in source_text
    tree = ast.parse(source_text)
    embedded_assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    assert len(embedded_assignments) == 1
    embedded_raw = embedded_assignments[0].value.value
    assert embedded_raw == acquisition["_PENDING_ENVELOPE_V2_STATIC_TEMPLATE_JSON"]
    embedded_template = json.loads(embedded_raw)
    assert embedded_template["authorization_preimage"][
        "envelope_git_status_exclusion_profile"
    ] == acquisition["PENDING_ENVELOPE_GIT_EXCLUSION_PROFILE"]
    assert embedded_template["authorization_preimage"][
        "git_snapshot_commitment_profile"
    ] == acquisition["GIT_SNAPSHOT_COMMITMENT_PROFILE_V2"]
    assert embedded_template["execution_plan"][
        "git_child_sandbox_profile"
    ] == acquisition["GIT_CHILD_SANDBOX_PROFILE_V3"]
    embedded_read_role = next(
        entry for entry in embedded_template["execution_plan"]["evidence_command_templates"]
        if entry["role"] == "git-read-only-evidence"
    )
    assert embedded_read_role["argv_allowlist"] == acquisition["git_read_only_argv_templates_v2"]()
    snapshot_function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "git_snapshot"
    )
    diff_snapshot_calls = [
        node for node in ast.walk(snapshot_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_git"
        and any(
            isinstance(argument, ast.Constant) and argument.value == "GIT_DIFF_FILES"
            for argument in node.args
        )
    ]
    assert len(diff_snapshot_calls) == 1
    diff_snapshot_call = diff_snapshot_calls[0]
    assert len(diff_snapshot_call.args) == 5
    assert isinstance(diff_snapshot_call.args[3], ast.List)
    assert [element.value for element in diff_snapshot_call.args[3].elts] == [
        "diff-files", "--ignore-submodules=all", "--name-only", "-z",
    ]
    assert {
        keyword.arg: keyword.value.value
        for keyword in diff_snapshot_call.keywords
        if isinstance(keyword.value, ast.Constant)
    }.get("enumerates_worktree") is True
    ref_snapshot_calls = [
        node for node in ast.walk(snapshot_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_git"
        and any(
            isinstance(argument, ast.Constant) and argument.value == "GIT_FOR_EACH_REF"
            for argument in node.args
        )
    ]
    assert len(ref_snapshot_calls) == 1
    ref_snapshot_call = ref_snapshot_calls[0]
    assert isinstance(ref_snapshot_call.args[3], ast.List)
    assert [element.value for element in ref_snapshot_call.args[3].elts] == [
        "for-each-ref",
        "--sort=refname",
        "--format=%(objectname) %(refname)",
        "refs",
    ]
    assert source_text.count("show" + "-ref") == 0
    assert source_text.count('"for-each-ref"') == 4
    forbidden_commands = {
        ("ls-tree", "-r"),
        ("diff-index",),
        ("status", "--porcelain=v2"),
    }
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        values = [element.value for element in node.elts if isinstance(element, ast.Constant) and isinstance(element.value, str)]
        for command in forbidden_commands:
            assert not all(part in values for part in command)
    assert "parse_git_ls_tree_object_closure" not in acquisition
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "parse_git_ls_tree_object_closure"
        for node in ast.walk(tree)
    )
    create = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "create_git_metadata_adapter")
    create_source = ast.get_source_segment(ACQ_PATH.read_text(encoding="utf-8"), create) or ""
    capture_calls = [
        node for node in ast.walk(create)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "capture_git_metadata_source"
    ]
    mkdtemp_calls = [
        node for node in ast.walk(create)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "tempfile"
        and node.func.attr == "mkdtemp"
    ]
    assert len(capture_calls) == 1 and len(mkdtemp_calls) == 1
    assert capture_calls[0].lineno < mkdtemp_calls[0].lineno
    capture_source_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "capture_git_metadata_source"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "parse_captured_git_ref_state"
        for node in ast.walk(capture_source_node)
    )
    for event in (
        "SOURCE_CAPTURE_REVALIDATED",
        "SOURCE_SEALED_PREVALIDATED",
        "SOURCE_SEALED_POSTVALIDATED",
    ):
        assert event in create_source
    finalize = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "finalize_git_metadata_adapter")
    finalize_source = ast.get_source_segment(ACQ_PATH.read_text(encoding="utf-8"), finalize) or ""
    assert "SOURCE_CLEANUP_PREVALIDATED" in finalize_source
    report["git_required_path_trie_index_root_and_checkpoint_cas"] = "PASS"


def main(argv=None):
    parser = fixture_argument_parser()
    fixture_args = parser.parse_args(argv)
    try:
        configure_repo_paths(fixture_args.repo_root)
    except ValueError:
        parser.exit(2, parser.prog + ": error: fixture-repo-root-contract\n")

    # Python 3.14 returns a shallow copy from runpy.run_path(); mutating that
    # copy does not patch the globals actually used by loaded functions.  Use
    # one sentinel function's true globals so fault injection exercises the
    # production call graph on every supported interpreter.
    verifier_loaded = runpy.run_path(str(VERIFIER_PATH))
    verifier = verifier_loaded["parse_package_archive"].__globals__
    acquisition_loaded = runpy.run_path(str(ACQ_PATH))
    acquisition = acquisition_loaded["main"].__globals__
    report = {}
    run_process_stderr_boundary_fixtures(acquisition, report)
    run_captured_ref_observation_fixtures(acquisition, report)
    run_verify_pack_parser_fixtures(acquisition, report)
    run_partial_git_boundary_fixtures(acquisition, report)

    good = package_archive()
    parsed = verifier["parse_package_archive"](
        "node_modules/fixture",
        {"version": "1.0.0"},
        good,
        {"node_modules": ("D", 0o755, 0, "-")},
    )
    assert parsed["package_name"] == "fixture"
    report["ustar_two_zero_eoa"] = "PASS"
    expect_error(
        "single EOA block",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            package_archive(eoa_blocks=1),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-eoa-or-root-count",
    )
    report["ustar_single_zero_rejected"] = "PASS"
    bundled = ustar_member("package/node_modules/evil.txt", b"bad")
    expect_error(
        "bundled node_modules",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            package_archive((bundled,)),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-bundled-node-modules-prohibited",
    )
    nested_bundled = ustar_member("package/lib/node_modules/evil.txt", b"bad")
    expect_error(
        "nested bundled node_modules",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            package_archive((nested_bundled,)),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-bundled-node-modules-prohibited",
    )
    report["bundled_node_modules_rejected"] = "PASS"
    regular_trailing_slash = ustar_member("package/file/", b"bad")
    expect_error(
        "regular member trailing slash",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            package_archive((regular_trailing_slash,)),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-regular-trailing-slash",
    )
    directory_double_slash = ustar_member("package/dir//", b"", 0o755, b"5")
    expect_error(
        "directory member double trailing slash",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            package_archive((directory_double_slash,)),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-directory-empty-segment",
    )
    report["ustar_path_type_and_empty_segment_enforced"] = "PASS"
    hidden_name_tail = mutate_first_ustar_header(good, len("package/") + 1, b"X")
    expect_error(
        "USTAR name hidden tail",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            hidden_name_tail,
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-name-nonzero-padding",
    )
    hidden_header_padding = mutate_first_ustar_header(good, 500, b"X")
    expect_error(
        "USTAR header hidden padding",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": "1.0.0"},
            hidden_header_padding,
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "tar-header-nonzero-padding",
    )
    report["ustar_header_zero_padding_enforced"] = "PASS"
    poisoned_version = "1.0.0\tpoison"
    expect_error(
        "package version TSV control",
        lambda: verifier["parse_package_archive"](
            "node_modules/fixture",
            {"version": poisoned_version},
            package_archive(package_manifest={"name": "fixture", "version": poisoned_version}),
            {"node_modules": ("D", 0o755, 0, "-")},
        ),
        "package-version-control",
    )
    concatenated = good + gzip.compress(b"", mtime=0)
    expect_error(
        "concatenated gzip",
        lambda: verifier["inflate_single_gzip"](concatenated),
        "gzip-multistream-or-trailing-data",
    )
    report["gzip_concatenation_rejected"] = "PASS"
    oversized = gzip.compress(b"x" * (verifier["MAX_TAR_STREAM"] + 1), mtime=0)
    expect_error(
        "oversized gzip",
        lambda: verifier["inflate_single_gzip"](oversized),
        "tar-stream-too-large",
    )
    report["gzip_output_ceiling"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-root-map-", dir="/private/tmp") as temporary:
        fixture_root = pathlib.Path(temporary)
        repo = fixture_root / "repo"
        cache = fixture_root / "cache"
        repo.mkdir()
        cache.mkdir()
        blob = good
        digest = hashlib.sha512(blob).digest()
        integrity = "sha512-" + base64.b64encode(digest).decode("ascii")
        digest_hex = digest.hex()
        cache_blob = cache / "_cacache/content-v2/sha512" / digest_hex[:2] / digest_hex[2:4] / digest_hex[4:]
        cache_blob.parent.mkdir(parents=True)
        write_bytes(cache_blob, blob, 0o600)
        manifest = {"name": "root-fixture", "version": "1.0.0", "devDependencies": {"fixture": "^1.0.0"}}
        lock = {
            "name": "root-fixture",
            "version": "1.0.0",
            "lockfileVersion": 3,
            "packages": {
                "": {"name": "root-fixture", "version": "1.0.0", "devDependencies": {"fixture": "^2.0.0"}},
                "node_modules/fixture": {
                    "version": "1.0.0",
                    "resolved": "https://registry.npmjs.org/fixture/-/fixture-1.0.0.tgz",
                    "integrity": integrity,
                },
            },
        }
        write_bytes(repo / "package.json", json.dumps(manifest, separators=(",", ":")).encode(), 0o600)
        write_bytes(repo / "package-lock.json", json.dumps(lock, separators=(",", ":")).encode(), 0o600)
        expect_error(
            "root dependency mismatch",
            lambda: verifier["build_expected"](str(repo), str(cache)),
            "root-dependency-map-mismatch",
        )
        lock["packages"][""]["devDependencies"]["fixture"] = "^1.0.0"
        rewrite_json(repo / "package-lock.json", lock)
        minimal = verifier["build_expected"](str(repo), str(cache))
        assert minimal["selected_package_count"] == 1 and minimal["resolution"]["required_missing"] == 0
        manifest["devDependencies"]["fixture"] = "^1.0.0\npoison"
        lock["packages"][""]["devDependencies"]["fixture"] = "^1.0.0\npoison"
        rewrite_json(repo / "package.json", manifest)
        rewrite_json(repo / "package-lock.json", lock)
        expect_error(
            "root dependency spec TSV control",
            lambda: verifier["build_expected"](str(repo), str(cache)),
            "root-dependency-spec-control",
        )
        manifest["devDependencies"]["fixture"] = "^1.0.0"
        lock["packages"][""]["devDependencies"]["fixture"] = "^1.0.0"
        lock["packages"]["node_modules/fixture"]["resolved"] += "\tpoison"
        rewrite_json(repo / "package.json", manifest)
        rewrite_json(repo / "package-lock.json", lock)
        expect_error(
            "registry URL TSV control",
            lambda: verifier["build_expected"](str(repo), str(cache)),
            "registry-url-control",
        )
        expect_error(
            "executor registry URL control",
            lambda: acquisition["validate_registry_url"](
                "https://registry.npmjs.org/fixture/-/fixture-1.0.0.tgz\tpoison"
            ),
            "RESOLVED_CONTROL_CHARACTER",
        )
        lock["packages"]["node_modules/fixture"]["resolved"] = (
            "https://registry.npmjs.org/fixture/-/fixture-1.0.0.tgz"
        )
        manifest["dependencies"] = {"missing": "1.0.0"}
        lock["packages"][""]["dependencies"] = {"missing": "1.0.0"}
        for path, value in ((repo / "package.json", manifest), (repo / "package-lock.json", lock)):
            rewrite_json(path, value)
        expect_error(
            "required dependency missing",
            lambda: verifier["build_expected"](str(repo), str(cache)),
            "required-dependency-missing",
        )
        del manifest["dependencies"]
        del lock["packages"][""]["dependencies"]
        rewrite_json(repo / "package.json", manifest)
        rewrite_json(repo / "package-lock.json", lock)
        outside_cache = fixture_root / "outside-cacache"
        os.rename(str(cache / "_cacache"), str(outside_cache))
        os.symlink(str(outside_cache), str(cache / "_cacache"))
        expect_error(
            "cache ancestor symlink",
            lambda: verifier["build_expected"](str(repo), str(cache)),
            "cache-content-unsafe-ancestor",
        )
    report["root_dependency_maps_exact"] = "PASS"
    report["required_dependency_missing_rejected"] = "PASS"
    report["tsv_control_fields_rejected"] = "PASS"
    report["cache_ancestor_symlink_rejected"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-verifier-tree-", dir="/private/tmp") as temporary:
        tree = pathlib.Path(temporary) / "node_modules"
        tree.mkdir(mode=0o755)
        os.chown(tree, -1, os.getgid())
        package = tree / "fixture"
        package.mkdir(mode=0o755)
        file_path = package / "index.js"
        write_bytes(file_path, b"fixture\n", 0o644)
        bin_dir = tree / ".bin"
        bin_dir.mkdir(mode=0o755)
        os.symlink("../fixture/index.js", str(bin_dir / "fixture"))
        root_fd = os.open(str(tree), os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
        try:
            layout, xattr_count = verifier["fingerprint_tree_fd"](root_fd)
            second_layout, second_count = verifier["fingerprint_tree_fd"](root_fd)
            assert layout == second_layout and xattr_count == second_count
            tree_manifest = verifier["layout_manifest"](layout)
            assert tree_manifest == verifier["layout_manifest"](second_layout)
            verifier_api = types.SimpleNamespace(
                fingerprint_tree_fd=verifier["fingerprint_tree_fd"],
                layout_manifest=verifier["layout_manifest"],
            )
            stable = acquisition["stable_tree_attestation"](
                root_fd,
                verifier_api,
                {"layout": layout, "tree": tree_manifest},
                acquisition["Exit"].POST_INSTALL,
                "FIXTURE_STABLE",
            )
            assert stable == tree_manifest
            bad_api = types.SimpleNamespace(
                fingerprint_tree_fd=lambda _fd: layout,
                layout_manifest=verifier["layout_manifest"],
            )
            expect_error(
                "verifier ABI tuple",
                lambda: acquisition["stable_tree_attestation"](
                    root_fd,
                    bad_api,
                    {"layout": layout, "tree": tree_manifest},
                    acquisition["Exit"].POST_INSTALL,
                    "FIXTURE_BAD_ABI",
                ),
                "FIXTURE_BAD_ABI_VERIFIER_ABI",
            )
            hardlink = package / "hardlink.js"
            os.link(str(file_path), str(hardlink))
            expect_error(
                "hardlink",
                lambda: verifier["fingerprint_tree_fd"](root_fd),
                "tree-file-hardlink",
            )
            hardlink.unlink()
            symlink_hardlink = bin_dir / "fixture-hard"
            os.link(str(bin_dir / "fixture"), str(symlink_hardlink), follow_symlinks=False)
            expect_error(
                "symlink hardlink",
                lambda: verifier["fingerprint_tree_fd"](root_fd),
                "tree-symlink-hardlink",
            )
            symlink_hardlink.unlink()
            run_checked(["/usr/bin/xattr", "-w", "com.gov01.fixture.bad", "1", str(file_path)], tree)
            expect_error(
                "unexpected xattr",
                lambda: verifier["fingerprint_tree_fd"](root_fd),
                "tree-unapproved-xattr",
            )
            run_checked(["/usr/bin/xattr", "-d", "com.gov01.fixture.bad", str(file_path)], tree)
            acl_text = "user:%s allow read" % pwd.getpwuid(os.getuid()).pw_name
            acl_setup = subprocess.run(
                ["/bin/chmod", "+a", acl_text, str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if acl_setup.returncode == 0:
                expect_error(
                    "extended ACL",
                    lambda: verifier["fingerprint_tree_fd"](root_fd),
                    "tree-extended-acl",
                )
                run_checked(["/bin/chmod", "-a#", "0", str(file_path)], tree)
                report["extended_acl_rejected"] = "PASS"
            else:
                report["extended_acl_rejected"] = "SKIP_SETUP_UNAVAILABLE"
        finally:
            os.close(root_fd)
    report["fingerprint_stability_hardlink_xattr_and_abi"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-stage-", dir="/private/tmp") as temporary:
        stage_repo = pathlib.Path(temporary) / "repo"
        stage_repo.mkdir(mode=0o700)
        os.chown(stage_repo, -1, os.getgid())
        payload = b"static payload\n"
        stage_layout = {
            "node_modules": ("D", 0o755, 0, "-"),
            "node_modules/fixture": ("D", 0o755, 0, "-"),
            "node_modules/fixture/index.js": ("F", 0o644, len(payload), hashlib.sha256(payload).hexdigest()),
        }
        stage_expected = {"layout": stage_layout, "tree": verifier["layout_manifest"](stage_layout)}
        challenge = "GOV01-SA-20260820-" + ("d" * 64)
        marker = acquisition["marker_bytes"](b"m" * 32, challenge, "e" * 64)
        repo_fd = os.open(str(stage_repo), os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
        stage_fd = None
        try:
            stage_fd, _ = acquisition["materialize_stage"](
                repo_fd,
                ".gov01-toolchain-stage-" + challenge,
                marker,
                stage_expected,
                {"node_modules/fixture/index.js": payload},
            )
            staged_layout, staged_tree = acquisition["fingerprint_stage_with_marker"](
                stage_fd, marker, types.SimpleNamespace(layout_manifest=verifier["layout_manifest"])
            )
            assert staged_layout == stage_layout and staged_tree == stage_expected["tree"]
            acquisition["finalize_stage_marker"](stage_fd, marker)
            acquisition["stable_tree_attestation"](
                stage_fd,
                types.SimpleNamespace(
                    fingerprint_tree_fd=verifier["fingerprint_tree_fd"],
                    layout_manifest=verifier["layout_manifest"],
                ),
                stage_expected,
                acquisition["Exit"].PRE_WORKTREE_CAS,
                "FIXTURE_SEALED_STAGE",
            )
        finally:
            if stage_fd is not None:
                os.close(stage_fd)
            os.close(repo_fd)
    report["stage_materialize_marker_and_double_attest"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-attempt-state-", dir="/private/tmp") as temporary:
        repo = pathlib.Path(temporary) / "repo"
        repo.mkdir(mode=0o700)
        challenge = "GOV01-SA-20260820-" + ("b" * 64)
        stage_name = ".gov01-toolchain-stage-" + challenge
        stage = repo / stage_name
        stage.mkdir(mode=0o700)
        write_bytes(stage / acquisition["INCOMPLETE_MARKER"], b"marker", 0o600)
        repo_fd = os.open(str(repo), os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
        try:
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](repo_fd, stage_name, observed)
            assert observed.stage_state == "retained-marker-present"
            (stage / acquisition["INCOMPLETE_MARKER"]).unlink()
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](repo_fd, stage_name, observed)
            assert observed.stage_state == "retained-marker-not-yet-created"
            os.chmod(stage, 0o755)
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](repo_fd, stage_name, observed)
            assert observed.stage_state == "retained-marker-removed"
            os.rename(stage_name, acquisition["TARGET_NAME"], src_dir_fd=repo_fd, dst_dir_fd=repo_fd)
            target_meta = os.stat(acquisition["TARGET_NAME"], dir_fd=repo_fd, follow_symlinks=False)
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](repo_fd, stage_name, observed)
            assert observed.publication_state == "target-observed-unattributed-fail-closed"
            assert observed.target_disposition == "retain-unattributed-target-user-decision-required"
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](
                repo_fd,
                stage_name,
                observed,
                promoted_by_this_attempt=True,
                expected_target_inode=(target_meta.st_dev, target_meta.st_ino),
            )
            assert observed.stage_state == "renamed-to-target"
            assert observed.target_disposition == "retain-unauthorized-target-user-decision-required"
            original_observer_stat = acquisition["os"].stat

            def target_stat_error(path, *args, **kwargs):
                if path == acquisition["TARGET_NAME"] and kwargs.get("dir_fd") == repo_fd:
                    raise OSError("fixture target stat failure")
                return original_observer_stat(path, *args, **kwargs)

            observed = acquisition["AttemptState"]()
            observed.target_promoted()
            acquisition["os"].stat = target_stat_error
            try:
                acquisition["observe_retained_publication_state"](
                    repo_fd,
                    stage_name,
                    observed,
                    promoted_by_this_attempt=True,
                    expected_target_inode=(target_meta.st_dev, target_meta.st_ino),
                )
            finally:
                acquisition["os"].stat = original_observer_stat
            assert observed.publication_state == "unknown-fail-closed"
            assert observed.stage_state == "renamed-to-target"
            observed.terminal_success_publication_failed()
            assert observed.publication_state == "unknown-fail-closed"
            assert observed.ledger_terminal_state == "terminal-success-recorded"

            def stage_stat_error(path, *args, **kwargs):
                if path == stage_name and kwargs.get("dir_fd") == repo_fd:
                    raise OSError("fixture stage stat failure")
                return original_observer_stat(path, *args, **kwargs)

            observed = acquisition["AttemptState"]()
            observed.target_promoted()
            acquisition["os"].stat = stage_stat_error
            try:
                acquisition["observe_retained_publication_state"](
                    repo_fd,
                    stage_name,
                    observed,
                    promoted_by_this_attempt=True,
                    expected_target_inode=(target_meta.st_dev, target_meta.st_ino),
                )
            finally:
                acquisition["os"].stat = original_observer_stat
            assert observed.publication_state == "rename-succeeded-attestation-incomplete"
            assert observed.stage_state == "unknown-fail-closed"
            assert observed.target_disposition == "unknown-user-decision-required"
            observed.terminal_success_publication_failed()
            assert observed.publication_state == "rename-succeeded-attestation-incomplete"
            assert observed.ledger_terminal_state == "terminal-success-recorded"
            stage.mkdir(mode=0o700)
            write_bytes(stage / acquisition["INCOMPLETE_MARKER"], b"marker", 0o600)
            observed = acquisition["AttemptState"]()
            acquisition["observe_retained_publication_state"](
                repo_fd,
                stage_name,
                observed,
                promoted_by_this_attempt=True,
                expected_target_inode=(target_meta.st_dev, target_meta.st_ino),
            )
            assert observed.publication_state == "attributed-target-and-stage-both-observed-fail-closed"
            assert observed.stage_state == "retained-marker-present"
            assert observed.target_disposition == "retain-unauthorized-target-user-decision-required"
        finally:
            os.close(repo_fd)
    report["attempt_state_marker_present_removed_and_post_rename"] = "PASS"

    ContractError = acquisition["ContractError"]
    Exit = acquisition["Exit"]
    base = pathlib.Path("/private/tmp/gov01-fixture")
    locator_challenge = "GOV01-SA-20260820-" + ("e" * 64)
    locator_generation_challenge = "GOV01-GEN-20260820-" + ("e" * 64)
    pending_name = "GOV-01-toolchain-static-acquisition-pending-" + locator_generation_challenge + ".json"
    vault_args = argparse.Namespace(
        repo_root=str(base / "repo"),
        cache_root=str(base / "private-canvas-vault-cache"),
        state_root=str(base / "state"),
        key_file=str(base / "state/hmac.key"),
        envelope=str(base / "repo/_bmad-output/审查/phase0a-annotation-truth" / pending_name),
    )
    reason = expect_error("vault locator", lambda: acquisition["validate_locator_boundaries"](vault_args))
    assert isinstance(reason, str) and reason.endswith("_VAULT_LOCATOR")
    overlap_args = argparse.Namespace(**vars(vault_args))
    overlap_args.cache_root = str(base / "cache")
    overlap_args.state_root = str(base / "cache/state")
    overlap_args.key_file = str(base / "cache/state/hmac.key")
    expect_error("overlap", lambda: acquisition["validate_locator_boundaries"](overlap_args), "CACHE_STATE_OVERLAP")
    exact_child_args = argparse.Namespace(**vars(vault_args))
    exact_child_args.cache_root = str(base / "cache")
    expected_relative = acquisition["validate_locator_boundaries"](exact_child_args)
    assert expected_relative.endswith(pending_name)
    for label, key_file in (
        ("misnamed", exact_child_args.state_root + "/other.key"),
        ("sibling", str(base / "hmac.key")),
        ("ancestor", exact_child_args.state_root),
        ("outside", str(base / "outside/hmac.key")),
    ):
        invalid_key_args = argparse.Namespace(**vars(exact_child_args))
        invalid_key_args.key_file = key_file
        expect_error(
            "state key " + label,
            lambda value=invalid_key_args: acquisition["validate_locator_boundaries"](value),
            "STATE_KEY_EXACT_CHILD",
        )
    report["vault_overlap_and_state_key_exact_child"] = "PASS"

    captured_git_invocations = []
    original_run_process = acquisition["run_process"]
    original_verify_adapter = acquisition["verify_git_metadata_adapter"]
    original_sandbox_profile = acquisition["git_read_sandbox_profile"]
    acquisition["_GIT_DEVELOPER_ROOTS"]["/fixture/git"] = "/fixture/developer"
    fixture_boundary = acquisition["GitMetadataAdapter"](
        "/fixture/developer",
        "/fixture/repo",
        "/fixture/repo/.git/worktrees/fixture",
        "/fixture/repo/.git",
        "/private/tmp/gov01-git-adapter-fixture",
        "/private/tmp/gov01-git-adapter-fixture/git",
        97,
        98,
        "1" * 64,
        ("a" * 40,),
        "2" * 64,
        "3" * 64,
        (1, 2),
        (1, 3),
        [],
    )
    acquisition["run_process"] = lambda argv, *_args, **kwargs: (
        captured_git_invocations.append((list(argv), dict(kwargs))) or b""
    )
    acquisition["verify_git_metadata_adapter"] = lambda _boundary: None
    acquisition["git_read_sandbox_profile"] = lambda *_args, **_kwargs: b"(version 1)\n(deny default)\n"
    try:
        for dirty_arguments, dirty_label in (
            (["diff-files", "--ignore-submodules=all", "--name-only", "-z"], "FIXTURE_GIT_DIFF_FILES"),
            (["ls-files", "--others", "--exclude-standard", "-z"], "FIXTURE_GIT_LS_FILES_OTHERS"),
        ):
            acquisition["run_git"](
                "/fixture/git",
                "/fixture/repo",
                fixture_boundary,
                dirty_arguments,
                dirty_label,
                enumerates_worktree=True,
                authorized_tree_excludes=(".gov01-toolchain-stage-" + locator_challenge, "node_modules"),
                authorized_exact_file_excludes=(expected_relative,),
            )
    finally:
        acquisition["run_process"] = original_run_process
        acquisition["verify_git_metadata_adapter"] = original_verify_adapter
        acquisition["git_read_sandbox_profile"] = original_sandbox_profile
        acquisition["_GIT_DEVELOPER_ROOTS"].pop("/fixture/git", None)
    assert len(captured_git_invocations) == 2
    exact_pathspec = ":(top,literal,exclude)" + expected_relative
    for git_argv, git_invocation_kwargs in captured_git_invocations:
        assert git_argv.count(exact_pathspec) == 1
        assert exact_pathspec + "/**" not in git_argv
        assert "-C" not in git_argv and not any(value.startswith("core.worktree=") for value in git_argv)
        assert git_argv.count("--git-dir=.") == 1
        assert git_argv.count("--work-tree=/fixture/repo") == 1
        assert git_invocation_kwargs.get("working_directory_fd") == 98
        assert ":(exclude).git" in git_argv and ":(exclude).git/**" in git_argv
        assert ":(exclude)node_modules" in git_argv and ":(exclude)node_modules/**" in git_argv
        assert ":(exclude).gov01-toolchain-stage-" + locator_challenge in git_argv
        assert ":(exclude).gov01-toolchain-stage-" + locator_challenge + "/**" in git_argv
    expect_error(
        "tree exact exclusion ancestor overlap",
        lambda: acquisition["git_snapshot"](
            "/fixture/repo",
            b"k" * 32,
            "/fixture/git",
            authorized_tree_excludes=("node_modules",),
            authorized_exact_file_excludes=("node_modules/child.json",),
        ),
        "GIT_EXCLUSION_CLASS_OVERLAP",
    )
    expect_error(
        "exact tree exclusion ancestor overlap",
        lambda: acquisition["git_snapshot"](
            "/fixture/repo",
            b"k" * 32,
            "/fixture/git",
            authorized_tree_excludes=("private/output",),
            authorized_exact_file_excludes=("private",),
        ),
        "GIT_EXCLUSION_CLASS_OVERLAP",
    )

    with tempfile.TemporaryDirectory(prefix="gov01-envelope-fixed-point-", dir="/private/tmp") as temporary:
        repo = pathlib.Path(temporary) / "repo"
        envelope_path = repo / expected_relative
        envelope_path.parent.mkdir(parents=True)
        write_bytes(envelope_path, b'{"generation":1}\n', 0o600)
        manifest_key = b"m" * 32
        excluded_first = acquisition["dirty_path_manifest_commitment"](str(repo), b"", manifest_key)
        rewrite_bytes(envelope_path, b'{"generation":2}\n')
        excluded_second = acquisition["dirty_path_manifest_commitment"](str(repo), b"", manifest_key)
        assert excluded_first == excluded_second
        included_status = b"? " + expected_relative.encode("utf-8") + b"\x00"
        included_second = acquisition["dirty_path_manifest_commitment"](
            str(repo), included_status, manifest_key
        )
        rewrite_bytes(envelope_path, b'{"generation":3}\n')
        included_third = acquisition["dirty_path_manifest_commitment"](
            str(repo), included_status, manifest_key
        )
        assert included_second != included_third
        sibling_path = envelope_path.with_name("user-owned-sibling.json")
        write_bytes(sibling_path, b'{"sibling":1}\n', 0o600)
        sibling_relative = sibling_path.relative_to(repo).as_posix()
        sibling_status = b"? " + sibling_relative.encode("utf-8") + b"\x00"
        sibling_first = acquisition["dirty_path_manifest_commitment"](
            str(repo), sibling_status, manifest_key
        )
        rewrite_bytes(sibling_path, b'{"sibling":2}\n')
        sibling_second = acquisition["dirty_path_manifest_commitment"](
            str(repo), sibling_status, manifest_key
        )
        assert sibling_first != sibling_second

    executor_tree = ast.parse(ACQ_PATH.read_text(encoding="utf-8"))
    snapshot_calls = {"build_census": [], "command_acquire": []}
    for node in executor_tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in snapshot_calls:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Name):
                continue
            if child.func.id != "git_snapshot":
                continue
            keywords = {keyword.arg: keyword.value for keyword in child.keywords if keyword.arg is not None}
            assert isinstance(keywords.get("authorized_tree_excludes"), ast.Name)
            assert keywords["authorized_tree_excludes"].id == "tree_exclusions"
            assert isinstance(keywords.get("authorized_exact_file_excludes"), ast.Name)
            assert keywords["authorized_exact_file_excludes"].id == "exact_file_exclusions"
            snapshot_calls[node.name].append(child)
    assert len(snapshot_calls["build_census"]) == 1
    assert len(snapshot_calls["command_acquire"]) == 3
    report["exact_envelope_file_exclusion_breaks_fixed_point"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-claim-", dir="/private/tmp") as temporary:
        state_root = pathlib.Path(temporary) / "state"
        state_root.mkdir(mode=0o700)
        os.chmod(state_root, 0o700)
        expected_owner_uid = os.getuid()
        expected_group_gid = os.stat(state_root, follow_symlinks=False).st_gid
        challenge = "GOV01-SA-20260820-" + ("a" * 64)
        expect_error(
            "missing claims",
            lambda: acquisition["verify_claim_preimage"](str(state_root), challenge),
            "PRIVATE_CONTAINER_OPEN",
        )
        assert not (state_root / "claims").exists()
        claims = state_root / "claims"
        claims.mkdir(mode=0o700)
        os.chmod(claims, 0o700)
        key = b"k" * 32
        claim_preimage = acquisition["verify_claim_preimage"](str(state_root), challenge)
        moved_claims = state_root / "claims-moved"
        os.rename(claims, moved_claims)
        claims.mkdir(mode=0o700)
        os.chown(claims, -1, os.getgid())
        expect_error(
            "claims container swap",
            lambda: acquisition["create_permanent_claim"](
                str(state_root), key, challenge, "b" * 64, claim_preimage,
                expected_owner_uid, expected_group_gid, "2099-01-01T00:00:00Z"
            ),
            "STATE_ROOT_IDENTITY_DRIFT",
        )
        assert not (claims / challenge).exists()
        os.rmdir(claims)
        os.rename(moved_claims, claims)
        claim_preimage = acquisition["verify_claim_preimage"](str(state_root), challenge)
        attempt = acquisition["AttemptState"]()
        original_getgid = acquisition["os"].getgid
        acquisition["os"].getgid = lambda: expected_group_gid + 777
        try:
            claim_fd, ledger = acquisition["create_permanent_claim"](
                str(state_root), key, challenge, "b" * 64, claim_preimage,
                expected_owner_uid, expected_group_gid, "2099-01-01T00:00:00Z", attempt=attempt
            )
        finally:
            acquisition["os"].getgid = original_getgid
        assert attempt.challenge_state == "claimed-consumed"
        assert attempt.claim_state == "created-0700"
        assert attempt.ledger_terminal_state == "receipt-consumed-recorded"
        ledger.append("attempt-failed", ledger_event_data("attempt-failed", False))
        terminal_report = ledger.verify_terminal()
        assert terminal_report["terminal_kind"] == "failure" and terminal_report["record_count"] == 2
        ledger.close()
        os.close(claim_fd)
        ledger_path = claims / challenge / "ledger.jsonl"
        assert ledger_path.is_file()
        ledger_lines = ledger_path.read_bytes().splitlines()
        if len(ledger_lines) != 2:
            raise AssertionError("ledger line count %d: %r" % (len(ledger_lines), ledger_lines))
        assert all(json.loads(line) for line in ledger_lines)
        expect_error(
            "claim replay",
            lambda: acquisition["verify_claim_preimage"](str(state_root), challenge),
            "CHALLENGE_ALREADY_CLAIMED",
        )
    report["claims_existing_first_write_and_replay"] = "PASS"

    for fault_name in (
        "post-mkdir-open",
        "post-mkdir-policy",
        "claims-directory-fsync",
        "ledger-create",
        "first-ledger-write",
        "ledger-directory-fsync",
    ):
        exercise_claim_fault(acquisition, fault_name)
    report["claim_first_write_faults_retained_and_consumed"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-expiry-", dir="/private/tmp") as temporary:
        state_root = pathlib.Path(temporary) / "state"
        state_root.mkdir(mode=0o700)
        claims = state_root / "claims"
        claims.mkdir(mode=0o700)
        owner_uid = os.stat(state_root, follow_symlinks=False).st_uid
        group_gid = os.stat(state_root, follow_symlinks=False).st_gid
        challenge = "GOV01-SA-20260820-" + ("9" * 64)
        preimage = acquisition["verify_claim_preimage"](
            str(state_root), challenge, expected_uid=owner_uid, expected_gid=group_gid
        )
        deadline = "2026-08-21T00:00:00Z"
        acquisition["assert_deadline_not_expired"](
            deadline,
            lambda: datetime.datetime(2026, 8, 20, 23, 59, 59, tzinfo=datetime.timezone.utc),
        )
        attempt = acquisition["AttemptState"]()
        expect_error(
            "expiry adjacent to claim mkdir",
            lambda: acquisition["create_permanent_claim"](
                str(state_root), b"k" * 32, challenge, "b" * 64, preimage,
                owner_uid, group_gid, deadline, attempt=attempt,
                clock=lambda: datetime.datetime(2026, 8, 21, 0, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            "ENVELOPE_EXPIRED_DURING_ATTEMPT",
        )
        assert not (claims / challenge).exists()
        assert attempt.claim_state == "not-created"
        assert attempt.failure_projection()["challenge_state"] == "preclaim-pending"
    report["expiry_rechecked_at_first_write_boundary"] = "PASS"

    with tempfile.TemporaryDirectory(prefix="gov01-historical-claims-", dir="/private/tmp") as temporary:
        state_root = pathlib.Path(temporary) / "state"
        claims = state_root / "claims"
        state_root.mkdir(mode=0o700)
        claims.mkdir(mode=0o700)
        old_challenge = "GOV01-SA-20260819-" + ("1" * 64)
        fresh_challenge = "GOV01-SA-20260820-" + ("2" * 64)
        (claims / old_challenge).mkdir(mode=0o700)
        # A retained failed historical claim consumes only its own challenge;
        # it does not globally brick a separately approved fresh SA.
        fresh_preimage = acquisition["verify_claim_preimage"](
            str(state_root),
            fresh_challenge,
        )
        assert set(fresh_preimage) == {"state_root", "claims"}
        (claims / fresh_challenge).mkdir(mode=0o700)
        expect_error(
            "fresh acquisition challenge already claimed",
            lambda: acquisition["verify_claim_preimage"](
                str(state_root),
                fresh_challenge,
            ),
            "CHALLENGE_ALREADY_CLAIMED",
        )
    report["historical_claim_retained_fresh_challenge_boundary"] = "PASS"

    key = b"p" * 32
    locator_args = argparse.Namespace(
        repo_root="/private/tmp/gov01/repo",
        cache_root="/private/tmp/gov01/cache",
        state_root="/private/tmp/gov01/state",
        key_file="/private/tmp/gov01/state/hmac.key",
        envelope=(
            "/private/tmp/gov01/repo/_bmad-output/审查/phase0a-annotation-truth/"
            "GOV-01-toolchain-static-acquisition-pending-GOV01-GEN-20260820-" + ("c" * 64) + ".json"
        ),
    )
    locators = acquisition["locator_commitments"](locator_args, key)
    zero = "0" * 64
    expected = {
        "content_receipt_sha256": zero,
        "ustar_closure_sha256": zero,
        "resolution": {"sha256": zero},
        "tree": {"sha256": zero},
    }
    body = acquisition["build_private_preapproval_body"](
        {"approval_challenge_id": "GOV01-SA-20260820-" + ("c" * 64), "census_at_utc": "2026-08-20T00:00:00Z"},
        key,
        locators,
        zero,
        zero,
        {"commitment": zero},
        {"toolchain_set_receipt_sha256": zero},
        b"{}",
        {"claude_session_count": 0},
        167,
        13916529,
        12,
        expected,
    )
    assert tuple(body) == acquisition["PRIVATE_PREAPPROVAL_FIELDS"]
    assert not {"receipt_digest", "envelope_raw_sha256", "captured_at_utc", "pid"}.intersection(body)
    first = acquisition["private_preapproval_commitment"](key, body)
    assert first == acquisition["private_preapproval_commitment"](key, dict(body))
    changed = dict(body)
    changed["host_selected_cache_bytes"] += 1
    assert first != acquisition["private_preapproval_commitment"](key, changed)
    report["deterministic_private_preapproval"] = "PASS"

    run_git_metadata_adapter_hostile_fixtures(acquisition, report)

    schemas = {
        "envelope": load_json_no_duplicates(ENVELOPE_SCHEMA_PATH),
        "private": load_json_no_duplicates(PRIVATE_SCHEMA_PATH),
        "public": load_json_no_duplicates(PUBLIC_SCHEMA_PATH),
    }
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        verify_local_refs(schema)
    report["schemas_duplicate_key_meta_schema_and_local_refs"] = "PASS"

    synthetic_envelope = synthesize_schema_instance(schemas["envelope"])
    envelope_validator = Draft202012Validator(schemas["envelope"])
    envelope_validator.validate(synthetic_envelope)
    witness_now = datetime.datetime(2026, 8, 20, 0, 0, 0, tzinfo=datetime.timezone.utc)

    def validate_synthetic_manual(value):
        return acquisition["validate_manual_envelope_contract"](value, now=witness_now)

    validate_synthetic_manual(synthetic_envelope)
    assert synthetic_envelope["execution_plan"][
        "git_metadata_adapter_bootstrap_sandbox_profile"
    ] == acquisition["GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE_V4"]
    retired_bootstrap_profile = copy.deepcopy(synthetic_envelope)
    retired_bootstrap_profile["execution_plan"][
        "git_metadata_adapter_bootstrap_sandbox_profile"
    ] = "retired-bootstrap-sandbox-profile-v3"
    expect_schema_error(
        "retired bootstrap sandbox profile schema",
        envelope_validator,
        retired_bootstrap_profile,
    )
    expect_error(
        "retired bootstrap sandbox profile runtime",
        lambda: validate_synthetic_manual(retired_bootstrap_profile),
        "GIT_METADATA_ADAPTER_BOOTSTRAP_SANDBOX_PROFILE",
    )
    report["git_metadata_adapter_bootstrap_v4_schema_runtime_contract"] = "PASS"
    builder_envelope = build_real_pending_envelope_from_synthetic_observations(
        acquisition,
        synthetic_envelope,
    )
    builder_source_raw = ACQ_PATH.read_bytes()
    builder_source_sha256 = hashlib.sha256(builder_source_raw).hexdigest()
    builder_artifact = next(
        entry for entry in builder_envelope["artifacts"] if entry["role"] == "static-executor"
    )
    if (
        builder_artifact["raw_file_sha256"] != builder_source_sha256
        or builder_artifact["byte_length"] != len(builder_source_raw)
    ):
        raise AssertionError("production pending builder content address drift")
    builder_scalar_parity = pending_builder_bool_int_scalar_type_parity(
        acquisition,
        envelope_validator,
        builder_envelope,
        witness_now,
    )
    builder_scalar_parity.update(
        {
            "builder_source_sha256": builder_source_sha256,
            "builder_source_bytes": len(builder_source_raw),
        }
    )
    assert synthetic_envelope["state"] == "pending-user-confirmation"
    assert synthetic_envelope["private_state_authorization"]["hmac_key_id"] == "0" * 64
    bad_architecture = copy.deepcopy(synthetic_envelope)
    bad_architecture["frozen_toolchain"]["architecture"] = "x86_64"
    expect_schema_error("x86 envelope", envelope_validator, bad_architecture)
    duplicate_path = copy.deepcopy(synthetic_envelope)
    duplicate_path["artifacts"][1]["path"] = duplicate_path["artifacts"][0]["path"]
    expect_schema_error("duplicate artifact path schema", envelope_validator, duplicate_path)
    expect_error(
        "duplicate artifact path manual contract",
        lambda: validate_synthetic_manual(duplicate_path),
        "ARTIFACT_DUPLICATE_PATH",
    )
    sha1_with_sha256_oids = copy.deepcopy(synthetic_envelope)
    sha1_with_sha256_oids["authorization_preimage"]["git_object_format"] = "sha1"
    expect_schema_error("sha1 with 64-byte OIDs", envelope_validator, sha1_with_sha256_oids)
    expect_error(
        "sha1 with 64-byte OIDs manual contract",
        lambda: validate_synthetic_manual(sha1_with_sha256_oids),
        "PREIMAGE_OID",
    )
    wrong_package_path = copy.deepcopy(synthetic_envelope)
    package_artifact = next(item for item in wrong_package_path["artifacts"] if item["role"] == "package-manifest")
    package_artifact["path"] = "wrong-package.json"
    expect_schema_error("package role path", envelope_validator, wrong_package_path)
    expect_error(
        "package role path manual contract",
        lambda: validate_synthetic_manual(wrong_package_path),
        "ARTIFACT_ROLE_PATH_BINDING",
    )
    for label, control in (("DEL", "\u007f"), ("C1", "\u0085")):
        controlled = copy.deepcopy(synthetic_envelope)
        controlled["artifacts"][0]["path"] += control
        expect_schema_error(label + " artifact path", envelope_validator, controlled)
        expect_error(
            label + " artifact path manual contract",
            lambda value=controlled: validate_synthetic_manual(value),
        )
    for label, hostile_path in (
        ("casefold git alias", ".GIT/config"),
        ("nested casefold git alias", "public/.gIt/config"),
        ("obsidian component", "public/.ObSiDiAn/plugin.json"),
        ("vault component", "public/Private-Canvas-Vault/file.json"),
        ("empty segment", "public//file.json"),
        ("dot segment", "public/./file.json"),
        ("bidi override", "public/fi\u202ele.json"),
        ("bidi isolate", "public/fi\u2066le.json"),
        ("zero width", "public/fi\u200ble.json"),
    ):
        hostile = copy.deepcopy(synthetic_envelope)
        hostile["artifacts"][0]["path"] = hostile_path
        expect_schema_error(label + " artifact path schema", envelope_validator, hostile)
        expect_error(
            label + " artifact path manual",
            lambda value=hostile: validate_synthetic_manual(value),
        )
    for field in ("logical_id", "version"):
        hostile_tool = copy.deepcopy(synthetic_envelope)
        hostile_tool["frozen_toolchain"]["entries"][0][field] = synthetic_private_locator(
            "FixtureSecret", "private-tool"
        )
        expect_schema_error("private tool " + field + " schema", envelope_validator, hostile_tool)
        expect_error(
            "private tool " + field + " manual",
            lambda value=hostile_tool: validate_synthetic_manual(value),
            "ENVELOPE_PUBLIC_PRIVACY",
        )
        assert acquisition["has_forbidden_pending_envelope_value"](hostile_tool)
    misplaced_public_system_path = copy.deepcopy(synthetic_envelope)
    misplaced_public_system_path["frozen_toolchain"]["entries"][0]["version"] = "/usr/bin/xcode-select"
    expect_schema_error(
        "public system path relocated into tool version schema",
        envelope_validator,
        misplaced_public_system_path,
    )
    expect_error(
        "public system path relocated into tool version manual",
        lambda: validate_synthetic_manual(misplaced_public_system_path),
        "ENVELOPE_PUBLIC_PRIVACY",
    )
    assert acquisition["has_forbidden_pending_envelope_value"](misplaced_public_system_path)
    self_artifact = copy.deepcopy(synthetic_envelope)
    self_artifact["artifacts"][0]["path"] = self_artifact["authorization_preimage"][
        "envelope_repo_relative_path"
    ]
    expect_schema_error("pending envelope self artifact schema", envelope_validator, self_artifact)
    expect_error(
        "pending envelope self artifact manual",
        lambda: validate_synthetic_manual(self_artifact),
        "ARTIFACT_ROLE_PATH_BINDING",
    )
    wrong_generated_path = copy.deepcopy(synthetic_envelope)
    wrong_generated_path["generation_authorization"][
        "generated_acquisition_envelope_repo_relative_path"
    ] = wrong_generated_path["generation_authorization"][
        "generated_acquisition_envelope_repo_relative_path"
    ].replace(".json", "-sibling.json")
    expect_error(
        "generation output path cross binding",
        lambda: validate_synthetic_manual(wrong_generated_path),
        "GENERATION_AUTHORIZATION_PATH",
    )
    wrong_preimage_path = copy.deepcopy(synthetic_envelope)
    wrong_preimage_path["authorization_preimage"]["envelope_repo_relative_path"] = (
        wrong_preimage_path["authorization_preimage"]["envelope_repo_relative_path"].replace(
            ".json", "-sibling.json"
        )
    )
    expect_error(
        "authorization preimage output path cross binding",
        lambda: validate_synthetic_manual(wrong_preimage_path),
        "ENVELOPE_PATH_BINDING",
    )
    wrong_exclusion_profile = copy.deepcopy(synthetic_envelope)
    wrong_exclusion_profile["authorization_preimage"][
        "envelope_git_status_exclusion_profile"
    ] = "git-status-parent-subtree-exclusion"
    expect_schema_error(
        "generation exclusion profile schema",
        envelope_validator,
        wrong_exclusion_profile,
    )
    expect_error(
        "generation exclusion profile manual",
        lambda: validate_synthetic_manual(wrong_exclusion_profile),
        "ENVELOPE_PATH_BINDING",
    )
    for field, detail in (
        ("executor_argv_template_sha256", "EXECUTOR_ARGV_TEMPLATE_RECEIPT"),
        ("evidence_command_templates_sha256", "EVIDENCE_COMMAND_TEMPLATES_RECEIPT"),
    ):
        drifted_template = copy.deepcopy(synthetic_envelope)
        drifted_template["execution_plan"][field] = "f" * 64
        expect_error(
            field + " manual receipt drift",
            lambda value=drifted_template: validate_synthetic_manual(value),
            detail,
        )
    short_challenge = copy.deepcopy(synthetic_envelope)
    short_challenge["approval_challenge_id"] = "GOV01-SA-20260820-" + ("a" * 32)
    expect_schema_error("short challenge schema", envelope_validator, short_challenge)
    expect_error("short challenge manual", lambda: validate_synthetic_manual(short_challenge), "MANUAL_CHALLENGE")
    wrong_challenge_date = copy.deepcopy(synthetic_envelope)
    wrong_challenge_date["approval_challenge_id"] = "GOV01-SA-20260819-" + ("a" * 64)
    expect_error(
        "challenge census date manual",
        lambda: validate_synthetic_manual(wrong_challenge_date),
        "CHALLENGE_CENSUS_DATE",
    )
    exact_ttl = copy.deepcopy(synthetic_envelope)
    exact_ttl["not_after_utc"] = "2026-08-21T00:00:00Z"
    validate_synthetic_manual(exact_ttl)
    excessive_ttl = copy.deepcopy(synthetic_envelope)
    excessive_ttl["not_after_utc"] = "2026-08-21T00:00:01Z"
    expect_error("excessive ttl manual", lambda: validate_synthetic_manual(excessive_ttl), "ENVELOPE_TTL")
    exact_future_skew = copy.deepcopy(synthetic_envelope)
    exact_future_skew["census_at_utc"] = "2026-08-20T00:05:00Z"
    validate_synthetic_manual(exact_future_skew)
    excessive_future_skew = copy.deepcopy(synthetic_envelope)
    excessive_future_skew["census_at_utc"] = "2026-08-20T00:05:01Z"
    expect_error(
        "census future skew manual",
        lambda: validate_synthetic_manual(excessive_future_skew),
        "CENSUS_FUTURE_SKEW",
    )
    historical_census = copy.deepcopy(synthetic_envelope)
    historical_census["census_at_utc"] = "2026-08-19T23:00:00Z"
    historical_census["approval_challenge_id"] = "GOV01-SA-20260819-" + ("a" * 64)
    historical_census["artifact_id"] = "GOV-01-STATIC-ACQUISITION-20260819-" + ("a" * 16)
    historical_census["not_after_utc"] = "2026-08-20T01:00:00Z"
    historical_census["static_acquisition_contract"]["stage_repo_relative"] = (
        ".gov01-toolchain-stage-" + historical_census["approval_challenge_id"]
    )
    validate_synthetic_manual(historical_census)
    expiry_equal_now = copy.deepcopy(synthetic_envelope)
    expiry_equal_now["not_after_utc"] = "2026-08-20T00:00:00Z"
    expect_error(
        "expiry equality manual",
        lambda: validate_synthetic_manual(expiry_equal_now),
        "ENVELOPE_EXPIRED",
    )
    for label, timestamp in (
        ("invalid month", "2026-99-20T00:00:00Z"),
        ("invalid hour", "2026-08-20T25:00:00Z"),
        ("invalid leap day", "2025-02-29T00:00:00Z"),
    ):
        invalid_time = copy.deepcopy(synthetic_envelope)
        invalid_time["census_at_utc"] = timestamp
        expect_error(
            label + " strict UTC manual contract",
            lambda value=invalid_time: validate_synthetic_manual(value),
            "CENSUS_AT_FORMAT",
        )
    report["envelope_joint_schema_manual_positive_and_hostile_negatives"] = {
        "status": "PASS",
        "pending_real_builder_bool_int_scalar_type_parity": builder_scalar_parity,
    }

    # A GEN approval is consumed by a durable private claim, not merely by the
    # continued presence of the public final file.  Exercise the exact
    # production FD core against a synthetic private control container.  The
    # path wrapper remains responsible for real locator/control-preparation/key
    # binding; this narrow core performs the same O_EXCL write, durability,
    # semantic reread and crash-recovery checks without any monkeypatch.
    with tempfile.TemporaryDirectory(prefix="gov01-generation-claim-", dir="/private/tmp") as temporary:
        generation_root = pathlib.Path(temporary)
        state_root = generation_root / "state"
        claims_root = state_root / "claims"
        state_root.mkdir(mode=0o700)
        claims_root.mkdir(mode=0o700)
        os.chmod(state_root, 0o700)
        os.chmod(claims_root, 0o700)
        state_fd = os.open(state_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        claims_fd = os.open(claims_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        expected_uid = state_root.stat().st_uid
        expected_gid = state_root.stat().st_gid
        assert claims_root.stat().st_uid == expected_uid
        assert claims_root.stat().st_gid == expected_gid
        fixture_key = b"g" * 32
        generation_authorization = synthetic_envelope["generation_authorization"]
        final_raw = acquisition["canonical_json"](synthetic_envelope)
        original_fsync = acquisition["os"].fsync
        fsync_calls = []

        def counted_fsync(fd):
            fsync_calls.append(fd)
            return original_fsync(fd)

        acquisition["os"].fsync = counted_fsync
        previous_umask = os.umask(0o077)
        try:
            fd_arguments = {
                "state_fd": state_fd,
                "claims_fd": claims_fd,
                "expected_uid": expected_uid,
                "expected_gid": expected_gid,
                "key": fixture_key,
            }
            assert acquisition["probe_generation_claim_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
            ) is None
            record = acquisition["create_generation_claim_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
                final_envelope_raw=final_raw,
                clock=lambda: witness_now,
            )
            assert set(record) == set(acquisition["GENERATION_CLAIM_FIELDS"])
            claim_name = acquisition["generation_claim_name_v2"](generation_authorization)
            claim_path = claims_root / claim_name
            record_path = claim_path / "generation-record.json"
            assert stat.S_IMODE(claim_path.stat().st_mode) == 0o700
            assert stat.S_IMODE(record_path.stat().st_mode) == 0o600
            assert record_path.stat().st_nlink == 1
            assert len(fsync_calls) >= 4
            os.fstat(state_fd)
            os.fstat(claims_fd)
            recovered = acquisition["probe_generation_claim_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
            )
            assert recovered == record
            assert recovered["acquisition_approval_challenge_id"] == synthetic_envelope[
                "approval_challenge_id"
            ]
            assert acquisition["verify_generation_claim_recovery_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
                final_envelope_raw=final_raw,
            ) == record
            expect_error(
                "generation claim replay create",
                lambda: acquisition["create_generation_claim_from_verified_fds_v2"](
                    **fd_arguments,
                    generation_authorization=generation_authorization,
                    final_envelope_raw=final_raw,
                    clock=lambda: witness_now,
                ),
                "PRIVATE_CHILD_EXISTS",
            )
            # A racing loser may only recover the already-authenticated
            # winner; it may not mint another SA/time/raw identity.
            assert acquisition["probe_generation_claim_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
            ) == record
            changed_envelope = copy.deepcopy(synthetic_envelope)
            changed_envelope["authorization_preimage"]["worktree_state"] = (
                "dirty-user-owned-do-not-normalize"
                if changed_envelope["authorization_preimage"]["worktree_state"] == "clean"
                else "clean"
            )
            changed_raw = acquisition["canonical_json"](changed_envelope)
            expect_error(
                "generation claim same authority changed final",
                lambda: acquisition["verify_generation_claim_recovery_from_verified_fds_v2"](
                    **fd_arguments,
                    generation_authorization=generation_authorization,
                    final_envelope_raw=changed_raw,
                ),
                "GENERATION_CLAIM_RECOVERY_DRIFT",
            )
            # The public final may be absent or externally deleted; the
            # retained claim still fixes the same SA/time/raw identity.
            assert acquisition["probe_generation_claim_from_verified_fds_v2"](
                **fd_arguments,
                generation_authorization=generation_authorization,
            )["final_envelope_raw_sha256"] == hashlib.sha256(final_raw).hexdigest()

            partial_generation = copy.deepcopy(generation_authorization)
            partial_challenge = "GOV01-GEN-20260820-" + ("c" * 64)
            partial_generation["approval_challenge_id"] = partial_challenge
            partial_generation["approval_envelope_repo_relative_path"] = (
                "_bmad-output/审查/phase0a-annotation-truth/"
                "GOV-01-toolchain-static-envelope-generation-envelope-v1."
                + partial_challenge
                + ".json"
            )
            partial_generation["generated_acquisition_envelope_repo_relative_path"] = (
                acquisition["expected_pending_envelope_relative"](partial_challenge)
            )
            partial_path = claims_root / acquisition["generation_claim_name_v2"](partial_generation)
            partial_path.mkdir(mode=0o700)
            os.chmod(partial_path, 0o700)
            expect_error(
                "generation partial claim retained",
                lambda: acquisition["probe_generation_claim_from_verified_fds_v2"](
                    **fd_arguments,
                    generation_authorization=partial_generation,
                ),
                "GENERATION_CLAIM_PARTIAL_OR_UNEXPECTED",
            )

            tampered_record = json.loads(record_path.read_text(encoding="utf-8"))
            original_record_raw = record_path.read_bytes()
            tampered_record["record_hmac_sha256"] = "f" * 64
            rewrite_canonical_json(record_path, tampered_record)
            expect_error(
                "generation claim HMAC tamper",
                lambda: acquisition["probe_generation_claim_from_verified_fds_v2"](
                    **fd_arguments,
                    generation_authorization=generation_authorization,
                ),
                "GENERATION_CLAIM_HMAC",
            )
            rewrite_bytes(record_path, original_record_raw)
            write_bytes(claim_path / "unexpected-child", b"fixture", 0o600)
            expect_error(
                "generation claim extra child retained",
                lambda: acquisition["probe_generation_claim_from_verified_fds_v2"](
                    **fd_arguments,
                    generation_authorization=generation_authorization,
                ),
                "GENERATION_CLAIM_PARTIAL_OR_UNEXPECTED",
            )
            os.fstat(state_fd)
            os.fstat(claims_fd)
        finally:
            os.umask(previous_umask)
            acquisition["os"].fsync = original_fsync
            os.close(claims_fd)
            os.close(state_fd)
    report["durable_generation_claim_fd_core_single_use_and_recovery"] = "PASS"

    # Receipt, external challenge, expiry, privacy and the complete public G00
    # contract must fail before state/cache/key metadata, bytes or processes
    # are touched.  Exercise the production build_census entry rather than a
    # substitute ordering helper.
    with tempfile.TemporaryDirectory(prefix="gov01-public-before-private-", dir="/private/tmp") as temporary:
        public_repo = pathlib.Path(temporary) / "repo"
        public_repo.mkdir(mode=0o700)
        current = acquisition["utc_now"]()
        current_text = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        expiry_text = (current + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        current_challenge = "GOV01-SA-" + current.strftime("%Y%m%d") + "-" + ("d" * 64)
        current_generation_challenge = "GOV01-GEN-" + current.strftime("%Y%m%d") + "-" + ("d" * 64)
        relative = acquisition["expected_pending_envelope_relative"](current_generation_challenge)
        public_envelope_path = public_repo / relative
        public_envelope_path.parent.mkdir(parents=True)
        minimal_public_envelope = {
            "schema_version": "gov-01-toolchain-static-acquisition-envelope-v2",
            "artifact_type": "gov-01-toolchain-acquisition-envelope",
            "approval_challenge_id": current_challenge,
            "single_use": True,
            "census_at_utc": current_text,
            "not_after_utc": expiry_text,
        }

        def write_public_envelope(value):
            raw = acquisition["canonical_json"](value)
            if public_envelope_path.exists():
                output_fd = os.open(str(public_envelope_path), os.O_WRONLY | os.O_TRUNC)
                try:
                    offset = 0
                    while offset < len(raw):
                        offset += os.write(output_fd, raw[offset:])
                finally:
                    os.close(output_fd)
            else:
                write_bytes(public_envelope_path, raw, 0o600)
            domain = acquisition["RECEIPT_DOMAINS"][value["schema_version"]]
            return hashlib.sha256(domain + b"\x00" + raw).hexdigest()

        good_receipt = write_public_envelope(minimal_public_envelope)
        state_root = pathlib.Path(temporary) / "private-state-must-not-be-touched"
        cache_root = pathlib.Path(temporary) / "private-cache-must-not-be-touched"

        def entry_args(receipt, challenge, generation_challenge=current_generation_challenge):
            return argparse.Namespace(
                repo_root=str(public_repo),
                cache_root=str(cache_root),
                state_root=str(state_root),
                key_file=str(state_root / "hmac.key"),
                envelope=str(public_envelope_path),
                receipt_digest=receipt,
                approval_challenge=challenge,
                generation_challenge=generation_challenge,
            )

        original_entry_functions = {
            name: acquisition[name]
            for name in (
                "require_python_isolation", "require_host", "require_owned_directory",
                "open_directory", "load_hmac_key", "run_process", "verify_bound_schema_artifact",
            )
        }
        private_accesses = []

        def guarded_owned_directory(path, label, exact_mode=None):
            if label != "REPO_ROOT":
                private_accesses.append(("require_owned_directory", label))
                raise AssertionError("private locator touched before public authorization")
            return original_entry_functions["require_owned_directory"](path, label, exact_mode)

        def guarded_open_directory(path, label):
            if label != "REPO_ROOT":
                private_accesses.append(("open_directory", label))
                raise AssertionError("private locator opened before public authorization")
            return original_entry_functions["open_directory"](path, label)

        def forbidden_private_or_process(*_args, **_kwargs):
            private_accesses.append(("private-or-process", "reached"))
            raise AssertionError("private bytes or subprocess reached before public authorization")

        acquisition["require_python_isolation"] = lambda: None
        acquisition["require_host"] = lambda: None
        acquisition["require_owned_directory"] = guarded_owned_directory
        acquisition["open_directory"] = guarded_open_directory
        acquisition["load_hmac_key"] = forbidden_private_or_process
        acquisition["run_process"] = forbidden_private_or_process
        try:
            cases = (
                ("missing receipt", entry_args(None, current_challenge), "APPROVED_RECEIPT_REQUIRED"),
                ("bad receipt", entry_args("f" * 64, current_challenge), "RECEIPT_MISMATCH"),
                (
                    "challenge mismatch",
                    entry_args(good_receipt, "GOV01-SA-" + current.strftime("%Y%m%d") + "-" + ("e" * 64)),
                    "APPROVAL_CHALLENGE_MISMATCH",
                ),
            )
            for label, candidate_args, reason in cases:
                private_accesses[:] = []
                expect_error(
                    label + " before private I/O",
                    lambda value=candidate_args: acquisition["build_census"](value, strict=True),
                    reason,
                )
                assert private_accesses == []

            expired = dict(minimal_public_envelope)
            expired["census_at_utc"] = (current - datetime.timedelta(hours=1)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            expired["not_after_utc"] = (current - datetime.timedelta(seconds=1)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            expired["approval_challenge_id"] = (
                "GOV01-SA-" + (current - datetime.timedelta(hours=1)).strftime("%Y%m%d") + "-" + ("d" * 64)
            )
            expired_generation_challenge = (
                "GOV01-GEN-" + (current - datetime.timedelta(hours=1)).strftime("%Y%m%d") + "-" + ("d" * 64)
            )
            expired_relative = acquisition["expected_pending_envelope_relative"](expired_generation_challenge)
            expired_path = public_repo / expired_relative
            expired_path.parent.mkdir(parents=True, exist_ok=True)
            public_envelope_path = expired_path
            expired_receipt = write_public_envelope(expired)
            private_accesses[:] = []
            expect_error(
                "expired envelope before private I/O",
                lambda: acquisition["build_census"](
                    entry_args(
                        expired_receipt,
                        expired["approval_challenge_id"],
                        expired_generation_challenge,
                    ),
                    strict=True,
                ),
                "ENVELOPE_EXPIRED",
            )
            assert private_accesses == []

            # A receipt-valid envelope that fails the manual public contract at
            # G00 likewise must not advance to any private locator.  Patch only
            # the already-public schema observation so the production ordering
            # reaches the manual checker without requiring a synthetic repo
            # artifact tree.
            public_envelope_path = public_repo / relative
            invalid_public_contract = copy.deepcopy(synthetic_envelope)
            invalid_public_contract["approval_challenge_id"] = current_challenge
            invalid_public_contract["census_at_utc"] = current_text
            invalid_public_contract["not_after_utc"] = expiry_text
            invalid_public_contract["artifact_id"] = "x"
            invalid_public_contract["generation_authorization"].update(
                {
                    "approval_challenge_id": current_generation_challenge,
                    "approval_envelope_repo_relative_path": (
                        "_bmad-output/审查/phase0a-annotation-truth/"
                        "GOV-01-toolchain-static-envelope-generation-envelope-v1."
                        + current_generation_challenge
                        + ".json"
                    ),
                    "generated_acquisition_envelope_repo_relative_path": relative,
                }
            )
            invalid_public_contract["authorization_preimage"]["envelope_repo_relative_path"] = relative
            invalid_receipt = write_public_envelope(invalid_public_contract)
            acquisition["verify_bound_schema_artifact"] = lambda *_args, **_kwargs: {
                "path": invalid_public_contract["schema_binding"]["schema_artifact_path"],
                "sha256": "0" * 64,
                "bytes": 1,
            }
            private_accesses[:] = []
            expect_error(
                "manual G00 rejection before private I/O",
                lambda: acquisition["build_census"](
                    entry_args(invalid_receipt, current_challenge), strict=True
                ),
                "MANUAL_ARTIFACT_ID",
            )
            assert private_accesses == []
        finally:
            for name, function in original_entry_functions.items():
                acquisition[name] = function
    report["receipt_challenge_expiry_and_g00_before_private_io"] = "PASS"

    private_validator = Draft202012Validator(schemas["private"])
    public_validator = Draft202012Validator(schemas["public"])
    challenge = "GOV01-SA-20260820-" + ("f" * 64)
    receipt = "e" * 64
    ledger_key = b"h" * 32
    success_events = [
        "receipt-consumed",
        "preflight-frozen",
        "stage-materialized",
        "pre-promotion-cas-pass",
        "stage-promoted",
        "static-attestation-complete",
    ]
    sequence_cases = {"S": success_events}
    for prefix_length in range(1, 6):
        promoted_value = prefix_length == 5
        sequence_cases["F%d" % prefix_length] = success_events[:prefix_length] + [
            ("attempt-failed", promoted_value)
        ]
    sequence_cases["F4-promoted-false"] = success_events[:4] + [("attempt-failed", False)]
    sequence_cases["F4-promoted-true"] = success_events[:4] + [("attempt-failed", True)]
    executor_raw = ACQ_PATH.read_bytes()
    executor_sha256 = hashlib.sha256(executor_raw).hexdigest()
    for label, events in sequence_cases.items():
        raw, _records, head = build_ledger(acquisition, events, ledger_key, challenge, receipt)
        checked = acquisition["validate_ledger_jsonl"](
            raw,
            ledger_key,
            challenge,
            receipt,
            expected_head=head,
        )
        projection = private_projection(acquisition, checked, executor_sha256, len(executor_raw))
        private_validator.validate(projection)
        expected_kind = "success" if label == "S" else "failure"
        assert checked["terminal_kind"] == expected_kind
    report["ledger_semantic_S_F1_F5_and_private_schema"] = "PASS"

    raw, records, head = build_ledger(acquisition, success_events, ledger_key, challenge, receipt)
    bad_hmac = copy.deepcopy(records)
    bad_hmac[-1]["hmac_sha256"] = "0" * 64
    expect_error(
        "bad ledger HMAC",
        lambda: acquisition["validate_ledger_jsonl"](
            b"".join(acquisition["canonical_json"](record) for record in bad_hmac),
            ledger_key,
            challenge,
            receipt,
        ),
        "LEDGER_HMAC_MISMATCH",
    )
    bad_chain_raw, _bad_chain_records, _ = build_ledger(
        acquisition,
        success_events,
        ledger_key,
        challenge,
        receipt,
        previous_override={1: "9" * 64},
    )
    expect_error(
        "bad ledger chain",
        lambda: acquisition["validate_ledger_jsonl"](
            bad_chain_raw, ledger_key, challenge, receipt
        ),
        "LEDGER_CHAIN",
    )
    reversed_times = [
        "2026-08-20T00:00:00Z",
        "2026-08-19T23:59:59Z",
        "2026-08-20T00:02:00Z",
        "2026-08-20T00:03:00Z",
        "2026-08-20T00:04:00Z",
        "2026-08-20T00:05:00Z",
    ]
    reversed_raw, _, _ = build_ledger(
        acquisition, success_events, ledger_key, challenge, receipt, times=reversed_times
    )
    expect_error(
        "reversed ledger time",
        lambda: acquisition["validate_ledger_jsonl"](
            reversed_raw, ledger_key, challenge, receipt
        ),
        "LEDGER_TIME_REVERSED",
    )
    noncanonical = json.dumps(records[0], ensure_ascii=False).encode("utf-8") + b"\n" + b"".join(
        acquisition["canonical_json"](record) for record in records[1:]
    )
    expect_error(
        "noncanonical ledger bytes",
        lambda: acquisition["validate_ledger_jsonl"](
            noncanonical, ledger_key, challenge, receipt
        ),
        "LEDGER_LINE_NONCANONICAL",
    )
    expect_error(
        "ledger CR",
        lambda: acquisition["validate_ledger_jsonl"](
            raw.replace(b"\n", b"\r\n", 1), ledger_key, challenge, receipt
        ),
        "LEDGER_RAW_PROFILE",
    )
    expect_error(
        "ledger duplicate key",
        lambda: acquisition["validate_ledger_jsonl"](
            b'{"schema_version":"x","schema_version":"y"}\n', ledger_key, challenge, receipt
        ),
        "JSON_DUPLICATE_KEY",
    )
    expect_error(
        "ledger float",
        lambda: acquisition["validate_ledger_jsonl"](
            b'{"sequence":1.0}\n', ledger_key, challenge, receipt
        ),
        "JSON_NUMBER_PROFILE",
    )
    drifted = copy.deepcopy(records)
    drifted[1]["challenge"] = "GOV01-SA-20260820-" + ("d" * 64)
    expect_error(
        "ledger challenge drift",
        lambda: acquisition["validate_ledger_jsonl"](
            b"".join(acquisition["canonical_json"](record) for record in drifted),
            ledger_key,
            challenge,
            receipt,
        ),
        "LEDGER_AUTHORITY_DRIFT",
    )
    early_promoted_raw, _, _ = build_ledger(
        acquisition,
        ["receipt-consumed", ("attempt-failed", True)],
        ledger_key,
        challenge,
        receipt,
    )
    expect_error(
        "early promoted failure",
        lambda: acquisition["validate_ledger_jsonl"](
            early_promoted_raw, ledger_key, challenge, receipt
        ),
        "LEDGER_FAILURE_PROMOTED_EARLY",
    )
    late_false_raw, _, _ = build_ledger(
        acquisition,
        success_events[:5] + [("attempt-failed", False)],
        ledger_key,
        challenge,
        receipt,
    )
    expect_error(
        "late unpromoted failure",
        lambda: acquisition["validate_ledger_jsonl"](
            late_false_raw, ledger_key, challenge, receipt
        ),
        "LEDGER_FAILURE_PROMOTED_LATE",
    )
    expect_error(
        "ledger head mismatch",
        lambda: acquisition["validate_ledger_jsonl"](
            raw, ledger_key, challenge, receipt, expected_head="0" * 64
        ),
        "LEDGER_HEAD_MISMATCH",
    )
    report["ledger_bad_hmac_chain_time_bytes_authority_and_state_rejected"] = "PASS"

    partial_recorder = acquisition["GateRecorder"]()
    partial_recorder.begin("G00", acquisition["GATE_PHASE_BY_ID"]["G00"])
    partial_recorder.passed("G00", synthetic_gate_evidence("G00"))
    partial_gates = partial_recorder.partial_projection()
    acquisition["validate_gate_projection"](partial_gates)
    tampered_gate = copy.deepcopy(partial_gates)
    tampered_gate["reached_gates"][0]["receipt_sha256"] = "0" * 64
    expect_error(
        "tampered gate receipt",
        lambda: acquisition["validate_gate_projection"](tampered_gate),
        "GATE_RECEIPT_MISMATCH",
    )
    wrong_partition = copy.deepcopy(partial_gates)
    wrong_partition["unreached_gate_ids"] = []
    expect_error(
        "gate partition",
        lambda: acquisition["validate_gate_projection"](wrong_partition),
        "GATE_UNREACHED_PARTITION",
    )
    wrong_order_recorder = acquisition["GateRecorder"]()
    wrong_order_recorder.begin("G01", acquisition["GATE_PHASE_BY_ID"]["G01"])
    wrong_order_recorder.passed("G01", synthetic_gate_evidence("G01"))
    wrong_order_recorder.begin("G00", acquisition["GATE_PHASE_BY_ID"]["G00"])
    wrong_order_recorder.passed("G00", synthetic_gate_evidence("G00"))
    acquisition["validate_gate_projection"](wrong_order_recorder.partial_projection())
    atomic_recorder = acquisition["GateRecorder"]()
    atomic_recorder.begin("G00", acquisition["GATE_PHASE_BY_ID"]["G00"])
    original_atomic_passed = atomic_recorder.passed
    atomic_recorder.passed = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        acquisition["ContractError"](acquisition["Exit"].INTERNAL, "FIXTURE_AUTHORITY_INTERRUPT")
    )
    try:
        expect_error(
            "gate authority atomic interruption",
            lambda: atomic_recorder.passed_with_authority(
                "G00",
                synthetic_gate_evidence("G00"),
                "schema",
                {
                    "path": "_bmad-output/审查/phase0a-annotation-truth/pending.schema.json",
                    "sha256": "0" * 64,
                    "bytes": 1,
                    "schema_count": 3,
                    "schema_bundle_receipt_sha256": "0" * 64,
                },
            ),
            "FIXTURE_AUTHORITY_INTERRUPT",
        )
    finally:
        atomic_recorder.passed = original_atomic_passed
    assert atomic_recorder.authority_binding() is None
    atomic_recorder.failed("FIXTURE_FAILURE", int(acquisition["Exit"].CONTRACT))
    atomic_projection = atomic_recorder.partial_projection()
    assert atomic_projection["reached_gates"][0]["gate_id"] == "G00"
    assert atomic_projection["reached_gates"][0]["status"] == "FAIL"
    report["gate_receipts_partition_and_canonical_projection"] = "PASS"
    report["gate_pass_and_authority_snapshot_atomic"] = "PASS"

    fixture_error = acquisition["ContractError"](acquisition["Exit"].CONTRACT, "FIXTURE_FAILURE")
    failure_toolchain = {
        "toolchain_set_receipt_sha256": "0" * 64,
        "dynamic_closure_receipt_sha256": "0" * 64,
    }
    generic_failure = acquisition["generic_public_failure"](fixture_error, "acquire")
    validate_public_contract(acquisition, public_validator, generic_failure)
    generic_unknown = acquisition["generic_public_failure"](fixture_error, "unknown")
    validate_public_contract(acquisition, public_validator, generic_unknown)

    read_only_result = synthetic_read_only(acquisition, "census")
    read_only_binding = recorder_authority_binding_for_result(acquisition, read_only_result)
    assert read_only_binding == public_authority_binding(read_only_result)
    validate_public_contract(
        acquisition,
        public_validator,
        read_only_result,
        read_only_binding,
    )
    read_only_failure_recorder = recorder_with_prefix(
        acquisition,
        READ_ONLY_EXECUTION_ORDER,
        5,
        failure_code="FIXTURE_FAILURE",
    )
    read_only_post_g03_failure = acquisition["read_only_failure_result"](
        fixture_error,
        "census",
        read_only_failure_recorder,
    )
    validate_public_contract(acquisition, public_validator, read_only_post_g03_failure)
    assert (
        read_only_post_g03_failure["runtime_assurance"]["toolchain_set_receipt_sha256"]
        == synthetic_gate_evidence("G03")["toolchain_set_receipt_sha256"]
    )

    success_report = acquisition["validate_ledger_jsonl"](
        raw,
        ledger_key,
        challenge,
        receipt,
        expected_head=head,
    )
    marker_removed = acquisition["AttemptState"]()
    marker_removed.claim_created()
    marker_removed.stage_created()
    marker_removed.stage_marker_removed()
    marker_removed.ledger_invalid()
    marker_removed.set_phase("sealed-marker-removed")
    marker_recorder = recorder_with_prefix(acquisition, ACQUIRE_EXECUTION_ORDER, 18)
    marker_failure = acquisition["acquire_failure_result"](
        acquisition["ContractError"](acquisition["Exit"].SEAL, "FIXTURE_FAILURE"),
        marker_removed,
        marker_recorder,
        challenge,
        receipt,
        failure_toolchain,
        None,
    )
    validate_public_contract(acquisition, public_validator, marker_failure)
    assert marker_failure["terminal_state"]["stage_state"] == "retained-marker-removed"

    post_rename = acquisition["AttemptState"]()
    post_rename.claim_created()
    post_rename.stage_created()
    post_rename.stage_marker_removed()
    post_rename.target_promoted()
    post_rename.ledger_invalid()
    post_rename.set_phase("rename-succeeded-attestation-incomplete")
    renamed_recorder = recorder_with_prefix(acquisition, ACQUIRE_EXECUTION_ORDER, 19)
    renamed_failure = acquisition["acquire_failure_result"](
        acquisition["ContractError"](acquisition["Exit"].POST_INSTALL, "FIXTURE_FAILURE"),
        post_rename,
        renamed_recorder,
        challenge,
        receipt,
        failure_toolchain,
        None,
    )
    validate_public_contract(acquisition, public_validator, renamed_failure)
    assert renamed_failure["terminal_state"]["target_disposition"] == "retain-unauthorized-target-user-decision-required"

    failure_raw, _, failure_head = build_ledger(
        acquisition,
        ["receipt-consumed", "preflight-frozen", ("attempt-failed", False)],
        ledger_key,
        challenge,
        receipt,
    )
    failure_report = acquisition["validate_ledger_jsonl"](
        failure_raw, ledger_key, challenge, receipt, expected_head=failure_head
    )
    failure_reports_by_count = {}
    for record_count in range(2, 7):
        promoted_value = record_count >= 6
        count_raw, _, count_head = build_ledger(
            acquisition,
            success_events[: record_count - 1] + [("attempt-failed", promoted_value)],
            ledger_key,
            challenge,
            receipt,
        )
        failure_reports_by_count[record_count] = acquisition["validate_ledger_jsonl"](
            count_raw,
            ledger_key,
            challenge,
            receipt,
            expected_head=count_head,
        )

    provenance_cases = []
    count2_attempt = acquisition["AttemptState"]()
    count2_attempt.claim_directory_created()
    count2_attempt.terminal_failure_recorded()
    count2_attempt.set_phase("persistent-claim")
    provenance_cases.append((2, count2_attempt, 15))

    count3_attempt = acquisition["AttemptState"]()
    count3_attempt.claim_created()
    count3_attempt.stage_directory_created()
    count3_attempt.terminal_failure_recorded()
    count3_attempt.set_phase("stage-materialization")
    provenance_cases.append((3, count3_attempt, 16))

    count4_attempt = acquisition["AttemptState"]()
    count4_attempt.claim_created()
    count4_attempt.stage_created()
    count4_attempt.terminal_failure_recorded()
    count4_attempt.set_phase("stage-tree-attestation")
    provenance_cases.append((4, count4_attempt, 17))

    count5_attempt = acquisition["AttemptState"]()
    count5_attempt.claim_created()
    count5_attempt.stage_created()
    count5_attempt.stage_marker_removed()
    count5_attempt.terminal_failure_recorded()
    count5_attempt.set_phase("sealed-marker-removed")
    provenance_cases.append((5, count5_attempt, 19))

    count6_attempt = acquisition["AttemptState"]()
    count6_attempt.claim_created()
    count6_attempt.stage_created()
    count6_attempt.stage_marker_removed()
    count6_attempt.target_promoted()
    count6_attempt.terminal_failure_recorded()
    count6_attempt.set_phase("post-promotion-containment")
    provenance_cases.append((6, count6_attempt, 21))

    for record_count, provenance_attempt, gate_length in provenance_cases:
        provenance_recorder = recorder_with_prefix(
            acquisition,
            ACQUIRE_EXECUTION_ORDER,
            gate_length,
            failure_code="FIXTURE_FAILURE",
        )
        provenance_result = acquisition["acquire_failure_result"](
            fixture_error,
            provenance_attempt,
            provenance_recorder,
            challenge,
            receipt,
            failure_toolchain,
            failure_reports_by_count[record_count],
        )
        validate_public_contract(acquisition, public_validator, provenance_result)

    for label, provenance_attempt, gate_length, wrong_report, expected_code in (
        (
            "G01 failure count3",
            count2_attempt,
            15,
            failure_reports_by_count[3],
            "PUBLIC_RESULT_ACQUIRE_FAILED_GATE_LEDGER_PROVENANCE",
        ),
        (
            "G13 failure count4",
            count3_attempt,
            16,
            failure_reports_by_count[4],
            "PUBLIC_RESULT_ACQUIRE_FAILED_GATE_LEDGER_PROVENANCE",
        ),
        (
            "G18 failure count6",
            count5_attempt,
            19,
            failure_reports_by_count[6],
            "PUBLIC_RESULT_ACQUIRE_FAILED_GATE_LEDGER_PROVENANCE",
        ),
    ):
        wrong_recorder = recorder_with_prefix(
            acquisition,
            ACQUIRE_EXECUTION_ORDER,
            gate_length,
            failure_code="FIXTURE_FAILURE",
        )
        expect_error(
            label,
            lambda attempt_value=provenance_attempt, recorder_value=wrong_recorder, report_value=wrong_report: acquisition["acquire_failure_result"](
                fixture_error,
                attempt_value,
                recorder_value,
                challenge,
                receipt,
                failure_toolchain,
                report_value,
            ),
            expected_code,
        )
    report["public_failure_ledger_count2_count6_provenance"] = "PASS"
    partial_attempt = acquisition["AttemptState"]()
    partial_attempt.claim_created()
    partial_attempt.terminal_failure_recorded()
    partial_attempt.set_phase("stage-materialization")
    partial_failure_recorder = recorder_with_prefix(
        acquisition, ACQUIRE_EXECUTION_ORDER, 16, failure_code="FIXTURE_FAILURE"
    )
    partial_ledger_failure = acquisition["acquire_failure_result"](
        fixture_error,
        partial_attempt,
        partial_failure_recorder,
        challenge,
        receipt,
        failure_toolchain,
        failure_report,
    )
    validate_public_contract(acquisition, public_validator, partial_ledger_failure)

    preclaim_attempt = acquisition["AttemptState"]()
    preclaim_attempt.set_phase("schema-contract")
    preclaim_recorder = recorder_with_prefix(
        acquisition, ACQUIRE_EXECUTION_ORDER, 1, failure_code="FIXTURE_FAILURE"
    )
    preclaim_failure = acquisition["acquire_failure_result"](
        fixture_error,
        preclaim_attempt,
        preclaim_recorder,
        challenge,
        receipt,
        None,
        None,
    )
    validate_public_contract(acquisition, public_validator, preclaim_failure)
    assert preclaim_failure["terminal_state"]["challenge_state"] == "preclaim-pending"
    assert preclaim_failure["authority"]["retry_authorized"] is True
    assert preclaim_failure["retention"]["private_state_inspection_required"] is False
    false_consumption = copy.deepcopy(preclaim_failure)
    false_consumption["terminal_state"]["challenge_state"] = "preclaim-rejected-new-envelope-required"
    false_consumption["authority"]["retry_authorized"] = False
    false_consumption["authority"]["next_required_authority"] = (
        "new explicit user approval after retained-state inspection; never retry automatically"
    )
    expect_schema_error("preclaim false consumption schema", public_validator, false_consumption)
    expect_error(
        "preclaim false consumption checker",
        lambda: acquisition["validate_public_result_projection"](false_consumption),
        "PUBLIC_RESULT_ACQUIRE_PRECLAIM_CHALLENGE",
    )

    process_attempt = acquisition["AttemptState"]()
    process_attempt.set_phase("process-census-before")
    process_recorder = recorder_with_prefix(
        acquisition, ACQUIRE_EXECUTION_ORDER, 6, failure_code="FIXTURE_FAILURE"
    )
    process_failure = acquisition["acquire_failure_result"](
        fixture_error,
        process_attempt,
        process_recorder,
        challenge,
        receipt,
        failure_toolchain,
        None,
    )
    validate_public_contract(acquisition, public_validator, process_failure)

    claim_attempt = acquisition["AttemptState"]()
    claim_attempt.claim_directory_created()
    claim_attempt.set_phase("persistent-claim")
    claim_recorder = recorder_with_prefix(
        acquisition, ACQUIRE_EXECUTION_ORDER, 15, failure_code="FIXTURE_FAILURE"
    )
    claim_failure = acquisition["acquire_failure_result"](
        fixture_error,
        claim_attempt,
        claim_recorder,
        challenge,
        receipt,
        failure_toolchain,
        None,
    )
    validate_public_contract(acquisition, public_validator, claim_failure)
    assert claim_failure["terminal_state"]["challenge_state"] == "claimed-consumed"
    assert claim_failure["authority"]["retry_authorized"] is False

    complete_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        25,
        evidence_overrides={"G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}},
    )
    finalization_attempt = acquisition["AttemptState"]()
    finalization_attempt.claim_created()
    finalization_attempt.stage_created()
    finalization_attempt.stage_marker_removed()
    finalization_attempt.target_promoted()
    finalization_attempt.terminal_success_recorded()
    resource_failure = acquisition["resource_finalization_failure_result"](
        finalization_attempt,
        complete_recorder,
        challenge,
        receipt,
        failure_toolchain,
        success_report,
    )
    validate_public_contract(acquisition, public_validator, resource_failure)

    g24_failure_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        24,
        evidence_overrides={"G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}},
    )
    g24_failure_recorder.begin("G24", acquisition["GATE_PHASE_BY_ID"]["G24"])
    prospective_g24 = copy.deepcopy(g24_failure_recorder)
    prospective_g24.passed("G24", synthetic_gate_evidence("G24"))
    acquisition["validate_gate_projection"](prospective_g24.complete_projection())
    g24_failure_recorder.failed("FIXTURE_FAILURE", int(acquisition["Exit"].CONTRACT))
    g24_attempt = acquisition["AttemptState"]()
    g24_attempt.claim_created()
    g24_attempt.stage_created()
    g24_attempt.stage_marker_removed()
    g24_attempt.target_promoted()
    g24_attempt.terminal_success_publication_failed()
    g24_attempt.set_phase("static-attestation-complete")
    g24_failure = acquisition["acquire_failure_result"](
        fixture_error,
        g24_attempt,
        g24_failure_recorder,
        challenge,
        receipt,
        failure_toolchain,
        success_report,
    )
    validate_public_contract(acquisition, public_validator, g24_failure)

    g23_failure_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        24,
        failure_code="FIXTURE_FAILURE",
        failure_exit=int(acquisition["Exit"].CONTRACT),
    )
    g23_failure_attempt = acquisition["AttemptState"]()
    g23_failure_attempt.claim_created()
    g23_failure_attempt.stage_created()
    g23_failure_attempt.stage_marker_removed()
    g23_failure_attempt.target_promoted()
    g23_failure_attempt.terminal_success_publication_failed()
    g23_failure_attempt.set_phase("static-attestation-complete")
    g23_late_success_failure = acquisition["acquire_failure_result"](
        fixture_error,
        g23_failure_attempt,
        g23_failure_recorder,
        challenge,
        receipt,
        failure_toolchain,
        success_report,
    )
    validate_public_contract(acquisition, public_validator, g23_late_success_failure)
    assert g23_late_success_failure["gate_results"]["reached_gates"][-1]["gate_id"] == "G23"
    assert g23_late_success_failure["gate_results"]["reached_gates"][-1]["status"] == "FAIL"

    class FailingSecondLedgerRead:
        sequence = 6

        def verify_terminal(self):
            raise OSError("fixture second terminal read failure")

    recovered_ledger_attempt = acquisition["AttemptState"]()
    recovered_ledger_attempt.claim_created()
    recovered_ledger_attempt.stage_created()
    recovered_ledger_attempt.stage_marker_removed()
    recovered_ledger_attempt.target_promoted()
    recovered_ledger_attempt.set_phase("static-attestation-complete")
    recovered_ledger_report = acquisition["recover_terminal_success_report"](
        FailingSecondLedgerRead(),
        success_report,
        recovered_ledger_attempt,
    )
    assert recovered_ledger_report == success_report
    assert recovered_ledger_attempt.challenge_state == "completed-consumed"
    assert recovered_ledger_attempt.ledger_terminal_state == "terminal-success-recorded"
    g23_pass_recorder = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        24,
        evidence_overrides={"G23": {"ledger_head_hmac_sha256": success_report["head_hmac_sha256"]}},
    )
    recovered_second_read_failure = acquisition["acquire_failure_result"](
        fixture_error,
        recovered_ledger_attempt,
        g23_pass_recorder,
        challenge,
        receipt,
        failure_toolchain,
        recovered_ledger_report,
    )
    validate_public_contract(
        acquisition,
        public_validator,
        recovered_second_read_failure,
    )
    recovered_second_read_error = acquisition["ContractError"](
        acquisition["Exit"].CONTRACT,
        "FIXTURE_FAILURE",
        recovered_second_read_failure,
    )
    recovered_second_read_rc, recovered_second_read_stdout = run_main_handler(
        acquisition,
        "acquire",
        lambda _args: (_ for _ in ()).throw(recovered_second_read_error),
    )
    assert recovered_second_read_rc == int(acquisition["Exit"].CONTRACT), (
        recovered_second_read_rc,
        recovered_second_read_stdout,
    )
    assert recovered_second_read_stdout["terminal_state"]["challenge_state"] == "completed-consumed"
    assert recovered_second_read_stdout["terminal_state"]["ledger_terminal_state"] == "terminal-success-recorded"
    assert recovered_second_read_stdout["ledger_evidence"]["head_hmac_sha256"] == success_report["head_hmac_sha256"]
    report["late_success_second_ledger_read_failure_preserves_verified_report"] = "PASS"

    for label, bound_payload, expected_phase, expected_reached in (
        ("read-only", read_only_post_g03_failure, "read-only-fail-closed", 5),
        ("acquire", process_failure, "process-census-before", 6),
        ("g23-late-success", g23_late_success_failure, "static-attestation-complete", 24),
    ):
        wrapped = acquisition["ContractError"](
            acquisition["Exit"].CONTRACT,
            "FIXTURE_FAILURE",
            bound_payload,
        )
        return_code, chained_result = run_main_handler(
            acquisition,
            "census" if label == "read-only" else "acquire",
            lambda _args, error=wrapped: (_ for _ in ()).throw(error),
        )
        public_validator.validate(chained_result)
        assert return_code == int(acquisition["Exit"].CONTRACT), label
        assert chained_result["phase"] == expected_phase, label
        assert chained_result["gate_results"]["reached_gate_count"] == expected_reached, label
        assert chained_result["error"]["detail_code"] == "FIXTURE_FAILURE", label

    success_result = synthetic_success(acquisition)
    success_binding = recorder_authority_binding_for_result(acquisition, success_result)
    assert success_binding == public_authority_binding(success_result)
    validate_public_contract(acquisition, public_validator, success_result, success_binding)

    # G24 is the linearization point.  An interruption thrown after the real
    # PASS record exists must recover the already checked success bytes instead
    # of fabricating an invalid partial 25-PASS failure or an entry failure.
    linearized_recorder = acquisition["GateRecorder"]()
    linearized_recorder.bind_run_authority(
        success_result["approval_challenge_id"], success_result["receipt_digest"]
    )
    for gate_id, _scope in acquisition["GATE_SCOPES"]:
        if gate_id == "G24":
            break
        linearized_recorder.begin(gate_id, acquisition["GATE_PHASE_BY_ID"][gate_id])
        record_synthetic_pass(
            acquisition,
            linearized_recorder,
            gate_id,
            synthetic_gate_evidence(gate_id),
        )
    committed_success = acquisition["AuthorityBoundPublicResult"](
        success_result,
        success_binding,
    )
    assert linearized_recorder.partial_projection()["reached_gate_count"] == 24
    linearized_recorder.begin("G24", acquisition["GATE_PHASE_BY_ID"]["G24"])
    original_g24_passed = linearized_recorder.passed

    def pass_g24_then_interrupt(gate_id, evidence):
        original_g24_passed(gate_id, evidence)
        raise KeyboardInterrupt()

    linearized_recorder.passed = pass_g24_then_interrupt
    try:
        try:
            linearized_recorder.passed("G24", synthetic_gate_evidence("G24"))
        except KeyboardInterrupt:
            recovered_success = acquisition["recover_linearized_success"](
                linearized_recorder,
                committed_success,
            )
        else:
            raise AssertionError("G24 after-record interruption did not fire")
    finally:
        linearized_recorder.passed = original_g24_passed
    assert isinstance(recovered_success, acquisition["AuthorityBoundPublicResult"])
    assert recovered_success["gate_results"]["complete"] is True
    assert recovered_success["gate_results"]["reached_gate_count"] == 25
    recovered_rc, recovered_stdout = run_main_handler(
        acquisition,
        "acquire",
        lambda _args: recovered_success,
    )
    assert recovered_rc == 0 and recovered_stdout["ok"] is True
    assert recovered_stdout["terminal_state"]["publication_state"] == "static-attested"

    private_stdout = io.StringIO()
    with contextlib.redirect_stdout(private_stdout):
        private_emit_exit = acquisition["emit"](
            {"private": synthetic_private_locator("fixture-private")}
        )
    privacy_failure = json.loads(private_stdout.getvalue())
    validate_public_contract(acquisition, public_validator, privacy_failure)
    assert private_emit_exit == int(acquisition["Exit"].PRIVACY)
    secondary_checker_stdout = io.StringIO()
    with contextlib.redirect_stdout(secondary_checker_stdout):
        secondary_emit_exit = acquisition["emit"]({"ok": False})
    secondary_checker_failure = json.loads(secondary_checker_stdout.getvalue())
    validate_public_contract(acquisition, public_validator, secondary_checker_failure)
    assert secondary_checker_failure["error"]["detail_code"] == "PUBLIC_PROJECTION_REJECTED"
    assert secondary_emit_exit == int(acquisition["Exit"].PRIVACY)

    # The actual serialized projection is the sole exit-code authority.  Both
    # an invalid success and an invalid ContractError payload must therefore
    # produce privacy exit 55 at stdout and at the process boundary.
    invalid_success_rc, invalid_success_stdout = run_main_handler(
        acquisition,
        "acquire",
        lambda _args: {},
    )
    assert invalid_success_rc == int(acquisition["Exit"].PRIVACY)
    assert invalid_success_stdout["error"]["exit"] == invalid_success_rc
    invalid_error = acquisition["ContractError"](
        acquisition["Exit"].CONTRACT,
        "FIXTURE_FAILURE",
        {"ok": False},
    )
    invalid_error_rc, invalid_error_stdout = run_main_handler(
        acquisition,
        "acquire",
        lambda _args: (_ for _ in ()).throw(invalid_error),
    )
    assert invalid_error_rc == int(acquisition["Exit"].PRIVACY)
    assert invalid_error_stdout["error"]["exit"] == invalid_error_rc
    generic_rc, generic_stdout = run_main_handler(
        acquisition,
        "unknown",
        lambda _args: (_ for _ in ()).throw(
            acquisition["ContractError"](acquisition["Exit"].CONTRACT, "FIXTURE_FAILURE")
        ),
    )
    assert generic_rc == int(acquisition["Exit"].CONTRACT)
    assert generic_stdout["error"]["exit"] == generic_rc
    report["g24_linearized_after_record_interrupt_recovers_success"] = "PASS"
    report["stdout_json_and_process_exit_single_authority"] = "PASS"

    legacy_failure = {"ok": False, "code": "OLD", "exit": 70}
    expect_schema_error("legacy three-field public result", public_validator, legacy_failure)
    extra_public = copy.deepcopy(generic_failure)
    extra_public["private_locator"] = synthetic_private_locator("fixture-private", "value")
    expect_schema_error("public extra private locator", public_validator, extra_public)
    schema_bad_complete = copy.deepcopy(success_result)
    schema_bad_complete["gate_results"]["reached_gate_count"] = 24
    expect_schema_error("public bad complete gate count", public_validator, schema_bad_complete)
    semantic_bad_success = copy.deepcopy(success_result)
    semantic_bad_success["gate_results"]["reached_gates"][0]["receipt_sha256"] = "0" * 64
    expect_error(
        "public success gate receipt semantic mismatch",
        lambda: acquisition["validate_gate_projection"](semantic_bad_success["gate_results"]),
        "GATE_RECEIPT_MISMATCH",
    )
    gate_schema_mutation_count = 0
    for source_record in success_result["gate_results"]["reached_gates"]:
        gate_id = source_record["gate_id"]
        extra_evidence = copy.deepcopy(success_result)
        extra_record = next(
            record for record in extra_evidence["gate_results"]["reached_gates"]
            if record["gate_id"] == gate_id
        )
        extra_record["evidence"]["generic_unbound_evidence"] = 0
        refresh_gate_receipts(acquisition, extra_evidence, validate=False)
        expect_schema_error("gate extra evidence schema " + gate_id, public_validator, extra_evidence)
        expect_error(
            "gate extra evidence checker " + gate_id,
            lambda item=extra_evidence: acquisition["validate_public_result_projection"](
                item,
                success_binding,
            ),
        )
        gate_schema_mutation_count += 1
        for evidence_field, original_value in source_record["evidence"].items():
            mutated_evidence = copy.deepcopy(success_result)
            mutated_record = next(
                record for record in mutated_evidence["gate_results"]["reached_gates"]
                if record["gate_id"] == gate_id
            )
            if type(original_value) is bool:
                hostile_value = not original_value
            elif type(original_value) is int:
                hostile_value = False
            else:
                hostile_value = False
            mutated_record["evidence"][evidence_field] = hostile_value
            refresh_gate_receipts(acquisition, mutated_evidence, validate=False)
            expect_schema_error(
                "gate evidence type or const schema " + gate_id + "." + evidence_field,
                public_validator,
                mutated_evidence,
            )
            expect_error(
                "gate evidence type or const checker " + gate_id + "." + evidence_field,
                lambda item=mutated_evidence: acquisition["validate_public_result_projection"](
                    item,
                    success_binding,
                ),
            )
            gate_schema_mutation_count += 1
    malformed_unreached = copy.deepcopy(generic_failure)
    malformed_unreached["gate_results"]["unreached_gate_ids"][0] = False
    expect_schema_error("unreached gate id boolean schema", public_validator, malformed_unreached)
    expect_error(
        "unreached gate id boolean checker",
        lambda: acquisition["validate_public_result_projection"](malformed_unreached),
        "GATE_UNREACHED_PARTITION",
    )
    assert gate_schema_mutation_count >= 125
    report["public_gate_evidence_schema_whole_parity"] = "PASS"
    missing_read_only_gate = copy.deepcopy(read_only_result)
    missing_read_only_gate["gate_results"]["reached_gates"] = [
        record for record in missing_read_only_gate["gate_results"]["reached_gates"]
        if record["gate_id"] != "G04"
    ]
    missing_read_only_gate["gate_results"]["reached_gate_count"] -= 1
    missing_read_only_gate["gate_results"]["unreached_gate_ids"] = [
        gate_id for gate_id, _ in acquisition["GATE_SCOPES"]
        if gate_id not in {record["gate_id"] for record in missing_read_only_gate["gate_results"]["reached_gates"]}
    ]
    acquisition["validate_gate_projection"](missing_read_only_gate["gate_results"])
    expect_error(
        "read-only exact gate set",
        lambda: acquisition["validate_public_result_projection"](
            missing_read_only_gate, public_authority_binding(missing_read_only_gate)
        ),
        "PUBLIC_RESULT_READ_ONLY_GATE_SET",
    )
    mixed_challenge = copy.deepcopy(success_result)
    mixed_challenge["approval_challenge_id"] = "GOV01-SA-20260820-" + ("c" * 64)
    expect_error(
        "mixed public authority challenge",
        lambda: acquisition["validate_public_result_projection"](mixed_challenge, success_binding),
        "PUBLIC_RESULT_SUCCESS_CHALLENGE_BINDING",
    )
    mixed_toolchain = copy.deepcopy(success_result)
    mixed_toolchain["attestation"]["toolchain"]["hashes"]["static-executor"] = "f" * 64
    expect_error(
        "mixed executor generation",
        lambda: acquisition["validate_public_result_projection"](mixed_toolchain, success_binding),
        "PUBLIC_RESULT_SUCCESS_AUTHORITY_TOOLCHAIN",
    )
    mixed_bundle = copy.deepcopy(success_result)
    mixed_bundle["attestation"]["schema_binding_observation"]["schema_bundle_receipt_sha256"] = "f" * 64
    expect_error(
        "mixed schema bundle",
        lambda: acquisition["validate_public_result_projection"](mixed_bundle, success_binding),
        "PUBLIC_RESULT_SUCCESS_SCHEMA_BINDING",
    )
    mixed_ledger = copy.deepcopy(success_result)
    mixed_ledger["attestation"]["publication"]["private_ledger_head_hmac_sha256"] = "f" * 64
    expect_error(
        "mixed ledger head",
        lambda: acquisition["validate_public_result_projection"](mixed_ledger, success_binding),
        "PUBLIC_RESULT_SUCCESS_LEDGER_HEAD",
    )
    for field, expected_code in (
        ("public_repo_artifact_set_receipt_sha256", "PUBLIC_RESULT_SUCCESS_AUTHORITY_PUBLIC_REPO_ARTIFACT_SET_RECEIPT_SHA256"),
        ("git_snapshot_commitment", "PUBLIC_RESULT_SUCCESS_AUTHORITY_GIT_SNAPSHOT_COMMITMENT"),
        ("private_preapproval_commitment", "PUBLIC_RESULT_SUCCESS_AUTHORITY_PRIVATE_PREAPPROVAL_COMMITMENT"),
    ):
        mixed_success_authority = copy.deepcopy(success_result)
        mixed_success_authority["attestation"][field] = "f" * 64
        expect_error(
            "mixed success authority " + field,
            lambda item=mixed_success_authority: acquisition["validate_public_result_projection"](item, success_binding),
            expected_code,
        )
    mixed_success_control = copy.deepcopy(success_result)
    mixed_success_control["attestation"]["private_control_identity_commitment"] = "f" * 64
    expect_error(
        "mixed success private control",
        lambda: acquisition["validate_public_result_projection"](mixed_success_control, success_binding),
        "PUBLIC_RESULT_SUCCESS_PRIVATE_CONTROL",
    )
    coordinated_toolchain_drift = copy.deepcopy(success_result)
    coordinated_toolchain_drift["runtime_assurance"]["toolchain_set_receipt_sha256"] = "f" * 64
    coordinated_toolchain_drift["attestation"]["toolchain"]["toolchain_set_receipt_sha256"] = "f" * 64
    for record in coordinated_toolchain_drift["gate_results"]["reached_gates"]:
        if record["gate_id"] == "G03":
            record["evidence"]["toolchain_set_receipt_sha256"] = "f" * 64
    refresh_gate_receipts(acquisition, coordinated_toolchain_drift)
    expect_error(
        "coordinated success toolchain receipt drift",
        lambda: acquisition["validate_public_result_projection"](coordinated_toolchain_drift, success_binding),
        "PUBLIC_RESULT_SUCCESS_AUTHORITY_TOOLCHAIN_RECEIPTS",
    )
    coordinated_read_only_schema_drift = copy.deepcopy(read_only_result)
    coordinated_read_only_schema_drift["observation"]["schema_binding_observation"]["sha256"] = "f" * 64
    for record in coordinated_read_only_schema_drift["gate_results"]["reached_gates"]:
        if record["gate_id"] == "G00":
            record["evidence"]["schema_sha256"] = "f" * 64
    refresh_gate_receipts(acquisition, coordinated_read_only_schema_drift)
    expect_error(
        "recorder authority rejects coordinated G00 generation drift",
        lambda: acquisition["validate_public_result_projection"](
            coordinated_read_only_schema_drift,
            read_only_binding,
        ),
        "PUBLIC_RESULT_READ_ONLY_AUTHORITY_SCHEMA",
    )
    coordinated_read_only_locator_drift = copy.deepcopy(read_only_result)
    coordinated_read_only_locator_drift["observation"]["authorized_locator_commitments"]["repo_root"][
        "commitment"
    ] = "f" * 64
    expect_error(
        "recorder authority rejects coordinated G02 locator drift",
        lambda: acquisition["validate_public_result_projection"](
            coordinated_read_only_locator_drift,
            read_only_binding,
        ),
        "PUBLIC_RESULT_READ_ONLY_AUTHORITY_AUTHORIZED_LOCATOR_COMMITMENTS",
    )
    coordinated_run_drift = copy.deepcopy(read_only_result)
    coordinated_run_drift["approval_challenge_id"] = "GOV01-SA-20260820-" + ("c" * 64)
    coordinated_run_drift["receipt_digest"] = "f" * 64
    expect_error(
        "recorder authority rejects coordinated run drift",
        lambda: acquisition["validate_public_result_projection"](
            coordinated_run_drift,
            read_only_binding,
        ),
        "PUBLIC_RESULT_READ_ONLY_AUTHORITY_CHALLENGE",
    )
    for field in (
        "public_repo_artifact_set_receipt_sha256", "git_snapshot_commitment",
        "private_preapproval_commitment", "hmac_key_id", "authorized_locator_commitments",
        "package_lock_raw_sha256",
    ):
        mixed_read_only_authority = copy.deepcopy(read_only_result)
        if field == "authorized_locator_commitments":
            mixed_read_only_authority["observation"][field]["repo_root"]["commitment"] = "f" * 64
        else:
            mixed_read_only_authority["observation"][field] = "f" * 64
        expect_error(
            "mixed read-only authority " + field,
            lambda item=mixed_read_only_authority: acquisition["validate_public_result_projection"](
                item, public_authority_binding(read_only_result)
            ),
            "PUBLIC_RESULT_READ_ONLY_AUTHORITY_" + field.upper(),
        )
    for field in (
        "public_repo_artifact_set_receipt_sha256",
        "git_snapshot_commitment",
        "private_preapproval_commitment",
        "private_control_identity_commitment",
        "hmac_key_id",
    ):
        invalid_read_only_digest = copy.deepcopy(read_only_result)
        invalid_read_only_binding = public_authority_binding(read_only_result)
        invalid_read_only_digest["observation"][field] = False
        invalid_read_only_binding[field] = False
        expect_error(
            "read-only synchronized invalid digest " + field,
            lambda item=invalid_read_only_digest, binding=invalid_read_only_binding: acquisition[
                "validate_public_result_projection"
            ](item, binding),
            "PUBLIC_RESULT_READ_ONLY_" + field.upper() + "_SHA256",
        )
    invalid_read_only_locators = copy.deepcopy(read_only_result)
    invalid_read_only_locator_binding = public_authority_binding(read_only_result)
    invalid_read_only_locators["observation"]["authorized_locator_commitments"] = False
    invalid_read_only_locator_binding["authorized_locator_commitments"] = False
    expect_error(
        "read-only synchronized invalid locator commitments",
        lambda: acquisition["validate_public_result_projection"](
            invalid_read_only_locators,
            invalid_read_only_locator_binding,
        ),
        "PUBLIC_RESULT_LOCATOR_COMMITMENTS",
    )
    for field in (
        "public_repo_artifact_set_receipt_sha256",
        "git_snapshot_commitment",
        "private_preapproval_commitment",
        "private_control_identity_commitment",
    ):
        invalid_success_digest = copy.deepcopy(success_result)
        invalid_success_binding = copy.deepcopy(success_binding)
        invalid_success_digest["attestation"][field] = False
        invalid_success_binding[field] = False
        expect_error(
            "success synchronized invalid digest " + field,
            lambda item=invalid_success_digest, binding=invalid_success_binding: acquisition[
                "validate_public_result_projection"
            ](item, binding),
            "PUBLIC_RESULT_SUCCESS_" + field.upper() + "_SHA256",
        )
    invalid_success_key_binding = copy.deepcopy(success_binding)
    invalid_success_key_binding["hmac_key_id"] = False
    expect_error(
        "success invalid hidden hmac key id",
        lambda: acquisition["validate_public_result_projection"](
            success_result,
            invalid_success_key_binding,
        ),
        "PUBLIC_RESULT_SUCCESS_AUTHORITY_KEY_SHA256",
    )
    invalid_success_locator_binding = copy.deepcopy(success_binding)
    invalid_success_locator_binding["authorized_locator_commitments"] = False
    expect_error(
        "success invalid hidden locator commitments",
        lambda: acquisition["validate_public_result_projection"](
            success_result,
            invalid_success_locator_binding,
        ),
        "PUBLIC_RESULT_LOCATOR_COMMITMENTS",
    )
    read_only_extra_lock_evidence = copy.deepcopy(read_only_result)
    read_only_extra_lock_evidence["observation"]["lock_closure_observed"]["generic_unbound_evidence"] = 42
    expect_error(
        "read-only generic lock evidence",
        lambda: acquisition["validate_public_result_projection"](
            read_only_extra_lock_evidence,
            public_authority_binding(read_only_result),
        ),
        "PUBLIC_RESULT_READ_ONLY_LOCK_CLOSURE_FIELDS",
    )
    success_extra_lock_evidence = copy.deepcopy(success_result)
    success_extra_lock_evidence["attestation"]["source_and_receipts"]["lock_closure_observed"][
        "generic_unbound_evidence"
    ] = 42
    expect_error(
        "success generic lock evidence",
        lambda: acquisition["validate_public_result_projection"](
            success_extra_lock_evidence,
            success_binding,
        ),
        "PUBLIC_RESULT_SUCCESS_LOCK_CLOSURE_FIELDS",
    )
    invalid_schema_path = copy.deepcopy(read_only_result)
    invalid_schema_path["observation"]["schema_binding_observation"]["path"] = 17
    invalid_schema_path_binding = public_authority_binding(read_only_result)
    invalid_schema_path_binding["schema_binding_observation"]["path"] = 17
    expect_schema_error("schema observation path type", public_validator, invalid_schema_path)
    expect_error(
        "schema observation path type checker",
        lambda: acquisition["validate_public_result_projection"](invalid_schema_path, invalid_schema_path_binding),
        "PUBLIC_RESULT_SCHEMA_OBSERVATION_PATH_TYPE",
    )
    bool_counter = copy.deepcopy(success_result)
    bool_counter["attestation"]["execution_counters"]["network_attempt_count"] = False
    expect_schema_error("bool as integer public schema", public_validator, bool_counter)
    expect_error(
        "bool as integer whole checker",
        lambda: acquisition["validate_public_result_projection"](bool_counter, success_binding),
        "PUBLIC_RESULT_SUCCESS_COUNTER_SHAPE",
    )
    empty_failure_error = copy.deepcopy(generic_unknown)
    empty_failure_error["error"] = {}
    expect_schema_error("empty public failure error", public_validator, empty_failure_error)
    expect_error(
        "empty public failure error checker",
        lambda: acquisition["validate_public_result_projection"](empty_failure_error),
        "PUBLIC_RESULT_ERROR_FIELDS",
    )
    bool_failure_exit = copy.deepcopy(generic_unknown)
    bool_failure_exit["error"]["exit"] = False
    expect_schema_error("bool public failure exit", public_validator, bool_failure_exit)
    expect_error(
        "bool public failure exit checker",
        lambda: acquisition["validate_public_result_projection"](bool_failure_exit),
        "PUBLIC_RESULT_FAILURE_ERROR_EXIT",
    )
    mismatched_failure_identity = copy.deepcopy(generic_unknown)
    mismatched_failure_identity["error"]["code"] = "USAGE_FAIL_CLOSED"
    expect_schema_error("mismatched public failure identity", public_validator, mismatched_failure_identity)
    expect_error(
        "mismatched public failure identity checker",
        lambda: acquisition["validate_public_result_projection"](mismatched_failure_identity),
        "PUBLIC_RESULT_FAILURE_ERROR_CATEGORY",
    )
    wrong_failure_code = copy.deepcopy(partial_ledger_failure)
    wrong_failure_code["error"]["detail_code"] = "DIFFERENT_FAILURE"
    expect_error(
        "failure gate error authority",
        lambda: acquisition["validate_public_result_projection"](wrong_failure_code),
        "PUBLIC_RESULT_FAILURE_GATE_CODE",
    )
    leaked_authority = copy.deepcopy(generic_unknown)
    leaked_authority["authority"]["next_required_authority"] = "x/.ObSiDiAn/plugins"
    expect_schema_error("obsidian public authority schema", public_validator, leaked_authority)
    expect_error(
        "obsidian public authority checker",
        lambda: acquisition["validate_public_result_projection"](leaked_authority),
        "PUBLIC_RESULT_PRIVATE_VALUE",
    )
    for label, value in (("DEL", "x\u007fy"), ("C1", "x\u0085y")):
        controlled_public = copy.deepcopy(generic_unknown)
        controlled_public["authority"]["next_required_authority"] = value
        expect_schema_error(label + " public control", public_validator, controlled_public)
        expect_error(
            label + " public control checker",
            lambda item=controlled_public: acquisition["validate_public_result_projection"](item),
            "PUBLIC_RESULT_PRIVATE_VALUE",
        )
    resource_ledger_drift = copy.deepcopy(resource_failure)
    resource_ledger_drift["ledger_evidence"]["head_hmac_sha256"] = "f" * 64
    expect_error(
        "resource finalization ledger head drift",
        lambda: acquisition["validate_public_result_projection"](resource_ledger_drift),
        "PUBLIC_RESULT_G23_SUCCESS_LEDGER",
    )
    resource_no_inspection = copy.deepcopy(resource_failure)
    resource_no_inspection["retention"]["private_state_inspection_required"] = False
    expect_schema_error("resource finalization inspection schema", public_validator, resource_no_inspection)
    expect_error(
        "resource finalization inspection checker",
        lambda: acquisition["validate_public_result_projection"](resource_no_inspection),
        "PUBLIC_RESULT_FINALIZATION_RETENTION",
    )
    resource_wrong_authority = copy.deepcopy(resource_failure)
    resource_wrong_authority["authority"]["next_required_authority"] = (
        "new explicit user approval after fail-closed evidence review"
    )
    expect_schema_error("resource finalization authority schema", public_validator, resource_wrong_authority)
    expect_error(
        "resource finalization authority checker",
        lambda: acquisition["validate_public_result_projection"](resource_wrong_authority),
        "PUBLIC_RESULT_FINALIZATION_NEXT_AUTHORITY",
    )
    generic_runtime_injection = copy.deepcopy(generic_unknown)
    generic_runtime_injection["runtime_assurance"].update(failure_toolchain)
    expect_error(
        "generic failure toolchain injection",
        lambda: acquisition["validate_public_result_projection"](generic_runtime_injection),
        "PUBLIC_RESULT_FAILURE_TOOLCHAIN_RECEIPTS_ABSENT",
    )
    coordinated_failure_toolchain_drift = copy.deepcopy(marker_failure)
    coordinated_failure_toolchain_drift["runtime_assurance"]["toolchain_set_receipt_sha256"] = "f" * 64
    for record in coordinated_failure_toolchain_drift["gate_results"]["reached_gates"]:
        if record["gate_id"] == "G03":
            record["evidence"]["toolchain_set_receipt_sha256"] = "f" * 64
    refresh_gate_receipts(acquisition, coordinated_failure_toolchain_drift)
    expect_error(
        "coordinated failure toolchain drift",
        lambda: acquisition["validate_public_result_projection"](coordinated_failure_toolchain_drift),
        "PUBLIC_RESULT_FAILURE_TOOLCHAIN_RECEIPTS",
    )
    coordinated_failure_run_drift = copy.deepcopy(marker_failure)
    coordinated_failure_run_drift["approval_challenge_id"] = (
        "GOV01-SA-20260820-" + ("d" * 64)
    )
    coordinated_failure_run_drift["receipt_digest"] = "d" * 64
    expect_error(
        "coordinated failure run authority drift",
        lambda: acquisition["validate_public_result_projection"](coordinated_failure_run_drift),
        "PUBLIC_RESULT_FAILURE_RUN_AUTHORITY",
    )
    coordinated_failure_schema_drift = copy.deepcopy(marker_failure)
    for record in coordinated_failure_schema_drift["gate_results"]["reached_gates"]:
        if record["gate_id"] == "G00":
            record["evidence"]["schema_sha256"] = "f" * 64
            record["evidence"]["schema_bundle_receipt_sha256"] = "f" * 64
    refresh_gate_receipts(acquisition, coordinated_failure_schema_drift)
    expect_error(
        "coordinated failure schema authority drift",
        lambda: acquisition["validate_public_result_projection"](coordinated_failure_schema_drift),
        "PUBLIC_RESULT_FAILURE_SCHEMA_AUTHORITY",
    )
    coordinated_failure_private_drift = copy.deepcopy(marker_failure)
    for record in coordinated_failure_private_drift["gate_results"]["reached_gates"]:
        if record["gate_id"] == "G02":
            record["evidence"]["private_control_identity_commitment"] = "f" * 64
    refresh_gate_receipts(acquisition, coordinated_failure_private_drift)
    expect_error(
        "coordinated failure private authority drift",
        lambda: acquisition["validate_public_result_projection"](coordinated_failure_private_drift),
        "PUBLIC_RESULT_FAILURE_PRIVATE_AUTHORITY",
    )
    early_claim = copy.deepcopy(preclaim_failure)
    early_claim["terminal_state"].update(
        {
            "challenge_state": "claimed-consumed",
            "claim_state": "created-0700",
            "ledger_terminal_state": "absent-partial-or-semantic-invalid",
        }
    )
    early_claim["retention"]["private_state_inspection_required"] = True
    expect_error(
        "pre-G01 claim attribution",
        lambda: acquisition["validate_public_result_projection"](early_claim),
        "PUBLIC_RESULT_ACQUIRE_PRE_G01_CLAIM",
    )
    early_rename = copy.deepcopy(preclaim_failure)
    early_rename["terminal_state"].update(
        {
            "stage_state": "renamed-to-target",
            "publication_state": "rename-succeeded-attestation-incomplete",
            "target_disposition": "retain-unauthorized-target-user-decision-required",
        }
    )
    expect_error(
        "pre-G18 local rename attribution",
        lambda: acquisition["validate_public_result_projection"](early_rename),
        "PUBLIC_RESULT_ACQUIRE_PRE_G18_STAGE",
    )
    static_failure_target = copy.deepcopy(marker_failure)
    static_failure_target["terminal_state"]["target_disposition"] = "static-attested-target-retained"
    expect_error(
        "failure static target disposition",
        lambda: acquisition["validate_public_result_projection"](static_failure_target),
        "PUBLIC_RESULT_ACQUIRE_FAILURE_STATIC_TARGET",
    )
    ledger_without_evidence = copy.deepcopy(partial_ledger_failure)
    del ledger_without_evidence["ledger_evidence"]
    if isinstance(ledger_without_evidence, acquisition["AuthorityBoundPublicResult"]):
        ledger_without_evidence.authority_binding.pop("ledger_evidence", None)
    expect_error(
        "terminal ledger state without evidence",
        lambda: acquisition["validate_public_result_projection"](ledger_without_evidence),
        "PUBLIC_RESULT_FAILURE_TERMINAL_LEDGER_EVIDENCE",
    )
    unknown_claim = copy.deepcopy(claim_failure)
    unknown_claim["terminal_state"]["claim_state"] = "unknown-fail-closed"
    expect_error(
        "partial acquire unknown claim",
        lambda: acquisition["validate_public_result_projection"](unknown_claim),
        "PUBLIC_RESULT_ACQUIRE_FAILURE_CLAIM",
    )
    created_without_ledger = copy.deepcopy(claim_failure)
    created_without_ledger["terminal_state"]["ledger_terminal_state"] = "not-created"
    expect_error(
        "created claim without ledger state",
        lambda: acquisition["validate_public_result_projection"](created_without_ledger),
        "PUBLIC_RESULT_ACQUIRE_CREATED_CLAIM_LEDGER",
    )
    retained_stage_wrong_disposition = copy.deepcopy(marker_failure)
    retained_stage_wrong_disposition["terminal_state"]["target_disposition"] = "target-absent"
    expect_schema_error("retained stage disposition schema", public_validator, retained_stage_wrong_disposition)
    expect_error(
        "retained stage disposition checker",
        lambda: acquisition["validate_public_result_projection"](retained_stage_wrong_disposition),
        "PUBLIC_RESULT_ACQUIRE_PUBLICATION_DISPOSITION_REACHABILITY",
    )
    missing_partial_authority = copy.deepcopy(marker_failure)
    del missing_partial_authority["approval_challenge_id"]
    del missing_partial_authority["receipt_digest"]
    if isinstance(missing_partial_authority, acquisition["AuthorityBoundPublicResult"]):
        missing_partial_authority.authority_binding.pop("approval_challenge_id", None)
        missing_partial_authority.authority_binding.pop("receipt_digest", None)
    expect_schema_error("partial acquire authority required schema", public_validator, missing_partial_authority)
    expect_error(
        "partial acquire authority required checker",
        lambda: acquisition["validate_public_result_projection"](missing_partial_authority),
        "PUBLIC_RESULT_ACQUIRE_FAILURE_AUTHORITY_REQUIRED",
    )
    for terminal_field in (
        "challenge_state", "claim_state", "stage_state", "publication_state",
        "ledger_terminal_state", "target_disposition",
    ):
        unknown_terminal = copy.deepcopy(marker_failure)
        unknown_terminal["terminal_state"][terminal_field] = "evil-state"
        expect_schema_error("unknown terminal " + terminal_field, public_validator, unknown_terminal)
        expect_error(
            "unknown terminal checker " + terminal_field,
            lambda item=unknown_terminal: acquisition["validate_public_result_projection"](item),
            "PUBLIC_RESULT_TERMINAL_" + terminal_field.upper(),
        )
    for label, publication, stage, disposition in (
        ("rename-not-created", "rename-succeeded-attestation-incomplete", "not-created", "retain-unauthorized-target-user-decision-required"),
        ("rename-retained", "rename-succeeded-attestation-incomplete", "retained-marker-removed", "retain-unauthorized-target-user-decision-required"),
        ("attributed-not-created", "attributed-target-and-stage-both-observed-fail-closed", "not-created", "retain-unauthorized-target-user-decision-required"),
        ("attributed-renamed", "attributed-target-and-stage-both-observed-fail-closed", "renamed-to-target", "retain-unauthorized-target-user-decision-required"),
    ):
        impossible_publication_stage = copy.deepcopy(renamed_failure)
        impossible_publication_stage["terminal_state"].update(
            {"publication_state": publication, "stage_state": stage, "target_disposition": disposition}
        )
        expect_schema_error(label + " schema", public_validator, impossible_publication_stage)
        expect_error(
            label + " checker",
            lambda item=impossible_publication_stage: acquisition["validate_public_result_projection"](item),
            "PUBLIC_RESULT_ACQUIRE_PUBLICATION_STAGE_REACHABILITY",
        )
    g18_pass_not_attempted = copy.deepcopy(renamed_failure)
    g18_pass_not_attempted["terminal_state"].update(
        {
            "publication_state": "not-attempted",
            "stage_state": "retained-marker-removed",
            "target_disposition": "target-absent-stage-retained-user-decision-required",
        }
    )
    expect_schema_error("G18 PASS not attempted schema", public_validator, g18_pass_not_attempted)
    expect_error(
        "G18 PASS not attempted checker",
        lambda: acquisition["validate_public_result_projection"](g18_pass_not_attempted),
        "PUBLIC_RESULT_ACQUIRE_G18_PASS_PUBLICATION",
    )
    g18_pass_sealed_phase = copy.deepcopy(renamed_failure)
    g18_pass_sealed_phase["phase"] = "sealed-marker-removed"
    expect_schema_error("G18 PASS sealed phase schema", public_validator, g18_pass_sealed_phase)
    expect_error(
        "G18 PASS sealed phase checker",
        lambda: acquisition["validate_public_result_projection"](g18_pass_sealed_phase),
        "PUBLIC_RESULT_ACQUIRE_FAILURE_PHASE_GATE",
    )
    g18_failed_but_renamed = copy.deepcopy(marker_failure)
    g18_failed_but_renamed["gate_results"] = recorder_with_prefix(
        acquisition,
        ACQUIRE_EXECUTION_ORDER,
        19,
        failure_code="FIXTURE_FAILURE",
        failure_exit=int(acquisition["Exit"].SEAL),
    ).partial_projection()
    g18_failed_but_renamed["terminal_state"].update(
        {
            "publication_state": "not-attempted",
            "stage_state": "renamed-to-target",
            "target_disposition": "retain-unauthorized-target-user-decision-required",
        }
    )
    expect_schema_error("G18 FAIL not-attempted renamed schema", public_validator, g18_failed_but_renamed)
    expect_error(
        "G18 FAIL not-attempted renamed checker",
        lambda: acquisition["validate_public_result_projection"](g18_failed_but_renamed),
        "PUBLIC_RESULT_ACQUIRE_PUBLICATION_STAGE_REACHABILITY",
    )
    for phase in ("stage-tree-attestation", "pre-promotion-cas"):
        post_materialization_missing_stage = copy.deepcopy(marker_failure)
        post_materialization_missing_stage["phase"] = phase
        post_materialization_missing_stage["terminal_state"].update(
            {
                "publication_state": "not-attempted",
                "stage_state": "not-created",
                "target_disposition": "target-absent",
            }
        )
        expect_schema_error(phase + " missing stage schema", public_validator, post_materialization_missing_stage)
        expect_error(
            phase + " missing stage checker",
            lambda item=post_materialization_missing_stage: acquisition["validate_public_result_projection"](item),
            "PUBLIC_RESULT_ACQUIRE_POST_MATERIALIZATION_PHASE_STAGE",
        )
    g13_pass_missing_stage = copy.deepcopy(partial_ledger_failure)
    g13_pass_missing_stage["gate_results"] = recorder_with_prefix(
        acquisition, ACQUIRE_EXECUTION_ORDER, 16
    ).partial_projection()
    g13_pass_missing_stage["terminal_state"].update(
        {"publication_state": "not-attempted", "stage_state": "not-created", "target_disposition": "target-absent"}
    )
    expect_schema_error("G13 PASS missing stage schema", public_validator, g13_pass_missing_stage)
    expect_error(
        "G13 PASS missing stage checker",
        lambda: acquisition["validate_public_result_projection"](g13_pass_missing_stage),
        "PUBLIC_RESULT_ACQUIRE_G13_PASS_STAGE",
    )
    downgraded_g23 = copy.deepcopy(g24_failure)
    del downgraded_g23["ledger_evidence"]
    if isinstance(downgraded_g23, acquisition["AuthorityBoundPublicResult"]):
        downgraded_g23.authority_binding.pop("ledger_evidence", None)
    downgraded_g23["terminal_state"].update(
        {
            "challenge_state": "claimed-consumed",
            "ledger_terminal_state": "absent-partial-or-semantic-invalid",
            "publication_state": "rename-succeeded-attestation-incomplete",
            "stage_state": "renamed-to-target",
            "target_disposition": "retain-unauthorized-target-user-decision-required",
        }
    )
    expect_schema_error("G23 PASS downgraded schema", public_validator, downgraded_g23)
    expect_error(
        "G23 PASS downgraded checker",
        lambda: acquisition["validate_public_result_projection"](downgraded_g23),
        "PUBLIC_RESULT_ACQUIRE_STATIC_PHASE_LEDGER",
    )
    g23_pass_ledger_phase = copy.deepcopy(g24_failure)
    g23_pass_ledger_phase["phase"] = "ledger-terminal-success"
    expect_schema_error("G23 PASS ledger phase schema", public_validator, g23_pass_ledger_phase)
    expect_error(
        "G23 PASS ledger phase checker",
        lambda: acquisition["validate_public_result_projection"](g23_pass_ledger_phase),
        "PUBLIC_RESULT_ACQUIRE_FAILURE_PHASE_GATE",
    )
    retained_stages = (
        "retained-marker-not-yet-created",
        "retained-marker-present",
        "retained-marker-removed",
        "retained-marker-state-unknown",
        "retained-marker-unexpected-type",
    )
    hard_stages = ("unexpected-stage-type-fail-closed", "unknown-fail-closed")
    late_success_matrix = {
        "static-ledger-success-public-result-failed": {
            "renamed-to-target": "retain-target-user-decision-required",
        },
        "rename-succeeded-attestation-incomplete": {
            stage: "unknown-user-decision-required" for stage in hard_stages
        },
        "target-observed-unattributed-fail-closed": {
            **{
                stage: "retain-unattributed-target-user-decision-required"
                for stage in ("renamed-to-target",) + retained_stages
            },
            **{stage: "unknown-user-decision-required" for stage in hard_stages},
        },
        "unexpected-target-type-fail-closed": {
            **{
                stage: "retain-unauthorized-target-user-decision-required"
                for stage in ("renamed-to-target",) + retained_stages
            },
            **{stage: "unknown-user-decision-required" for stage in hard_stages},
        },
        "promoted-target-missing-fail-closed": {
            stage: "unknown-user-decision-required"
            for stage in ("renamed-to-target",) + retained_stages + hard_stages
        },
        "attributed-target-and-stage-both-observed-fail-closed": {
            stage: "retain-unauthorized-target-user-decision-required"
            for stage in retained_stages
        },
        "unknown-fail-closed": {
            stage: "unknown-user-decision-required"
            for stage in ("renamed-to-target",) + retained_stages + hard_stages
        },
    }
    late_success_case_count = 0
    for publication_state, stage_map in late_success_matrix.items():
        for stage_state, disposition in stage_map.items():
            recovered_late_success = copy.deepcopy(g24_failure)
            recovered_late_success["terminal_state"].update(
                {
                    "stage_state": stage_state,
                    "publication_state": publication_state,
                    "target_disposition": disposition,
                }
            )
            validate_public_contract(acquisition, public_validator, recovered_late_success)
            late_success_case_count += 1
    assert late_success_case_count == 40
    unnormalized_late_success = copy.deepcopy(g24_failure)
    unnormalized_late_success["terminal_state"].update(
        {
            "stage_state": "renamed-to-target",
            "publication_state": "rename-succeeded-attestation-incomplete",
            "target_disposition": "retain-unauthorized-target-user-decision-required",
        }
    )
    expect_schema_error("late success unnormalized renamed schema", public_validator, unnormalized_late_success)
    expect_error(
        "late success unnormalized renamed checker",
        lambda: acquisition["validate_public_result_projection"](unnormalized_late_success),
        "PUBLIC_RESULT_ACQUIRE_SUCCESS_LEDGER_RENAME_RECOVERY",
    )
    validate_public_result_branch_schema_equivalence(
        acquisition,
        schemas["public"],
        public_validator,
        fixture_error,
        challenge,
        receipt,
        failure_toolchain,
        failure_reports_by_count,
        success_report,
    )
    validate_public_failure_state_schema_equivalence(
        acquisition,
        schemas["public"],
        public_validator,
        fixture_error,
        challenge,
        receipt,
        failure_toolchain,
        failure_reports_by_count,
        success_report,
    )
    report["public_failure_state_schema_whole_equivalence"] = "PASS"
    report["public_real_builders_schema_and_whole_checker"] = "PASS"
    report["public_authority_generation_gate_ledger_privacy_negatives"] = "PASS"
    report["public_failure_prefix_recovery_state_matrix"] = "PASS"
    report["public_entry_chain_authority_and_reachable_state_matrix"] = "PASS"
    report["public_late_success_observer_40_state_matrix"] = "PASS"

    source_bytes = pathlib.Path(__file__).read_bytes()
    forbidden_source_prefixes = (
        (os.sep + "Users" + os.sep).encode("ascii"),
        (os.sep + "home" + os.sep).encode("ascii"),
    )
    if any(prefix in source_bytes for prefix in forbidden_source_prefixes):
        raise AssertionError("fixture source contains a host-private absolute locator")
    report["fixture_repo_discovery_and_public_privacy"] = "PASS"
    if acquisition["has_forbidden_public_value"](report):
        raise AssertionError("fixture public report violates the privacy contract")

    private_argument = synthetic_private_locator("FixtureSecret", "private-repo")
    parser_failure_vectors = (
        ("--unknown", private_argument),
        ("--repo-root",),
        (private_argument,),
        ("--unknown", "\u0085" + private_argument),
    )
    for vector in parser_failure_vectors:
        parser_stdout = io.StringIO()
        parser_stderr = io.StringIO()
        with contextlib.redirect_stdout(parser_stdout), contextlib.redirect_stderr(parser_stderr):
            try:
                fixture_argument_parser().parse_args(vector)
            except SystemExit as error:
                assert error.code == 2
            else:
                raise AssertionError("fixture parser hostile vector unexpectedly passed")
        combined_output = parser_stdout.getvalue() + parser_stderr.getvalue()
        for token in vector:
            assert token not in combined_output
        assert not acquisition["has_forbidden_public_value"](combined_output.strip())
    report["fixture_cli_failure_privacy"] = "PASS"

    # The production executor accepts only public receipt/challenge values.
    # Raw repo/cache/state/key/envelope locators must not exist in its CLI ABI,
    # and hostile argparse inputs must never be echoed.
    forbidden_locator_options = {
        "--repo-root", "--cache-root", "--state-root", "--key-file", "--envelope",
    }
    production_parser = acquisition["parser"]()
    all_option_strings = set()
    parsers_to_visit = [production_parser]
    while parsers_to_visit:
        current_parser = parsers_to_visit.pop()
        for action in current_parser._actions:
            all_option_strings.update(action.option_strings)
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                parsers_to_visit.extend(choices.values())
    assert forbidden_locator_options.isdisjoint(all_option_strings)
    public_cli = (
        "--generation-challenge", "GOV01-GEN-20260820-" + ("c" * 64),
        "--receipt-digest", "d" * 64,
        "--approval-challenge", "GOV01-SA-20260820-" + ("e" * 64),
    )
    for mode in ("census", "verify", "acquire"):
        parsed = production_parser.parse_args((mode,) + public_cli)
        assert parsed.mode == mode
        assert all(not hasattr(parsed, name) for name in ("repo_root", "cache_root", "state_root", "key_file", "envelope"))
    for option in sorted(forbidden_locator_options):
        vector = ("acquire", option, private_argument) + public_cli
        parser_stdout = io.StringIO()
        parser_stderr = io.StringIO()
        with contextlib.redirect_stdout(parser_stdout), contextlib.redirect_stderr(parser_stderr):
            expect_error(
                "production private-locator CLI " + option,
                lambda value=vector: acquisition["parser"]().parse_args(value),
                "USAGE",
            )
        combined_output = parser_stdout.getvalue() + parser_stderr.getvalue()
        assert private_argument not in combined_output and option not in combined_output
        assert not acquisition["has_forbidden_public_value"](combined_output.strip())
    report["production_cli_public_receipt_only_and_private_locator_free"] = "PASS"

    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
