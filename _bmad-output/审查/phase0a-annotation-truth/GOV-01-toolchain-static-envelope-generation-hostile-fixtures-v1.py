#!/usr/bin/env python3
"""Hostile, public-only contract checks for the GOV-01 generation issuer.

The fixture imports the issuer as source, uses deterministic synthetic contract
values, and writes only inside a temporary directory.  It never invokes
``issue`` or ``generate`` and never resolves any private locator.
"""

import argparse
import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker


FIXTURE_VERSION = "gov01-static-envelope-generation-hostile-fixtures-v1"
CONTROL_SUFFIX = pathlib.Path(
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-static-envelope-generation-hostile-fixtures-v1.py"
)
GENERATOR_RELATIVE = pathlib.Path(
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-static-envelope-generation-v1.py"
)
SCHEMA_RELATIVE = pathlib.Path(
    "_bmad-output/审查/phase0a-annotation-truth/"
    "GOV-01-toolchain-static-envelope-generation-envelope-v1.schema.json"
)
HOST_SANDBOX_POSITIVE = "host-sandbox-enforced-positive"
HOST_SANDBOX_NESTED_REFUSED = "nested-host-sandbox-refused-second-sandbox-fail-closed"
EXPECTED_GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1 = (
    "the kernel and each owning same-UID production process are trusted; POSIX 0600 and 0700 modes isolate other "
    "UIDs but do not isolate an unsandboxed process with the same effective UID, so each adapter root has exactly "
    "one owning process and compliant same-UID product processes never mutate another invocation's root; "
    "non-cooperating same-UID filesystem mutation, out-of-process ptrace or code injection, and out-of-process "
    "access to the 0600 private HMAC key are outside the supported threat model"
)
EXPECTED_GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1 = (
    "every spawned Git child is sandboxed and has no authority to create, rename, unlink or write the "
    "private-temporary parent namespace or any sibling adapter root; the product owns only the fresh exact adapter "
    "entry, root and descendants for that invocation, while /private/tmp and sibling entries remain ambient host "
    "namespace; every product invocation creates one fresh unique adapter root; the process-wide non-reentrant "
    "scope and registry forbid interleaved adapter ownership within one process and do not claim cross-process "
    "exclusion"
)
EXPECTED_GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1 = (
    "under the declared Git metadata adapter trust boundary and host assurance, cleanup success or retryable "
    "pre-claim failure requires pre-removal root and Git identity agreement, authorized-path removal, post-removal "
    "absence, and zero pathname and registry residue; any observed root or Git identity drift, missing authorized "
    "pathname, cleanup error, or residue is terminal and quiescence must fail; preservation against a "
    "non-cooperating same-UID replacement at the final pathname-deletion linearization point is outside the "
    "supported guarantee"
)


class FixtureFailure(Exception):
    pass


class PrivacySafeParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        self.exit(2, self.prog + ": error: fixture-arguments-invalid\n")


def require(condition: bool, label: str) -> None:
    if not condition:
        raise FixtureFailure(label)


def derive_repo_root() -> pathlib.Path:
    source = pathlib.Path(__file__).resolve(strict=True)
    suffix = pathlib.Path(*CONTROL_SUFFIX.parts)
    if tuple(source.parts[-len(suffix.parts) :]) != suffix.parts:
        raise FixtureFailure("fixture-source-suffix")
    root = source
    for _part in suffix.parts:
        root = root.parent
    return root.resolve(strict=True)


def load_json(path: pathlib.Path) -> Any:
    raw = path.read_bytes()
    require(raw and not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw, "json-encoding")
    seen: List[str] = []

    def object_pairs(pairs: Sequence[tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "json-duplicate-key")
            result[key] = value
            seen.append(key)
        return result

    value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=object_pairs)
    require(bool(seen), "json-empty-object-stream")
    return value


