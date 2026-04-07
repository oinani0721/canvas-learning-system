#!/usr/bin/env python3
# scripts/test-a11-end-to-end.py
# A11 KG-Relevance end-to-end user-observable verification driver
# openspec change: fix-fr-kg-04-schema-drift-and-sync-hardening (A11)
"""A11 KG-Relevance end-to-end verification — **user-observable** report.

A11 is the user's real complaint: "the exam node-selection algorithm is
fabricated". Root cause was schema drift between SyncService writes
(``{id}`` + ``canvasId``) and ``_get_kg_relevance`` queries (``{uuid}`` +
``canvas_id``), producing a silent constant ``0.5`` fallback for every
node. 30% of the exam priority weight was dead, but no log ever said so.

The fix is invisible in the UI (exam API does not expose ``kg_relevance``).
This driver translates the log numbers into a Rich-formatted comparison
report so a human can *see* the fix working:

    1. Seed a test canvas with 5 primary nodes + 8 filler neighbors +
       18 CANVAS_EDGEs, all in the dedicated test Neo4j at port 7692.
    2. Verify the schema has no legacy ``{uuid}`` nodes (negative assertion).
    3. Compute ``kg_relevance`` directly for each primary node.
    4. Simulate 5 sequential picks via ``select_target_node`` (real algo).
    5. Print a counterfactual BEFORE/AFTER table that contrasts the old
       constant-0.5 behavior with the fixed weighted-degree formula.
    6. Cleanup.

The thing *under test* (``_get_kg_relevance``) uses **real Neo4j data**.
Orthogonal dependencies (``_get_mastery_data`` and ``_get_canvas_nodes``)
are stubbed so ``kg_relevance`` becomes the only variable — this amplifies
the A11 fix's observable effect to the single dimension it actually changes.

Usage
-----
    cd /Users/Heishing/Desktop/canvas/canvas-learning-system
    docker compose --profile test up -d neo4j-test
    # Wait ~20s for healthcheck
    backend/.venv/bin/python scripts/test-a11-end-to-end.py

Exit codes
----------
    0 — A11 FIX VERIFIED (all assertions pass)
    1 — assertion failed or Neo4j unreachable

Not to be confused with the pytest regression variant at
``backend/tests/e2e/test_a11_kg_relevance_e2e.py`` — this script is the
*user-facing* report; the pytest file is the CI regression guard.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or backend/ without PYTHONPATH
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# Test Neo4j environment — MUST be set before any ``app.*`` import so the
# pydantic Settings instance picks up the test URI instead of the product
# URI (port 7691) from .env.
# ---------------------------------------------------------------------------
TEST_NEO4J_URI = "bolt://localhost:7692"
TEST_NEO4J_USER = "neo4j"
TEST_NEO4J_PASSWORD = "testpassword"
TEST_CANVAS_ID = "a11-test-canvas"

os.environ["NEO4J_URI"] = TEST_NEO4J_URI
os.environ["NEO4J_USER"] = TEST_NEO4J_USER
os.environ["NEO4J_PASSWORD"] = TEST_NEO4J_PASSWORD
os.environ["NEO4J_DATABASE"] = "neo4j"
os.environ["NEO4J_ENABLED"] = "true"

# ---------------------------------------------------------------------------
# Backend imports (AFTER env setup)
# ---------------------------------------------------------------------------
try:
    from app.clients import neo4j_client as neo4j_module
    from app.clients.neo4j_client import Neo4jClient
    from app.models.exam_models import ExamMode, NodePriority
    from app.services.question_generator import QuestionGenerator
except ImportError as exc:  # pragma: no cover - defensive
    print(f"[FATAL] backend imports failed: {exc}", file=sys.stderr)
    print(
        "  Hint: run from the repo root with backend/.venv/bin/python",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError as exc:  # pragma: no cover - defensive
    print(f"[FATAL] rich not installed: {exc}", file=sys.stderr)
    print("  Hint: backend/.venv has rich; activate that venv", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Test fixture design — 5 primary nodes, 8 fillers, 18 edges
#
# All expected kg_relevance values assume the weighted formula:
#     min(1.0, weighted_degree / 8.0)
# where CANVAS_EDGE has weight 1.0. With mastery=0.5 and R=1.0 held
# constant across all 5 primary nodes, kg_relevance becomes the single
# variable driving priority_score. Any regression to the old constant-0.5
# behavior collapses all 5 priorities to 0.35 and this script exits 1.
# ---------------------------------------------------------------------------
PRIMARY_NODE_IDS = ["nodeE", "nodeD", "nodeC", "nodeA", "nodeB"]
FILLER_NODE_IDS = [f"fill-{i}" for i in range(1, 9)]

# (primary_node, edge_count) — the filler neighbors come from FILLER_NODE_IDS[:count]
EDGE_MAP: Dict[str, int] = {
    "nodeA": 0,  # zero edges → empty_graph degraded marker
    "nodeB": 0,  # zero edges → empty_graph degraded marker
    "nodeC": 4,  # 4/8 = 0.5 (same raw score as degraded, but NOT marked)
    "nodeD": 6,  # 6/8 = 0.75
    "nodeE": 8,  # 8/8 = 1.0 (clipped at the normalization cap)
}

EXPECTED: Dict[str, Tuple[float, Optional[str]]] = {
    "nodeA": (0.5, "empty_graph"),
    "nodeB": (0.5, "empty_graph"),
    "nodeC": (0.5, None),
    "nodeD": (0.75, None),
    "nodeE": (1.0, None),
}

# Orthogonal BKT/FSRS dimensions held constant so kg_relevance is the only variable.
STUB_MASTERY: Dict[str, Any] = {
    "p_mastery": 0.5,
    "retrievability": 1.0,
    "effective_proficiency": 0.0,
    "mastery_level": 0.0,
    "mastery_label": "Not Assessed",
}

# Priority formula: 0.4 * (1 - p_mastery) + 0.3 * (1 - R) + 0.3 * kg_relevance
#                 = 0.4 * 0.5 + 0.3 * 0.0 + 0.3 * kg_relevance
#                 = 0.2 + 0.3 * kg_relevance
def _expected_priority(kg_relevance: float) -> float:
    return round(0.2 + 0.3 * kg_relevance, 4)


EXPECTED_SEQUENCE = ["nodeE", "nodeD", "nodeC", "nodeA", "nodeB"]


# ---------------------------------------------------------------------------
# Neo4j test fixture seeding — raw Cypher that mirrors SyncService schema
# exactly. Using raw Cypher (not SyncService.process_sync_batch) avoids the
# settings/driver override dance while producing byte-identical nodes.
# ---------------------------------------------------------------------------
async def _clear_canvas(client: Neo4jClient, canvas_id: str) -> None:
    await client.run_query(
        "MATCH (n:CanvasNode) WHERE n.canvasId = $canvas_id DETACH DELETE n",
        canvas_id=canvas_id,
    )


async def _seed_node(
    client: Neo4jClient, node_id: str, canvas_id: str, title: str
) -> None:
    """Create a CanvasNode with the same label + canonical property keys
    (``id`` + ``canvasId``) that SyncService._upsert_node writes to. The
    createdAt/updatedAt timestamps are intentionally omitted — the A11 fix
    only cares about the label + id + canvasId triple, and keeping the
    Cypher shape simple avoids the Neo4j 5 ``MERGE ... SET ... ON CREATE``
    ordering pitfall.
    """
    await client.run_query(
        """
        MERGE (n:CanvasNode {id: $node_id})
        SET n.title = $title,
            n.content = $content,
            n.canvasId = $canvas_id,
            n.type = 'text',
            n.x = 0,
            n.y = 0,
            n.width = 200,
            n.height = 120
        """,
        node_id=node_id,
        title=title,
        content=f"[a11-e2e] test node {node_id}",
        canvas_id=canvas_id,
    )


async def _seed_edge(
    client: Neo4jClient,
    edge_id: str,
    src_id: str,
    tgt_id: str,
    canvas_id: str,
) -> None:
    """Create a CANVAS_EDGE with the canonical property keys SyncService
    writes. Same rationale as ``_seed_node`` re: dropping the ON CREATE SET
    clause — the A11 fix only cares about (type, canvasId) on the relation.
    """
    await client.run_query(
        """
        MATCH (src:CanvasNode {id: $src_id})
        MATCH (tgt:CanvasNode {id: $tgt_id})
        MERGE (src)-[e:CANVAS_EDGE {id: $edge_id}]->(tgt)
        SET e.canvasId = $canvas_id,
            e.label = ''
        """,
        edge_id=edge_id,
        src_id=src_id,
        tgt_id=tgt_id,
        canvas_id=canvas_id,
    )


async def seed_test_fixture(client: Neo4jClient, canvas_id: str) -> int:
    """Seed the A11 test canvas and return the edge count actually written."""
    await _clear_canvas(client, canvas_id)

    # Primary nodes
    for nid in PRIMARY_NODE_IDS:
        await _seed_node(client, nid, canvas_id, title=f"Primary {nid}")

    # Filler nodes — neighbors for the weighted-degree test
    for fid in FILLER_NODE_IDS:
        await _seed_node(client, fid, canvas_id, title=f"Filler {fid}")

    # Edges: nodeC×4 + nodeD×6 + nodeE×8 = 18
    edge_count = 0
    for primary, count in EDGE_MAP.items():
        for i in range(count):
            filler = FILLER_NODE_IDS[i]
            edge_id = f"e-{primary}-{filler}"
            await _seed_edge(client, edge_id, primary, filler, canvas_id)
            edge_count += 1
    return edge_count


# ---------------------------------------------------------------------------
# Schema verification — negative assertion: no legacy {uuid} nodes remain
# ---------------------------------------------------------------------------
@dataclass
class SchemaProbe:
    canonical_nodes: int  # CanvasNode with non-null {id} + {canvasId}
    legacy_uuid_nodes: int  # CanvasNode with {uuid} property (should be 0)
    edge_count: int  # CANVAS_EDGE in our canvas

    @property
    def ok(self) -> bool:
        return self.legacy_uuid_nodes == 0 and self.canonical_nodes >= len(
            PRIMARY_NODE_IDS
        ) + len(FILLER_NODE_IDS)


async def verify_schema(client: Neo4jClient, canvas_id: str) -> SchemaProbe:
    canonical = await client.run_query(
        """
        MATCH (n:CanvasNode)
        WHERE n.canvasId = $canvas_id AND n.id IS NOT NULL
        RETURN count(n) AS c
        """,
        canvas_id=canvas_id,
    )
    legacy = await client.run_query(
        """
        MATCH (n:CanvasNode)
        WHERE n.canvasId = $canvas_id AND n.uuid IS NOT NULL
        RETURN count(n) AS c
        """,
        canvas_id=canvas_id,
    )
    edges = await client.run_query(
        """
        MATCH ()-[e:CANVAS_EDGE]->()
        WHERE e.canvasId = $canvas_id
        RETURN count(e) AS c
        """,
        canvas_id=canvas_id,
    )
    return SchemaProbe(
        canonical_nodes=int(canonical[0]["c"]) if canonical else 0,
        legacy_uuid_nodes=int(legacy[0]["c"]) if legacy else 0,
        edge_count=int(edges[0]["c"]) if edges else 0,
    )


# ---------------------------------------------------------------------------
# Stubbing strategy — replace orthogonal helpers on the QuestionGenerator
# instance so kg_relevance is the only live variable. This is NOT a mock of
# the thing under test — the real ``_get_kg_relevance`` still hits the real
# test Neo4j via the real singleton client.
# ---------------------------------------------------------------------------
def make_stubbed_question_generator() -> QuestionGenerator:
    qg = QuestionGenerator()

    async def _stub_mastery(node_id: str) -> Dict[str, Any]:
        return dict(STUB_MASTERY)

    async def _stub_canvas_nodes(canvas_id: str) -> List[Dict[str, str]]:
        return [{"id": nid} for nid in PRIMARY_NODE_IDS]

    # Replace bound methods with plain callables — Python binding protocol
    # means these functions receive no ``self`` at call sites.
    qg._get_mastery_data = _stub_mastery  # type: ignore[method-assign]
    qg._get_canvas_nodes = _stub_canvas_nodes  # type: ignore[method-assign]
    return qg


# ---------------------------------------------------------------------------
# Pin the get_neo4j_client singleton to our test client so ``_get_kg_relevance``
# talks to the 7692 test container, not a stray 7691 product singleton left
# over from an earlier test run in the same Python process.
# ---------------------------------------------------------------------------
def pin_test_neo4j_client(test_client: Neo4jClient) -> None:
    def _return_test_client(*args: Any, **kwargs: Any) -> Neo4jClient:
        return test_client

    neo4j_module.get_neo4j_client = _return_test_client  # type: ignore[assignment]
    neo4j_module._client_instance = test_client  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Rendering — Rich tables that make the A11 fix visible to a human
# ---------------------------------------------------------------------------
def render_report(
    console: Console,
    schema: SchemaProbe,
    kg_rows: List[Tuple[str, int, float, float, Optional[str]]],
    sequence: List[NodePriority],
    all_assertions_passed: bool,
) -> None:
    console.print()
    console.rule("[bold cyan]A11 KG-RELEVANCE END-TO-END VERIFICATION[/bold cyan]")
    console.print()

    # --- Test setup summary ---
    setup = Table.grid(padding=(0, 2))
    setup.add_column(style="dim")
    setup.add_column()
    setup.add_row("Canvas", f"[bold]{TEST_CANVAS_ID}[/bold]")
    setup.add_row("Neo4j", f"{TEST_NEO4J_URI} (dedicated test container)")
    setup.add_row("Primary nodes", ", ".join(PRIMARY_NODE_IDS))
    setup.add_row(
        "Holding constant",
        "mastery p=0.5, retrievability R=1.0 (stubbed so kg is the only variable)",
    )
    console.print(Panel(setup, title="[bold]Test Setup[/bold]", border_style="cyan"))

    # --- Schema verification ---
    schema_status = (
        "[green]✅ schema ok[/green]"
        if schema.ok
        else "[red]❌ schema broken[/red]"
    )
    schema_tbl = Table.grid(padding=(0, 2))
    schema_tbl.add_column(style="dim")
    schema_tbl.add_column()
    schema_tbl.add_row(
        "Canonical {id, canvasId} nodes", f"{schema.canonical_nodes}"
    )
    schema_tbl.add_row(
        "Legacy {uuid} nodes",
        f"[red]{schema.legacy_uuid_nodes}[/red]"
        if schema.legacy_uuid_nodes
        else "[green]0[/green]",
    )
    schema_tbl.add_row("CANVAS_EDGE relationships", f"{schema.edge_count}")
    schema_tbl.add_row("Overall", schema_status)
    console.print(
        Panel(
            schema_tbl,
            title="[bold]Schema Verification[/bold]",
            border_style="cyan",
        )
    )

    # --- _get_kg_relevance direct computation table ---
    kg_table = Table(
        title="_get_kg_relevance() — direct computation (real Neo4j query)",
        title_style="bold",
        show_lines=False,
    )
    kg_table.add_column("Node", style="bold")
    kg_table.add_column("Edges", justify="right")
    kg_table.add_column("Expected", justify="right")
    kg_table.add_column("Actual", justify="right")
    kg_table.add_column("Degraded reason")
    for node_id, edges, expected, actual, degraded in kg_rows:
        exp_str = f"{expected:.3f}"
        act_str = f"{actual:.3f}"
        style = "green" if abs(expected - actual) < 1e-6 else "red"
        degraded_display = degraded if degraded else "—"
        if degraded == "empty_graph":
            degraded_display = "[yellow]empty_graph[/yellow]"
        elif degraded == "neo4j_unavailable":
            degraded_display = "[red]neo4j_unavailable[/red]"
        kg_table.add_row(
            node_id,
            str(edges),
            exp_str,
            f"[{style}]{act_str}[/{style}]",
            degraded_display,
        )
    console.print(kg_table)

    # --- select_target_node sequence ---
    seq_table = Table(
        title="select_target_node() — 5 sequential picks (with examined_nodes tracking)",
        title_style="bold",
    )
    seq_table.add_column("Pick", justify="right")
    seq_table.add_column("Node", style="bold")
    seq_table.add_column("priority_score", justify="right")
    seq_table.add_column("kg_relevance", justify="right")
    seq_table.add_column("degraded")
    seq_table.add_column("note", style="dim")
    for i, pick in enumerate(sequence, start=1):
        note = ""
        if pick.kg_relevance_degraded == "empty_graph":
            note = "no edges — degraded fallback"
        elif pick.kg_relevance >= 0.99:
            note = "highest connectivity"
        elif i == 1:
            note = "← first pick"
        deg_cell = (
            f"[yellow]{pick.kg_relevance_degraded}[/yellow]"
            if pick.kg_relevance_degraded
            else "—"
        )
        seq_table.add_row(
            str(i),
            pick.node_id,
            f"{pick.priority_score:.4f}",
            f"{pick.kg_relevance:.3f}",
            deg_cell,
            note,
        )
    console.print(seq_table)

    # --- Counterfactual BEFORE/AFTER panel ---
    before_lines = [
        "[dim]Before fix (kg ≡ 0.5 constant — the A11 bug):[/dim]",
        "  Every node priority = 0.4×0.5 + 0.3×0.0 + 0.3×0.5 = [red]0.35[/red]",
        "  → Identical ties across the board. Selection order is effectively",
        "    the order of the input list (stable sort), not connectivity.",
        "  → 30% of the priority weight is [red]dead code[/red] with no observability.",
        "",
        "[dim]After fix (weighted degree + degraded marker):[/dim]",
        "  nodeE (kg=1.00) → priority [green]0.500[/green] (unique highest)",
        "  nodeD (kg=0.75) → priority [green]0.425[/green]",
        "  nodeC (kg=0.50, degraded=None)       → priority 0.350",
        "  nodeA (kg=0.50, degraded=empty_graph)→ priority 0.350  [yellow](observable fallback)[/yellow]",
        "  nodeB (kg=0.50, degraded=empty_graph)→ priority 0.350  [yellow](observable fallback)[/yellow]",
        "",
        "[bold]The fix produces 3 distinct kg_relevance values (0.5, 0.75, 1.0)[/bold]",
        "[bold]AND preserves fallback observability via kg_relevance_degraded.[/bold]",
    ]
    console.print(
        Panel(
            "\n".join(before_lines),
            title="[bold]Counterfactual — BEFORE vs AFTER[/bold]",
            border_style="cyan",
        )
    )

    # --- Final verdict ---
    if all_assertions_passed:
        console.print(
            Panel(
                Text.from_markup(
                    "[bold green]✅ A11 FIX VERIFIED[/bold green]\n\n"
                    "  ✓ kg_relevance is NOT constant — 3 distinct values observed\n"
                    "  ✓ Selection sequence reflects connectivity ranking (E→D→C→A→B)\n"
                    "  ✓ degraded markers correctly distinguish empty_graph from computed 0.5\n"
                    "  ✓ Schema drift eliminated (0 legacy {uuid} nodes)"
                ),
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                Text.from_markup(
                    "[bold red]❌ A11 VERIFICATION FAILED[/bold red]\n\n"
                    "  Inspect the red cells above. Likely causes:\n"
                    "  • Commit a6da4f7 (Phase 1) not present → kg is still constant 0.5\n"
                    "  • Commit fcd0131 (Phase 6) not present → degraded marker missing\n"
                    "  • Unexpected schema in test Neo4j → rerun after clean seed"
                ),
                border_style="red",
            )
        )


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------
async def main() -> int:
    console = Console()

    # Connect directly (bypass singleton so we control lifecycle)
    test_client = Neo4jClient(
        uri=TEST_NEO4J_URI,
        user=TEST_NEO4J_USER,
        password=TEST_NEO4J_PASSWORD,
        database="neo4j",
    )
    try:
        await test_client.initialize()
    except Exception as exc:
        console.print(
            f"[red][FATAL] cannot reach test Neo4j at {TEST_NEO4J_URI}: {exc}[/red]"
        )
        console.print(
            "[yellow]Hint:[/yellow] docker compose --profile test up -d neo4j-test"
        )
        return 1
    if getattr(test_client, "is_fallback_mode", False):
        console.print(
            "[red][FATAL] Neo4jClient fell back to JSON mode — test Neo4j is down[/red]"
        )
        return 1

    pin_test_neo4j_client(test_client)

    all_passed = True
    try:
        # Step 1 — seed
        edge_count = await seed_test_fixture(test_client, TEST_CANVAS_ID)
        if edge_count != sum(EDGE_MAP.values()):
            console.print(
                f"[red]seeding wrote {edge_count} edges, expected {sum(EDGE_MAP.values())}[/red]"
            )
            all_passed = False

        # Step 2 — schema verification
        schema = await verify_schema(test_client, TEST_CANVAS_ID)
        if not schema.ok:
            all_passed = False

        # Step 3 — direct kg_relevance computation per primary node
        qg = make_stubbed_question_generator()
        kg_rows: List[Tuple[str, int, float, float, Optional[str]]] = []
        for node_id in PRIMARY_NODE_IDS:
            score, degraded = await qg._get_kg_relevance(node_id, TEST_CANVAS_ID)
            expected_score, expected_degraded = EXPECTED[node_id]
            if (
                abs(score - expected_score) > 1e-3
                or degraded != expected_degraded
            ):
                all_passed = False
            kg_rows.append(
                (node_id, EDGE_MAP[node_id], expected_score, score, degraded)
            )

        # Sort kg_rows by expected score DESC for display clarity
        kg_rows.sort(key=lambda r: (-r[2], r[0]))

        # Step 4 — sequential selection simulating 5 user exam rounds
        examined: List[str] = []
        sequence: List[NodePriority] = []
        for _ in range(len(PRIMARY_NODE_IDS)):
            picked = await qg.select_target_node(
                exam_id="a11-e2e",
                source_canvas_id=TEST_CANVAS_ID,
                exam_mode=ExamMode.MIXED,
                examined_nodes=list(examined),
            )
            if picked is None:
                console.print("[red]select_target_node returned None unexpectedly[/red]")
                all_passed = False
                break
            sequence.append(picked)
            examined.append(picked.node_id)

        # Step 5 — assert the exact pick sequence matches the connectivity ranking
        actual_sequence = [p.node_id for p in sequence]
        if actual_sequence != EXPECTED_SEQUENCE:
            console.print(
                f"[red]sequence mismatch — expected {EXPECTED_SEQUENCE}, got {actual_sequence}[/red]"
            )
            all_passed = False

        # Step 6 — assert distinct kg_relevance values (catches regression to constant 0.5)
        distinct_kg = {round(p.kg_relevance, 3) for p in sequence}
        if len(distinct_kg) < 3:
            console.print(
                f"[red]expected ≥3 distinct kg_relevance values, got {sorted(distinct_kg)}[/red]"
            )
            all_passed = False

        # Step 7 — render the user-facing report
        render_report(console, schema, kg_rows, sequence, all_passed)

    finally:
        # Cleanup test data (even on failure)
        try:
            await _clear_canvas(test_client, TEST_CANVAS_ID)
        except Exception:
            pass
        await test_client.cleanup()

    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        exit_code = 130
    sys.exit(exit_code)
