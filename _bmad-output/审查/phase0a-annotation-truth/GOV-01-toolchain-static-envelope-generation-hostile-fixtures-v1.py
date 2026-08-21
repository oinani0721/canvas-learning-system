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
import subprocess
import sys
import tempfile
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
    first_write["mutation_scope"]["first_authorized_write"] = "write public output before claim"
    cases["first_write_scope"] = first_write

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


def git_post_preflight_sandbox_matrix(
    generator: Any,
    root: pathlib.Path,
    git_binary: str,
    boundary: Any,
) -> bool:
    """Prove a post-scan include/alternates insertion cannot escape Git."""

    temp_parent = os.path.realpath(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(
        prefix="gov01-generation-external-git-",
        dir=temp_parent,
    ) as external_temporary:
        external_root = pathlib.Path(external_temporary)
        included = external_root / "included.cfg"
        included.write_bytes(b"[core]\n\tbare = false\n")
        os.chmod(included, 0o600)
        run_synthetic_git(root, ["config", "include.path", str(included)])
        try:
            generator.git_scalar(
                git_binary,
                str(root),
                boundary,
                ["rev-parse", "--verify", "HEAD"],
                "GIT_POST_PREFLIGHT_INCLUDE",
            )
        except generator.GenerationError as error:
            if error.public_code != "GIT_POST_PREFLIGHT_INCLUDE_RETURN":
                return False
        else:
            return False
        run_synthetic_git(root, ["config", "--unset-all", "include.path"])

        external_git = external_root / "objects.git"
        external_git.mkdir(mode=0o700)
        run_synthetic_git(external_git, ["init", "--bare", "-q"])
        hashed = subprocess.run(
            [git_binary, "--git-dir", str(external_git), "hash-object", "-w", "--stdin"],
            input=b"synthetic external object\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "LANG": "C"},
            check=False,
            timeout=30,
        )
        if hashed.returncode != 0 or len(hashed.stdout.strip()) not in (40, 64):
            return False
        info = root / ".git/objects/info"
        info.mkdir(mode=0o700, exist_ok=True)
        alternates = info / "alternates"
        alternates.write_bytes((str(external_git / "objects") + "\n").encode("utf-8"))
        os.chmod(alternates, 0o600)
        try:
            generator.run_git(
                git_binary,
                str(root),
                boundary,
                ["cat-file", "-t", hashed.stdout.strip().decode("ascii")],
                "GIT_POST_PREFLIGHT_ALTERNATES",
            )
        except generator.GenerationError as error:
            if error.public_code != "GIT_POST_PREFLIGHT_ALTERNATES_RETURN":
                return False
        else:
            return False
        alternates.unlink()
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


def committed_transition_matrix(root: pathlib.Path, generator: Any, validator: Draft202012Validator) -> str:
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
        try:
            baseline = synthetic_generator.repository_baseline(str(synthetic_root))
        except BaseException as error:
            # Distinguish an outer host which refuses every nested sandbox_init
            # from a malformed product profile.  Only the former is an
            # expected fail-closed validation mode.
            if getattr(error, "public_code", None) == "GIT_HEAD_SANDBOX_INIT":
                try:
                    synthetic_generator.run_process(
                        ["/usr/bin/true"],
                        "MINIMAL_SANDBOX",
                        sandbox_profile=b"(version 1)\n(allow default)\n",
                    )
                except synthetic_generator.GenerationError as minimal_error:
                    if minimal_error.public_code == "MINIMAL_SANDBOX_SANDBOX_INIT":
                        return "nested-host-sandbox-refused-second-sandbox-fail-closed"
                    raise
            raise
        artifacts = synthetic_generator.artifact_observations(str(synthetic_root))
        synthetic_generator.assert_artifacts_match_head(
            baseline["git_binary"],
            str(synthetic_root),
            baseline["git_boundary"],
            artifacts,
        )
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
            and bound_executor.GENERATION_CLAIM_PROFILE == synthetic_generator.GENERATION_CLAIM_PROFILE
            and bound_executor.GENERATION_CLAIM_RECORD_PROFILE
            == synthetic_generator.GENERATION_CLAIM_RECORD_PROFILE
            and bound_executor.GENERATION_CLAIM_RETENTION == synthetic_generator.GENERATION_CLAIM_RETENTION
            and git_post_preflight_sandbox_matrix(
                synthetic_generator,
                synthetic_root,
                baseline["git_binary"],
                baseline["git_boundary"],
            )
        )
        return "host-sandbox-enforced-positive" if positive else "transition-check-failed"


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


def cli_privacy_matrix(root: pathlib.Path) -> bool:
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
    invalid_receipt = subprocess.run(
        [
            "/usr/bin/python3",
            "-I",
            "-S",
            "-B",
            str(source),
            "generate",
            "--receipt-digest",
            private_token,
            "--approval-challenge",
            valid_gen,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    invalid_output = invalid_receipt.stdout + invalid_receipt.stderr
    if (
        invalid_receipt.returncode != 10
        or private_token.encode("utf-8") in invalid_output
        or b"GENERATION_RECEIPT_FORMAT" not in invalid_receipt.stdout
    ):
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


def run() -> Dict[str, Any]:
    root = derive_repo_root()
    generator = load_generator(root)
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
    transition_mode = committed_transition_matrix(root, generator, validator)
    checks = {
        "schema_meta_and_positive": True,
        "canonical_receipt": True,
        "artifact_exact_set": True,
        "runtime_manual_covers_schema_scalar_rejections": scalar_leaf_manual_coverage_matrix(
            generator,
            validator,
            baseline,
        ),
        "path_and_ref_privacy": path_grammar_matrix(schema, generator),
        "final_gen_single_publish_name_binding": final_name_matrix(generator),
        "authenticated_generation_claim_projection": authenticated_claim_projection_matrix(generator),
        "generation_claim_race_branching": claim_race_branch_matrix(generator),
        "production_generation_orchestrator_trace": generation_orchestrator_trace_matrix(generator),
        "production_existing_output_recovery": production_existing_recovery_matrix(generator),
        "exclusive_create_no_overwrite": exclusive_write_matrix(generator),
        "git_control_fail_closed": git_control_matrix(generator),
        "committed_micro_transition": transition_mode
        in (
            "host-sandbox-enforced-positive",
            "nested-host-sandbox-refused-second-sandbox-fail-closed",
        ),
        "receipt_before_git_or_private": receipt_first_matrix(root, generator),
        "regular_file_no_alias": regular_file_policy_matrix(generator),
        "cli_argument_privacy": cli_privacy_matrix(root),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    require(not failed_checks, "fixture-check-" + "-".join(failed_checks))
    return {
        "fixture_version": FIXTURE_VERSION,
        "ok": True,
        "checks": checks,
        "mutation_count": len(mutation_results),
        "git_sandbox_validation_mode": transition_mode,
        "private_read_count": 0,
        "network_call_count": 0,
        "acquisition_execution_count": 0,
    }


def parser() -> PrivacySafeParser:
    result = PrivacySafeParser(prog="gov01-static-envelope-generation-hostile-fixtures-v1")
    result.add_argument("--version", action="version", version=FIXTURE_VERSION)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        parser().parse_args(argv)
        report = run()
        sys.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
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