def load_generator(root: pathlib.Path) -> Any:
    path = root / GENERATOR_RELATIVE
    spec = importlib.util.spec_from_file_location("gov01_generation_fixture_target", path)
    require(spec is not None and spec.loader is not None, "generator-import-spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def strict_format_checker(generator: Any) -> FormatChecker:
    checker = FormatChecker()

    @checker.checks("date-time", raises=Exception)
    def strict_utc_second(value: object) -> bool:
        if not isinstance(value, str):
            return False
        generator.parse_utc(value, "FIXTURE_TIME")
        return True

    return checker


def host_sandbox_capability_mode(generator: Any) -> str:
    """Classify nested sandbox_init before any adapter-backed check runs."""

    try:
        generator.run_process(
            ["/usr/bin/true"],
            "HOST_SANDBOX_CAPABILITY",
            sandbox_profile=b"(version 1)\n(allow default)\n",
        )
    except generator.GenerationError as error:
        if error.public_code == "HOST_SANDBOX_CAPABILITY_SANDBOX_INIT":
            return HOST_SANDBOX_NESTED_REFUSED
        raise
    return "host-sandbox-init-available"


def synthetic_artifacts(generator: Any) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    predecessor_digests = {
        "first-receipt-envelope": generator.FIRST_ENVELOPE_SHA256,
        "bootstrap-patch": generator.BOOTSTRAP_PATCH_SHA256,
        "control-prep-envelope": generator.CONTROL_PREP_ENVELOPE_SHA256,
    }
    for role, path in generator.ARTIFACT_SPECS:
        raw = ("fixture\x00" + role + "\x00" + path).encode("utf-8")
        digest = predecessor_digests.get(role, generator.sha256(raw))
        result.append(
            {
                "role": role,
                "path": path,
                "file_kind": "regular",
                "byte_length": len(raw),
                "raw_file_sha256": digest,
            }
        )
    return result


def synthetic_envelope(generator: Any) -> Dict[str, Any]:
    issued = dt.datetime(2026, 8, 21, 1, 2, 3, tzinfo=dt.timezone.utc)
    challenge = "GOV01-GEN-20260821-" + "a" * 64
    head_ref = "refs/heads/gov01-generation-fixture"
    repository = {
        "head": "1" * 40,
        "tree": "2" * 40,
        "head_ref": head_ref,
        "head_ref_sha256": generator.head_ref_digest(head_ref),
        "head_ref_bytes": len(head_ref.encode("ascii")),
        "other_refs_sha256": "3" * 64,
        "other_refs_bytes": 0,
        "git_control_profile": {
            "marker_kind": "gitfile",
            "common_directory_relation": "git-directory-contained-under-common-worktrees",
            "include_controls_absent": True,
            "alternate_object_controls_absent": True,
        },
    }
    return generator.build_issue_envelope(
        challenge,
        issued,
        repository,
        synthetic_artifacts(generator),
    )


def synthetic_static_expected(bound_executor: Any) -> Dict[str, Any]:
    """One locator-free witness for the executor's frozen static contract."""

    return {
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
        "resolution": {
            "row_count": 256,
            "body_bytes": 26_629,
            "sha256": "2cecc0432d6f13be979b884b570e81c1ba443c9956e2149ba08b64d1a40433b0",
            "required_missing": 0,
            "allowed_missing": 10,
        },
        "tree": {
            "entry_count": 4665,
            "file_count": 4099,
            "directory_count": 554,
            "symlink_count": 12,
            "body_bytes": 539_842,
            "sha256": bound_executor.EXPECTED_TREE_SHA256,
        },
    }


def bound_executor_fd_claim_core_matrix(
    bound_executor: Any,
    generation_authorization: Mapping[str, Any],
    final_envelope_raw: bytes,
    census_at: str,
) -> Dict[str, Any]:
    """Exercise the production durable-claim core through caller-owned FDs."""

    def identity_and_policy(fd: int) -> Tuple[int, int, int, int, int, int]:
        metadata = os.fstat(fd)
        return (
            metadata.st_dev,
            metadata.st_ino,
            stat.S_IFMT(metadata.st_mode),
            stat.S_IMODE(metadata.st_mode),
            metadata.st_uid,
            metadata.st_gid,
        )

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-claim-core-",
        dir=temp_parent,
    ) as temporary:
        state_root = pathlib.Path(temporary) / "state"
        claims_root = state_root / "claims"
        state_root.mkdir(mode=0o700)
        claims_root.mkdir(mode=0o700)
        state_fd = os.open(
            state_root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        claims_fd: Optional[int] = None
        try:
            claims_fd = os.open(
                "claims",
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=state_fd,
            )
            state_identity = identity_and_policy(state_fd)
            claims_identity = identity_and_policy(claims_fd)
            require(state_identity[3] == 0o700, "bound-claim-state-mode")
            require(claims_identity[3] == 0o700, "bound-claim-container-mode")
            require(
                state_identity[4:] == claims_identity[4:],
                "bound-claim-container-owner",
            )
            expected_uid, expected_gid = state_identity[4], state_identity[5]
            key = b"g" * 32
            common = {
                "state_fd": state_fd,
                "claims_fd": claims_fd,
                "expected_uid": expected_uid,
                "expected_gid": expected_gid,
                "key": key,
                "generation_authorization": generation_authorization,
            }

            first_probe = bound_executor.probe_generation_claim_from_verified_fds_v2(**common)
            require(first_probe is None, "bound-claim-initial-probe")
            require(
                identity_and_policy(state_fd) == state_identity
                and identity_and_policy(claims_fd) == claims_identity,
                "bound-claim-probe-fd-identity",
            )

            witness = bound_executor.parse_utc(census_at, "FIXTURE_BOUND_CLAIM_CLOCK")
            created = bound_executor.create_generation_claim_from_verified_fds_v2(
                **common,
                final_envelope_raw=final_envelope_raw,
                clock=lambda: witness,
            )
            require(
                identity_and_policy(state_fd) == state_identity
                and identity_and_policy(claims_fd) == claims_identity,
                "bound-claim-create-fd-identity",
            )

            probed = bound_executor.probe_generation_claim_from_verified_fds_v2(**common)
            require(
                bound_executor.canonical_json(probed) == bound_executor.canonical_json(created),
                "bound-claim-probe-record",
            )
            require(
                identity_and_policy(state_fd) == state_identity
                and identity_and_policy(claims_fd) == claims_identity,
                "bound-claim-second-probe-fd-identity",
            )

            recovered = bound_executor.verify_generation_claim_recovery_from_verified_fds_v2(
                **common,
                final_envelope_raw=final_envelope_raw,
            )
            require(
                bound_executor.canonical_json(recovered) == bound_executor.canonical_json(created),
                "bound-claim-recovery-record",
            )
            require(
                identity_and_policy(state_fd) == state_identity
                and identity_and_policy(claims_fd) == claims_identity,
                "bound-claim-recovery-fd-identity",
            )

            replay_code = ""
            try:
                bound_executor.create_generation_claim_from_verified_fds_v2(
                    **common,
                    final_envelope_raw=final_envelope_raw,
                    clock=lambda: witness,
                )
            except bound_executor.ContractError as error:
                replay_code = error.public_code
            require(replay_code == "PRIVATE_CHILD_EXISTS", "bound-claim-replay-rejection")
            require(
                identity_and_policy(state_fd) == state_identity
                and identity_and_policy(claims_fd) == claims_identity,
                "bound-claim-replay-fd-identity",
            )

            claim_name = bound_executor.generation_claim_name_v2(generation_authorization)
            claim_meta = os.stat(claim_name, dir_fd=claims_fd, follow_symlinks=False)
            claim_fd = os.open(
                claim_name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=claims_fd,
            )
            record_fd: Optional[int] = None
            try:
                record_fd = os.open(
                    "generation-record.json",
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=claim_fd,
                )
                record_meta = os.fstat(record_fd)
                require(
                    stat.S_ISDIR(claim_meta.st_mode)
                    and stat.S_IMODE(claim_meta.st_mode) == 0o700
                    and stat.S_ISREG(record_meta.st_mode)
                    and stat.S_IMODE(record_meta.st_mode) == 0o600
                    and record_meta.st_nlink == 1,
                    "bound-claim-durable-policy",
                )
            finally:
                if record_fd is not None:
                    os.close(record_fd)
                os.close(claim_fd)

            return {
                "ok": True,
                "probe_module": bound_executor.probe_generation_claim_from_verified_fds_v2.__module__,
                "create_module": bound_executor.create_generation_claim_from_verified_fds_v2.__module__,
                "recovery_module": (
                    bound_executor.verify_generation_claim_recovery_from_verified_fds_v2.__module__
                ),
                "caller_fd_identity_stable": True,
                "initial_probe_absent": True,
                "durable_record_policy": True,
                "replay_public_code": replay_code,
            }
        finally:
            if claims_fd is not None:
                os.close(claims_fd)
            os.close(state_fd)


def pending_contract_pointer(path: tuple[Any, ...]) -> str:
    return "#" if not path else "#/" + "/".join(
        str(component).replace("~", "~0").replace("/", "~1") for component in path
    )


def iter_pending_bool_int_paths(value: Any, path: tuple[Any, ...] = ()) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_pending_bool_int_paths(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_pending_bool_int_paths(child, path + (index,))
    elif type(value) in (bool, int):
        yield path, value


def bound_pending_bool_int_scalar_type_matrix(
    bound_executor: Any,
    validator: Draft202012Validator,
    baseline: Mapping[str, Any],
    census_at: str,
) -> Dict[str, Any]:
    """Run the full pending bool/int type matrix through Draft and production manual checks."""
    scalar_rows = sorted(
        iter_pending_bool_int_paths(baseline),
        key=lambda item: pending_contract_pointer(item[0]),
    )
    typed_paths = [
        {
            "path": pending_contract_pointer(path),
            "type": "boolean" if type(value) is bool else "integer",
        }
        for path, value in scalar_rows
    ]
    schema_rejection_count = 0
    manual_rejection_count = 0
    witness_now = bound_executor.parse_utc(census_at, "FIXTURE_BOUND_PENDING_TIME")
    for path, value in scalar_rows:
        candidate = copy.deepcopy(baseline)
        current: Any = candidate
        for component in path[:-1]:
            current = current[component]
        current[path[-1]] = int(value) if type(value) is bool else bool(value)
        schema_rejected = not validator.is_valid(candidate)
        try:
            bound_executor.validate_manual_envelope_contract(candidate, now=witness_now)
        except bound_executor.ContractError:
            manual_rejected = True
        else:
            manual_rejected = False
        schema_rejection_count += int(schema_rejected)
        manual_rejection_count += int(manual_rejected)
        require(
            schema_rejected == manual_rejected,
            "bound-pending-schema-manual-type-difference-"
            + "-".join(str(component) for component in path),
        )
        require(
            schema_rejected,
            "bound-pending-bool-int-accepted-" + "-".join(str(component) for component in path),
        )
    bool_count = sum(row["type"] == "boolean" for row in typed_paths)
    int_count = sum(row["type"] == "integer" for row in typed_paths)
    require(
        len(typed_paths) == 145
        and bool_count == 66
        and int_count == 79
        and schema_rejection_count == len(typed_paths)
        and manual_rejection_count == len(typed_paths),
        "bound-pending-bool-int-frozen-counts",
    )
    return {
        "ok": True,
        "mutation_count": len(typed_paths),
        "bool_path_count": bool_count,
        "int_path_count": int_count,
        "integer_zero_or_one_baseline_count": sum(
            type(value) is int and value in (0, 1) for _path, value in scalar_rows
        ),
        "schema_rejection_count": schema_rejection_count,
        "manual_rejection_count": manual_rejection_count,
        "typed_paths": typed_paths,
        "typed_path_set_sha256": bound_executor.sha256(
            b"CLS/GOV01/PENDING-BOOL-INT-SCALAR-PATH-SET/v1\x00"
            + bound_executor.canonical_json(typed_paths)
        ),
    }


def bound_executor_pure_contract_matrix(
    synthetic_root: pathlib.Path,
    generator: Any,
    bound_executor: Any,
    context: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    """Execute the content-addressed builder and both production checkers."""

    artifact_observations: List[Dict[str, Any]] = []
    for role, relative in bound_executor.PENDING_STATIC_ARTIFACT_SPECS:
        raw = (synthetic_root / relative).read_bytes()
        artifact_observations.append(
            {
                "role": role,
                "path": relative,
                "bytes": len(raw),
                "sha256": generator.sha256(raw),
            }
        )
    micro_raw = context["micro_raw"]
    artifact_observations.append(
        {
            "role": bound_executor.GENERATION_APPROVAL_ROLE,
            "path": context["micro_relative"],
            "bytes": len(micro_raw),
            "sha256": generator.sha256(micro_raw),
        }
    )
    artifacts = bound_executor.public_artifact_entries_v2(artifact_observations)
    by_role = {entry["role"]: entry for entry in artifacts}
    pending_schema = by_role["pending-envelope-schema"]

    tool_entries: List[Dict[str, Any]] = []
    for role in bound_executor.TOOLCHAIN_ROLES:
        artifact_kind, digest_profile, execution_authority = bound_executor.TOOLCHAIN_ROLE_PROFILE[role]
        artifact = by_role.get(role)
        digest = (
            artifact["raw_file_sha256"]
            if isinstance(artifact, Mapping)
            else generator.sha256(("synthetic-tool\x00" + role).encode("ascii"))
        )
        tool_entries.append(
            {
                "role": role,
                "logical_id": bound_executor.TOOLCHAIN_LOGICAL_ID_BY_ROLE[role],
                "artifact_kind": artifact_kind,
                "version": bound_executor.expected_tool_version(role),
                "digest_profile": digest_profile,
                "raw_digest_sha256": digest,
                "private_locator_omitted": True,
                "execution_authority": execution_authority,
            }
        )

    expected = synthetic_static_expected(bound_executor)
    lock_observation = {
        "host_selected_package_count": expected["selected_package_count"],
        "host_selected_cache_bytes": expected["compressed_bytes"],
        "host_bin_link_count": expected["bin_link_count"],
        "expected_archive_member_count": expected["raw_member_count"],
        "expected_resolved_tree_entry_count": expected["tree"]["entry_count"],
        "content_receipt_sha256": expected["content_receipt_sha256"],
        "ustar_closure_sha256": expected["ustar_closure_sha256"],
        "resolution_receipt_sha256": expected["resolution"]["sha256"],
        "expected_tree_sha256": expected["tree"]["sha256"],
    }
    zero = "0" * 64
    labels = {
        "repo_root": "repo-root",
        "cache_root": "npm-cache",
        "state_root": "state-root",
        "key_file": "hmac-key",
        "envelope": "envelope",
    }
    acquisition_challenge = "GOV01-SA-20260821-" + "e" * 64
    census_at = "2026-08-21T00:00:00Z"
    not_after = "2026-08-21T01:00:00Z"
    observations = {
        "artifacts": artifacts,
        "schema_binding_observation": {
            "path": pending_schema["path"],
            "sha256": pending_schema["raw_file_sha256"],
            "bytes": pending_schema["byte_length"],
            "schema_count": 3,
            "schema_bundle_receipt_sha256": generator.sha256(b"synthetic-schema-bundle"),
        },
        "toolchain": {
            "entries": tool_entries,
            "toolchain_set_receipt_sha256": bound_executor.toolchain_set_receipt(tool_entries),
            "dynamic_closure_receipt_sha256": bound_executor.dynamic_toolchain_receipt(tool_entries),
        },
        "git_snapshot": {
            "head": authorization["authorization_commit_oid"],
            "tree": authorization["authorization_tree_oid"],
            "object_format": "sha1"
            if len(authorization["authorization_commit_oid"]) == 40
            else "sha256",
            "commitment": generator.sha256(b"synthetic-git-snapshot"),
            "dirty_manifest_commitment": generator.sha256(b"synthetic-dirty-manifest"),
            "git_metadata_source_commitment": generator.sha256(b"synthetic-git-source"),
            "git_metadata_adapter_profile": bound_executor.GIT_METADATA_ADAPTER_PROFILE_V5,
            "git_metadata_adapter_cleanup_state": "removed",
            "git_metadata_adapter_residue_count": 0,
            "live_git_control_child_read_count": 0,
            "worktree_tree_exclusions": (
                bound_executor.OPAQUE_INDEX_GITLINK_RELATIVE,
                ".gov01-toolchain-stage-" + acquisition_challenge,
                bound_executor.TARGET_NAME,
            ),
            "worktree_exact_file_exclusions": (
                authorization["generated_acquisition_envelope_repo_relative_path"],
            ),
            "status_bytes": 0,
        },
        "process_census": {"claude_session_count": 0},
        "package_lock_raw_sha256": by_role["package-lock"]["raw_file_sha256"],
        "lock_observation": lock_observation,
        "static_expected": expected,
        "hmac_key_id": generator.sha256(b"synthetic-key-id"),
        "authorized_locator_commitments": {
            name: {"label": label, "commitment": zero}
            for name, label in labels.items()
        },
        "private_control_identity_commitment": generator.sha256(b"synthetic-control-identity"),
        "public_repo_artifact_set_receipt_sha256": bound_executor.public_artifact_set_receipt(
            artifact_observations
        ),
        "private_preapproval_commitment": generator.sha256(b"synthetic-preapproval"),
        "predecessor_projection": {
            "control_preparation_result_raw_sha256": generator.sha256(b"synthetic-control-result"),
            "control_preparation_evidence_receipt_sha256": generator.sha256(b"synthetic-control-evidence"),
            "control_preparation_approval_challenge_id": "GOV01-CP-20260821-" + "f" * 32,
            "control_preparation_state": "CONTROL-PREPARED-FULL-TREE-REVALIDATED-PASS",
        },
        "envelope_repo_relative_path": authorization[
            "generated_acquisition_envelope_repo_relative_path"
        ],
    }
    candidate = bound_executor.build_pending_envelope_v2(
        approval_challenge_id=acquisition_challenge,
        census_at_utc=census_at,
        not_after_utc=not_after,
        generation_authorization=authorization,
        observations=observations,
    )
    raw = bound_executor.canonical_json(candidate)
    require(
        bound_executor.parse_json_bytes(raw, "FIXTURE_BOUND_PENDING") == candidate,
        "bound-executor-canonical-roundtrip",
    )
    bound_executor.validate_manual_envelope_contract(
        candidate,
        now=bound_executor.parse_utc(census_at, "FIXTURE_BOUND_PENDING_TIME"),
    )
    require(
        not bound_executor.has_forbidden_pending_envelope_value(candidate),
        "bound-executor-privacy",
    )
    pending_schema_value = load_json(synthetic_root / pending_schema["path"])
    Draft202012Validator.check_schema(pending_schema_value)
    pending_validator = Draft202012Validator(
        pending_schema_value,
        format_checker=strict_format_checker(generator),
    )
    schema_errors = sorted(
        pending_validator.iter_errors(candidate),
        key=lambda error: tuple(str(component) for component in error.absolute_path),
    )
    error_sections = sorted(
        {
            str(next(iter(error.absolute_path), "<root>"))
            for error in schema_errors
        }
    )
    bool_int_scalar_type_parity = bound_pending_bool_int_scalar_type_matrix(
        bound_executor,
        pending_validator,
        candidate,
        census_at,
    )
    claim_core = bound_executor_fd_claim_core_matrix(
        bound_executor,
        authorization,
        raw,
        census_at,
    )
    return {
        "ok": not schema_errors,
        "builder_module": bound_executor.build_pending_envelope_v2.__module__,
        "manual_module": bound_executor.validate_manual_envelope_contract.__module__,
        "privacy_module": bound_executor.has_forbidden_pending_envelope_value.__module__,
        "canonical_bytes": len(raw),
        "schema_error_count": len(schema_errors),
        "schema_error_sections": error_sections,
        "bool_int_scalar_type_parity": bool_int_scalar_type_parity,
        "claim_core": claim_core,
    }


def schema_accepts(validator: Draft202012Validator, value: Any) -> bool:
    return not list(validator.iter_errors(value))


def manual_accepts(generator: Any, value: Any) -> bool:
    try:
        generator.validate_generation_envelope(
            value,
            dt.datetime(2026, 8, 21, 1, 2, 3, tzinfo=dt.timezone.utc),
            require_pending=True,
        )
        return True
    except generator.GenerationError:
        return False


def mutation_rejection_matrix(
    generator: Any,
    validator: Draft202012Validator,
    baseline: Mapping[str, Any],
) -> Dict[str, bool]:
    cases: Dict[str, Any] = {}

    wrong_path = copy.deepcopy(baseline)
    wrong_path["artifacts"][0]["path"] = ".gitignore"
    cases["artifact_role_path"] = wrong_path

    duplicate_role = copy.deepcopy(baseline)
    duplicate_role["artifacts"][1]["role"] = "static-executor"
    duplicate_role["artifacts"][1]["path"] = generator.GENERATOR_RELATIVE
    cases["artifact_duplicate_role_wrong_path"] = duplicate_role

    swapped = copy.deepcopy(baseline)
    swapped["artifacts"][0], swapped["artifacts"][1] = swapped["artifacts"][1], swapped["artifacts"][0]
    cases["artifact_order"] = swapped

    bad_ref_digest = copy.deepcopy(baseline)
    bad_ref_digest["repository_transition"]["authorization_baseline_head_ref_sha256"] = "0"
    cases["head_ref_digest"] = bad_ref_digest

    challenge_date = copy.deepcopy(baseline)
    challenge_date["approval_challenge_id"] = "GOV01-GEN-20260820-" + "a" * 64
    cases["challenge_date"] = challenge_date

    bad_ttl = copy.deepcopy(baseline)
    bad_ttl["not_after_utc"] = "2026-08-21T02:02:03Z"
    cases["ttl"] = bad_ttl

    invalid_calendar = copy.deepcopy(baseline)
    invalid_calendar["issued_at_utc"] = "2026-02-30T01:02:03Z"
    cases["calendar"] = invalid_calendar

    private_text = copy.deepcopy(baseline)
    private_text["success_contract"]["next_required_authority"] = os.sep + "Users" + os.sep + "private"
    cases["private_locator"] = private_text

    claim_profile = copy.deepcopy(baseline)
    claim_profile["generation_claim_contract"]["generation_claim_profile"] = "weaker-claim"
    cases["generation_claim_profile"] = claim_profile

    read_scope = copy.deepcopy(baseline)
    read_scope["authorized_reads"]["private_roles_after_approval"][0] = "read any private key"
    cases["private_read_scope"] = read_scope

    first_write = copy.deepcopy(baseline)
    first_write["mutation_scope"]["first_authority_consuming_persistent_write"] = "write public output before claim"
    cases["first_write_scope"] = first_write

    adapter_profile = copy.deepcopy(baseline)
    adapter_profile["mutation_scope"]["temporary_git_metadata_adapter_profile"] = "unbounded-temp-tree"
    cases["temporary_adapter_profile"] = adapter_profile

    captured_index_profile = copy.deepcopy(baseline)
    captured_index_profile["repository_transition"]["captured_index_root_profile"] = (
        "accept arbitrary gitlinks"
    )
    cases["captured_index_root_profile"] = captured_index_profile

    adapter_trust = copy.deepcopy(baseline)
    adapter_trust["mutation_scope"]["git_metadata_adapter_trust_boundary"] = "trust every same-UID actor"
    cases["git_metadata_adapter_trust_boundary"] = adapter_trust

    adapter_host = copy.deepcopy(baseline)
    adapter_host["mutation_scope"]["git_metadata_adapter_host_assurance"] = "cross-process lock implied"
    cases["git_metadata_adapter_host_assurance"] = adapter_host

    adapter_guarantee = copy.deepcopy(baseline)
    adapter_guarantee["mutation_scope"]["git_metadata_adapter_cleanup_guarantee"] = "cleanup best effort"
    cases["git_metadata_adapter_cleanup_guarantee"] = adapter_guarantee

    privacy_trust = copy.deepcopy(baseline)
    privacy_trust["privacy"]["git_metadata_adapter_trust_boundary"] = "omit host trust premise"
    cases["privacy_git_metadata_adapter_trust_boundary"] = privacy_trust

    adapter_cleanup = copy.deepcopy(baseline)
    adapter_cleanup["mutation_scope"]["temporary_adapter_cleanup_required"] = False
    cases["temporary_adapter_cleanup"] = adapter_cleanup

    adapter_residue = copy.deepcopy(baseline)
    adapter_residue["mutation_scope"]["temporary_adapter_residue_allowed"] = True
    cases["temporary_adapter_residue"] = adapter_residue

    product_cleanup = copy.deepcopy(baseline)
    product_cleanup["mutation_scope"]["product_state_cleanup_allowed"] = True
    cases["product_state_cleanup"] = product_cleanup

    adapter_failure = copy.deepcopy(baseline)
    adapter_failure["failure_contract"]["temporary_adapter_failure"] = "ignore cleanup failure and retry"
    cases["temporary_adapter_failure"] = adapter_failure

    subprocess_scope = copy.deepcopy(baseline)
    subprocess_scope["authorized_subprocesses"]["roles"].append("shell")
    cases["subprocess_scope"] = subprocess_scope

    gitfile_wrong_relation = copy.deepcopy(baseline)
    gitfile_wrong_relation["repository_transition"]["git_control_profile"][
        "common_directory_relation"
    ] = "git-directory-is-common-directory"
    cases["gitfile_relation_binding"] = gitfile_wrong_relation

    directory_wrong_relation = copy.deepcopy(baseline)
    directory_wrong_relation["repository_transition"]["git_control_profile"].update(
        {
            "marker_kind": "directory",
            "common_directory_relation": "git-directory-contained-under-common-worktrees",
        }
    )
    cases["directory_relation_binding"] = directory_wrong_relation

    for role in ("first-receipt-envelope", "bootstrap-patch", "control-prep-envelope"):
        predecessor_artifact = copy.deepcopy(baseline)
        for artifact in predecessor_artifact["artifacts"]:
            if artifact["role"] == role:
                artifact["raw_file_sha256"] = "f" * 64
                break
        cases["predecessor_artifact_" + role] = predecessor_artifact

    result: Dict[str, bool] = {}
    for label, value in cases.items():
        schema_ok = schema_accepts(validator, value)
        manual_ok = manual_accepts(generator, value)
        if label in ("challenge_date", "ttl"):
            # Cross-field time arithmetic is intentionally enforced by the
            # content-addressed manual checker, not by JSON Schema shape alone.
            result[label] = not manual_ok
        else:
            result[label] = (not schema_ok) and (not manual_ok)
    return result


def scalar_leaf_manual_coverage_matrix(
    generator: Any,
    validator: Draft202012Validator,
    baseline: Mapping[str, Any],
) -> bool:
    def leaves(value: Any, path: tuple[Any, ...] = ()) -> Any:
        if isinstance(value, dict):
            for key, child in value.items():
                yield from leaves(child, path + (key,))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from leaves(child, path + (index,))
        else:
            yield path, value

    def changed(value: Any) -> Any:
        if isinstance(value, bool):
            return not value
        if type(value) is int:
            return value + 1
        if value is None:
            return "x"
        if isinstance(value, str):
            if value and all(character in "0123456789abcdef" for character in value):
                return ("0" if value[0] != "0" else "1") + value[1:]
            return value + "x"
        raise FixtureFailure("scalar-leaf-type")

    for path, value in leaves(baseline):
        candidate = copy.deepcopy(baseline)
        current: Any = candidate
        for component in path[:-1]:
            current = current[component]
        current[path[-1]] = changed(value)
        if not schema_accepts(validator, candidate) and manual_accepts(generator, candidate):
            return False
    return True


def bool_int_schema_manual_parity_matrix(
    generator: Any,
    validator: Draft202012Validator,
    baseline: Mapping[str, Any],
) -> int:
    """Reject every JSON bool/int substitution on both validation paths."""

    def leaves(value: Any, path: tuple[Any, ...] = ()) -> Any:
        if isinstance(value, dict):
            for key, child in value.items():
                yield from leaves(child, path + (key,))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from leaves(child, path + (index,))
        else:
            yield path, value

    mutation_count = 0
    for path, value in leaves(baseline):
        if type(value) is bool:
            replacement: Any = int(value)
        elif type(value) is int and value in (0, 1):
            replacement = bool(value)
        else:
            continue
        candidate = copy.deepcopy(baseline)
        current: Any = candidate
        for component in path[:-1]:
            current = current[component]
        current[path[-1]] = replacement
        schema_ok = schema_accepts(validator, candidate)
        manual_ok = manual_accepts(generator, candidate)
        require(
            not schema_ok and not manual_ok,
            "bool-int-schema-manual-parity-" + "-".join(str(component) for component in path),
        )
        mutation_count += 1
    require(mutation_count > 0, "bool-int-mutation-empty")
    return mutation_count


def path_grammar_matrix(schema: Mapping[str, Any], generator: Any) -> bool:
    path_schema = schema["$defs"]["repoRelativePath"]
    validator = Draft202012Validator(path_schema)
    invalid = [
        ".GIT",
        "./package.json",
        "foo//bar",
        "canvas-vault/secret.md",
        ".obsidian/plugins/x",
        "path/" + chr(0x00AD) + "soft",
        "path/" + chr(0x110BD) + "format",
        "path/" + chr(0x13439) + "format",
        "path/" + chr(0x2028) + "line",
        "path/" + chr(0x85) + "control",
    ]
    for value in invalid:
        if validator.is_valid(value):
            return False
        try:
            generator.validate_relative(value, "FIXTURE_PATH")
        except generator.GenerationError:
            continue
        return False
    for reference in ("refs/heads/foo//bar", "refs/heads/canvas-vault-private", "refs/heads/.obsidian/x"):
        try:
            generator.validate_head_ref(reference)
        except generator.GenerationError:
            continue
        return False
    return validator.is_valid("_bmad-output/审查/phase0a-annotation-truth/contract.json")


def final_name_matrix(generator: Any) -> bool:
    generation = "GOV01-GEN-20260821-" + "b" * 64
    expected = (
        generator.CONTROL_PREFIX
        + "GOV-01-toolchain-static-acquisition-pending-"
        + generation
        + ".json"
    )
    if generator.final_relative(generation) != expected:
        return False
    try:
        generator.final_relative("GOV01-SA-20260821-" + "b" * 64)
    except generator.GenerationError:
        return True
    return False


def synthetic_claim_projection(generator: Any) -> tuple[Dict[str, Any], Dict[str, Any]]:
    generation_challenge = "GOV01-GEN-20260821-" + "b" * 64
    acquisition_challenge = "GOV01-SA-20260821-" + "c" * 64
    authorization = {
        "profile": "gov01-static-envelope-generation-authority-v1",
        "approval_challenge_id": generation_challenge,
        "approval_envelope_repo_relative_path": generator.micro_relative(generation_challenge),
        "generated_acquisition_envelope_repo_relative_path": generator.final_relative(generation_challenge),
        "raw_envelope_sha256": "1" * 64,
        "receipt_digest": "2" * 64,
        "receipt_domain_profile": "fixture",
        "authorization_parent_commit_oid": "3" * 40,
        "authorization_parent_tree_oid": "4" * 40,
        "authorization_commit_oid": "5" * 40,
        "authorization_tree_oid": "6" * 40,
        "commit_transition_profile": "fixture",
        "state": "approved-single-path-commit",
        "generation_claim_required": True,
        "generation_claim_profile": generator.GENERATION_CLAIM_PROFILE,
        "generation_claim_record_profile": generator.GENERATION_CLAIM_RECORD_PROFILE,
        "generation_claim_retention": generator.GENERATION_CLAIM_RETENTION,
    }
    record = {
        "profile": "gov01-static-envelope-generation-claim-v1",
        "generation_authorization_challenge_id": generation_challenge,
        "generation_authorization_envelope_raw_sha256": authorization["raw_envelope_sha256"],
        "generation_authorization_receipt_digest": authorization["receipt_digest"],
        "generation_authorization_parent_commit_oid": authorization["authorization_parent_commit_oid"],
        "generation_authorization_parent_tree_oid": authorization["authorization_parent_tree_oid"],
        "generation_authorization_commit_oid": authorization["authorization_commit_oid"],
        "generation_authorization_tree_oid": authorization["authorization_tree_oid"],
        "acquisition_approval_challenge_id": acquisition_challenge,
        "census_at_utc": "2026-08-21T01:02:03Z",
        "not_after_utc": "2026-08-22T01:02:03Z",
        "final_envelope_repo_relative_path": authorization[
            "generated_acquisition_envelope_repo_relative_path"
        ],
        "final_envelope_raw_sha256": "7" * 64,
        "final_envelope_bytes": 4096,
        "final_envelope_receipt_digest": "8" * 64,
        "state": "OUTPUT-IDENTITY-FIXED",
        "record_hmac_sha256": "9" * 64,
    }
    return authorization, record


def authenticated_claim_projection_matrix(generator: Any) -> bool:
    authorization, record = synthetic_claim_projection(generator)
    now = dt.datetime(2026, 8, 21, 1, 2, 4, tzinfo=dt.timezone.utc)
    if generator.checked_generation_claim_record(record, authorization, now=now) != record:
        return False
    mutations: List[Dict[str, Any]] = []
    wrong_path = copy.deepcopy(record)
    wrong_path["final_envelope_repo_relative_path"] = generator.CONTROL_PREFIX + "other.json"
    mutations.append(wrong_path)
    wrong_authority = copy.deepcopy(record)
    wrong_authority["generation_authorization_receipt_digest"] = "a" * 64
    mutations.append(wrong_authority)
    extra = copy.deepcopy(record)
    extra["extra"] = True
    mutations.append(extra)
    bad_challenge = copy.deepcopy(record)
    bad_challenge["acquisition_approval_challenge_id"] = authorization["approval_challenge_id"]
    mutations.append(bad_challenge)
    for mutation in mutations:
        try:
            generator.checked_generation_claim_record(mutation, authorization, now=now)
        except generator.GenerationError:
            continue
        return False
    try:
        generator.checked_generation_claim_record(
            record,
            authorization,
            now=dt.datetime(2026, 8, 22, 1, 2, 3, tzinfo=dt.timezone.utc),
        )
    except generator.GenerationError:
        return True
    return False


def claim_race_branch_matrix(generator: Any) -> bool:
    authorization, record = synthetic_claim_projection(generator)
    raw = b'{"fixture":"pending"}\n'

    class DeterministicContractError(Exception):
        def __init__(self, code: str, public_code: str) -> None:
            super().__init__(public_code)
            self.code = code
            self.public_code = public_code

    class DeterministicExit:
        REPLAY = "REPLAY"

    class DeterministicClaimBoundary:
        ContractError = DeterministicContractError
        Exit = DeterministicExit

        def __init__(self, *, failure_code: Optional[str], winner: Optional[Mapping[str, Any]]) -> None:
            self.failure_code = failure_code
            self.record = None if winner is None else dict(winner)
            self.create_calls = 0
            self.probe_calls = 0
            self.verify_calls = 0

        def create_generation_claim_v2(self, **_arguments: Any) -> Dict[str, Any]:
            self.create_calls += 1
            if self.failure_code is not None:
                code = self.Exit.REPLAY if self.failure_code == "PRIVATE_CHILD_EXISTS" else "EVIDENCE"
                raise self.ContractError(code, self.failure_code)
            self.record = dict(record)
            return dict(record)

        def probe_generation_claim_v2(self, **_arguments: Any) -> Optional[Dict[str, Any]]:
            self.probe_calls += 1
            return None if self.record is None else dict(self.record)

        def verify_generation_claim_recovery_v2(self, **arguments: Any) -> Dict[str, Any]:
            self.verify_calls += 1
            if arguments.get("final_envelope_raw") != raw or self.record is None:
                raise RuntimeError("deterministic-claim-drift")
            return dict(self.record)

    created_boundary = DeterministicClaimBoundary(failure_code=None, winner=None)
    created, won = generator.create_or_observe_generation_claim(
        created_boundary,
        object(),
        authorization,
        raw,
    )
    if (
        not won
        or created != record
        or created_boundary.create_calls != 1
        or created_boundary.probe_calls != 0
        or created_boundary.verify_calls != 1
    ):
        raise FixtureFailure("claim-race-created")

    concurrent_boundary = DeterministicClaimBoundary(failure_code="PRIVATE_CHILD_EXISTS", winner=record)
    observed, won = generator.create_or_observe_generation_claim(
        concurrent_boundary,
        object(),
        authorization,
        b"loser-candidate\n",
    )
    if (
        won
        or observed != record
        or concurrent_boundary.create_calls != 1
        or concurrent_boundary.probe_calls != 1
        or concurrent_boundary.verify_calls != 0
    ):
        raise FixtureFailure("claim-race-concurrent")

    partial_boundary = DeterministicClaimBoundary(failure_code="PRIVATE_CHILD_EXISTS", winner=None)
    try:
        generator.create_or_observe_generation_claim(
            partial_boundary,
            object(),
            authorization,
            raw,
        )
    except generator.GenerationError as error:
        partial_rejected = (
            error.public_code == "GENERATION_CLAIM_CREATE"
            and partial_boundary.create_calls == 1
            and partial_boundary.probe_calls == 1
            and partial_boundary.verify_calls == 0
        )
    else:
        return False
    if not partial_rejected:
        return False

    durability_boundary = DeterministicClaimBoundary(
        failure_code="GENERATION_CLAIM_DIRECTORY_FSYNC",
        winner=record,
    )
    try:
        generator.create_or_observe_generation_claim(
            durability_boundary,
            object(),
            authorization,
            raw,
        )
    except generator.GenerationError as error:
        return (
            error.public_code == "GENERATION_CLAIM_CREATE"
            and durability_boundary.create_calls == 1
            and durability_boundary.probe_calls == 0
            and durability_boundary.verify_calls == 0
        )
    return False


def generation_orchestrator_trace_matrix(generator: Any) -> bool:
    """Run real build, durable-claim, O_EXCL, and recovery transitions."""

    forbidden_boundary_methods = {
        "generation_authorization",
        "probe_generation_claim",
        "build_current_pending_candidate",
        "create_or_observe_generation_claim",
        "revalidate_micro_before_claim",
        "publish_or_recover_claimed_pending",
    }
    if forbidden_boundary_methods & set(generator.ProductionGenerationBoundaryV1.__dict__):
        raise FixtureFailure("orchestrator-boundary-surface")

    challenge = "GOV01-GEN-20260821-" + "7" * 64
    fixed_now = generator.utc_now_second()
    winner_challenge = "GOV01-SA-" + fixed_now.strftime("%Y%m%d") + "-" + "e" * 64
    winner_census = generator.format_utc(fixed_now)
    winner_expiry = generator.format_utc(fixed_now + dt.timedelta(hours=1))

    def candidate_envelope(
        authorization: Mapping[str, Any],
        acquisition_challenge: str,
        census_at_utc: str,
        not_after_utc: str,
        observations: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "fixture": "production-generation-state-machine",
            "approval_challenge_id": acquisition_challenge,
            "census_at_utc": census_at_utc,
            "not_after_utc": not_after_utc,
            "generation_authorization": dict(authorization),
            "observations": dict(observations),
        }

    def record_for_raw(
        authorization: Mapping[str, Any],
        raw: bytes,
        acquisition_challenge: str,
        census_at_utc: str,
        not_after_utc: str,
    ) -> Dict[str, Any]:
        return {
            "profile": "gov01-static-envelope-generation-claim-v1",
            "generation_authorization_challenge_id": authorization["approval_challenge_id"],
            "generation_authorization_envelope_raw_sha256": authorization["raw_envelope_sha256"],
            "generation_authorization_receipt_digest": authorization["receipt_digest"],
            "generation_authorization_parent_commit_oid": authorization["authorization_parent_commit_oid"],
            "generation_authorization_parent_tree_oid": authorization["authorization_parent_tree_oid"],
            "generation_authorization_commit_oid": authorization["authorization_commit_oid"],
            "generation_authorization_tree_oid": authorization["authorization_tree_oid"],
            "acquisition_approval_challenge_id": acquisition_challenge,
            "census_at_utc": census_at_utc,
            "not_after_utc": not_after_utc,
            "final_envelope_repo_relative_path": authorization[
                "generated_acquisition_envelope_repo_relative_path"
            ],
            "final_envelope_raw_sha256": generator.sha256(raw),
            "final_envelope_bytes": len(raw),
            "final_envelope_receipt_digest": generator.acquisition_receipt_digest(raw),
            "state": "OUTPUT-IDENTITY-FIXED",
            "record_hmac_sha256": "9" * 64,
        }

    class ProductionScenarioExit:
        REPLAY = 41

    class ProductionScenarioContractError(Exception):
        def __init__(self, code: int, public_code: str) -> None:
            super().__init__(public_code)
            self.code = code
            self.public_code = public_code

    class ProductionScenarioExecutor:
        ContractError = ProductionScenarioContractError
        Exit = ProductionScenarioExit

        def __init__(self, boundary: Any, authorization: Mapping[str, Any]) -> None:
            self.boundary = boundary
            self.authorization = dict(authorization)
            self.stored_record: Optional[Dict[str, Any]] = None
            if boundary.existing_claim:
                self.stored_record = self.winner_record()

        def called(self, name: str) -> None:
            self.boundary.called(name)

        def stable_observations(self) -> Dict[str, Any]:
            count = self.boundary.calls.get("collect", 0)
            return {"revision": count if self.boundary.observation_drift else 1}

        def winner_raw(self) -> bytes:
            envelope = candidate_envelope(
                self.authorization,
                winner_challenge,
                winner_census,
                winner_expiry,
                {"revision": 1},
            )
            return generator.canonical_json(envelope)

        def winner_record(self) -> Dict[str, Any]:
            return record_for_raw(
                self.authorization,
                self.winner_raw(),
                winner_challenge,
                winner_census,
                winner_expiry,
            )

        def probe_generation_claim_v2(self, **_kwargs: Any) -> Optional[Dict[str, Any]]:
            self.called("claim_probe")
            count = self.boundary.calls["claim_probe"]
            if count == 1 and self.boundary.existing_claim:
                self.stored_record = self.winner_record()
                return copy.deepcopy(self.stored_record)
            if count == 2 and self.boundary.concurrent_claim:
                self.stored_record = self.winner_record()
                return copy.deepcopy(self.stored_record)
            if self.boundary.claim_create_race and self.stored_record is not None:
                return copy.deepcopy(self.stored_record)
            return None

        def collect_generation_observations_v2(self, **_kwargs: Any) -> Dict[str, Any]:
            self.called("collect")
            return self.stable_observations()

        def build_pending_envelope_v2(self, **kwargs: Any) -> Dict[str, Any]:
            self.called("build")
            return candidate_envelope(
                kwargs["generation_authorization"],
                kwargs["approval_challenge_id"],
                kwargs["census_at_utc"],
                kwargs["not_after_utc"],
                kwargs["observations"],
            )

        def canonical_json(self, value: Mapping[str, Any]) -> bytes:
            self.called("canonical")
            return generator.canonical_json(dict(value))

        def parse_json_bytes(self, value: bytes, label: str) -> Dict[str, Any]:
            self.called("parse")
            return generator.parse_json(value, label)

        def validate_manual_envelope_contract(self, _value: Mapping[str, Any]) -> None:
            self.called("manual")

        def has_forbidden_pending_envelope_value(self, _value: Mapping[str, Any]) -> bool:
            self.called("privacy")
            return False

        def create_generation_claim_v2(self, **kwargs: Any) -> Dict[str, Any]:
            self.called("claim_create")
            if self.boundary.create_failure:
                raise OSError("synthetic-durability-failure")
            raw = kwargs["final_envelope_raw"]
            value = generator.parse_json(raw, "SCENARIO_CLAIM")
            record = record_for_raw(
                self.authorization,
                raw,
                value["approval_challenge_id"],
                value["census_at_utc"],
                value["not_after_utc"],
            )
            self.stored_record = record
            if self.boundary.claim_create_race:
                raise ProductionScenarioContractError(
                    ProductionScenarioExit.REPLAY,
                    "PRIVATE_CHILD_EXISTS",
                )
            return copy.deepcopy(record)

        def verify_generation_claim_recovery_v2(self, **kwargs: Any) -> Dict[str, Any]:
            self.called("claim_verify")
            raw = kwargs["final_envelope_raw"]
            if self.stored_record is None:
                raise RuntimeError("synthetic-claim-absent")
            if (
                self.stored_record["final_envelope_raw_sha256"] != generator.sha256(raw)
                or self.stored_record["final_envelope_bytes"] != len(raw)
                or self.stored_record["final_envelope_receipt_digest"]
                != generator.acquisition_receipt_digest(raw)
            ):
                raise RuntimeError("synthetic-claim-raw-drift")
            return copy.deepcopy(self.stored_record)

    class ProductionScenarioBoundary:
        def __init__(
            self,
            repo_root: pathlib.Path,
            *,
            approval_failure: bool = False,
            existing_claim: bool = False,
            concurrent_claim: bool = False,
            orphan_output: bool = False,
            entropy: bytes = b"q" * 32,
            create_failure: bool = False,
            claim_create_race: bool = False,
            observation_drift: bool = False,
            inject_output_on_public_load: Optional[int] = None,
            fail_public_load: Optional[int] = None,
        ) -> None:
            self.repo_root = repo_root
            self.approval_failure = approval_failure
            self.existing_claim = existing_claim
            self.concurrent_claim = concurrent_claim
            self.orphan_output = orphan_output
            self.entropy = entropy
            self.create_failure = create_failure
            self.claim_create_race = claim_create_race
            self.observation_drift = observation_drift
            self.inject_output_on_public_load = inject_output_on_public_load
            self.fail_public_load = fail_public_load
            self.calls: Dict[str, int] = {}
            self.executor: Optional[ProductionScenarioExecutor] = None
            self.output_path = repo_root / pathlib.Path(generator.final_relative(challenge))
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            transition = {
                "authorization_baseline_head": "3" * 40,
                "authorization_baseline_tree": "4" * 40,
            }
            claim_contract = {
                "generation_claim_required": True,
                "generation_claim_profile": generator.GENERATION_CLAIM_PROFILE,
                "generation_claim_record_profile": generator.GENERATION_CLAIM_RECORD_PROFILE,
                "generation_claim_retention": generator.GENERATION_CLAIM_RETENTION,
            }
            micro = {
                "approval_challenge_id": challenge,
                "repository_transition": transition,
                "generation_claim_contract": claim_contract,
            }
            micro_raw = generator.canonical_json(micro)
            self.context: Dict[str, Any] = {
                "repo_root": str(repo_root),
                "micro_envelope": micro,
                "micro_raw": micro_raw,
                "micro_receipt": generator.receipt_digest(micro_raw),
                "micro_relative": generator.micro_relative(challenge),
                "generation_output_relative": generator.final_relative(challenge),
                "generation_output_preexisting": False,
                "current_head": "5" * 40,
                "current_tree": "6" * 40,
            }
            self.receipt = str(self.context["micro_receipt"])
            authorization = generator.generation_authorization(self.context)
            if existing_claim:
                raw = generator.canonical_json(
                    candidate_envelope(
                        authorization,
                        winner_challenge,
                        winner_census,
                        winner_expiry,
                        {"revision": 1},
                    )
                )
                self.output_path.write_bytes(raw)
                self.output_path.chmod(0o644)
            elif orphan_output:
                self.output_path.write_bytes(b'{"orphan":true}\n')
                self.output_path.chmod(0o644)
            self.initial_output_identity = self.output_identity()

        def output_identity(self) -> Optional[Tuple[int, int, int, int, int]]:
            try:
                metadata = self.output_path.stat()
            except FileNotFoundError:
                return None
            return (
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_size,
                metadata.st_mtime_ns,
            )

        def called(self, name: str) -> None:
            self.calls[name] = self.calls.get(name, 0) + 1

        def load_approved_generation_request(self, value_receipt: str, value_challenge: str) -> Dict[str, Any]:
            self.called("public_load")
            if self.approval_failure:
                raise generator.GenerationError(generator.Exit.CONTRACT, "SCENARIO_APPROVAL_REJECTED")
            if value_receipt != self.receipt or value_challenge != challenge:
                raise AssertionError("scenario-approval-input")
            if self.fail_public_load == self.calls["public_load"]:
                raise generator.GenerationError(generator.Exit.PREFLIGHT, "SCENARIO_PUBLIC_REVALIDATION")
            if (
                self.inject_output_on_public_load == self.calls["public_load"]
                and not self.output_path.exists()
            ):
                if self.executor is None or self.executor.stored_record is None:
                    raise AssertionError("scenario-race-without-claim")
                raw = self.executor.winner_raw()
                if self.executor.stored_record["acquisition_approval_challenge_id"] != winner_challenge:
                    value = self.executor.stored_record
                    raw = generator.canonical_json(
                        candidate_envelope(
                            self.executor.authorization,
                            value["acquisition_approval_challenge_id"],
                            value["census_at_utc"],
                            value["not_after_utc"],
                            {"revision": 1},
                        )
                    )
                self.output_path.write_bytes(raw)
                self.output_path.chmod(0o644)
            result = copy.deepcopy(self.context)
            result["generation_output_preexisting"] = self.output_path.exists()
            return result

        def load_content_addressed_executor(self, context: Mapping[str, Any]) -> Any:
            self.called("executor_load")
            self.executor = ProductionScenarioExecutor(
                self,
                generator.generation_authorization(context),
            )
            return self.executor

        def derive_generation_runtime_args(
            self,
            _executor: Any,
            _context: Mapping[str, Any],
            _authorization: Mapping[str, Any],
        ) -> object:
            self.called("private_derive")
            return object()

        def now_second(self) -> dt.datetime:
            self.called("clock")
            return fixed_now

        def random_bytes(self, length: int) -> bytes:
            self.called("random")
            if length != 32:
                raise AssertionError("scenario-entropy-length")
            return self.entropy

    def event_names(trace: Sequence[Mapping[str, str]]) -> List[str]:
        names: List[str] = []
        for entry in trace:
            if set(entry) != {"event", "phase"}:
                raise FixtureFailure("orchestrator-trace-fields")
            if not all(isinstance(value, str) and value and "/" not in value and "\\" not in value for value in entry.values()):
                raise FixtureFailure("orchestrator-trace-public")
            names.append(entry["event"])
        return names

    def execute(**scenario: Any) -> Tuple[Any, List[Dict[str, str]], ProductionScenarioBoundary]:
        temporary = tempfile.TemporaryDirectory(prefix="gov01-generation-state-")
        root = pathlib.Path(temporary.name)
        boundary = ProductionScenarioBoundary(root, **scenario)
        trace: List[Dict[str, str]] = []
        try:
            result: Any = generator.generate_with_boundary_v1(
                boundary.receipt,
                challenge,
                boundary=boundary,
                trace=trace,
            )
        except generator.GenerationError as error:
            result = error.public_code
        boundary._temporary = temporary
        event_names(trace)
        return result, trace, boundary

    rejected_result, rejected_trace, rejected = execute(approval_failure=True)
    if (
        rejected_result != "SCENARIO_APPROVAL_REJECTED"
        or event_names(rejected_trace) != ["PUBLIC_APPROVAL_LOAD"]
        or any(rejected.calls.get(name, 0) for name in ("private_derive", "random", "collect", "claim_create"))
    ):
        raise FixtureFailure("orchestrator-receipt-first")

    existing_result, existing_trace, existing = execute(existing_claim=True)
    if (
        existing_result.get("state") != "ACQUISITION-ENVELOPE-CANDIDATE-REQUIRES-EXTERNAL-DRAFT-VALIDATION"
        or existing.calls.get("random", 0) != 0
        or existing.calls.get("claim_create", 0) != 0
        or existing.output_identity() != existing.initial_output_identity
        or "EXISTING_OUTPUT_RECOVERY_VERIFIED" not in event_names(existing_trace)
        or "FINAL_CREATE_ATTEMPT" in event_names(existing_trace)
    ):
        raise FixtureFailure("orchestrator-existing")

    orphan_result, _orphan_trace, orphan = execute(orphan_output=True)
    if (
        orphan_result != "GENERATION_OUTPUT_WITHOUT_CLAIM"
        or any(orphan.calls.get(name, 0) for name in ("clock", "random", "collect", "claim_create"))
        or orphan.output_identity() != orphan.initial_output_identity
    ):
        raise FixtureFailure("orchestrator-orphan-output")

    fresh_result, fresh_trace, fresh = execute()
    fresh_events = event_names(fresh_trace)
    if (
        fresh_result.get("state") != "ACQUISITION-ENVELOPE-CANDIDATE-REQUIRES-EXTERNAL-DRAFT-VALIDATION"
        or fresh.calls.get("random") != 1
        or fresh.calls.get("claim_create") != 1
        or fresh.calls.get("collect", 0) < 5
        or fresh.output_identity() is None
        or not {
            "GENERATION_CLAIM_CREATE_DURABLE",
            "FINAL_CREATE_ATTEMPT",
            "FINAL_CREATE_DURABLE",
            "FINAL_CREATE_REOPEN_VERIFIED",
            "POSTWRITE_PUBLIC_REVALIDATE_COMPLETE",
            "EXISTING_OUTPUT_RECOVERY_VERIFIED",
        }.issubset(set(fresh_events))
    ):
        raise FixtureFailure("orchestrator-fresh")

    concurrent_result, concurrent_trace, concurrent = execute(concurrent_claim=True)
    if (
        concurrent_result.get("approval_challenge_id") != winner_challenge
        or concurrent.calls.get("random") != 1
        or concurrent.calls.get("claim_create", 0) != 0
        or "CONCURRENT_WINNER_RECOVERY_DISPATCH" not in event_names(concurrent_trace)
    ):
        raise FixtureFailure("orchestrator-concurrent")

    race_result, race_trace, race = execute(claim_create_race=True)
    if not isinstance(race_result, dict):
        raise FixtureFailure("orchestrator-claim-race-result")
    if (
        race_result.get("state") != "ACQUISITION-ENVELOPE-CANDIDATE-REQUIRES-EXTERNAL-DRAFT-VALIDATION"
        or race.calls.get("claim_create") != 1
        or race.calls.get("claim_probe") != 3
        or "GENERATION_CLAIM_CONCURRENT_WINNER" not in event_names(race_trace)
    ):
        raise FixtureFailure("orchestrator-claim-race")

    lost_result, lost_trace, lost = execute(inject_output_on_public_load=6)
    if not isinstance(lost_result, dict):
        raise FixtureFailure("orchestrator-output-race-result")
    if (
        lost_result.get("state") != "ACQUISITION-ENVELOPE-CANDIDATE-REQUIRES-EXTERNAL-DRAFT-VALIDATION"
        or "FINAL_CREATE_LOST_RACE" not in event_names(lost_trace)
        or lost.calls.get("claim_create") != 1
    ):
        raise FixtureFailure("orchestrator-output-race")

    bad_entropy_result, _bad_entropy_trace, bad_entropy = execute(entropy=b"short")
    if (
        bad_entropy_result != "ACQUISITION_ENTROPY"
        or bad_entropy.calls.get("random") != 1
        or any(bad_entropy.calls.get(name, 0) for name in ("collect", "claim_create"))
        or bad_entropy.output_identity() is not None
    ):
        raise FixtureFailure("orchestrator-entropy")

    durability_result, durability_trace, durability = execute(create_failure=True)
    if (
        durability_result != "GENERATION_CLAIM_CREATE"
        or durability.calls.get("claim_create") != 1
        or "FINAL_CREATE_ATTEMPT" in event_names(durability_trace)
        or durability.output_identity() is not None
    ):
        raise FixtureFailure("orchestrator-claim-durability")

    drift_result, _drift_trace, drift = execute(observation_drift=True)
    if (
        drift_result != "GENERATION_PRIVATE_CONTEXT_DRIFT"
        or drift.calls.get("claim_create", 0) != 0
        or drift.output_identity() is not None
    ):
        raise FixtureFailure("orchestrator-private-drift")

    postwrite_result, postwrite_trace, postwrite = execute(fail_public_load=7)
    if (
        postwrite_result != "SCENARIO_PUBLIC_REVALIDATION"
        or postwrite.output_identity() is None
        or "FINAL_CREATE_DURABLE" not in event_names(postwrite_trace)
        or "EXISTING_OUTPUT_RECOVERY_VERIFIED" in event_names(postwrite_trace)
    ):
        raise FixtureFailure("orchestrator-postwrite-retention")
    return True


def production_existing_recovery_matrix(generator: Any) -> bool:
    """Run the real recovery function against a retained synthetic output."""

    authorization, record = synthetic_claim_projection(generator)
    now = generator.utc_now_second()
    census = now - dt.timedelta(minutes=1)
    expiry = census + dt.timedelta(hours=24)
    acquisition_challenge = "GOV01-SA-" + census.strftime("%Y%m%d") + "-" + "d" * 64
    envelope = {
        "fixture": "pending",
        "approval_challenge_id": acquisition_challenge,
        "generation_authorization": dict(authorization),
    }
    raw = generator.canonical_json(envelope)
    record.update(
        {
            "acquisition_approval_challenge_id": acquisition_challenge,
            "census_at_utc": generator.format_utc(census),
            "not_after_utc": generator.format_utc(expiry),
            "final_envelope_raw_sha256": generator.sha256(raw),
            "final_envelope_bytes": len(raw),
            "final_envelope_receipt_digest": generator.acquisition_receipt_digest(raw),
        }
    )

    class DeterministicRecoveryExecutor:
        def __init__(self, built_envelope: Mapping[str, Any]) -> None:
            self.built_envelope = dict(built_envelope)
            self.calls: Dict[str, int] = {}

        def called(self, name: str) -> None:
            self.calls[name] = self.calls.get(name, 0) + 1

        def parse_json_bytes(self, value: bytes, label: str) -> Dict[str, Any]:
            self.called("parse")
            return generator.parse_json(value, label)

        def validate_manual_envelope_contract(self, _value: Mapping[str, Any]) -> None:
            self.called("manual")

        def has_forbidden_pending_envelope_value(self, _value: Mapping[str, Any]) -> bool:
            self.called("privacy")
            return False

        def canonical_json(self, value: Mapping[str, Any]) -> bytes:
            self.called("canonical")
            return generator.canonical_json(dict(value))

        def verify_generation_claim_recovery_v2(self, **_arguments: Any) -> Dict[str, Any]:
            self.called("claim_verify")
            return dict(record)

        def collect_generation_observations_v2(self, **_arguments: Any) -> Dict[str, Any]:
            self.called("collect")
            return {"fixture": "stable-observation"}

        def build_pending_envelope_v2(self, **_arguments: Any) -> Dict[str, Any]:
            self.called("build")
            return dict(self.built_envelope)

    class RecoveryPublicBoundary:
        def __init__(self, stable_context: Mapping[str, Any], fail_on_call: Optional[int] = None) -> None:
            self.stable_context = dict(stable_context)
            self.fail_on_call = fail_on_call
            self.calls = 0

        def load_approved_generation_request(self, _receipt: str, _challenge: str) -> Dict[str, Any]:
            self.calls += 1
            if self.fail_on_call == self.calls:
                raise generator.GenerationError(
                    generator.Exit.PREFLIGHT,
                    "SYNTHETIC_GEN_EXPIRED_OR_HEAD_DRIFT",
                )
            return dict(self.stable_context)

    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-existing-recovery-",
        dir=os.path.realpath(tempfile.gettempdir()),
    ) as temporary:
        repo_root = pathlib.Path(temporary)
        relative = authorization["generated_acquisition_envelope_repo_relative_path"]
        output = repo_root / relative
        output.parent.mkdir(parents=True, mode=0o700)
        output.write_bytes(raw)
        os.chmod(output, 0o644)
        before = output.stat()
        context = {
            "repo_root": str(repo_root),
            "generation_output_relative": relative,
            "generation_output_preexisting": True,
        }
        executor = DeterministicRecoveryExecutor(envelope)
        public_boundary = RecoveryPublicBoundary(context)
        result = generator.recover_existing_pending(
            executor,
            context,
            authorization,
            object(),
            record,
            boundary=public_boundary,
            expected_receipt="a" * 64,
            expected_challenge=authorization["approval_challenge_id"],
        )
        after = output.stat()
        if (
            result.get("raw_envelope_receipt_digest") != generator.acquisition_receipt_digest(raw)
            or output.read_bytes() != raw
            or (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            != (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            or executor.calls.get("parse") != 1
            or executor.calls.get("collect") != 1
            or executor.calls.get("build") != 1
            or executor.calls.get("claim_verify") != 2
            or public_boundary.calls != 2
        ):
            return False

        drifted = DeterministicRecoveryExecutor(
            {
                "fixture": "drifted",
                "approval_challenge_id": acquisition_challenge,
                "generation_authorization": dict(authorization),
            }
        )
        try:
            generator.recover_existing_pending(
                drifted,
                context,
                authorization,
                object(),
                record,
                boundary=RecoveryPublicBoundary(context),
                expected_receipt="a" * 64,
                expected_challenge=authorization["approval_challenge_id"],
            )
        except generator.GenerationError as error:
            if error.public_code != "EXISTING_PENDING_DRIFT":
                return False
        else:
            return False
        expiring_boundary = RecoveryPublicBoundary(context, fail_on_call=2)
        try:
            generator.recover_existing_pending(
                DeterministicRecoveryExecutor(envelope),
                context,
                authorization,
                object(),
                record,
                boundary=expiring_boundary,
                expected_receipt="a" * 64,
                expected_challenge=authorization["approval_challenge_id"],
            )
        except generator.GenerationError as error:
            if error.public_code != "SYNTHETIC_GEN_EXPIRED_OR_HEAD_DRIFT":
                return False
        else:
            return False
        final = output.stat()
        return (
            output.read_bytes() == raw
            and (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            == (final.st_dev, final.st_ino, final.st_mode, final.st_size, final.st_mtime_ns, final.st_ctime_ns)
        )


def exclusive_write_matrix(generator: Any) -> bool:
    with tempfile.TemporaryDirectory(prefix="gov01-generation-fixture-") as temporary:
        root = pathlib.Path(temporary)
        parent = root / "evidence"
        parent.mkdir(mode=0o700)
        relative = "evidence/result.json"
        raw = b'{"state":"fixture"}\n'
        blocked_relative = "evidence/blocked.json"
        callback_count = 0

        def block_before_create() -> None:
            nonlocal callback_count
            callback_count += 1
            generator.fail(generator.Exit.PREFLIGHT, "FIXTURE_DEADLINE")

        try:
            generator.try_write_exclusive_public_file(
                str(root),
                blocked_relative,
                raw,
                before_create=block_before_create,
            )
        except generator.GenerationError:
            pass
        else:
            return False
        if callback_count != 1 or (root / blocked_relative).exists():
            return False
        escaped_parent = root / "escaped-evidence"

        def move_parent_before_create() -> None:
            parent.rename(escaped_parent)

        try:
            generator.try_write_exclusive_public_file(
                str(root),
                relative,
                raw,
                before_create=move_parent_before_create,
            )
        except generator.GenerationError as error:
            if error.public_code != "OUTPUT_PARENT":
                return False
        else:
            return False
        if (escaped_parent / "result.json").exists() or (root / relative).exists():
            return False
        escaped_parent.rename(parent)
        companion_relative = "evidence/final.json"
        events: List[str] = []
        original_open = generator.os.open

        def record_exclusive_open(path_value: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if path_value == "result.json" and flags & os.O_EXCL:
                events.append("create")
            return original_open(path_value, flags, *args, **kwargs)

        def before_public_create() -> None:
            events.append("before")
            require(not (root / relative).exists(), "exclusive-before-create-absent")
            require(not (root / companion_relative).exists(), "exclusive-before-companion-absent")

        def after_public_create() -> None:
            events.append("after")
            require((root / relative).read_bytes() == raw, "exclusive-after-create-bytes")
            require(not (root / companion_relative).exists(), "exclusive-after-companion-absent")

        generator.os.open = record_exclusive_open
        try:
            generator.write_exclusive_public_file(
                str(root),
                relative,
                raw,
                before_create=before_public_create,
                after_create=after_public_create,
                companion_absent_relative=companion_relative,
            )
        finally:
            generator.os.open = original_open
        if events != ["before", "create", "after"]:
            return False
        path = root / relative
        if path.read_bytes() != raw or (path.stat().st_mode & 0o777) != 0o644:
            return False

        companion = root / companion_relative
        companion.write_bytes(b"preexisting final output\n")
        blocked_target = "evidence/companion-blocked.json"
        try:
            generator.write_exclusive_public_file(
                str(root),
                blocked_target,
                raw,
                companion_absent_relative=companion_relative,
            )
        except generator.GenerationError as error:
            if error.public_code != "GENERATION_OUTPUT_NOT_ABSENT":
                return False
        else:
            return False
        if (root / blocked_target).exists():
            return False
        companion.unlink()

        retained_target = "evidence/post-checkpoint-retained.json"

        def fail_after_create() -> None:
            generator.fail(generator.Exit.PREFLIGHT, "FIXTURE_POST_SOURCE_DRIFT")

        try:
            generator.write_exclusive_public_file(
                str(root),
                retained_target,
                raw,
                after_create=fail_after_create,
                companion_absent_relative=companion_relative,
            )
        except generator.GenerationError as error:
            if error.public_code != "FIXTURE_POST_SOURCE_DRIFT":
                return False
        else:
            return False
        if (root / retained_target).read_bytes() != raw:
            return False
        try:
            generator.write_exclusive_public_file(str(root), relative, b"changed\n")
        except generator.GenerationError:
            return path.read_bytes() == raw
    return False


def git_control_matrix(generator: Any) -> bool:
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-git-control-",
        dir=os.path.realpath(tempfile.gettempdir()),
    ) as temporary:
        root = pathlib.Path(temporary)
        git_dir = root / ".git"
        objects = git_dir / "objects"
        objects.mkdir(parents=True, mode=0o700)
        config = git_dir / "config"
        config.write_bytes(b"[core]\n\trepositoryformatversion = 0\n")
        os.chmod(config, 0o600)
        expected = {
            "marker_kind": "directory",
            "common_directory_relation": "git-directory-is-common-directory",
            "include_controls_absent": True,
            "alternate_object_controls_absent": True,
        }
        if generator.git_control_preflight(str(root)) != expected:
            return False
        config.write_bytes(b"[include]\n\tpath = external\n")
        try:
            generator.git_control_preflight(str(root))
        except generator.GenerationError:
            pass
        else:
            return False
        config.write_bytes(b"[core]\n\trepositoryformatversion = 0\n")
        info = objects / "info"
        info.mkdir(mode=0o700)
        alternates = info / "alternates"
        alternates.write_bytes(b"external\n")
        os.chmod(alternates, 0o600)
        try:
            generator.git_control_preflight(str(root))
        except generator.GenerationError:
            pass
        else:
            return False

        # A gitfile must never redirect this public generator into a
        # Vault-family or Obsidian control directory.  The rejection happens
        # lexically, before any stat/open of the declared target.
        for index, private_component in enumerate(("Canvas-Vault-fixture", ".obsidian")):
            linked_root = root / ("linked-%d" % index)
            linked_root.mkdir(mode=0o700)
            declared = root / private_component / "gitdir"
            marker = linked_root / ".git"
            marker.write_bytes(("gitdir: " + str(declared) + "\n").encode("utf-8"))
            os.chmod(marker, 0o600)
            try:
                generator.git_control_preflight(str(linked_root))
            except generator.GenerationError as error:
                if error.public_code != "GIT_DIRECTORY_PRIVATE_COMPONENT":
                    return False
            else:
                return False

        # The only accepted linked layout is the project's exact
        # <main>/.claude/worktrees/<id> <-> <main>/.git/worktrees/<id>
        # relation, including Git's reverse gitdir pointer.
        main_root = root / "project"
        main_root.mkdir(mode=0o700)
        tracked = main_root / "tracked.txt"
        tracked.write_bytes(b"tracked\n")
        run_synthetic_git(main_root, ["init", "-q"])
        run_synthetic_git(main_root, ["add", "tracked.txt"])
        add_synthetic_opaque_gitlink(main_root)
        run_synthetic_git(main_root, ["commit", "-q", "-m", "fixture-linked-baseline"])
        linked_root = main_root / ".claude/worktrees/fixture-linked"
        linked_root.parent.mkdir(parents=True, mode=0o700)
        run_synthetic_git(
            main_root,
            ["worktree", "add", "-q", "-b", "fixture-linked", str(linked_root)],
        )
        linked_observation = generator.git_control_preflight(str(linked_root))
        if linked_observation.get("marker_kind") != "gitfile" or linked_observation.get(
            "common_directory_relation"
        ) != "git-directory-contained-under-common-worktrees":
            return False
        marker_raw = (linked_root / ".git").read_text(encoding="utf-8")
        linked_git_dir = pathlib.Path(marker_raw[len("gitdir: ") :].strip())

        unrelated = main_root / "unrelated-linked"
        unrelated.mkdir(mode=0o700)
        (unrelated / ".git").write_text("gitdir: " + str(linked_git_dir) + "\n", encoding="utf-8")
        try:
            generator.git_control_preflight(str(unrelated))
        except generator.GenerationError as error:
            if error.public_code != "GIT_DIRECTORY_ADMIN_ANCHOR":
                return False
        else:
            return False

        reverse = linked_git_dir / "gitdir"
        original_reverse = reverse.read_bytes()
        reverse.write_bytes((str(unrelated / ".git") + "\n").encode("utf-8"))
        try:
            generator.git_control_preflight(str(linked_root))
        except generator.GenerationError as error:
            if error.public_code != "GIT_WORKTREE_GITDIR_BINDING":
                return False
        else:
            return False
        reverse.write_bytes(original_reverse)
        return True


def git_adapter_capture_cleanup_matrix(generator: Any) -> bool:
    """Exercise frozen-ref use, exact cleanup and loader exception cleanup."""

    git_binary, developer_root = generator.resolve_git()
    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix="gov01-generation-adapter-", dir=temp_parent) as temporary:
        root = pathlib.Path(temporary) / "repo"
        root.mkdir(mode=0o700)
        tracked = root / "tracked.txt"
        tracked.write_bytes(b"tracked\n")
        run_synthetic_git(root, ["init", "-q"])
        run_synthetic_git(root, ["add", "tracked.txt"])
        add_synthetic_opaque_gitlink(root)
        run_synthetic_git(root, ["commit", "-q", "-m", "fixture-adapter-baseline"])

        # A live ref change after capture must not change the bytes copied from
        # that capture.  Revalidation is a separate operation and will reject
        # the live drift; the adapter never performs a second ref read.
        capture = generator.capture_git_source(str(root))
        _head_oid, head_ref = generator.captured_head_oid_and_ref(capture)
        relative_ref = head_ref[len("refs/") :]
        live_ref = pathlib.Path(capture["common_dir"]) / "refs" / relative_ref
        original_ref = live_ref.read_bytes()
        copied_root = pathlib.Path(temporary) / "copied"
        copied_root.mkdir(mode=0o700)
        live_ref.write_bytes((b"0" * len(original_ref.rstrip(b"\n"))) + b"\n")
        try:
            generator.copy_captured_refs(capture, str(copied_root))
            copied_ref = copied_root.joinpath(*head_ref.split("/"))
            if copied_ref.read_bytes() != original_ref:
                return False
        finally:
            live_ref.write_bytes(original_ref)

        _git_control, boundary = generator.create_git_metadata_adapter(
            str(root),
            git_binary,
            developer_root,
        )
        adapter_path = pathlib.Path(boundary.adapter_root)
        generator.cleanup_git_metadata_adapter(boundary)
        if adapter_path.exists() or not boundary.closed:
            return False
        if any(candidate is boundary for candidate in generator._OPEN_GIT_ADAPTERS):
            return False

        # Rename the root and place a sentinel replacement exactly when the
        # production builder performs its first fd-relative mkdir.  All
        # adapter writes must follow the already-open directory descriptor;
        # the replacement must remain byte-for-byte untouched and authorized-
        # pathname cleanup must fail closed instead of claiming quiescence.
        original_mkdir = generator.os.mkdir
        build_swap: Dict[str, Any] = {"injected": False}

        def swapping_mkdir(path: Any, *args: Any, **kwargs: Any) -> None:
            directory_fd = kwargs.get("dir_fd")
            if not build_swap["injected"] and path == "git" and isinstance(directory_fd, int):
                original_root = pathlib.Path(
                    generator.identity_bound_directory_path(directory_fd, "FIXTURE_BUILD_SWAP")
                )
                metadata = os.stat(original_root, follow_symlinks=False)
                retained_root = original_root.with_name(original_root.name + ".build-retained")
                replacement_root = original_root
                sentinel_raw = b"replacement-must-remain-unchanged\n"
                original_root.rename(retained_root)
                original_mkdir(str(replacement_root), 0o700)
                sentinel = replacement_root / "sentinel"
                sentinel.write_bytes(sentinel_raw)
                os.chmod(sentinel, 0o600)
                build_swap.update(
                    {
                        "injected": True,
                        "original": original_root,
                        "retained": retained_root,
                        "replacement": replacement_root,
                        "sentinel_raw": sentinel_raw,
                        "device": metadata.st_dev,
                        "inode": metadata.st_ino,
                    }
                )
            original_mkdir(path, *args, **kwargs)

        generator.os.mkdir = swapping_mkdir
        try:
            try:
                generator.create_git_metadata_adapter(
                    str(root),
                    git_binary,
                    developer_root,
                )
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_CLEANUP_ROOT_DRIFT":
                    return False
            else:
                return False
        finally:
            generator.os.mkdir = original_mkdir
        if not build_swap.get("injected"):
            return False
        build_staged = [
            candidate
            for candidate in generator._OPEN_GIT_ADAPTERS
            if isinstance(candidate, generator.StagedGitAdapter)
            and candidate.adapter_root == str(build_swap["original"])
        ]
        if (
            len(build_staged) != 1
            or build_staged[0].adapter_root_fd < 0
            or build_staged[0].adapter_git_fd < 0
            or build_staged[0].closed
        ):
            return False
        try:
            generator.require_git_adapter_quiescent("FIXTURE_BUILD_STAGED")
        except generator.GenerationError as error:
            if error.public_code != "FIXTURE_BUILD_STAGED_GIT_ADAPTER_RESIDUE":
                return False
        else:
            return False
        build_replacement = build_swap["replacement"]
        build_retained = build_swap["retained"]
        if (
            sorted(entry.name for entry in build_replacement.iterdir()) != ["sentinel"]
            or (build_replacement / "sentinel").read_bytes() != build_swap["sentinel_raw"]
            or not (build_retained / "git").is_dir()
            or not (build_retained / "git" / "objects" / "pack").is_dir()
        ):
            return False
        (build_replacement / "sentinel").unlink()
        build_replacement.rmdir()
        build_retained.rename(build_swap["original"])
        generator.cleanup_staged_git_adapter(build_staged[0])
        try:
            generator.require_git_adapter_quiescent("FIXTURE_BUILD_SWAP")
        except generator.GenerationError:
            return False

        # Rename the already-open Git directory away and replace only its
        # pathname at the first fd-relative metadata write.  Parent writes and
        # every bootstrap/import child must remain on the pinned original Git
        # inode.  Exact cleanup must reject the replacement without mutating
        # it or falsely claiming quiescence.
        original_write_at = generator.write_adapter_file_at
        git_swap: Dict[str, Any] = {"injected": False}

        def swapping_write_at(
            directory_fd: int,
            name: str,
            raw: bytes,
            label: str,
        ) -> None:
            if not git_swap["injected"] and name == "config" and label == "GIT_ADAPTER_CONFIG":
                original_git = pathlib.Path(
                    generator.identity_bound_directory_path(directory_fd, "FIXTURE_GIT_SWAP")
                )
                original_root = original_git.parent
                retained_git = original_root.with_name(original_root.name + ".git-retained")
                root_metadata = os.stat(original_root, follow_symlinks=False)
                git_metadata = os.fstat(directory_fd)
                sentinel_raw = b"git-replacement-must-remain-unchanged\n"
                original_git.rename(retained_git)
                original_git.mkdir(mode=0o700)
                sentinel = original_git / "sentinel"
                sentinel.write_bytes(sentinel_raw)
                os.chmod(sentinel, 0o600)
                git_swap.update(
                    {
                        "injected": True,
                        "root": original_root,
                        "original_git": original_git,
                        "retained_git": retained_git,
                        "sentinel_raw": sentinel_raw,
                        "root_device": root_metadata.st_dev,
                        "root_inode": root_metadata.st_ino,
                        "git_device": git_metadata.st_dev,
                        "git_inode": git_metadata.st_ino,
                    }
                )
            original_write_at(directory_fd, name, raw, label)

        generator.write_adapter_file_at = swapping_write_at
        try:
            try:
                generator.create_git_metadata_adapter(
                    str(root),
                    git_binary,
                    developer_root,
                )
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_CLEANUP_GIT_DRIFT":
                    return False
            else:
                return False
        finally:
            generator.write_adapter_file_at = original_write_at
        if not git_swap.get("injected"):
            return False
        git_staged = [
            candidate
            for candidate in generator._OPEN_GIT_ADAPTERS
            if isinstance(candidate, generator.StagedGitAdapter)
            and candidate.adapter_root == str(git_swap["root"])
        ]
        if (
            len(git_staged) != 1
            or git_staged[0].adapter_root_fd < 0
            or git_staged[0].adapter_git_fd < 0
            or git_staged[0].closed
        ):
            return False
        try:
            generator.require_git_adapter_quiescent("FIXTURE_GIT_STAGED")
        except generator.GenerationError as error:
            if error.public_code != "FIXTURE_GIT_STAGED_GIT_ADAPTER_RESIDUE":
                return False
        else:
            return False
        git_replacement = git_swap["original_git"]
        git_retained = git_swap["retained_git"]
        git_root = git_swap["root"]
        if (
            not git_root.is_dir()
            or sorted(entry.name for entry in git_replacement.iterdir()) != ["sentinel"]
            or (git_replacement / "sentinel").read_bytes() != git_swap["sentinel_raw"]
            or not (git_retained / "config").is_file()
            or (git_retained / "objects").exists()
        ):
            return False
        os.chmod(git_root, 0o700)
        (git_replacement / "sentinel").unlink()
        git_replacement.rmdir()
        os.chmod(git_retained, 0o700)
        git_retained.rename(git_replacement)
        generator.cleanup_staged_git_adapter(git_staged[0])
        try:
            generator.require_git_adapter_quiescent("FIXTURE_GIT_SWAP")
        except generator.GenerationError:
            return False

        # Pure rename-away without a replacement must not be mistaken for
        # successful cleanup.  Scope exit must propagate the failure, retain
        # the open registry entry, and make quiescence fail until the fixture
        # restores the exact inode at its authorized pathname.
        renamed_boundary: Any = None
        renamed_original: Optional[pathlib.Path] = None
        renamed_retained: Optional[pathlib.Path] = None
        retained_fingerprint = ""
        try:
            try:
                with generator.GitAdapterScope():
                    _control, renamed_boundary = generator.create_git_metadata_adapter(
                        str(root),
                        git_binary,
                        developer_root,
                    )
                    renamed_original = pathlib.Path(renamed_boundary.adapter_root)
                    renamed_retained = renamed_original.with_name(renamed_original.name + ".renamed-away")
                    renamed_original.rename(renamed_retained)
                    retained_fingerprint = generator.adapter_tree_fingerprint(str(renamed_retained))
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_CLEANUP_ROOT_MISSING":
                    return False
            else:
                return False
            if (
                renamed_boundary is None
                or renamed_retained is None
                or renamed_original is None
                or renamed_boundary.closed
                or not renamed_retained.is_dir()
                or generator.adapter_tree_fingerprint(str(renamed_retained)) != retained_fingerprint
                or not any(candidate is renamed_boundary for candidate in generator._OPEN_GIT_ADAPTERS)
            ):
                return False
            try:
                generator.require_git_adapter_quiescent("FIXTURE_RENAME_AWAY")
            except generator.GenerationError as error:
                if error.public_code != "FIXTURE_RENAME_AWAY_GIT_ADAPTER_RESIDUE":
                    return False
            else:
                return False
        finally:
            if renamed_retained is not None and renamed_original is not None and renamed_retained.exists():
                renamed_retained.rename(renamed_original)
            if renamed_boundary is not None and not renamed_boundary.closed:
                generator.cleanup_git_metadata_adapter(renamed_boundary)

        # Replacing the pathname must never make cleanup silently succeed or
        # delete the replacement.  Restore the original inode only to perform
        # the fixture's own exact cleanup afterward.
        _git_control, swapped = generator.create_git_metadata_adapter(
            str(root),
            git_binary,
            developer_root,
        )
        original_path = pathlib.Path(swapped.adapter_root)
        retained_path = original_path.with_name(original_path.name + ".retained")
        replacement_path = original_path
        original_path.rename(retained_path)
        replacement_path.mkdir(mode=0o700)
        try:
            try:
                generator.cleanup_git_metadata_adapter(swapped)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_CLEANUP_ROOT_DRIFT":
                    return False
            else:
                return False
            if not replacement_path.is_dir() or not retained_path.is_dir() or swapped.closed:
                return False
        finally:
            replacement_path.rmdir()
            retained_path.rename(original_path)
            generator.cleanup_git_metadata_adapter(swapped)

        # Inject the narrower rename race after final lstat but inside rmdir.
        # The open expected-inode descriptor must make false success
        # impossible even though the racing replacement itself is empty.
        _git_control, final_race = generator.create_git_metadata_adapter(
            str(root),
            git_binary,
            developer_root,
        )
        final_path = pathlib.Path(final_race.adapter_root)
        final_retained = final_path.with_name(final_path.name + ".final-retained")
        original_rmdir = generator.os.rmdir
        injected = {"value": False}

        def racing_rmdir(path: Any, *args: Any, **kwargs: Any) -> None:
            if (
                not injected["value"]
                and path == final_path.name
                and kwargs.get("dir_fd") is not None
            ):
                final_path.rename(final_retained)
                final_path.mkdir(mode=0o700)
                injected["value"] = True
            original_rmdir(path, *args, **kwargs)

        generator.os.rmdir = racing_rmdir
        try:
            try:
                generator.cleanup_git_metadata_adapter(final_race)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_CLEANUP_EXPECTED_INODE_RETAINED":
                    return False
            else:
                return False
            if not injected["value"] or final_race.closed or not final_retained.is_dir():
                return False
        finally:
            generator.os.rmdir = original_rmdir
            if final_path.exists():
                final_path.rmdir()
            if final_retained.exists():
                final_retained.rename(final_path)
            generator.cleanup_git_metadata_adapter(final_race)

        # The same production scope used by approved-request loading must close
        # every real adapter opened inside it before an exception escapes.
        leaked_paths: List[pathlib.Path] = []
        try:
            with generator.GitAdapterScope():
                _control, opened = generator.create_git_metadata_adapter(
                    str(root),
                    git_binary,
                    developer_root,
                )
                leaked_paths.append(pathlib.Path(opened.adapter_root))
                generator.fail(generator.Exit.PREFLIGHT, "FIXTURE_SCOPE_FAILURE")
        except generator.GenerationError as error:
            if error.public_code != "FIXTURE_SCOPE_FAILURE":
                return False
        else:
            return False
        if not leaked_paths or any(path.exists() for path in leaked_paths):
            return False

        # Hold one real scope and adapter in the main thread while a second
        # thread reaches the same start barrier.  The contender must be
        # rejected at __enter__ without executing its body or touching the
        # owner's registered adapter; owner exit then performs exact cleanup.
        start_barrier = threading.Barrier(2)
        finish_barrier = threading.Barrier(2)
        contender: Dict[str, Any] = {"body_entered": False, "rejected": False}
        contender_errors: List[BaseException] = []
        concurrent_boundary: Any = None
        concurrent_path: Optional[pathlib.Path] = None

        def contend_for_scope() -> None:
            try:
                start_barrier.wait(timeout=10)
                try:
                    with generator.GitAdapterScope():
                        contender["body_entered"] = True
                except generator.GenerationError as error:
                    contender["rejected"] = error.public_code == "GIT_ADAPTER_SCOPE_CONCURRENT"
                contender["owner_intact"] = (
                    concurrent_boundary is not None
                    and concurrent_path is not None
                    and not concurrent_boundary.closed
                    and concurrent_path.is_dir()
                    and any(
                        candidate is concurrent_boundary
                        for candidate in generator._OPEN_GIT_ADAPTERS
                    )
                )
                finish_barrier.wait(timeout=10)
            except BaseException as error:
                contender_errors.append(error)

        with generator.GitAdapterScope():
            _control, concurrent_boundary = generator.create_git_metadata_adapter(
                str(root),
                git_binary,
                developer_root,
            )
            concurrent_path = pathlib.Path(concurrent_boundary.adapter_root)
            contender_thread = threading.Thread(target=contend_for_scope, daemon=True)
            contender_thread.start()
            start_barrier.wait(timeout=10)
            finish_barrier.wait(timeout=10)
            contender_thread.join(timeout=10)
            if (
                contender_thread.is_alive()
                or contender_errors
                or contender["body_entered"]
                or not contender["rejected"]
                or not contender.get("owner_intact")
                or concurrent_boundary.closed
                or not concurrent_path.is_dir()
            ):
                return False
        if (
            concurrent_boundary is None
            or concurrent_path is None
            or not concurrent_boundary.closed
            or concurrent_path.exists()
        ):
            return False
        try:
            generator.require_git_adapter_quiescent("FIXTURE_SCOPE_CONCURRENT")
        except generator.GenerationError:
            return False
        return True


def git_adapter_final_delete_capability_characterization(generator: Any) -> Dict[str, bool]:
    """Characterize the out-of-model same-UID final-rmdir replacement race."""

    git_binary, developer_root = generator.resolve_git()
    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-final-delete-witness-",
        dir=temp_parent,
    ) as temporary:
        root = pathlib.Path(temporary) / "repo"
        root.mkdir(mode=0o700)
        tracked = root / "tracked.txt"
        tracked.write_bytes(b"tracked\n")
        run_synthetic_git(root, ["init", "-q"])
        run_synthetic_git(root, ["add", "tracked.txt"])
        add_synthetic_opaque_gitlink(root)
        run_synthetic_git(root, ["commit", "-q", "-m", "fixture-final-delete-witness"])

        _control, boundary = generator.create_git_metadata_adapter(
            str(root),
            git_binary,
            developer_root,
        )
        final_path = pathlib.Path(boundary.adapter_root)
        retained_path = final_path.with_name(final_path.name + ".witness-retained")
        replacement_identity: Optional[Tuple[int, int]] = None
        original_rmdir = generator.os.rmdir
        injected = False

        def racing_rmdir(path: Any, *args: Any, **kwargs: Any) -> None:
            nonlocal injected, replacement_identity
            if not injected and path == final_path.name and kwargs.get("dir_fd") is not None:
                final_path.rename(retained_path)
                final_path.mkdir(mode=0o700)
                replacement_meta = final_path.stat(follow_symlinks=False)
                replacement_identity = (replacement_meta.st_dev, replacement_meta.st_ino)
                injected = True
            original_rmdir(path, *args, **kwargs)

        generator.os.rmdir = racing_rmdir
        cleanup_failed = False
        quiescence_rejected = False
        replacement_preserved = False
        try:
            try:
                generator.cleanup_git_metadata_adapter(boundary)
            except generator.GenerationError:
                cleanup_failed = True
            try:
                generator.require_git_adapter_quiescent("FIXTURE_FINAL_DELETE_REPLACEMENT")
            except generator.GenerationError as error:
                quiescence_rejected = (
                    error.public_code
                    == "FIXTURE_FINAL_DELETE_REPLACEMENT_GIT_ADAPTER_RESIDUE"
                )
            if injected and replacement_identity is not None and final_path.is_dir():
                replacement_meta = final_path.stat(follow_symlinks=False)
                replacement_preserved = (
                    (replacement_meta.st_dev, replacement_meta.st_ino)
                    == replacement_identity
                    and not any(final_path.iterdir())
                )
        finally:
            generator.os.rmdir = original_rmdir
            if final_path.exists():
                final_path.rmdir()
            if retained_path.exists():
                retained_path.rename(final_path)
            if not boundary.closed:
                generator.cleanup_git_metadata_adapter(boundary)
        boundary_declared = (
            generator.GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
            == EXPECTED_GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
            and generator.GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
            == EXPECTED_GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
            and generator.GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
            == EXPECTED_GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
        )
        supported = "outside the supported guarantee" not in (
            generator.GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
        )
        return {
            "observed_unsafe": (
                injected
                and cleanup_failed
                and quiescence_rejected
                and not replacement_preserved
            ),
            "supported": supported,
            "boundary_declared": boundary_declared,
            "replacement_preserved": replacement_preserved,
        }


def git_child_parent_namespace_denial_matrix(generator: Any) -> bool:
    """Run native syscalls after sandbox_init and require EPERM outside pack."""

    adapter_root = pathlib.Path(
        tempfile.mkdtemp(prefix="gov01-git-adapter-", dir="/private/tmp")
    )
    adapter_git = adapter_root / "git"
    pack_directory = adapter_git / "objects" / "pack"
    pack_directory.mkdir(parents=True, mode=0o700)
    create_target = adapter_root.with_name(adapter_root.name + ".child-create")
    rename_source = adapter_root.with_name(adapter_root.name + ".child-source")
    rename_target = adapter_root.with_name(adapter_root.name + ".child-renamed")
    rename_source.mkdir(mode=0o700)
    sentinel = rename_source / "sentinel"
    sentinel_raw = b"sandboxed-child-must-not-mutate-sibling\n"
    sentinel.write_bytes(sentinel_raw)
    os.chmod(sentinel, 0o600)
    source_meta = rename_source.stat(follow_symlinks=False)
    adapter_git_fd = os.open(
        adapter_git,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    python_binary = os.path.realpath(
        os.path.join(
            sys.base_prefix,
            "Resources/Python.app/Contents/MacOS/Python",
        )
    )
    python_developer_root = "/opt/homebrew"
    require(
        os.path.commonpath([python_developer_root, python_binary])
        == python_developer_root,
        "native-probe-python-binding",
    )
    require(
        os.path.isfile(python_binary) and os.access(python_binary, os.X_OK),
        "native-probe-python-executable",
    )
    probe_code = (
        "import ctypes,errno,json,os,sys\n"
        "libc=ctypes.CDLL(None,use_errno=True)\n"
        "AT_FDCWD=-2\n"
        "AT_REMOVEDIR=0x80\n"
        "def invoke(function,*arguments):\n"
        " ctypes.set_errno(0)\n"
        " result=function(*arguments)\n"
        " return result,ctypes.get_errno()\n"
        "create,source,target,positive=(value.encode() for value in sys.argv[1:5])\n"
        "mkdir_result,mkdir_errno=invoke(libc.mkdirat,AT_FDCWD,create,0o700)\n"
        "rename_result,rename_errno=invoke(libc.renameat,AT_FDCWD,source,AT_FDCWD,target)\n"
        "rmdir_result,rmdir_errno=invoke(libc.unlinkat,AT_FDCWD,source,AT_REMOVEDIR)\n"
        "fd,open_errno=invoke(libc.openat,AT_FDCWD,positive,"
        "os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
        "positive_write=False\n"
        "if fd>=0:\n"
        " positive_write=(os.write(fd,b'pack-probe\\n')==11 and os.fsync(fd) is None)\n"
        " os.close(fd)\n"
        " unlink_result,unlink_errno=invoke(libc.unlinkat,AT_FDCWD,positive,0)\n"
        " positive_write=positive_write and unlink_result==0 and unlink_errno==0\n"
        "print(json.dumps({'entered':True,'mkdirat_errno':mkdir_errno,"
        "'mkdirat_result':mkdir_result,'positive_write':positive_write,"
        "'renameat_errno':rename_errno,'renameat_result':rename_result,"
        "'rmdir_errno':rmdir_errno,'rmdir_result':rmdir_result},"
        "sort_keys=True,separators=(',',':')))\n"
    )
    try:
        raw = generator.run_process(
            [
                python_binary,
                "-I",
                "-S",
                "-B",
                "-c",
                probe_code,
                "../../" + create_target.name,
                "../../" + rename_source.name,
                "../../" + rename_target.name,
                "objects/pack/positive-write-probe",
            ],
            "FIXTURE_GIT_CHILD_PARENT_SYSCALL",
            max_bytes=4096,
            sandbox_profile=generator.git_adapter_import_sandbox_profile(
                python_binary,
                python_developer_root,
                str(adapter_git),
            ),
            inherited_directory_fd=adapter_git_fd,
        )
        result = json.loads(raw.decode("utf-8", "strict"))
        source_after = rename_source.stat(follow_symlinks=False)
        return (
            result
            == {
                "entered": True,
                "mkdirat_errno": 1,
                "mkdirat_result": -1,
                "positive_write": True,
                "renameat_errno": 1,
                "renameat_result": -1,
                "rmdir_errno": 1,
                "rmdir_result": -1,
            }
            and not create_target.exists()
            and not rename_target.exists()
            and (source_after.st_dev, source_after.st_ino)
            == (source_meta.st_dev, source_meta.st_ino)
            and sentinel.read_bytes() == sentinel_raw
            and not (pack_directory / "positive-write-probe").exists()
        )
    finally:
        os.close(adapter_git_fd)
        if create_target.exists():
            create_target.rmdir()
        if rename_target.exists() and not rename_source.exists():
            rename_target.rename(rename_source)
        if sentinel.exists():
            sentinel.unlink()
        if rename_source.exists():
            rename_source.rmdir()
        positive_probe = pack_directory / "positive-write-probe"
        if positive_probe.exists():
            positive_probe.unlink()
        pack_directory.rmdir()
        pack_directory.parent.rmdir()
        adapter_git.rmdir()
        adapter_root.rmdir()


def git_post_preflight_sandbox_matrix(
    generator: Any,
    root: pathlib.Path,
    git_binary: str,
    _boundary: Any,
) -> bool:
    """Prove Git reads only a sealed adapter and source drift fails closed."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-external-git-",
        dir=temp_parent,
    ) as external_temporary:
        external_root = pathlib.Path(external_temporary)
        included = external_root / "included.cfg"
        included.write_bytes(b"this is deliberately not valid git config\n")
        os.chmod(included, 0o600)

        # Capture a fresh, clean adapter after the approved micro commit.  Then
        # poison both live configuration and live object alternates.  The
        # adapter command must still return its frozen HEAD because neither
        # live control is on the child allowlist; parent-side revalidation must
        # nevertheless reject the retained live drift.
        isolated = generator.repository_baseline(str(root))
        isolated_boundary = isolated["git_boundary"]
        live_config = pathlib.Path(isolated_boundary.live_common_dir) / "config"
        original_config = live_config.read_bytes()
        live_info = pathlib.Path(isolated_boundary.live_common_dir) / "objects/info"
        live_info.mkdir(mode=0o700, exist_ok=True)
        alternates = live_info / "alternates"
        live_config.write_bytes(
            original_config + ("\n[include]\n\tpath = %s\n" % included).encode("utf-8")
        )
        os.chmod(live_config, 0o600)
        alternates.write_bytes((str(external_root / "missing-objects") + "\n").encode("utf-8"))
        os.chmod(alternates, 0o600)
        try:
            observed = generator.git_scalar(
                git_binary,
                str(root),
                isolated_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            )
            if observed != isolated["head"]:
                return False
            try:
                generator.revalidate_git_metadata_source(isolated_boundary)
            except generator.GenerationError as error:
                if error.public_code not in (
                    "GIT_COMMON_CONFIG_EXTERNAL_CONTROL",
                    "GIT_ALTERNATES_PRESENT",
                    "GIT_ADAPTER_SOURCE_DRIFT",
                ):
                    return False
            else:
                return False
        finally:
            if alternates.exists():
                alternates.unlink()
            live_config.write_bytes(original_config)
            os.chmod(live_config, 0o600)
            generator.cleanup_git_metadata_adapter(isolated_boundary)

        # Alternates drift alone is invisible to every sealed-adapter child,
        # but the parent source-CAS boundary must still reject it.
        alternates_drift = generator.repository_baseline(str(root))
        alternates_boundary = alternates_drift["git_boundary"]
        live_info = pathlib.Path(alternates_boundary.live_common_dir) / "objects/info"
        info_preexisting = live_info.exists()
        live_info.mkdir(mode=0o700, exist_ok=True)
        alternates = live_info / "alternates"
        alternates.write_bytes((str(external_root / "missing-objects") + "\n").encode("utf-8"))
        os.chmod(alternates, 0o600)
        try:
            if generator.git_scalar(
                git_binary,
                str(root),
                alternates_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            ) != alternates_drift["head"]:
                return False
            try:
                generator.revalidate_git_metadata_source(alternates_boundary)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ALTERNATES_PRESENT":
                    return False
            else:
                return False
        finally:
            if alternates.exists():
                alternates.unlink()
            if not info_preexisting and live_info.exists():
                live_info.rmdir()
            generator.cleanup_git_metadata_adapter(alternates_boundary)

        # A benign-looking config rewrite is not executable authority, but it
        # still invalidates the capture identity at the parent boundary.
        config_drift = generator.repository_baseline(str(root))
        config_boundary = config_drift["git_boundary"]
        live_config = pathlib.Path(config_boundary.live_common_dir) / "config"
        original_config = live_config.read_bytes()
        live_config.write_bytes(original_config + b"\n[fixture]\n\tdrift = true\n")
        os.chmod(live_config, 0o600)
        try:
            if generator.git_scalar(
                git_binary,
                str(root),
                config_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            ) != config_drift["head"]:
                return False
            try:
                generator.revalidate_git_metadata_source(config_boundary)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_SOURCE_DRIFT":
                    return False
            else:
                return False
        finally:
            live_config.write_bytes(original_config)
            os.chmod(live_config, 0o600)
            generator.cleanup_git_metadata_adapter(config_boundary)

        # The copied index remains usable after live index drift, but final
        # source revalidation must reject the attempt.
        index_drift = generator.repository_baseline(str(root))
        index_boundary = index_drift["git_boundary"]
        live_index = pathlib.Path(index_boundary.live_git_dir) / "index"
        original_index = live_index.read_bytes()
        live_index.write_bytes(original_index + b"fixture-drift")
        try:
            if generator.git_scalar(
                git_binary,
                str(root),
                index_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            ) != index_drift["head"]:
                return False
            try:
                generator.revalidate_git_metadata_source(index_boundary)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_SOURCE_DRIFT":
                    return False
            else:
                return False
        finally:
            live_index.write_bytes(original_index)
            generator.cleanup_git_metadata_adapter(index_boundary)

        # Loose HEAD-ref drift is equally isolated from the child and equally
        # fatal at the parent capture boundary.
        ref_drift = generator.repository_baseline(str(root))
        ref_boundary = ref_drift["git_boundary"]
        live_head = pathlib.Path(ref_boundary.live_git_dir) / "HEAD"
        head_raw = live_head.read_bytes()
        if not head_raw.startswith(b"ref: ") or not head_raw.endswith(b"\n"):
            return False
        reference = head_raw[5:-1].decode("ascii")
        live_ref = pathlib.Path(ref_boundary.live_common_dir).joinpath(*reference.split("/"))
        original_ref = live_ref.read_bytes()
        live_ref.write_bytes((b"0" * (len(original_ref.rstrip(b"\n")))) + b"\n")
        try:
            if generator.git_scalar(
                git_binary,
                str(root),
                ref_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            ) != ref_drift["head"]:
                return False
            try:
                generator.revalidate_git_metadata_source(ref_boundary)
            except generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_SOURCE_DRIFT":
                    return False
            else:
                return False
        finally:
            live_ref.write_bytes(original_ref)
            generator.cleanup_git_metadata_adapter(ref_boundary)

        # Any write to the adapter itself is detected before the next Git
        # child, independently of source revalidation.
        adapter_drift = generator.repository_baseline(str(root))
        adapter_boundary = adapter_drift["git_boundary"]
        adapter_config = pathlib.Path(adapter_boundary.git_dir) / "config"
        os.chmod(adapter_config, 0o600)
        with adapter_config.open("ab") as stream:
            stream.write(b"\n[include]\n\tpath = /private/tmp/forbidden\n")
        try:
            generator.git_scalar(
                git_binary,
                str(root),
                adapter_boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            )
        except generator.GenerationError as error:
            if error.public_code != "GIT_ADAPTER_DRIFT":
                return False
        else:
            return False
        finally:
            generator.cleanup_git_metadata_adapter(adapter_boundary)
    return True


def frozen_ref_capture(
    head_ref: str,
    loose: Mapping[str, bytes],
    packed: Optional[bytes],
    worktree: Optional[Mapping[str, bytes]] = None,
) -> Dict[str, Any]:
    """Build the exact capture subset consumed by ``parse_captured_refs``."""

    common_ref_raw = {
        reference[len("refs/") :]: raw for reference, raw in loose.items()
    }
    worktree_ref_raw = {
        reference[len("refs/") :]: raw
        for reference, raw in (worktree or {}).items()
    }
    linked = worktree is not None
    return {
        "git_dir": "/capture/common/worktrees/linked" if linked else "/capture/common",
        "common_dir": "/capture/common",
        "raw_files": {
            "head": ("ref: " + head_ref + "\n").encode("ascii"),
            "packed_refs": packed,
        },
        "identity": {
            "common_refs": {
                "files": [
                    {"relative": relative}
                    for relative in sorted(common_ref_raw)
                ]
            },
            "worktree_refs": {
                "files": [
                    {"relative": relative}
                    for relative in sorted(worktree_ref_raw)
                ]
            },
        },
        "common_ref_raw": common_ref_raw,
        "worktree_ref_raw": worktree_ref_raw,
    }


def captured_refs_contract_matrix(generator: Any) -> bool:
    """Exercise strict ref parsing before any adapter or child can exist."""

    oid_a = "1" * 40
    oid_b = "2" * 40
    oid_c = "3" * 40
    peeled = "4" * 40
    valid = frozen_ref_capture(
        "refs/heads/main",
        {
            "refs/heads/main": (oid_b + "\n").encode("ascii"),
            "refs/heads/alias": b"ref: refs/tags/release\n",
        },
        (
            "# pack-refs with: peeled fully-peeled sorted \n"
            + oid_a
            + " refs/heads/main\n"
            + oid_c
            + " refs/tags/release\n^"
            + peeled
            + "\n"
        ).encode("ascii"),
    )
    parsed = generator.parse_captured_refs(valid)
    if (
        parsed.head_oid != oid_b
        or parsed.head_ref != "refs/heads/main"
        or parsed.oid_width != 40
        or parsed.expected
        != (
            (oid_c, "refs/heads/alias"),
            (oid_b, "refs/heads/main"),
            (oid_c, "refs/tags/release"),
        )
        or peeled in {oid for oid, _reference in parsed.expected}
        or dict(parsed.effective_raw)["refs/heads/main"]
        != (oid_b + "\n").encode("ascii")
    ):
        return False

    headerless = generator.parse_captured_refs(
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (oid_c + " refs/tags/headerless\n").encode("ascii"),
        )
    )
    if (oid_c, "refs/tags/headerless") not in headerless.expected:
        return False

    legal_private_word = generator.parse_captured_refs(
        frozen_ref_capture(
            "refs/heads/main",
            {
                "refs/heads/main": (oid_a + "\n").encode("ascii"),
                "refs/heads/canvas-vault-audit": (oid_b + "\n").encode("ascii"),
            },
            None,
        )
    )
    if (oid_b, "refs/heads/canvas-vault-audit") not in legal_private_word.expected:
        return False

    linked = generator.parse_captured_refs(
        frozen_ref_capture(
            "refs/heads/main",
            {
                "refs/heads/main": (oid_a + "\n").encode("ascii"),
                "refs/worktree/slot": b"not-an-oid\n",
                "refs/bisect/common-only": ("9" * 64 + "\n").encode("ascii"),
            },
            (
                oid_c
                + " refs/bisect/packed-only\n"
                + oid_a
                + " refs/worktree/slot\n"
            ).encode("ascii"),
            worktree={
                "refs/worktree/slot": (peeled + "\n").encode("ascii"),
                "refs/rewritten/topic": (oid_b + "\n").encode("ascii"),
            },
        )
    )
    if linked.expected != (
        (oid_c, "refs/bisect/packed-only"),
        (oid_a, "refs/heads/main"),
        (oid_b, "refs/rewritten/topic"),
        (peeled, "refs/worktree/slot"),
    ):
        return False

    def symbolic_chain(hops: int) -> Dict[str, bytes]:
        names = ["refs/heads/depth-" + str(index) for index in range(hops)]
        result = {
            "refs/heads/main": (oid_a + "\n").encode("ascii"),
            "refs/heads/depth-terminal": (oid_b + "\n").encode("ascii"),
        }
        for index, name in enumerate(names):
            target = names[index + 1] if index + 1 < len(names) else "refs/heads/depth-terminal"
            result[name] = ("ref: " + target + "\n").encode("ascii")
        return result

    depth_at_limit = generator.parse_captured_refs(
        frozen_ref_capture(
            "refs/heads/main",
            symbolic_chain(generator.MAX_CAPTURED_REF_SYMREF_DEPTH),
            None,
        )
    )
    if (oid_b, "refs/heads/depth-0") not in depth_at_limit.expected:
        return False

    depth_over_limit_loose = symbolic_chain(
        generator.MAX_CAPTURED_REF_SYMREF_DEPTH + 1
    )
    hostile = [
        frozen_ref_capture(
            "refs/heads/main",
            {
                "refs/heads/main": (oid_a + "\n").encode("ascii"),
                "refs/heads/alias": b"ref: refs/heads/missing\n",
            },
            None,
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {
                "refs/heads/main": b"ref: refs/heads/alias\n",
                "refs/heads/alias": b"ref: refs/heads/main\n",
            },
            None,
        ),
        frozen_ref_capture(
            "refs/heads/main", {"refs/heads/main": oid_a.encode("ascii")}, None
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": ("0" * 40 + "\n").encode("ascii")},
            None,
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {
                "refs/heads/main": (oid_a + "\n").encode("ascii"),
                "refs/tags/mixed": ("2" * 64 + "\n").encode("ascii"),
            },
            None,
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            ("^" + peeled + "\n" + oid_c + " refs/tags/release\n").encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (
                oid_c
                + " refs/tags/release\n# peeled separated\n^"
                + peeled
                + "\n"
            ).encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (
                oid_c
                + " refs/tags/release\n^"
                + "0" * 40
                + "\n"
            ).encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (
                oid_c
                + " refs/tags/release\n^"
                + "4" * 64
                + "\n"
            ).encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (("A" * 40) + " refs/tags/uppercase\n").encode("ascii"),
        ),
        frozen_ref_capture("refs/heads/main", depth_over_limit_loose, None),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            ("# pack-refs with: peeled unknown\n" + oid_b + " refs/tags/x\n").encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (oid_b + " refs/tags/x\n" + oid_c + " refs/tags/x\n").encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            (
                "# pack-refs with: sorted\n"
                + oid_b
                + " refs/tags/z\n"
                + oid_c
                + " refs/tags/a\n"
            ).encode("ascii"),
        ),
        frozen_ref_capture(
            "refs/heads/main",
            {"refs/heads/main": (oid_a + "\n").encode("ascii")},
            None,
            worktree={"refs/heads/outside": (oid_b + "\n").encode("ascii")},
        ),
    ]
    for capture in hostile:
        try:
            generator.parse_captured_refs(capture)
        except generator.GenerationError:
            continue
        return False

    original_capture = generator.capture_git_source
    original_mkdtemp = generator.tempfile.mkdtemp
    original_run_process = generator.run_process
    events: List[str] = []

    def forbidden_mkdtemp(*_args: Any, **_kwargs: Any) -> str:
        events.append("adapter")
        raise FixtureFailure("captured-refs-adapter-created")

    def forbidden_child(*_args: Any, **_kwargs: Any) -> bytes:
        events.append("child")
        raise FixtureFailure("captured-refs-child-created")

    generator.tempfile.mkdtemp = forbidden_mkdtemp
    generator.run_process = forbidden_child
    try:
        for capture in hostile:
            events.clear()
            generator.capture_git_source = lambda _repo_root, frozen=capture: frozen
            try:
                generator._create_git_metadata_adapter_guarded(
                    "/private/tmp",
                    "/usr/bin/git",
                    "/usr/bin",
                    0,
                    (),
                    (),
                    None,
                )
            except generator.GenerationError:
                if events:
                    return False
            else:
                return False
    finally:
        generator.capture_git_source = original_capture
        generator.tempfile.mkdtemp = original_mkdtemp
        generator.run_process = original_run_process
    return True


def captured_ref_limit_pre_adapter_matrix(generator: Any) -> bool:
    """Prove every captured-ref limit fails before adapter creation or child exec."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-ref-limits-", dir=temp_parent
    ) as temporary:
        root = pathlib.Path(temporary) / "repo"
        root.mkdir(mode=0o700)
        run_synthetic_git(root, ["init", "-q"])
        run_synthetic_git(
            root,
            ["commit", "--allow-empty", "-q", "-m", "fixture ref limits"],
        )
        original_limits = (
            generator.MAX_CAPTURED_REF_BYTES,
            generator.MAX_CAPTURED_REF_ENTRIES,
            generator.MAX_CAPTURED_REF_DIRECTORIES,
        )
        original_capture = generator.capture_git_source
        original_mkdtemp = generator.tempfile.mkdtemp
        original_run_process = generator.run_process
        events: List[str] = []

        def forbidden_mkdtemp(*_args: Any, **_kwargs: Any) -> str:
            events.append("adapter")
            raise FixtureFailure("ref-limit-adapter-created")

        def forbidden_child(*_args: Any, **_kwargs: Any) -> bytes:
            events.append("child")
            raise FixtureFailure("ref-limit-child-created")

        generator.tempfile.mkdtemp = forbidden_mkdtemp
        generator.run_process = forbidden_child
        try:
            cases = (
                ((40, original_limits[1], original_limits[2]), "GIT_SOURCE_REFS_BYTE_LIMIT"),
                ((original_limits[0], 1, original_limits[2]), "GIT_SOURCE_REFS_ENTRY_LIMIT"),
                ((original_limits[0], original_limits[1], 1), "GIT_SOURCE_REFS_DIRECTORY_LIMIT"),
            )
            for limits, expected_code in cases:
                events.clear()
                generator.capture_git_source = original_capture
                (
                    generator.MAX_CAPTURED_REF_BYTES,
                    generator.MAX_CAPTURED_REF_ENTRIES,
                    generator.MAX_CAPTURED_REF_DIRECTORIES,
                ) = limits
                try:
                    generator._create_git_metadata_adapter_guarded(
                        str(root),
                        "/usr/bin/git",
                        "/usr/bin",
                        0,
                        (),
                        (),
                        None,
                    )
                except generator.GenerationError as error:
                    if error.public_code != expected_code or events:
                        return False
                else:
                    return False

            oid = "1" * 40
            effective_overflow = frozen_ref_capture(
                "refs/heads/main",
                {
                    "refs/heads/main": (oid + "\n").encode("ascii"),
                    "refs/heads/second": ("2" * 40 + "\n").encode("ascii"),
                },
                ("3" * 40 + " refs/tags/third\n").encode("ascii"),
            )
            events.clear()
            generator.MAX_CAPTURED_REF_BYTES = original_limits[0]
            generator.MAX_CAPTURED_REF_ENTRIES = 2
            generator.MAX_CAPTURED_REF_DIRECTORIES = original_limits[2]
            generator.capture_git_source = lambda _repo_root: effective_overflow
            try:
                generator._create_git_metadata_adapter_guarded(
                    str(root),
                    "/usr/bin/git",
                    "/usr/bin",
                    0,
                    (),
                    (),
                    None,
                )
            except generator.GenerationError as error:
                if error.public_code != "GIT_CAPTURE_EFFECTIVE_REF_LIMIT" or events:
                    return False
            else:
                return False
        finally:
            (
                generator.MAX_CAPTURED_REF_BYTES,
                generator.MAX_CAPTURED_REF_ENTRIES,
                generator.MAX_CAPTURED_REF_DIRECTORIES,
            ) = original_limits
            generator.capture_git_source = original_capture
            generator.tempfile.mkdtemp = original_mkdtemp
            generator.run_process = original_run_process
    return True


def for_each_ref_observation_matrix(generator: Any) -> bool:
    """Bind the exact child argv and every returned ref value to the capture."""

    head_oid = "1" * 40
    other_oid = "2" * 40
    head_ref = "refs/heads/main"
    other_ref = "refs/tags/release"

    class Boundary:
        pass

    boundary = Boundary()
    boundary.head_oid = head_oid
    boundary.expected_refs = ((head_oid, head_ref), (other_oid, other_ref))
    exact_raw = (
        head_oid + " " + head_ref + "\n" + other_oid + " " + other_ref + "\n"
    ).encode("ascii")
    output = [exact_raw]
    calls: List[Tuple[Tuple[str, ...], str]] = []
    original_run_git = generator.run_git

    def frozen_run_git(
        _git_binary: str,
        _repo_root: str,
        _boundary: Any,
        arguments: Sequence[str],
        label: str,
        *_args: Any,
        **_kwargs: Any,
    ) -> bytes:
        calls.append((tuple(arguments), label))
        return output[0]

    generator.run_git = frozen_run_git
    try:
        observed = generator.other_refs_observation(
            "/usr/bin/git", "/private/tmp", boundary, head_ref
        )
        other_body = (other_oid + " " + other_ref + "\n").encode("ascii")
        if (
            observed != (generator.sha256(other_body), len(other_body))
            or calls
            != [
                (
                    (
                        "for-each-ref",
                        "--sort=refname",
                        "--format=%(objectname) %(refname)",
                        "refs",
                    ),
                    "GIT_FOR_EACH_REF",
                )
            ]
        ):
            return False
        hostile_outputs = (
            b"",
            (head_oid + " " + head_ref + "\n").encode("ascii"),
            exact_raw + ("3" * 40 + " refs/tags/extra\n").encode("ascii"),
            ("4" * 40 + " " + head_ref + "\n" + other_oid + " " + other_ref + "\n").encode("ascii"),
            exact_raw + (other_oid + " " + other_ref + "\n").encode("ascii"),
            (other_oid + " " + other_ref + "\n" + head_oid + " " + head_ref + "\n").encode("ascii"),
            ("0" * 40 + " " + head_ref + "\n" + other_oid + " " + other_ref + "\n").encode("ascii"),
            ("5" * 64 + " " + head_ref + "\n" + other_oid + " " + other_ref + "\n").encode("ascii"),
        )
        for raw in hostile_outputs:
            output[0] = raw
            try:
                generator.other_refs_observation(
                    "/usr/bin/git", "/private/tmp", boundary, head_ref
                )
            except generator.GenerationError as error:
                if not error.public_code.startswith("GIT_FOR_EACH_REF_"):
                    return False
                continue
            return False
    finally:
        generator.run_git = original_run_git
    return True


def generation_git_argv_closure_matrix(root: pathlib.Path, generator: Any) -> bool:
    """Cover every production label and prove full argv rejection pre-child."""

    git_binary = "/usr/bin/git"
    repo_root = "/private/tmp/gov01-generation-argv-repo"
    object_oids = ("1" * 40, "2" * 40)

    class Boundary:
        pass

    boundary = Boundary()
    boundary.expected_object_oids = object_oids
    boundary.adapter_git_fd = 7
    artifact_path = generator.ARTIFACT_SPECS[0][1]
    challenge = "GOV01-GEN-20260821-" + "a" * 64
    cases = {
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
        "GIT_ARTIFACT_TREE": (
            "ls-tree",
            "-z",
            "--full-tree",
            "HEAD",
            "--",
            artifact_path,
        ),
        "GIT_ARTIFACT_BLOB": ("show", "HEAD:" + artifact_path),
        "GIT_MICRO_CURRENT_BYTES": (
            "show",
            "HEAD:" + generator.micro_relative(challenge),
        ),
    }
    if set(cases) != set(generator.GENERATION_GIT_READ_LABELS):
        return False
    for label, tail in cases.items():
        stdin_bytes = (
            ("\n".join(object_oids) + "\n").encode("ascii")
            if label == "GIT_ADAPTER_OBJECT_HASHES"
            else None
        )
        argv = generator.generation_git_child_argv(git_binary, repo_root, tail)
        generator.require_generation_git_child_argv(
            argv,
            git_binary,
            repo_root,
            tail,
            label,
            boundary,
            (0,),
            stdin_bytes,
        )
        for hostile_tail in (tail[:-1], tail + ("--hostile-insertion",)):
            try:
                generator.require_generation_git_child_argv(
                    generator.generation_git_child_argv(
                        git_binary, repo_root, hostile_tail
                    ),
                    git_binary,
                    repo_root,
                    hostile_tail,
                    label,
                    boundary,
                    (0,),
                    stdin_bytes,
                )
            except generator.GenerationError:
                continue
            return False

    head_tail = cases["GIT_HEAD"]
    head_argv = generator.generation_git_child_argv(
        git_binary, repo_root, head_tail
    )
    for hostile_argv in (
        head_argv[:1] + head_argv[2:],
        head_argv[:1] + ["--hostile-prefix"] + head_argv[1:],
        head_argv[:-1],
        head_argv + ["--hostile-tail"],
    ):
        try:
            generator.require_generation_git_child_argv(
                hostile_argv,
                git_binary,
                repo_root,
                head_tail,
                "GIT_HEAD",
                boundary,
                (0,),
                None,
            )
        except generator.GenerationError:
            continue
        return False

    original_verify = generator.verify_git_metadata_adapter
    original_identity_path = generator.identity_bound_directory_path
    original_profile = generator.git_read_sandbox_profile
    original_builder = generator.generation_git_child_argv
    original_run_process = generator.run_process
    child_events: List[Tuple[str, ...]] = []
    generator.verify_git_metadata_adapter = lambda _boundary: None
    generator.identity_bound_directory_path = lambda _fd, _label: "/private/tmp/adapter/git"
    generator.git_read_sandbox_profile = lambda *_args, **_kwargs: b"(version 1)\n(deny default)\n"

    def recording_child(argv: Sequence[str], *_args: Any, **_kwargs: Any) -> bytes:
        child_events.append(tuple(argv))
        return b"1\n"

    generator.run_process = recording_child
    try:
        if generator.run_git(
            git_binary,
            repo_root,
            boundary,
            head_tail,
            "GIT_HEAD",
        ) != b"1\n" or len(child_events) != 1:
            return False
        child_events.clear()

        def inserted_builder(
            binary: str, repository: str, arguments: Sequence[str]
        ) -> List[str]:
            argv = original_builder(binary, repository, arguments)
            return argv[:1] + ["--hostile-prefix"] + argv[1:]

        generator.generation_git_child_argv = inserted_builder
        try:
            generator.run_git(
                git_binary,
                repo_root,
                boundary,
                head_tail,
                "GIT_HEAD",
            )
        except generator.GenerationError as error:
            if error.public_code != "GIT_READ_ARGV_PREFIX" or child_events:
                return False
        else:
            return False
        generator.generation_git_child_argv = original_builder
        for hostile_tail in (head_tail[:-1], head_tail + ("--hostile-tail",)):
            try:
                generator.run_git(
                    git_binary,
                    repo_root,
                    boundary,
                    hostile_tail,
                    "GIT_HEAD",
                )
            except generator.GenerationError as error:
                if error.public_code != "GIT_READ_ARGV_TAIL" or child_events:
                    return False
                continue
            return False
    finally:
        generator.verify_git_metadata_adapter = original_verify
        generator.identity_bound_directory_path = original_identity_path
        generator.git_read_sandbox_profile = original_profile
        generator.generation_git_child_argv = original_builder
        generator.run_process = original_run_process

    module = ast.parse((root / GENERATOR_RELATIVE).read_text(encoding="utf-8"))
    literal_labels = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in ("run_git", "git_scalar") or len(node.args) < 5:
            continue
        label_node = node.args[4]
        if isinstance(label_node, ast.Constant) and isinstance(label_node.value, str):
            literal_labels.add(label_node.value)
    return literal_labels == set(generator.GENERATION_GIT_READ_LABELS)


def ref_boundary_ast_matrix(root: pathlib.Path) -> bool:
    """Lock the parse ordering and exact for-each-ref call as source shape."""

    source = (root / GENERATOR_RELATIVE).read_text(encoding="utf-8")
    module = ast.parse(source)
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    create = functions.get("_create_git_metadata_adapter_guarded")
    observe = functions.get("other_refs_observation")
    if create is None or observe is None:
        return False
    parse_lines = [
        node.lineno
        for node in ast.walk(create)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "parse_captured_refs"
    ]
    adapter_lines = [
        node.lineno
        for node in ast.walk(create)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "tempfile"
        and node.func.attr == "mkdtemp"
    ]
    child_boundary_lines = [
        node.lineno
        for node in ast.walk(create)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "materialize_reachable_git_objects"
    ]
    if (
        len(parse_lines) != 1
        or len(adapter_lines) != 1
        or len(child_boundary_lines) != 1
        or not parse_lines[0] < adapter_lines[0] < child_boundary_lines[0]
    ):
        return False
    run_git_calls = [
        node
        for node in ast.walk(observe)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_git"
    ]
    if len(run_git_calls) != 1 or len(run_git_calls[0].args) < 5:
        return False
    try:
        arguments = ast.literal_eval(run_git_calls[0].args[3])
        label = ast.literal_eval(run_git_calls[0].args[4])
    except (TypeError, ValueError):
        return False
    return arguments == [
        "for-each-ref",
        "--sort=refname",
        "--format=%(objectname) %(refname)",
        "refs",
    ] and label == "GIT_FOR_EACH_REF"


def run_synthetic_git(root: pathlib.Path, arguments: Sequence[str]) -> None:
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": os.path.realpath(tempfile.gettempdir()),
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "user.name=GOV01 Fixture",
            "-c",
            "user.email=fixture.invalid@invalid",
            "-C",
            str(root),
        ]
        + list(arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
        timeout=30,
    )
    require(completed.returncode == 0, "synthetic-git-command")


def run_synthetic_git_output(
    root: pathlib.Path,
    arguments: Sequence[str],
    stdin_bytes: Optional[bytes] = None,
) -> bytes:
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": os.path.realpath(tempfile.gettempdir()),
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    keywords: Dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "env": environment,
        "check": False,
        "timeout": 30,
    }
    if stdin_bytes is None:
        keywords["stdin"] = subprocess.DEVNULL
    else:
        keywords["input"] = stdin_bytes
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "user.name=GOV01 Fixture",
            "-c",
            "user.email=fixture.invalid@invalid",
            "-C",
            str(root),
        ]
        + list(arguments),
        **keywords,
    )
    require(completed.returncode == 0 and not completed.stderr, "synthetic-git-output-command")
    return completed.stdout


