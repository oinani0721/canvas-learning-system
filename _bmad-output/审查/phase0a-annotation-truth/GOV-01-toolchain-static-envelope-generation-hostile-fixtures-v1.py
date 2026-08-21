#!/usr/bin/env python3
"""Hostile, public-only contract checks for the GOV-01 generation issuer.

The fixture imports the issuer as source, uses deterministic synthetic contract
values, and writes only inside a temporary directory.  It never invokes
``issue`` or ``generate`` and never resolves any private locator.
"""

import argparse
import copy
import datetime as dt
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
            "git_metadata_adapter_profile": bound_executor.GIT_METADATA_ADAPTER_PROFILE_V3,
            "git_metadata_adapter_cleanup_state": "removed",
            "git_metadata_adapter_residue_count": 0,
            "live_git_control_child_read_count": 0,
            "worktree_tree_exclusions": (
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
        generator.write_exclusive_public_file(str(root), relative, raw)
        path = root / relative
        if path.read_bytes() != raw or (path.stat().st_mode & 0o777) != 0o644:
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
        run_synthetic_git(root, ["commit", "-q", "-m", "fixture-adapter-baseline"])

        # A live ref change after capture must not change the bytes copied from
        # that capture.  Revalidation is a separate operation and will reject
        # the live drift; the adapter never performs a second ref read.
        capture = generator.capture_git_source(str(root))
        _head_oid, head_ref = generator.captured_head_oid(capture)
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
                "GIT_POST_PREFLIGHT_INCLUDE",
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
                "GIT_POST_CAPTURE_ALTERNATES",
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
                "GIT_POST_CAPTURE_CONFIG",
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
                "GIT_POST_CAPTURE_INDEX",
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
                "GIT_POST_CAPTURE_REF",
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
                "GIT_ADAPTER_TAMPER",
            )
        except generator.GenerationError as error:
            if error.public_code != "GIT_ADAPTER_DRIFT":
                return False
        else:
            return False
        finally:
            generator.cleanup_git_metadata_adapter(adapter_boundary)
    return True


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


def reachable_object_adapter_matrix(generator: Any) -> bool:
    """Prove only authorized blobs enter the final sealed object database."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix="gov01-generation-reachable-", dir=temp_parent) as temporary:
        root = pathlib.Path(temporary) / "repo"
        root.mkdir(mode=0o700)
        authorized = root / "authorized.txt"
        unrelated = root / "ordinary-tracked.txt"
        authorized_raw = b"authorized fixture payload\n"
        tracked_secret_raw = b"tracked but unauthorized fixture secret\n"
        dangling_secret_raw = b"dangling unreachable fixture secret\n"
        authorized.write_bytes(authorized_raw)
        unrelated.write_bytes(tracked_secret_raw)
        run_synthetic_git(root, ["init", "-q"])
        run_synthetic_git(root, ["add", "authorized.txt", "ordinary-tracked.txt"])
        run_synthetic_git(root, ["commit", "-q", "-m", "fixture-reachable-baseline"])
        head_oid = run_synthetic_git_output(root, ["rev-parse", "HEAD"]).decode("ascii").strip()
        unrelated_oid = run_synthetic_git_output(
            root, ["rev-parse", "HEAD:ordinary-tracked.txt"]
        ).decode("ascii").strip()
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

        raw_oid_bytes = len(head_oid) // 2
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
                b"100644 Canvas-Vault-secret\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_NAME_PRIVATE_COMPONENT",
            ),
            (
                (b"100644 duplicate\x00" + raw_oid) * 2,
                "GIT_BOOTSTRAP_RAW_TREE_DUPLICATE",
            ),
            (
                b"100644 control-\x01\x00" + raw_oid,
                "GIT_BOOTSTRAP_RAW_TREE_NAME_CONTROL_OR_FORMAT",
            ),
        )
        for hostile_raw, expected_code in hostile_tree_objects:
            try:
                generator.parse_bootstrap_tree_object_entries(hostile_raw, len(head_oid))
            except generator.GenerationError as error:
                require(error.public_code == expected_code, "reachable-hostile-tree-label")
            else:
                return False

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

        generator.os.open = deny_unrelated_pack_open
        try:
            _control, boundary = generator.create_git_metadata_adapter(
                str(root),
                git_binary,
                developer_root,
                required_current_blob_paths=("authorized.txt",),
            )
        finally:
            generator.os.open = original_open
        try:
            expected = set(boundary.expected_object_oids)
            require(
                head_oid in expected and unrelated_oid not in expected and dangling_oid not in expected,
                "reachable-exact-object-set",
            )
            require(generator.git_scalar(
                git_binary,
                str(root),
                boundary,
                ["rev-parse", "--verify", "HEAD"],
                "FIXTURE_REACHABLE_HEAD",
            ) == head_oid, "reachable-head")
            require(generator.run_git(
                git_binary,
                str(root),
                boundary,
                ["show", "HEAD:authorized.txt"],
                "FIXTURE_REACHABLE_AUTHORIZED_BLOB",
            ) == authorized_raw, "reachable-authorized-blob")
            generator.run_git(
                git_binary,
                str(root),
                boundary,
                ["diff-index", "--cached", "--quiet", "HEAD", "--"],
                "FIXTURE_REACHABLE_INDEX",
            )
            for absent_oid in (unrelated_oid, dangling_oid):
                require(not generator.run_git(
                    git_binary,
                    str(root),
                    boundary,
                    ["cat-file", "-e", absent_oid],
                    "FIXTURE_REACHABLE_ABSENT",
                    allowed_returncodes=(1,),
                ), "reachable-absent-blob")
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
                        required_current_blob_paths=("authorized.txt",),
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
        issued = synthetic_generator.utc_now_second()
        challenge = "GOV01-GEN-" + issued.strftime("%Y%m%d") + "-" + "c" * 64
        envelope = synthetic_generator.build_issue_envelope(challenge, issued, baseline, artifacts)
        require(schema_accepts(validator, envelope), "transition-envelope-schema")
        raw = synthetic_generator.canonical_json(envelope)
        micro_relative = synthetic_generator.micro_relative(challenge)
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
