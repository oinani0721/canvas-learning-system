"""FR-KG-04 Phase 3 — record_learning_memory docstring hardening.

LangChain's ``@tool`` decorator serializes the wrapped function's docstring
directly into the tool description that LiteLLM sends to the model for
tool selection. That means the docstring is *already part of the prompt*
the model sees, so hardening the docstring is equivalent to hardening the
tool's runtime description — no separate LLM prompt rewrite needed.

This test pins three invariants on ``record_learning_memory.__doc__``:

1. It contains the literal string ``WRITE OPERATION`` (explicit write-op marker).
2. It contains the literal string ``UNTRUSTED`` (the tag family name the
   model must defer to).
3. It contains the existing ``每次请求最多调用2次`` frequency cap
   (preserved from the pre-hardening version so we don't silently lose
   an established constraint).
4. It contains the literal string ``严禁`` (explicit prohibition clause).

The test imports the tool module lazily to keep transitive import cost
low (pytest-native ``@tool`` wrappers set ``.__doc__`` from the wrapped
function's docstring, so the assertion works on the wrapped object).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def docstring() -> str:
    """Grab record_learning_memory's docstring via the @tool wrapper.

    LangChain's ``@tool`` returns a BaseTool instance whose ``.description``
    mirrors the wrapped function's docstring. Either ``.__doc__`` on the
    BaseTool or ``.description`` can be asserted; we use ``.description``
    because that's what LiteLLM actually reads at tool-selection time.
    """
    from app.services.react_agent import record_learning_memory

    # Prefer .description (what LiteLLM reads) over .__doc__.
    desc = getattr(record_learning_memory, "description", None) or getattr(
        record_learning_memory, "__doc__", ""
    )
    assert desc, (
        "record_learning_memory exposes neither .description nor .__doc__ — "
        "LiteLLM will send an empty tool description to the model, which defeats "
        "the purpose of docstring hardening."
    )
    return desc


def test_docstring_contains_write_operation_marker(docstring: str):
    """Explicit 'WRITE OPERATION' marker so the model treats the tool as
    side-effecting (not read-only) at selection time.
    """
    assert "WRITE OPERATION" in docstring, (
        "record_learning_memory docstring must contain the literal substring "
        "'WRITE OPERATION' so the model knows this tool mutates Neo4j."
    )


def test_docstring_contains_untrusted_reference(docstring: str):
    """Reference to the UNTRUSTED tag family so the model binds the tool's
    precondition to the prompt-injection defense mechanism.
    """
    assert "UNTRUSTED" in docstring, (
        "record_learning_memory docstring must reference the 'UNTRUSTED' tag "
        "family so the model understands it cannot fire on content from "
        "<UNTRUSTED_*> wrapped reference material."
    )


def test_docstring_preserves_frequency_cap(docstring: str):
    """The pre-hardening '每次请求最多调用2次' cap MUST still be present.
    This prevents the hardening rewrite from silently dropping an established
    constraint.
    """
    assert "每次请求最多调用2次" in docstring, (
        "record_learning_memory docstring must preserve the existing "
        "'每次请求最多调用2次' frequency cap — dropping it would silently "
        "weaken a pre-existing constraint."
    )


def test_docstring_contains_prohibition_clause(docstring: str):
    """The docstring must contain an explicit '严禁' (strict prohibition)
    clause so the prohibition is syntactically distinguishable from the
    general advice paragraphs above it.
    """
    assert "严禁" in docstring, (
        "record_learning_memory docstring must contain a '严禁' clause that "
        "explicitly enumerates scenarios where calling the tool is forbidden."
    )


def test_docstring_names_record_learning_memory_itself(docstring: str):
    """Sanity check: the docstring should mention the tool's own name so
    that the model can self-reference when reasoning about whether to
    call it — this is a common prompt-engineering pattern.
    """
    # The docstring refers to the tool name in the prohibition examples.
    assert "record_learning_memory" in docstring, (
        "record_learning_memory docstring should mention its own name "
        "(e.g. in the '严禁' examples) so the model's attention binds the "
        "prohibition to this specific tool."
    )
