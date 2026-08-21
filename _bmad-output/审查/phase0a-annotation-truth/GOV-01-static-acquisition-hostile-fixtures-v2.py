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
        "G01": {"challenge_claim_created": True, "ledger_receipt_consumed_recorded": True, "first_authorized_write_contract": "exclusive-0700-challenge-mkdir"},
        "G02": {"authorized_locator_commitment_count": 5, "private_control_identity_commitment": zero, "private_locator_public_count": 0, "private_vault_read_count": 0},
        "G03": {"toolchain_role_count": 9, "toolchain_set_receipt_sha256": zero, "dynamic_closure_receipt_sha256": zero, "assurance": "runtime-self-attested-not-pre-exec", "pre_exec_launcher_attested": False},
        "G04": {"authorized_subprocess_role_count": 5, "shell_allowed": False, "network_capable_child_authorized": False, "authorized_network_call_site_invocation_count": 0, "runtime_network_syscall_observation_available": False, "assurance": "static-structural-self-attestation-not-syscall-observation"},
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

    captured_git_argv = []
    original_run_process = acquisition["run_process"]
    acquisition["_GIT_DEVELOPER_ROOTS"]["/fixture/git"] = "/fixture/developer"
    acquisition["_GIT_READ_BOUNDARIES"]["/fixture/repo"] = (
        "/fixture/repo/.git/worktrees/fixture",
        "/fixture/repo/.git",
    )
    acquisition["run_process"] = lambda argv, *_args, **_kwargs: captured_git_argv.append(list(argv)) or b""
    try:
        acquisition["run_git"](
            "/fixture/git",
            "/fixture/repo",
            ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
            "FIXTURE_GIT_STATUS",
            enumerates_worktree=True,
            authorized_tree_excludes=(".gov01-toolchain-stage-" + locator_challenge, "node_modules"),
            authorized_exact_file_excludes=(expected_relative,),
        )
    finally:
        acquisition["run_process"] = original_run_process
        acquisition["_GIT_DEVELOPER_ROOTS"].pop("/fixture/git", None)
        acquisition["_GIT_READ_BOUNDARIES"].pop("/fixture/repo", None)
    assert len(captured_git_argv) == 1
    git_argv = captured_git_argv[0]
    exact_pathspec = ":(top,literal,exclude)" + expected_relative
    assert git_argv.count(exact_pathspec) == 1
    assert exact_pathspec + "/**" not in git_argv
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

    with tempfile.TemporaryDirectory(prefix="gov01-fsmonitor-", dir="/private/tmp") as temporary:
        repo = pathlib.Path(temporary) / "repo"
        repo.mkdir()
        git_binary = "/Library/Developer/CommandLineTools/usr/bin/git"
        run_checked([git_binary, "init", "-q"], repo)
        run_checked([git_binary, "config", "user.name", "fixture"], repo)
        run_checked([git_binary, "config", "user.email", "fixture@example.invalid"], repo)
        tracked = repo / "tracked.txt"
        write_bytes(tracked, b"tracked\n", 0o600)
        run_checked([git_binary, "add", "tracked.txt"], repo)
        run_checked([git_binary, "commit", "-q", "-m", "fixture"], repo)
        marker = repo / "FSMONITOR_EXECUTED"
        monitor = repo / "fsmonitor.sh"
        write_bytes(monitor, ("#!/bin/sh\n/usr/bin/touch '%s'\nexit 0\n" % marker).encode(), 0o700)
        run_checked([git_binary, "config", "core.fsmonitor", str(monitor)], repo)
        git_hash = acquisition["hash_regular_absolute"](git_binary, "FIXTURE_GIT")["sha256"]
        acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][git_binary] = git_hash
        acquisition["_GIT_DEVELOPER_ROOTS"][git_binary] = str(pathlib.Path(git_binary).parents[2])
        acquisition["git_control_preflight"](str(repo), b"z" * 32)
        contract_error_type = acquisition["ContractError"]
        try:
            acquisition["run_git"](
                git_binary,
                str(repo),
                ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
                "FIXTURE_STATUS",
                enumerates_worktree=True,
            )
        except contract_error_type as error:
            public_code = getattr(error, "reason", getattr(error, "public_code", ""))
            if public_code != "FIXTURE_STATUS_SANDBOX_INIT":
                raise
            true_binary = "/usr/bin/true"
            acquisition["_AUTHORIZED_EXECUTABLE_HASHES"][true_binary] = acquisition[
                "hash_regular_absolute"
            ](true_binary, "FIXTURE_TRUE")["sha256"]
            try:
                acquisition["run_process"](
                    [true_binary],
                    acquisition["git_env"](),
                    4096,
                    "FIXTURE_MINIMAL_SANDBOX",
                    sandbox_profile=b"(version 1)\n(allow default)\n",
                )
            except contract_error_type as minimal_error:
                minimal_code = getattr(
                    minimal_error,
                    "reason",
                    getattr(minimal_error, "public_code", ""),
                )
                if minimal_code != "FIXTURE_MINIMAL_SANDBOX_SANDBOX_INIT":
                    raise
                git_sandbox_mode = "nested-host-sandbox-refused-second-sandbox-fail-closed"
            else:
                raise error
            finally:
                acquisition["_AUTHORIZED_EXECUTABLE_HASHES"].pop(true_binary, None)
        else:
            git_sandbox_mode = "host-sandbox-enforced-positive"
            assert not marker.exists()

            # Inject an include only after the direct control preflight.  The
            # child sandbox, not a second source scan, must prevent Git from
            # following this external locator.
            post_preflight_include = pathlib.Path(temporary) / "post-preflight-include.cfg"
            write_bytes(post_preflight_include, b"[core]\n\tbare = false\n", 0o600)
            run_checked([git_binary, "config", "include.path", str(post_preflight_include)], repo)
            expect_error(
                "post-preflight git include sandbox",
                lambda: acquisition["safe_git_scalar"](
                    git_binary,
                    str(repo),
                    ["rev-parse", "--verify", "HEAD"],
                    "FIXTURE_POST_PREFLIGHT_INCLUDE",
                ),
                "FIXTURE_POST_PREFLIGHT_INCLUDE_RESULT",
            )
            run_checked([git_binary, "config", "--unset-all", "include.path"], repo)

            # Likewise, make an object available only through a newly inserted
            # alternates file.  A command that would succeed without sandboxing
            # must fail after the preflight-to-exec race.
            external_git = pathlib.Path(temporary) / "external-objects.git"
            run_checked([git_binary, "init", "--bare", "-q", str(external_git)], repo)
            hashed = subprocess.run(
                [git_binary, "--git-dir", str(external_git), "hash-object", "-w", "--stdin"],
                input=b"synthetic external object\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
            )
            assert hashed.returncode == 0 and len(hashed.stdout.strip()) in (40, 64)
            post_info = repo / ".git/objects/info"
            post_info.mkdir(mode=0o700, exist_ok=True)
            post_alternates = post_info / "alternates"
            write_bytes(post_alternates, (str(external_git / "objects") + "\n").encode("utf-8"), 0o600)
            expect_error(
                "post-preflight git alternates sandbox",
                lambda: acquisition["run_git"](
                    git_binary,
                    str(repo),
                    ["cat-file", "-t", hashed.stdout.strip().decode("ascii")],
                    "FIXTURE_POST_PREFLIGHT_ALTERNATES",
                ),
                "FIXTURE_POST_PREFLIGHT_ALTERNATES_RESULT",
            )
            post_alternates.unlink()

            # With a worktree-reading profile, explicit Vault-family denies
            # must override the broad repository subtree allowance.
            for private_component in ("canvas-vault-fixture", ".obsidian"):
                private_file = repo / private_component / "sentinel.txt"
                private_file.parent.mkdir(mode=0o700)
                write_bytes(private_file, b"synthetic private sentinel\n", 0o600)
                expect_error(
                    "git worktree privacy sandbox " + private_component,
                    lambda path=str(private_file): acquisition["run_process"](
                        [git_binary, "-C", str(repo), "hash-object", path],
                        acquisition["git_env"](),
                        4096,
                        "FIXTURE_WORKTREE_PRIVACY",
                        sandbox_profile=acquisition["git_read_sandbox_profile"](
                            git_binary,
                            str(repo),
                            True,
                        ),
                    ),
                    "FIXTURE_WORKTREE_PRIVACY_RESULT",
                )

        included = repo / "external-include.cfg"
        write_bytes(included, b"[core]\n\tbare = false\n", 0o600)
        run_checked([git_binary, "config", "include.path", str(included)], repo)
        expect_error(
            "git config include",
            lambda: acquisition["git_control_preflight"](str(repo), b"z" * 32),
            "GIT_CONFIG_INCLUDE_PROHIBITED",
        )
        run_checked([git_binary, "config", "--unset-all", "include.path"], repo)
        alternates = repo / ".git/objects/info/alternates"
        write_bytes(alternates, b"/private/tmp/prohibited-object-store\n", 0o600)
        expect_error(
            "git object alternate",
            lambda: acquisition["git_control_preflight"](str(repo), b"z" * 32),
            "GIT_ALTERNATE_CONTROL_PROHIBITED",
        )
        alternates.unlink()

        linked_root = repo / ".claude/worktrees/fixture-linked"
        linked_root.parent.mkdir(parents=True, mode=0o700)
        run_checked(
            [git_binary, "worktree", "add", "-q", "-b", "fixture-linked", str(linked_root)],
            repo,
        )
        linked_observation = acquisition["git_control_preflight"](str(linked_root), b"z" * 32)
        assert linked_observation["marker"]["kind"] == "gitfile"
        linked_marker = (linked_root / ".git").read_text(encoding="utf-8")
        linked_git_dir = pathlib.Path(linked_marker[len("gitdir: ") :].strip())

        unrelated = repo / "unrelated-linked"
        unrelated.mkdir(mode=0o700)
        write_bytes(
            unrelated / ".git",
            ("gitdir: " + str(linked_git_dir) + "\n").encode("utf-8"),
            0o600,
        )
        expect_error(
            "unrelated ancestor git worktree",
            lambda: acquisition["git_control_preflight"](str(unrelated), b"z" * 32),
            "GIT_CONTROL_ADMIN_ANCHOR",
        )

        linked_info = linked_git_dir / "objects/info"
        linked_info.mkdir(parents=True, mode=0o700)
        linked_alternates = linked_info / "alternates"
        write_bytes(linked_alternates, b"synthetic external objects\n", 0o600)
        expect_error(
            "worktree-local object alternate",
            lambda: acquisition["git_control_preflight"](str(linked_root), b"z" * 32),
            "GIT_ALTERNATE_CONTROL_PROHIBITED",
        )
        linked_alternates.unlink()

        reverse_pointer = linked_git_dir / "gitdir"
        original_reverse = reverse_pointer.read_bytes()
        rewrite_bytes(reverse_pointer, (str(unrelated / ".git") + "\n").encode("utf-8"))
        expect_error(
            "linked worktree reverse pointer",
            lambda: acquisition["git_control_preflight"](str(linked_root), b"z" * 32),
            "GIT_WORKTREE_GITDIR_BINDING",
        )
        rewrite_bytes(reverse_pointer, original_reverse)
    report["git_fsmonitor_override_zero_marker"] = "PASS"
    report["git_include_and_alternate_rejected_pre_command"] = "PASS"
    report["git_read_sandbox_validation_mode"] = git_sandbox_mode

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
    report["envelope_joint_schema_manual_positive_and_hostile_negatives"] = "PASS"

    # A GEN approval is consumed by a durable private claim, not merely by the
    # continued presence of the public final file.  Exercise the production
    # claim ABI against a synthetic private control container while replacing
    # only the already-tested control-preparation projection/locator derivation
    # boundary; record construction, O_EXCL writes, HMAC validation, modes and
    # recovery comparison remain production code.
    with tempfile.TemporaryDirectory(prefix="gov01-generation-claim-", dir="/private/tmp") as temporary:
        generation_root = pathlib.Path(temporary)
        state_root = generation_root / "state"
        claims_root = state_root / "claims"
        state_root.mkdir(mode=0o700)
        claims_root.mkdir(mode=0o700)
        os.chmod(state_root, 0o700)
        os.chmod(claims_root, 0o700)
        key_path = state_root / "hmac.key"
        write_bytes(key_path, b"g" * 32, 0o600)
        runtime_args = acquisition["GenerationRuntimeArgsV2"](
            str(generation_root / "repo"),
            str(generation_root / "cache"),
            str(state_root),
            str(key_path),
            str(generation_root / "repo" / synthetic_envelope["authorization_preimage"]["envelope_repo_relative_path"]),
        )
        generation_authorization = synthetic_envelope["generation_authorization"]
        final_raw = acquisition["canonical_json"](synthetic_envelope)
        original_revalidate = acquisition["revalidate_generation_runtime_args_v2"]
        original_control_projection = acquisition["verify_control_preparation_projection_v2"]
        original_load_key = acquisition["load_hmac_key"]
        original_fsync = acquisition["os"].fsync
        fsync_calls = []

        def counted_fsync(fd):
            fsync_calls.append(fd)
            return original_fsync(fd)

        acquisition["revalidate_generation_runtime_args_v2"] = (
            lambda _runtime, _generation: synthetic_envelope["authorization_preimage"][
                "envelope_repo_relative_path"
            ]
        )
        acquisition["verify_control_preparation_projection_v2"] = lambda _runtime: {}
        acquisition["load_hmac_key"] = lambda *_args, **_kwargs: b"g" * 32
        acquisition["os"].fsync = counted_fsync
        previous_umask = os.umask(0o077)
        try:
            assert acquisition["probe_generation_claim_v2"](
                runtime_args=runtime_args,
                generation_authorization=generation_authorization,
            ) is None
            record = acquisition["create_generation_claim_v2"](
                runtime_args=runtime_args,
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
            recovered = acquisition["probe_generation_claim_v2"](
                runtime_args=runtime_args,
                generation_authorization=generation_authorization,
            )
            assert recovered == record
            assert recovered["acquisition_approval_challenge_id"] == synthetic_envelope[
                "approval_challenge_id"
            ]
            assert acquisition["verify_generation_claim_recovery_v2"](
                runtime_args=runtime_args,
                generation_authorization=generation_authorization,
                final_envelope_raw=final_raw,
            ) == record
            expect_error(
                "generation claim replay create",
                lambda: acquisition["create_generation_claim_v2"](
                    runtime_args=runtime_args,
                    generation_authorization=generation_authorization,
                    final_envelope_raw=final_raw,
                    clock=lambda: witness_now,
                ),
                "PRIVATE_CHILD_EXISTS",
            )
            # A racing loser may only recover the already-authenticated
            # winner; it may not mint another SA/time/raw identity.
            assert acquisition["probe_generation_claim_v2"](
                runtime_args=runtime_args,
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
                lambda: acquisition["verify_generation_claim_recovery_v2"](
                    runtime_args=runtime_args,
                    generation_authorization=generation_authorization,
                    final_envelope_raw=changed_raw,
                ),
                "GENERATION_CLAIM_RECOVERY_DRIFT",
            )
            # The public final may be absent or externally deleted; the
            # retained claim still fixes the same SA/time/raw identity.
            assert not pathlib.Path(runtime_args.envelope).exists()
            assert acquisition["probe_generation_claim_v2"](
                runtime_args=runtime_args,
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
                lambda: acquisition["probe_generation_claim_v2"](
                    runtime_args=runtime_args,
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
                lambda: acquisition["probe_generation_claim_v2"](
                    runtime_args=runtime_args,
                    generation_authorization=generation_authorization,
                ),
                "GENERATION_CLAIM_HMAC",
            )
            rewrite_bytes(record_path, original_record_raw)
            write_bytes(claim_path / "unexpected-child", b"fixture", 0o600)
            expect_error(
                "generation claim extra child retained",
                lambda: acquisition["probe_generation_claim_v2"](
                    runtime_args=runtime_args,
                    generation_authorization=generation_authorization,
                ),
                "GENERATION_CLAIM_PARTIAL_OR_UNEXPECTED",
            )
        finally:
            os.umask(previous_umask)
            acquisition["os"].fsync = original_fsync
            acquisition["load_hmac_key"] = original_load_key
            acquisition["verify_control_preparation_projection_v2"] = original_control_projection
            acquisition["revalidate_generation_runtime_args_v2"] = original_revalidate
    report["durable_generation_claim_single_use_and_recovery"] = "PASS"

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