SYNTHETIC_OPAQUE_GITLINK_RELATIVE = "_reference/obsidian-sample-plugin"


def add_synthetic_opaque_gitlink(root: pathlib.Path) -> str:
    """Add the exact public opaque gitlink without creating its object body."""

    object_format = run_synthetic_git_output(
        root, ["rev-parse", "--show-object-format"]
    ).decode("ascii").strip()
    require(object_format in ("sha1", "sha256"), "synthetic-gitlink-object-format")
    oid = "1" * (40 if object_format == "sha1" else 64)
    run_synthetic_git(
        root,
        [
            "update-index",
            "--add",
            "--cacheinfo",
            "160000," + oid + "," + SYNTHETIC_OPAQUE_GITLINK_RELATIVE,
        ],
    )
    return oid


def non_head_missing_tip_adapter_matrix(root: pathlib.Path, generator: Any) -> bool:
    """A missing non-HEAD tip remains observable but never enters the pack."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-missing-ref-tip-", dir=temp_parent
    ) as temporary:
        synthetic_root = pathlib.Path(temporary)
        for _role, relative in generator.ARTIFACT_SPECS:
            source = root / relative
            target = synthetic_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            os.chmod(target, source.stat().st_mode & 0o777)
        run_synthetic_git(synthetic_root, ["init", "-q"])
        run_synthetic_git(
            synthetic_root,
            ["add", "--"] + [relative for _role, relative in generator.ARTIFACT_SPECS],
        )
        add_synthetic_opaque_gitlink(synthetic_root)
        run_synthetic_git(
            synthetic_root,
            ["commit", "-q", "-m", "chore(governance): missing-tip baseline"],
        )
        object_format = run_synthetic_git_output(
            synthetic_root, ["rev-parse", "--show-object-format"]
        ).decode("ascii").strip()
        missing_tip_oid = "9" * (40 if object_format == "sha1" else 64)
        missing_tip_ref = "refs/heads/unsealed-tip"
        missing_tip_path = synthetic_root / ".git" / missing_tip_ref
        missing_tip_path.parent.mkdir(parents=True, exist_ok=True)
        missing_tip_path.write_bytes((missing_tip_oid + "\n").encode("ascii"))
        symalias_ref = "refs/heads/unsealed-alias"
        symalias_path = synthetic_root / ".git" / symalias_ref
        symalias_path.write_bytes(("ref: " + missing_tip_ref + "\n").encode("ascii"))
        override_ref = "refs/tags/override"
        packed_override_oid = "8" * len(missing_tip_oid)
        loose_override_oid = "7" * len(missing_tip_oid)
        packed_refs_path = synthetic_root / ".git" / "packed-refs"
        packed_refs_path.write_bytes(
            (
                "# pack-refs with: peeled fully-peeled sorted \n"
                + packed_override_oid
                + " "
                + override_ref
                + "\n"
            ).encode("ascii")
        )
        loose_override_path = synthetic_root / ".git" / override_ref
        loose_override_path.parent.mkdir(parents=True, exist_ok=True)
        loose_override_path.write_bytes((loose_override_oid + "\n").encode("ascii"))
        synthetic_generator = load_generator(synthetic_root)
        baseline = synthetic_generator.repository_baseline(str(synthetic_root))
        boundary = baseline["git_boundary"]
        other_refs_body = (
            missing_tip_oid
            + " "
            + symalias_ref
            + "\n"
            + missing_tip_oid
            + " "
            + missing_tip_ref
            + "\n"
            + loose_override_oid
            + " "
            + override_ref
            + "\n"
        ).encode("ascii")
        passed = (
            (missing_tip_oid, missing_tip_ref) in boundary.expected_refs
            and (missing_tip_oid, symalias_ref) in boundary.expected_refs
            and (loose_override_oid, override_ref) in boundary.expected_refs
            and (packed_override_oid, override_ref) not in boundary.expected_refs
            and missing_tip_oid not in boundary.expected_object_oids
            and loose_override_oid not in boundary.expected_object_oids
            and baseline["other_refs_sha256"]
            == synthetic_generator.sha256(other_refs_body)
            and baseline["other_refs_bytes"] == len(other_refs_body)
        )
        try:
            synthetic_generator.finalize_git_metadata_adapter(boundary)
        except BaseException:
            synthetic_generator.cleanup_git_metadata_adapter(boundary)
            raise
        synthetic_generator.require_git_adapter_quiescent("FIXTURE_MISSING_REF_TIP")
        return passed


def linked_worktree_ref_namespace_matrix(root: pathlib.Path, generator: Any) -> bool:
    """Exercise real linked-worktree ref overlay, packed visibility and CAS."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-linked-refs-", dir=temp_parent
    ) as temporary:
        container = pathlib.Path(temporary)
        primary = container / "primary"
        worktree_name = "linked-ref-fixture"
        linked = primary / ".claude" / "worktrees" / worktree_name
        primary.mkdir(mode=0o700)
        for _role, relative in generator.ARTIFACT_SPECS:
            source = root / relative
            target = primary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            os.chmod(target, source.stat().st_mode & 0o777)
        run_synthetic_git(primary, ["init", "-q"])
        run_synthetic_git(
            primary,
            ["add", "--"] + [relative for _role, relative in generator.ARTIFACT_SPECS],
        )
        add_synthetic_opaque_gitlink(primary)
        run_synthetic_git(
            primary,
            ["commit", "-q", "-m", "chore(governance): linked ref baseline"],
        )
        run_synthetic_git(
            primary,
            ["worktree", "add", "-q", "-b", worktree_name, str(linked)],
        )
        object_format = run_synthetic_git_output(
            linked, ["rev-parse", "--show-object-format"]
        ).decode("ascii").strip()
        oid_width = 40 if object_format == "sha1" else 64
        common_hidden_oid = "6" * oid_width
        packed_visible_oid = "5" * oid_width
        packed_shadowed_oid = "4" * oid_width
        worktree_bisect_oid = "3" * oid_width
        worktree_override_oid = "7" * oid_width
        common_git_dir = primary / ".git"
        linked_git_dir = pathlib.Path(
            run_synthetic_git_output(linked, ["rev-parse", "--absolute-git-dir"])
            .decode("utf-8")
            .strip()
        )
        common_hidden = common_git_dir / "refs/bisect/common-only"
        common_hidden.parent.mkdir(parents=True, exist_ok=True)
        common_hidden.write_bytes((common_hidden_oid + "\n").encode("ascii"))
        common_override = common_git_dir / "refs/worktree/slot"
        common_override.parent.mkdir(parents=True, exist_ok=True)
        common_override.write_bytes((common_hidden_oid + "\n").encode("ascii"))
        (common_git_dir / "packed-refs").write_bytes(
            (
                "# pack-refs with: sorted\n"
                + packed_visible_oid
                + " refs/rewritten/packed-only\n"
                + packed_shadowed_oid
                + " refs/worktree/slot\n"
            ).encode("ascii")
        )
        worktree_bisect = linked_git_dir / "refs/bisect/linked"
        worktree_bisect.parent.mkdir(parents=True, exist_ok=True)
        worktree_bisect.write_bytes((worktree_bisect_oid + "\n").encode("ascii"))
        worktree_override = linked_git_dir / "refs/worktree/slot"
        worktree_override.parent.mkdir(parents=True, exist_ok=True)
        worktree_override.write_bytes((worktree_override_oid + "\n").encode("ascii"))
        worktree_alias = linked_git_dir / "refs/rewritten/alias"
        worktree_alias.parent.mkdir(parents=True, exist_ok=True)
        worktree_alias.write_bytes(b"ref: refs/worktree/slot\n")

        synthetic_generator = load_generator(linked)
        baseline = synthetic_generator.repository_baseline(str(linked))
        boundary = baseline["git_boundary"]
        expected_map = dict(
            (reference, oid) for oid, reference in boundary.expected_refs
        )
        passed = (
            expected_map.get("refs/bisect/linked") == worktree_bisect_oid
            and "refs/bisect/common-only" not in expected_map
            and expected_map.get("refs/rewritten/packed-only") == packed_visible_oid
            and expected_map.get("refs/rewritten/alias") == worktree_override_oid
            and expected_map.get("refs/worktree/slot") == worktree_override_oid
            and common_hidden_oid not in boundary.expected_object_oids
            and packed_visible_oid not in boundary.expected_object_oids
            and packed_shadowed_oid not in boundary.expected_object_oids
            and worktree_bisect_oid not in boundary.expected_object_oids
            and worktree_override_oid not in boundary.expected_object_oids
        )
        frozen_observation = (
            baseline["other_refs_sha256"],
            baseline["other_refs_bytes"],
        )
        original_override = worktree_override.read_bytes()
        worktree_override.write_bytes(("2" * oid_width + "\n").encode("ascii"))
        try:
            if synthetic_generator.other_refs_observation(
                baseline["git_binary"],
                str(linked),
                boundary,
                baseline["head_ref"],
            ) != frozen_observation:
                passed = False
            try:
                synthetic_generator.revalidate_git_metadata_source(boundary)
            except synthetic_generator.GenerationError as error:
                if error.public_code != "GIT_ADAPTER_SOURCE_DRIFT":
                    passed = False
            else:
                passed = False
        finally:
            worktree_override.write_bytes(original_override)
        # Restoring the bytes cannot restore the captured inode timestamps;
        # after the intentional CAS witness, only fail-closed cleanup is valid.
        synthetic_generator.cleanup_git_metadata_adapter(boundary)
        synthetic_generator.require_git_adapter_quiescent("FIXTURE_LINKED_REFS")
        return passed


def reachable_object_adapter_matrix(generator: Any) -> bool:
    """Prove only authorized blobs enter the final sealed object database."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix="gov01-generation-reachable-", dir=temp_parent) as temporary:
        root = pathlib.Path(temporary) / "repo"
        root.mkdir(mode=0o700)
        authorized_relative = "public/authorized.txt"
        unrelated_relative = "ordinary/deep/tracked.txt"
        private_relative = "Canvas-Vault/private/secret.txt"
        gitlink_relative = SYNTHETIC_OPAQUE_GITLINK_RELATIVE
        reference_sibling_relative = "_reference/public.txt"
        authorized = root / authorized_relative
        unrelated = root / unrelated_relative
        private_tracked = root / private_relative
        reference_sibling = root / reference_sibling_relative
        authorized.parent.mkdir(parents=True)
        unrelated.parent.mkdir(parents=True)
        private_tracked.parent.mkdir(parents=True)
        reference_sibling.parent.mkdir(parents=True)
        authorized_raw = b"authorized fixture payload\n"
        tracked_secret_raw = b"tracked but unauthorized fixture secret\n"
        private_secret_raw = b"tracked private subtree secret that must never be dereferenced\n"
        reference_sibling_raw = b"public sibling beside opaque gitlink\n"
        dangling_secret_raw = b"dangling unreachable fixture secret\n"
        authorized.write_bytes(authorized_raw)
        unrelated.write_bytes(tracked_secret_raw)
        private_tracked.write_bytes(private_secret_raw)
        reference_sibling.write_bytes(reference_sibling_raw)
        run_synthetic_git(root, ["init", "-q"])
        run_synthetic_git(
            root,
            [
                "add",
                authorized_relative,
                unrelated_relative,
                private_relative,
                reference_sibling_relative,
            ],
        )
        gitlink_oid = add_synthetic_opaque_gitlink(root)
        run_synthetic_git(root, ["commit", "-q", "-m", "fixture-reachable-baseline"])
        head_oid = run_synthetic_git_output(root, ["rev-parse", "HEAD"]).decode("ascii").strip()
        head_tree_oid = run_synthetic_git_output(root, ["rev-parse", "HEAD^{tree}"]).decode(
            "ascii"
        ).strip()
        unrelated_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:" + unrelated_relative]
        ).decode("ascii").strip()
        private_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:" + private_relative]
        ).decode("ascii").strip()
        reference_sibling_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:" + reference_sibling_relative]
        ).decode("ascii").strip()
        ordinary_tree_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:ordinary"]
        ).decode("ascii").strip()
        private_tree_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:Canvas-Vault"]
        ).decode("ascii").strip()
        one_object_pack = run_synthetic_git_output(
            root,
            ["pack-objects", "--stdout", "--no-reuse-delta", "--no-reuse-object"],
            (head_oid + "\n").encode("ascii"),
        )
        generator.validate_generated_pack_envelope(one_object_pack, 1, len(head_oid))
        wrong_pack_count = bytearray(one_object_pack)
        wrong_pack_count[8:12] = (2).to_bytes(4, "big")
        wrong_pack_checksum = bytearray(one_object_pack)
        wrong_pack_checksum[-1] ^= 1
        for hostile_pack, expected_code in (
            (bytes(wrong_pack_count), "GIT_BOOTSTRAP_PACK_FORMAT"),
            (bytes(wrong_pack_checksum), "GIT_BOOTSTRAP_PACK_CHECKSUM"),
        ):
            try:
                generator.validate_generated_pack_envelope(hostile_pack, 1, len(head_oid))
            except generator.GenerationError as error:
                require(error.public_code == expected_code, "reachable-generated-pack-label")
            else:
                return False
        # Force the required commit/tree/blob closure into a normal pack.  The
        # same selected source container deliberately also holds an unrelated
        # tracked secret; the final partial adapter must still omit its OID.
        run_synthetic_git(root, ["repack", "-a", "-d"])
        dangling_oid = run_synthetic_git_output(
            root,
            ["hash-object", "-w", "--stdin"],
            dangling_secret_raw,
        ).decode("ascii").strip()
        # Put the dangling secret in its own pack and remove its loose copy.
        # Dependency discovery may parse its idx metadata, but must neither
        # select nor open/copy the unrelated pack payload.
        dangling_pack_oid = run_synthetic_git_output(
            root,
            ["pack-objects", ".git/objects/pack/pack"],
            (dangling_oid + "\n").encode("ascii"),
        ).decode("ascii").strip()
        objects_path = root / ".git/objects"
        dangling_loose = objects_path / dangling_oid[:2] / dangling_oid[2:]
        dangling_loose.unlink()
        dangling_pack = objects_path / "pack" / ("pack-" + dangling_pack_oid + ".pack")
        dangling_index = objects_path / "pack" / ("pack-" + dangling_pack_oid + ".idx")
        require(dangling_pack.is_file() and dangling_index.is_file(), "reachable-dangling-pack")

        git_binary, developer_root = generator.resolve_git()
        original_open = generator.os.open
        forbidden_opens = {
            os.path.realpath(dangling_pack),
            os.path.realpath(objects_path / "pack/multi-pack-index"),
            os.path.realpath(objects_path / "info/commit-graph"),
        }
        info_dir = objects_path / "info"
        info_dir.mkdir(mode=0o700, exist_ok=True)
        multi_pack_trap = objects_path / "pack/multi-pack-index"
        commit_graph_trap = info_dir / "commit-graph"
        multi_pack_trap.write_bytes(b"untrusted-midx-must-not-be-opened\n")
        commit_graph_trap.write_bytes(b"untrusted-commit-graph-must-not-be-opened\n")
        os.chmod(multi_pack_trap, 0o600)
        os.chmod(commit_graph_trap, 0o600)
        capture = generator.capture_git_source(str(root))
        raw_index = capture["raw_files"]["index"]
        raw_oid_bytes = len(head_oid) // 2

        def signed_index(body: bytes) -> bytes:
            digest = hashlib.sha1() if len(head_oid) == 40 else hashlib.sha256()
            digest.update(body)
            return body + digest.digest()

        index_body = raw_index[:-raw_oid_bytes]
        index_proof = generator.prove_captured_index_root_tree(
            raw_index, len(head_oid), head_tree_oid
        )
        require(
            index_proof.entry_count == 5
            and index_proof.version == 2
            and index_proof.opaque_gitlink_count == 1,
            "reachable-index-v2-positive",
        )
        version_three = bytearray(index_body)
        version_three[4:8] = (3).to_bytes(4, "big")
        version_three_proof = generator.prove_captured_index_root_tree(
            signed_index(bytes(version_three)), len(head_oid), head_tree_oid
        )
        require(
            version_three_proof.version == 3
            and version_three_proof.opaque_gitlink_count == 1,
            "reachable-index-v3-positive",
        )
        tree_extension_at = index_body.rfind(b"TREE")
        if tree_extension_at >= 12 and tree_extension_at + 8 < len(index_body):
            tree_extension_size = int.from_bytes(
                index_body[tree_extension_at + 4 : tree_extension_at + 8], "big"
            )
            optional_tree_body = bytearray(index_body)
            require(tree_extension_size > 0, "reachable-index-tree-extension-body")
            optional_tree_body[tree_extension_at + 8] ^= 1
            optional_tree = signed_index(bytes(optional_tree_body))
        else:
            optional_tree = signed_index(index_body + b"ZZZZ" + (0).to_bytes(4, "big"))
        require(
            generator.prove_captured_index_root_tree(
                optional_tree, len(head_oid), head_tree_oid
            ).root_tree_oid
            == head_tree_oid,
            "reachable-index-optional-extension-ignored",
        )

        first_entry = 12
        first_oid = first_entry + 40
        first_flags = first_oid + raw_oid_bytes
        first_nul = index_body.index(b"\x00", first_flags + 2)
        first_end = first_nul + 1
        first_padding = (-(first_end - first_entry)) % 8
        gitlink_path_start = index_body.index(gitlink_relative.encode("ascii"))
        gitlink_entry = gitlink_path_start - (40 + raw_oid_bytes + 2)
        require(
            gitlink_entry >= 12
            and int.from_bytes(index_body[gitlink_entry + 24 : gitlink_entry + 28], "big")
            == 0o160000,
            "reachable-index-gitlink-vector",
        )
        hostile_captured_indexes: List[Tuple[bytes, str]] = []
        version_four = bytearray(index_body)
        version_four[4:8] = (4).to_bytes(4, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(version_four)), "GIT_INDEX_VERSION_UNSUPPORTED")
        )
        staged = bytearray(index_body)
        staged[first_oid] ^= 1
        hostile_captured_indexes.append(
            (signed_index(bytes(staged)), "GIT_INDEX_HEAD_TREE_MISMATCH")
        )
        unmerged = bytearray(index_body)
        flags_value = int.from_bytes(unmerged[first_flags : first_flags + 2], "big") | 0x1000
        unmerged[first_flags : first_flags + 2] = flags_value.to_bytes(2, "big")
        hostile_captured_indexes.append((signed_index(bytes(unmerged)), "GIT_INDEX_UNMERGED"))
        assume_valid = bytearray(index_body)
        assume_flags = int.from_bytes(
            assume_valid[first_flags : first_flags + 2], "big"
        ) | 0x8000
        assume_valid[first_flags : first_flags + 2] = assume_flags.to_bytes(2, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(assume_valid)), "GIT_INDEX_ASSUME_VALID")
        )
        extra_gitlink = bytearray(index_body)
        extra_gitlink[first_entry + 24 : first_entry + 28] = (0o160000).to_bytes(4, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(extra_gitlink)), "GIT_INDEX_GITLINK_SET")
        )
        missing_gitlink = bytearray(index_body)
        missing_gitlink[gitlink_entry + 24 : gitlink_entry + 28] = (0o100644).to_bytes(4, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(missing_gitlink)), "GIT_INDEX_GITLINK_SET")
        )
        substituted_gitlink = bytearray(missing_gitlink)
        substituted_gitlink[first_entry + 24 : first_entry + 28] = (0o160000).to_bytes(4, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(substituted_gitlink)), "GIT_INDEX_GITLINK_SET")
        )
        sparse = bytearray(index_body)
        sparse[first_entry + 24 : first_entry + 28] = (0o040000).to_bytes(4, "big")
        hostile_captured_indexes.append(
            (signed_index(bytes(sparse)), "GIT_INDEX_SPARSE_DIRECTORY")
        )
        dot_git = bytearray(index_body)
        first_path_start = first_flags + 2
        first_path_length = first_nul - first_path_start
        require(first_path_length >= 6, "reachable-index-dot-git-vector-length")
        dot_git[first_path_start:first_nul] = b".git/" + b"x" * (first_path_length - 5)
        hostile_captured_indexes.append((signed_index(bytes(dot_git)), "GIT_INDEX_DOT_GIT"))
        hostile_captured_indexes.append(
            (signed_index(index_body + b"link" + (0).to_bytes(4, "big")), "GIT_INDEX_REQUIRED_EXTENSION")
        )
        hostile_captured_indexes.append(
            (signed_index(index_body + b"sdir" + (0).to_bytes(4, "big")), "GIT_INDEX_REQUIRED_EXTENSION")
        )
        hostile_captured_indexes.append(
            (signed_index(index_body + b"zzzz" + (0).to_bytes(4, "big")), "GIT_INDEX_REQUIRED_EXTENSION")
        )
        hostile_captured_indexes.append(
            (
                signed_index(index_body + b"EOIE" + (32).to_bytes(4, "big") + b"x"),
                "GIT_INDEX_EXTENSION_FORMAT",
            )
        )
        bad_checksum = bytearray(raw_index)
        bad_checksum[-1] ^= 1
        hostile_captured_indexes.append((bytes(bad_checksum), "GIT_INDEX_CHECKSUM"))
        if first_padding:
            bad_padding = bytearray(index_body)
            bad_padding[first_end] = 1
            hostile_captured_indexes.append(
                (signed_index(bytes(bad_padding)), "GIT_INDEX_PADDING")
            )
        for hostile_index, expected_code in hostile_captured_indexes:
            try:
                generator.prove_captured_index_root_tree(
                    hostile_index, len(head_oid), head_tree_oid
                )
            except generator.GenerationError as error:
                require(error.public_code == expected_code, "reachable-captured-index-label")
            else:
                return False

        def deny_unrelated_pack_open(path: Any, *args: Any, **kwargs: Any) -> int:
            if isinstance(path, (str, bytes, os.PathLike)) and os.path.realpath(os.fsdecode(path)) in forbidden_opens:
                raise AssertionError("unrelated-live-object-container-opened")
            return original_open(path, *args, **kwargs)

        generator.os.open = deny_unrelated_pack_open
        try:
            object_store = generator.capture_git_object_store(str(objects_path), len(head_oid))
            dependencies = generator.capture_git_object_dependencies(capture, (head_oid,))
        finally:
            generator.os.open = original_open
        selected_pack_paths = tuple(dependencies["allowed_pack_paths"])
        require(
            object_store["pair_count"] == 2
            and dependencies["selected_pack_container_count"] == 1
            and selected_pack_paths
            and str(dangling_pack) not in selected_pack_paths
            and str(dangling_index) not in selected_pack_paths,
            "reachable-exact-container-selection",
        )
        bootstrap_profile = generator.git_bootstrap_sandbox_profile(
            git_binary,
            developer_root,
            capture,
            "/private/tmp/gov01-git-adapter-fixture/git",
            dependencies,
        ).decode("ascii")
        require(
            generator.sbpl_subpath(str(objects_path), "FIXTURE_OBJECTS") not in bootstrap_profile
            and str(dangling_pack) not in bootstrap_profile
            and str(dangling_index) not in bootstrap_profile
            and all(path in bootstrap_profile for path in selected_pack_paths),
            "reachable-bootstrap-exact-sandbox",
        )

        selected_index = next(path for path in selected_pack_paths if path.endswith(".idx"))
        selected_index_raw = pathlib.Path(selected_index).read_bytes()
        selected_index_name = pathlib.Path(selected_index).name
        replacement_digit = "0" if selected_index_name[5] != "0" else "1"
        wrong_index_name = "pack-" + replacement_digit + selected_index_name[6:]
        try:
            generator.parse_git_pack_index_v2(
                selected_index_raw,
                len(head_oid),
                wrong_index_name,
                (head_oid,),
            )
        except generator.GenerationError as error:
            require(
                error.public_code == "GIT_OBJECT_PACK_INDEX_PACK_BINDING",
                "reachable-wrong-index-binding-label",
            )
        else:
            return False

        object_count = int.from_bytes(selected_index_raw[8 + 255 * 4 : 12 + 255 * 4], "big")
        offsets_start = 8 + 256 * 4 + object_count * raw_oid_bytes + object_count * 4
        version_bad = bytearray(selected_index_raw)
        version_bad[4:8] = (3).to_bytes(4, "big")
        fanout_bad = bytearray(selected_index_raw)
        fanout_bad[8:12] = (1).to_bytes(4, "big")
        fanout_bad[12:16] = (0).to_bytes(4, "big")
        large_offset_bad = bytearray(selected_index_raw)
        large_offset_bad[offsets_start : offsets_start + 4] = (0x80000001).to_bytes(4, "big")
        checksum_bad = bytearray(selected_index_raw)
        checksum_bad[-1] ^= 1
        hostile_indexes = (
            (bytes(version_bad), "GIT_OBJECT_PACK_INDEX_FORMAT"),
            (bytes(fanout_bad), "GIT_OBJECT_PACK_INDEX_FANOUT"),
            (bytes(large_offset_bad), "GIT_OBJECT_PACK_INDEX_LARGE_OFFSET"),
            (selected_index_raw + b"\x00", "GIT_OBJECT_PACK_INDEX_LENGTH"),
            (bytes(checksum_bad), "GIT_OBJECT_PACK_INDEX_CHECKSUM"),
        )
        for hostile_index_raw, expected_code in hostile_indexes:
            try:
                generator.parse_git_pack_index_v2(
                    hostile_index_raw,
                    len(head_oid),
                    selected_index_name,
                    (head_oid,),
                )
            except generator.GenerationError as error:
                require(error.public_code == expected_code, "reachable-hostile-index-label")
            else:
                return False

        raw_oid = bytes.fromhex(head_oid)
        hostile_tree_objects = (
            (
                b"160000 submodule\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_KIND",
            ),
            (
                b"40000 .GiT\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_DOT_GIT",
            ),
            (
                b"100644 duplicate\x00" + raw_oid + b"40000 duplicate\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_DUPLICATE",
            ),
            (
                b"100644 z\x00" + raw_oid + b"100644 a\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_ORDER",
            ),
        )
        for hostile_raw, expected_code in hostile_tree_objects:
            try:
                generator.parse_bootstrap_tree_object_entries(hostile_raw, len(head_oid))
            except generator.GenerationError as error:
                require(error.public_code == expected_code, "reachable-hostile-tree-label")
            else:
                return False

        allowed_opaque_sibling_entries = generator.parse_bootstrap_tree_object_entries(
            b"160000 obsidian-sample-plugin\x00"
            + raw_oid
            + b"100644 public.txt\x00"
            + raw_oid,
            len(head_oid),
            tree_prefix="_reference",
        )
        require(
            tuple(entry.kind for entry in allowed_opaque_sibling_entries)
            == ("gitlink", "blob"),
            "reachable-unselected-same-tree-gitlink-parse",
        )

        opaque_entries = generator.parse_bootstrap_tree_object_entries(
            b"40000 Canvas-Vault\x00" + raw_oid + b"100644 control-\x01\x00" + raw_oid,
            len(head_oid),
        )
        require(
            [entry.name for entry in opaque_entries] == [b"Canvas-Vault", b"control-\x01"],
            "reachable-unselected-sibling-names-opaque",
        )
        for private_required in ("Canvas-Vault/private/secret.txt", ".obsidian/secret"):
            try:
                generator.build_required_path_trie((private_required,), ())
            except generator.GenerationError as error:
                require(
                    error.public_code == "GIT_BOOTSTRAP_REQUIRED_PATH_PRIVATE_COMPONENT",
                    "reachable-required-private-path-label",
                )
            else:
                return False
        original_capture_source = generator.capture_git_source
        capture_called = {"value": False}

        def trap_capture_after_private_path(*args: Any, **kwargs: Any) -> Any:
            capture_called["value"] = True
            return original_capture_source(*args, **kwargs)

        generator.capture_git_source = trap_capture_after_private_path
        try:
            try:
                generator.create_git_metadata_adapter(
                    str(root),
                    git_binary,
                    developer_root,
                    required_current_blob_paths=("Canvas-Vault/private/secret.txt",),
                )
            except generator.GenerationError as error:
                require(
                    error.public_code == "GIT_BOOTSTRAP_REQUIRED_PATH_PRIVATE_COMPONENT",
                    "reachable-private-path-pre-open-label",
                )
            else:
                return False
        finally:
            generator.capture_git_source = original_capture_source
        require(not capture_called["value"], "reachable-private-path-zero-source-open")
        generator.require_git_adapter_quiescent("FIXTURE_PRIVATE_PATH_PRE_OPEN")

        selected_stem = pathlib.Path(selected_index).stem
        promisor = pathlib.Path(selected_index).with_name(selected_stem + ".promisor")
        promisor.write_bytes(b"promisor-trap\n")
        os.chmod(promisor, 0o600)
        try:
            try:
                generator.capture_git_object_dependencies(capture, (head_oid,))
            except generator.GenerationError as error:
                require(
                    error.public_code == "GIT_OBJECT_DEPENDENCY_PROMISOR",
                    "reachable-promisor-label",
                )
            else:
                return False
        finally:
            promisor.unlink()

        original_capture_git_object_dependencies = generator.capture_git_object_dependencies
        dependency_oid_requests: List[Tuple[str, ...]] = []

        def record_object_dependency_request(
            source_capture: Mapping[str, Any],
            object_oids: Sequence[str],
        ) -> Dict[str, Any]:
            requested = tuple(object_oids)
            require(gitlink_oid not in requested, "reachable-gitlink-oid-not-requested")
            dependency_oid_requests.append(requested)
            return original_capture_git_object_dependencies(source_capture, object_oids)

        generator.os.open = deny_unrelated_pack_open
        generator.capture_git_object_dependencies = record_object_dependency_request
        try:
            _control, boundary = generator.create_git_metadata_adapter(
                str(root),
                git_binary,
                developer_root,
                required_current_blob_paths=(authorized_relative, reference_sibling_relative),
            )
        finally:
            generator.os.open = original_open
            generator.capture_git_object_dependencies = original_capture_git_object_dependencies
        try:
            expected = set(boundary.expected_object_oids)
            require(
                head_oid in expected
                and reference_sibling_oid in expected
                and gitlink_oid not in expected
                and unrelated_oid not in expected
                and private_oid not in expected
                and ordinary_tree_oid not in expected
                and private_tree_oid not in expected
                and dangling_oid not in expected,
                "reachable-exact-object-set",
            )
            require(
                boundary.index_tree_proof.root_tree_oid == boundary.head_tree
                and boundary.index_tree_proof.entry_count == 5
                and boundary.index_tree_proof.opaque_gitlink_count == 1
                and dict(boundary.expected_object_types).get(head_oid) == "commit",
                "reachable-index-root-proof",
            )
            require(bool(dependency_oid_requests), "reachable-gitlink-zero-request-witness")
            require(generator.git_scalar(
                git_binary,
                str(root),
                boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_HEAD",
            ) == head_oid, "reachable-head")
            require(
                "_reference" in dict(boundary.current_path_resolution.tree_contexts),
                "reachable-unselected-same-tree-gitlink-context",
            )
            enumerated = set(
                generator.run_git(
                    git_binary,
                    str(root),
                    boundary,
                    [
                        "cat-file",
                        "--batch-all-objects",
                        "--batch-check=%(objectname)",
                    ],
                    "GIT_ADAPTER_OBJECT_ENUMERATION",
                ).decode("ascii").splitlines()
            )
            require(enumerated == expected, "reachable-adapter-object-enumeration")
            require(not enumerated.intersection((
                gitlink_oid,
                unrelated_oid,
                private_oid,
                ordinary_tree_oid,
                private_tree_oid,
                dangling_oid,
            )), "reachable-absent-object-set")
            objects_root = pathlib.Path(boundary.git_dir) / "objects"
            relative_files = sorted(
                str(path.relative_to(objects_root))
                for path in objects_root.rglob("*")
                if path.is_file()
            )
            require(bool(relative_files), "reachable-pack-files")
            require(
                not any(not path.startswith("pack/pack-") for path in relative_files),
                "reachable-pack-layout",
            )
            suffixes = {pathlib.PurePosixPath(path).suffix for path in relative_files}
            require(
                {".idx", ".pack"}.issubset(suffixes) and suffixes.issubset({".idx", ".pack", ".rev"}),
                "reachable-pack-suffixes",
            )
            require(not hasattr(generator, "copy_git_object_store"), "reachable-no-recursive-copy")
        finally:
            generator.finalize_git_metadata_adapter(boundary)

        required_gitlink_requests: List[Tuple[str, ...]] = []

        def record_required_gitlink_dependency_request(
            source_capture: Mapping[str, Any],
            object_oids: Sequence[str],
        ) -> Dict[str, Any]:
            requested = tuple(object_oids)
            require(gitlink_oid not in requested, "reachable-required-gitlink-oid-not-requested")
            required_gitlink_requests.append(requested)
            return original_capture_git_object_dependencies(source_capture, object_oids)

        generator.capture_git_object_dependencies = record_required_gitlink_dependency_request
        try:
            try:
                generator.create_git_metadata_adapter(
                    str(root),
                    git_binary,
                    developer_root,
                    required_current_blob_paths=(gitlink_relative,),
                )
            except generator.GenerationError as error:
                require(
                    error.public_code == "GIT_BOOTSTRAP_REQUIRED_PATH_MODE",
                    "reachable-required-gitlink-label",
                )
            else:
                return False
        finally:
            generator.capture_git_object_dependencies = original_capture_git_object_dependencies
        require(bool(required_gitlink_requests), "reachable-required-gitlink-tree-request-witness")
        generator.require_git_adapter_quiescent("FIXTURE_REACHABLE_REQUIRED_GITLINK")

        # Replace each exact selected pack/index pathname between dependency
        # capture and Git execution.  Even byte-identical replacement content
        # has a new identity and must be rejected by post-child dependency CAS.
        for drift_path_text in (
            next(path for path in selected_pack_paths if path.endswith(".pack")),
            next(path for path in selected_pack_paths if path.endswith(".idx")),
        ):
            drift_path = pathlib.Path(drift_path_text)
            retained_path = drift_path.with_name(drift_path.name + ".fixture-retained")
            original_run_process = generator.run_process
            injected = {"value": False}

            def swap_container_before_bootstrap(*args: Any, **kwargs: Any) -> bytes:
                label = args[1] if len(args) > 1 else kwargs.get("label")
                if not injected["value"] and label == "GIT_BOOTSTRAP_OBJECTS":
                    drift_path.rename(retained_path)
                    shutil.copyfile(retained_path, drift_path)
                    os.chmod(drift_path, 0o444)
                    injected["value"] = True
                return original_run_process(*args, **kwargs)

            generator.run_process = swap_container_before_bootstrap
            try:
                try:
                    generator.create_git_metadata_adapter(
                        str(root),
                        git_binary,
                        developer_root,
                        required_current_blob_paths=(authorized_relative,),
                    )
                except generator.GenerationError as error:
                    require(
                        error.public_code == "GIT_BOOTSTRAP_OBJECT_SOURCE_DRIFT",
                        "reachable-container-drift-label",
                    )
                else:
                    return False
            finally:
                generator.run_process = original_run_process
                if drift_path.exists():
                    drift_path.unlink()
                if retained_path.exists():
                    retained_path.rename(drift_path)
            require(injected["value"], "reachable-container-drift-injected")
            generator.require_git_adapter_quiescent("FIXTURE_REACHABLE_CONTAINER_DRIFT")
        return True


def committed_transition_matrix(
    root: pathlib.Path,
    generator: Any,
    validator: Draft202012Validator,
) -> Tuple[str, Dict[str, Any]]:
    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix="gov01-generation-transition-", dir=temp_parent) as temporary:
        synthetic_root = pathlib.Path(temporary)
        for _role, relative in generator.ARTIFACT_SPECS:
            source = root / relative
            target = synthetic_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            os.chmod(target, source.stat().st_mode & 0o777)
        run_synthetic_git(synthetic_root, ["init", "-q"])
        run_synthetic_git(
            synthetic_root,
            ["add", "--"] + [relative for _role, relative in generator.ARTIFACT_SPECS],
        )
        add_synthetic_opaque_gitlink(synthetic_root)
        run_synthetic_git(synthetic_root, ["commit", "-q", "-m", "chore(governance): fixture baseline"])

        synthetic_generator = load_generator(synthetic_root)
        baseline = synthetic_generator.repository_baseline(str(synthetic_root))
        artifacts = synthetic_generator.artifact_observations(str(synthetic_root))
        synthetic_generator.assert_artifacts_match_head(
            baseline["git_binary"],
            str(synthetic_root),
            baseline["git_boundary"],
            artifacts,
        )
        synthetic_generator.finalize_git_metadata_adapter(baseline["git_boundary"])
        _checkpoint_baseline, _checkpoint_artifacts, checkpoint_receipt = (
            synthetic_generator.capture_issue_public_checkpoint(str(synthetic_root))
        )
        gitignore_path = synthetic_root / ".gitignore"
        gitignore_raw = gitignore_path.read_bytes()
        gitignore_path.write_bytes(gitignore_raw + b"\nfixture-uncommitted-drift\n")
        try:
            try:
                synthetic_generator.capture_issue_public_checkpoint(str(synthetic_root))
            except synthetic_generator.GenerationError as error:
                require(
                    error.public_code == "ARTIFACT_NOT_HEAD_BYTES",
                    "issue-checkpoint-uncommitted-artifact-drift-label",
                )
            else:
                raise FixtureFailure("issue-checkpoint-uncommitted-artifact-drift-accepted")
        finally:
            gitignore_path.write_bytes(gitignore_raw)
        gitignore_path.write_bytes(gitignore_raw + b"\nfixture-committed-drift\n")
        run_synthetic_git(synthetic_root, ["add", "--", ".gitignore"])
        run_synthetic_git(synthetic_root, ["commit", "-q", "-m", "fixture checkpoint drift"])
        _drift_baseline, _drift_artifacts, drift_checkpoint_receipt = (
            synthetic_generator.capture_issue_public_checkpoint(str(synthetic_root))
        )
        require(
            drift_checkpoint_receipt != checkpoint_receipt,
            "issue-checkpoint-committed-source-artifact-drift",
        )
        run_synthetic_git(synthetic_root, ["reset", "--hard", baseline["head"]])
        synthetic_generator.require_git_adapter_quiescent("FIXTURE_ISSUE_CHECKPOINT")
        issued = synthetic_generator.utc_now_second()
        challenge = "GOV01-GEN-" + issued.strftime("%Y%m%d") + "-" + "c" * 64
        envelope = synthetic_generator.build_issue_envelope(challenge, issued, baseline, artifacts)
        require(schema_accepts(validator, envelope), "transition-envelope-schema")
        raw = synthetic_generator.canonical_json(envelope)
        micro_relative = synthetic_generator.micro_relative(challenge)

        # A commit that adds the approved micro plus a private sibling subtree
        # must fail from ancestor-tree Merkle drift without opening that private
        # subtree tree or blob body.
        synthetic_generator.write_exclusive_public_file(str(synthetic_root), micro_relative, raw)
        private_path = "Canvas-Vault/private-transition-secret.txt"
        private_file = synthetic_root / private_path
        private_file.parent.mkdir(parents=True, exist_ok=True)
        private_file.write_bytes(b"private transition body must not be opened\n")
        run_synthetic_git(synthetic_root, ["add", "--", micro_relative, private_path])
        run_synthetic_git(synthetic_root, ["commit", "-q", "-m", "fixture hostile extra subtree"])
        private_tree_oid = run_synthetic_git_output(
            synthetic_root, ["rev-parse", "HEAD:Canvas-Vault"]
        ).decode("ascii").strip()
        requested_oids: List[str] = []
        original_bootstrap_read = synthetic_generator.bootstrap_git_object_read

        def record_transition_object_reads(*args: Any, **kwargs: Any) -> bytes:
            requested_oids.extend(str(oid) for oid in kwargs.get("object_oids", ()))
            return original_bootstrap_read(*args, **kwargs)

        synthetic_generator.bootstrap_git_object_read = record_transition_object_reads
        try:
            try:
                synthetic_generator.load_approved_generation_request(
                    synthetic_generator.receipt_digest(raw),
                    challenge,
                )
            except synthetic_generator.GenerationError as error:
                require(
                    error.public_code == "GIT_MICRO_TRANSITION_SIBLING_DRIFT",
                    "transition-extra-private-subtree-label",
                )
            else:
                raise FixtureFailure("transition-extra-private-subtree-accepted")
        finally:
            synthetic_generator.bootstrap_git_object_read = original_bootstrap_read
        require(
            private_tree_oid not in requested_oids,
            "transition-private-subtree-body-not-requested",
        )
        synthetic_generator.require_git_adapter_quiescent("FIXTURE_TRANSITION_HOSTILE")
        run_synthetic_git(synthetic_root, ["reset", "--hard", baseline["head"]])

        synthetic_generator.write_exclusive_public_file(str(synthetic_root), micro_relative, raw)
        run_synthetic_git(synthetic_root, ["add", "--", micro_relative])
        run_synthetic_git(synthetic_root, ["commit", "-q", "-m", "chore(governance): fixture micro"])

        context = synthetic_generator.load_approved_generation_request(
            synthetic_generator.receipt_digest(raw),
            challenge,
        )
        authorization = synthetic_generator.generation_authorization(context)
        bound_executor = synthetic_generator.load_content_addressed_executor(context)
        bound_pure = bound_executor_pure_contract_matrix(
            synthetic_root,
            synthetic_generator,
            bound_executor,
            context,
            authorization,
        )
        positive = (
            context["micro_raw"] == raw
            and context["micro_envelope"] == envelope
            and context["micro_relative"] == micro_relative
            and context["generation_output_preexisting"] is False
            and authorization["authorization_parent_commit_oid"] == baseline["head"]
            and authorization["authorization_parent_tree_oid"] == baseline["tree"]
            and authorization["authorization_commit_oid"] == context["current_head"]
            and authorization["authorization_tree_oid"] == context["current_tree"]
            and authorization["generated_acquisition_envelope_repo_relative_path"]
            == synthetic_generator.final_relative(challenge)
            and authorization["generation_claim_required"] is True
            and authorization["generation_claim_profile"] == synthetic_generator.GENERATION_CLAIM_PROFILE
            and authorization["generation_claim_record_profile"]
            == synthetic_generator.GENERATION_CLAIM_RECORD_PROFILE
            and authorization["generation_claim_retention"]
            == synthetic_generator.GENERATION_CLAIM_RETENTION
            and bound_executor.__file__
            == str(
                synthetic_root
                / synthetic_generator.CONTROL_PREFIX
                / "GOV-01-toolchain-static-acquisition-v2.py"
            )
            and callable(bound_executor.derive_generation_runtime_args_v2)
            and callable(bound_executor.collect_generation_observations_v2)
            and callable(bound_executor.build_pending_envelope_v2)
            and callable(bound_executor.probe_generation_claim_v2)
            and callable(bound_executor.create_generation_claim_v2)
            and callable(bound_executor.verify_generation_claim_recovery_v2)
            and callable(bound_executor.probe_generation_claim_from_verified_fds_v2)
            and callable(bound_executor.create_generation_claim_from_verified_fds_v2)
            and callable(bound_executor.verify_generation_claim_recovery_from_verified_fds_v2)
            and bound_executor.GENERATION_CLAIM_PROFILE == synthetic_generator.GENERATION_CLAIM_PROFILE
            and bound_executor.GENERATION_CLAIM_RECORD_PROFILE
            == synthetic_generator.GENERATION_CLAIM_RECORD_PROFILE
            and bound_executor.GENERATION_CLAIM_RETENTION == synthetic_generator.GENERATION_CLAIM_RETENTION
            and bound_pure["builder_module"] == bound_executor.__name__
            and bound_pure["manual_module"] == bound_executor.__name__
            and bound_pure["privacy_module"] == bound_executor.__name__
            and bound_pure["claim_core"]["probe_module"] == bound_executor.__name__
            and bound_pure["claim_core"]["create_module"] == bound_executor.__name__
            and bound_pure["claim_core"]["recovery_module"] == bound_executor.__name__
            and bound_pure["claim_core"]["ok"] is True
            and bound_pure["bool_int_scalar_type_parity"]["ok"] is True
            and bound_pure["bool_int_scalar_type_parity"]["mutation_count"] == 145
            and git_post_preflight_sandbox_matrix(
                synthetic_generator,
                synthetic_root,
                baseline["git_binary"],
                baseline["git_boundary"],
            )
        )
        return (
            HOST_SANDBOX_POSITIVE if positive else "transition-check-failed",
            bound_pure,
        )


def receipt_first_matrix(root: pathlib.Path, generator: Any) -> bool:
    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix="gov01-generation-receipt-first-", dir=temp_parent) as temporary:
        synthetic_root = pathlib.Path(temporary)
        source = root / GENERATOR_RELATIVE
        target = synthetic_root / GENERATOR_RELATIVE
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        os.chmod(target, 0o644)
        synthetic_generator = load_generator(synthetic_root)
        challenge = "GOV01-GEN-20260821-" + "d" * 64
        micro = synthetic_root / synthetic_generator.micro_relative(challenge)
        micro.parent.mkdir(parents=True, exist_ok=True)
        micro.write_bytes(b'{"not":"approved"}\n')
        os.chmod(micro, 0o644)
        try:
            synthetic_generator.load_approved_generation_request("0" * 64, challenge)
        except synthetic_generator.GenerationError as error:
            return error.public_code == "GENERATION_RECEIPT_MISMATCH"
    return False


def regular_file_policy_matrix(generator: Any) -> bool:
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-file-policy-",
        dir=os.path.realpath(tempfile.gettempdir()),
    ) as temporary:
        root = pathlib.Path(temporary)
        source = root / "source.json"
        hardlink = root / "hardlink.json"
        symlink = root / "symlink.json"
        source.write_bytes(b'{"fixture":true}\n')
        os.link(source, hardlink)
        os.symlink(source.name, symlink)
        for relative in (hardlink.name, symlink.name):
            try:
                generator.open_relative_regular(str(root), relative, "FIXTURE_FILE")
            except generator.GenerationError:
                continue
            return False
    return True


def cli_privacy_matrix(root: pathlib.Path, generator: Any) -> bool:
    source = root / GENERATOR_RELATIVE
    private_token = os.sep + "Users" + os.sep + "FixtureSecret" + os.sep + "private"
    unknown = subprocess.run(
        ["/usr/bin/python3", "-I", "-S", "-B", str(source), "--unknown", private_token],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    combined = unknown.stdout + unknown.stderr
    if unknown.returncode != 10 or private_token.encode("utf-8") in combined:
        return False
    if unknown.stderr != b"gov01-static-envelope-generation-v1: error: arguments-invalid\n":
        return False
    valid_gen = "GOV01-GEN-20260821-" + "e" * 64
    try:
        parsed = generator.parser().parse_args(
            [
                "generate",
                "--receipt-digest",
                private_token,
                "--approval-challenge",
                valid_gen,
            ]
        )
    except SystemExit:
        return False
    if (
        parsed.command != "generate"
        or parsed.receipt_digest != private_token
        or parsed.approval_challenge != valid_gen
    ):
        return False
    try:
        generator.load_approved_generation_request(
            parsed.receipt_digest,
            parsed.approval_challenge,
        )
    except generator.GenerationError as error:
        if (
            error.public_code != "GENERATION_RECEIPT_FORMAT"
            or private_token in error.public_code
        ):
            return False
    else:
        return False
    help_result = subprocess.run(
        ["/usr/bin/python3", "-I", "-S", "-B", str(source), "--help"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    return help_result.returncode == 0 and b"INTERNAL_FAIL_CLOSED" not in help_result.stdout + help_result.stderr


def _run_fixture_checks(root: pathlib.Path) -> Dict[str, Any]:
    generator = load_generator(root)
    host_mode = host_sandbox_capability_mode(generator)
    if host_mode == HOST_SANDBOX_NESTED_REFUSED:
        return {
            "fixture_version": FIXTURE_VERSION,
            "code": "HOST_SANDBOX_CAPABILITY_UNAVAILABLE",
            "ok": False,
            "checks": {},
            "checks_executed": 0,
            "checks_not_run_reason": "outer sandbox refused nested sandbox_init before adapter checks",
            "git_sandbox_validation_mode": HOST_SANDBOX_NESTED_REFUSED,
            "private_read_count": 0,
            "network_call_count": 0,
            "acquisition_execution_count": 0,
            "adapter_matrix_execution_count": 0,
        }
    require(host_mode == "host-sandbox-init-available", "host-sandbox-capability-mode")
    schema = load_json(root / SCHEMA_RELATIVE)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=strict_format_checker(generator))
    baseline = synthetic_envelope(generator)
    generator.validate_generation_envelope(
        baseline,
        dt.datetime(2026, 8, 21, 1, 2, 3, tzinfo=dt.timezone.utc),
        require_pending=True,
    )
    require(schema_accepts(validator, baseline), "positive-schema-instance")
    raw = generator.canonical_json(baseline)
    require(generator.parse_json(raw, "FIXTURE") == baseline, "canonical-roundtrip")
    require(generator.receipt_digest(raw) == generator.receipt_digest(raw), "receipt-stability")

    mutation_results = mutation_rejection_matrix(generator, validator, baseline)
    failed_mutations = [name for name, passed in mutation_results.items() if not passed]
    require(not failed_mutations, "fixture-mutation-" + "-".join(failed_mutations))
    bool_int_mutation_count = bool_int_schema_manual_parity_matrix(
        generator,
        validator,
        baseline,
    )
    captured_refs_bound = captured_refs_contract_matrix(generator)
    captured_ref_limits_bound = captured_ref_limit_pre_adapter_matrix(generator)
    for_each_ref_bound = for_each_ref_observation_matrix(generator)
    ref_boundary_ast_bound = ref_boundary_ast_matrix(root)
    git_argv_closure_bound = generation_git_argv_closure_matrix(root, generator)
    non_head_missing_tip_bound = non_head_missing_tip_adapter_matrix(root, generator)
    linked_worktree_refs_bound = linked_worktree_ref_namespace_matrix(root, generator)
    transition_mode, bound_pure = committed_transition_matrix(root, generator, validator)
    final_delete_capability = git_adapter_final_delete_capability_characterization(generator)
    require(
        final_delete_capability
        == {
            "observed_unsafe": True,
            "supported": False,
            "boundary_declared": True,
            "replacement_preserved": False,
        },
        "git-adapter-final-delete-capability-characterization",
    )
    host_contract_bound = (
        baseline["mutation_scope"]["git_metadata_adapter_trust_boundary"]
        == EXPECTED_GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
        and baseline["mutation_scope"]["git_metadata_adapter_host_assurance"]
        == EXPECTED_GIT_METADATA_ADAPTER_HOST_ASSURANCE_V1
        and baseline["mutation_scope"]["git_metadata_adapter_cleanup_guarantee"]
        == EXPECTED_GIT_METADATA_ADAPTER_CLEANUP_GUARANTEE_V1
        and baseline["privacy"]["git_metadata_adapter_trust_boundary"]
        == EXPECTED_GIT_METADATA_ADAPTER_TRUST_BOUNDARY_V1
    )
    checks = {
        "schema_meta_and_positive": True,
        "canonical_receipt": True,
        "artifact_exact_set": True,
        "runtime_manual_covers_schema_scalar_rejections": scalar_leaf_manual_coverage_matrix(
            generator,
            validator,
            baseline,
        ),
        "bool_int_schema_manual_intersection_parity": bool_int_mutation_count > 0,
        "content_addressed_bound_executor_pure_schema_parity": (
            bound_pure["ok"]
            and bound_pure["bool_int_scalar_type_parity"]["ok"]
            and bound_pure["bool_int_scalar_type_parity"]["mutation_count"] == 145
        ),
        "content_addressed_durable_claim_fd_core": bound_pure["claim_core"]["ok"],
        "path_and_ref_privacy": path_grammar_matrix(schema, generator),
        "final_gen_single_publish_name_binding": final_name_matrix(generator),
        "authenticated_generation_claim_projection": authenticated_claim_projection_matrix(generator),
        "generation_claim_race_branching": claim_race_branch_matrix(generator),
        "production_generation_orchestrator_trace": generation_orchestrator_trace_matrix(generator),
        "production_existing_output_recovery": production_existing_recovery_matrix(generator),
        "exclusive_create_no_overwrite": exclusive_write_matrix(generator),
        "git_control_fail_closed": git_control_matrix(generator),
        "captured_refs_strict_pre_adapter": captured_refs_bound,
        "captured_ref_limits_pre_adapter": captured_ref_limits_bound,
        "for_each_ref_value_equality": for_each_ref_bound,
        "ref_boundary_ast_shape": ref_boundary_ast_bound,
        "generation_git_full_argv_closure": git_argv_closure_bound,
        "non_head_missing_tip_outside_sealed_pack": non_head_missing_tip_bound,
        "linked_worktree_ref_namespaces": linked_worktree_refs_bound,
        "git_adapter_capture_cleanup": git_adapter_capture_cleanup_matrix(generator),
        "git_metadata_adapter_declared_host_contract": host_contract_bound,
        "git_child_temp_parent_namespace_denied": git_child_parent_namespace_denial_matrix(generator),
        "git_reachable_object_minimization": reachable_object_adapter_matrix(generator),
        "committed_micro_transition": transition_mode == HOST_SANDBOX_POSITIVE,
        "receipt_before_git_or_private": receipt_first_matrix(root, generator),
        "regular_file_no_alias": regular_file_policy_matrix(generator),
        "cli_argument_privacy": cli_privacy_matrix(root, generator),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    failure_detail = "fixture-check-" + "-".join(failed_checks)
    if not bound_pure["ok"]:
        failure_detail += (
            "-bound-draft-errors-"
            + str(bound_pure["schema_error_count"])
            + "-"
            + "-".join(bound_pure["schema_error_sections"])
        )
    return {
        "fixture_version": FIXTURE_VERSION,
        "code": "PASS" if not failed_checks else failure_detail,
        "ok": not failed_checks,
        "checks": checks,
        "mutation_count": len(mutation_results),
        "bool_int_mutation_count": bool_int_mutation_count,
        "bound_executor_pure_contract": bound_pure,
        "git_adapter_final_delete_capability_characterization": final_delete_capability,
        "git_sandbox_validation_mode": transition_mode,
        "private_read_count": 0,
        "network_call_count": 0,
        "acquisition_execution_count": 0,
    }


def count_production_mode_events(
    events: Sequence[Tuple[str, ...]],
    generator_source: pathlib.Path,
) -> int:
    source = str(generator_source)
    count = 0
    for argv in events:
        for index, value in enumerate(argv[:-1]):
            if value == source and argv[index + 1] in ("issue", "generate"):
                count += 1
    return count


def run() -> Dict[str, Any]:
    root = derive_repo_root()
    subprocess_events: List[Tuple[str, ...]] = []
    original_run = subprocess.run

    def recording_run(argv: Any, *args: Any, **kwargs: Any) -> Any:
        if not isinstance(argv, (list, tuple)):
            raise FixtureFailure("subprocess-argv-unrecordable")
        normalized: List[str] = []
        for value in argv:
            try:
                item = os.fspath(value)
            except TypeError as error:
                raise FixtureFailure("subprocess-argv-unrecordable") from error
            if not isinstance(item, str):
                raise FixtureFailure("subprocess-argv-unrecordable")
            normalized.append(item)
        subprocess_events.append(tuple(normalized))
        return original_run(argv, *args, **kwargs)

    subprocess.run = recording_run
    try:
        report = _run_fixture_checks(root)
    finally:
        subprocess.run = original_run
    production_mode_execution_count = count_production_mode_events(
        subprocess_events,
        root / GENERATOR_RELATIVE,
    )
    require(production_mode_execution_count == 0, "production-mode-subprocess-executed")
    report["production_mode_execution_count"] = production_mode_execution_count
    return report


def parser() -> PrivacySafeParser:
    result = PrivacySafeParser(prog="gov01-static-envelope-generation-hostile-fixtures-v1")
    result.add_argument("--version", action="version", version=FIXTURE_VERSION)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        parser().parse_args(argv)
        report = run()
        sys.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return 0 if report.get("ok") is True else 1
    except SystemExit:
        raise
    except FixtureFailure as error:
        code = str(error)
        if not code.replace("-", "").replace("_", "").isalnum():
            code = "fixture-contract"
        sys.stdout.write(json.dumps({"code": code, "ok": False}, sort_keys=True, separators=(",", ":")) + "\n")
        return 1
    except BaseException as error:
        error_type = type(error).__name__
        if not error_type.isalnum():
            error_type = "Exception"
        public_code = getattr(error, "public_code", "")
        if not isinstance(public_code, str) or not public_code.replace("_", "").isalnum():
            public_code = "UNCLASSIFIED"
        sys.stdout.write(
            json.dumps(
                {"code": "FIXTURE_FAIL_CLOSED_" + error_type + "_" + public_code, "ok": False},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
