# Canvas Learning System - Routing Accuracy Benchmark
# Story 33.5: Agent Routing Engine
# [Source: docs/stories/33.5.story.md]
"""
Accuracy benchmark for Agent Routing Engine.

Test Requirements (AC6):
- Test dataset of 50+ canonical node texts
- Measure precision/recall per Agent type
- Assert overall accuracy >= 80%

Run benchmark:
    cd backend && pytest tests/benchmark/test_routing_accuracy.py -v
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from app.models.agent_routing_models import RoutingRequest
from app.services.agent_routing_engine import AgentRoutingEngine


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def routing_engine():
    """Fresh routing engine for benchmark."""
    return AgentRoutingEngine()


@pytest.fixture
def benchmark_dataset() -> List[Dict]:
    """Load benchmark dataset from fixture file."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "routing_benchmark_dataset.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["examples"]


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════


def calculate_metrics(
    predictions: List[str],
    labels: List[str],
    agent_names: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate precision, recall, and F1 per agent type.

    Args:
        predictions: List of predicted agent names
        labels: List of expected agent names
        agent_names: List of all agent names

    Returns:
        Dict mapping agent_name -> {precision, recall, f1}
    """
    metrics = {}

    for agent in agent_names:
        # True positives, false positives, false negatives
        tp = sum(1 for p, l in zip(predictions, labels) if p == agent and l == agent)
        fp = sum(1 for p, l in zip(predictions, labels) if p == agent and l != agent)
        fn = sum(1 for p, l in zip(predictions, labels) if p != agent and l == agent)

        # Calculate precision
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # Calculate recall
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # Calculate F1
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[agent] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
        }

    return metrics


def calculate_overall_accuracy(predictions: List[str], labels: List[str]) -> float:
    """Calculate overall accuracy."""
    if not labels:
        return 0.0
    correct = sum(1 for p, l in zip(predictions, labels) if p == l)
    return correct / len(labels)


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRoutingAccuracy:
    """Test routing accuracy on benchmark dataset."""

    def test_overall_accuracy_at_least_80_percent(
        self,
        routing_engine: AgentRoutingEngine,
        benchmark_dataset: List[Dict]
    ):
        """Test overall routing accuracy >= 80% (AC6)."""
        predictions = []
        labels = []

        for example in benchmark_dataset:
            request = RoutingRequest(
                node_id=example["id"],
                node_text=example["text"]
            )
            result = routing_engine.route_single_node(request)
            predictions.append(result.recommended_agent)
            labels.append(example["expected_agent"])

        accuracy = calculate_overall_accuracy(predictions, labels)

        # Print detailed results for debugging
        print(f"\n{'='*60}")
        print(f"ROUTING ACCURACY BENCHMARK RESULTS")
        print(f"{'='*60}")
        print(f"Total examples: {len(benchmark_dataset)}")
        print(f"Correct predictions: {sum(1 for p, l in zip(predictions, labels) if p == l)}")
        print(f"Overall accuracy: {accuracy:.2%}")
        print(f"{'='*60}")

        # Assert >= 80% accuracy
        assert accuracy >= 0.80, f"Accuracy {accuracy:.2%} is below 80% threshold"

    def test_per_agent_precision_recall(
        self,
        routing_engine: AgentRoutingEngine,
        benchmark_dataset: List[Dict]
    ):
        """Test per-agent precision and recall metrics."""
        predictions = []
        labels = []

        for example in benchmark_dataset:
            request = RoutingRequest(
                node_id=example["id"],
                node_text=example["text"]
            )
            result = routing_engine.route_single_node(request)
            predictions.append(result.recommended_agent)
            labels.append(example["expected_agent"])

        # Get unique agents
        agent_names = list(set(labels))

        metrics = calculate_metrics(predictions, labels, agent_names)

        # Print per-agent metrics
        print(f"\n{'='*80}")
        print(f"PER-AGENT METRICS")
        print(f"{'='*80}")
        print(f"{'Agent':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'TP':>5} {'FP':>5} {'FN':>5}")
        print(f"{'-'*80}")

        for agent in sorted(agent_names):
            m = metrics[agent]
            print(
                f"{agent:<25} {m['precision']:>10.2%} {m['recall']:>10.2%} "
                f"{m['f1']:>10.2%} {m['true_positives']:>5} "
                f"{m['false_positives']:>5} {m['false_negatives']:>5}"
            )

        print(f"{'='*80}")

        # Verify each agent has reasonable precision/recall
        for agent, m in metrics.items():
            # Allow some flexibility - agents should have at least 50% recall
            # to ensure patterns are working
            if m["true_positives"] + m["false_negatives"] > 0:
                assert m["recall"] >= 0.50, \
                    f"Agent '{agent}' has recall {m['recall']:.2%} < 50%"

    def test_benchmark_dataset_has_50_plus_examples(
        self,
        benchmark_dataset: List[Dict]
    ):
        """Test benchmark dataset has at least 50 examples (AC6)."""
        assert len(benchmark_dataset) >= 50, \
            f"Dataset has only {len(benchmark_dataset)} examples, need at least 50"

    def test_benchmark_covers_all_pattern_types(
        self,
        benchmark_dataset: List[Dict]
    ):
        """Test benchmark covers all 6 pattern categories."""
        expected_agents = {
            "oral-explanation",
            "comparison-table",
            "clarification-path",
            "example-teaching",
            "memory-anchor",
            "deep-decomposition",
        }

        actual_agents = {ex["expected_agent"] for ex in benchmark_dataset}

        missing = expected_agents - actual_agents
        assert not missing, f"Benchmark missing examples for agents: {missing}"

    def test_misclassified_examples_report(
        self,
        routing_engine: AgentRoutingEngine,
        benchmark_dataset: List[Dict]
    ):
        """Generate report of misclassified examples for debugging."""
        misclassified = []

        for example in benchmark_dataset:
            request = RoutingRequest(
                node_id=example["id"],
                node_text=example["text"]
            )
            result = routing_engine.route_single_node(request)

            if result.recommended_agent != example["expected_agent"]:
                misclassified.append({
                    "id": example["id"],
                    "text": example["text"],
                    "expected": example["expected_agent"],
                    "predicted": result.recommended_agent,
                    "confidence": result.confidence,
                    "patterns_matched": result.patterns_matched,
                })

        if misclassified:
            print(f"\n{'='*80}")
            print(f"MISCLASSIFIED EXAMPLES ({len(misclassified)} total)")
            print(f"{'='*80}")

            for m in misclassified[:10]:  # Limit to first 10
                print(f"\nID: {m['id']}")
                print(f"Text: {m['text'][:50]}...")
                print(f"Expected: {m['expected']}")
                print(f"Predicted: {m['predicted']} (confidence: {m['confidence']:.2f})")
                print(f"Patterns: {m['patterns_matched'][:2]}")

            print(f"\n{'='*80}")

        # This test is informational - doesn't fail
        # But log warning if many misclassified
        if len(misclassified) > len(benchmark_dataset) * 0.2:
            print(f"\n⚠️ WARNING: {len(misclassified)} misclassified examples (>20%)")


class TestConfidenceDistribution:
    """Test confidence score distribution on benchmark."""

    def test_high_confidence_rate(
        self,
        routing_engine: AgentRoutingEngine,
        benchmark_dataset: List[Dict]
    ):
        """Test that most predictions have high confidence."""
        high_conf_count = 0
        total = len(benchmark_dataset)

        for example in benchmark_dataset:
            request = RoutingRequest(
                node_id=example["id"],
                node_text=example["text"]
            )
            result = routing_engine.route_single_node(request)

            if result.confidence >= 0.70:
                high_conf_count += 1

        high_conf_rate = high_conf_count / total if total > 0 else 0

        print(f"\nHigh confidence rate (>=0.70): {high_conf_rate:.2%}")

        # At least 70% should have high confidence
        assert high_conf_rate >= 0.70, \
            f"Only {high_conf_rate:.2%} of predictions have high confidence"

    def test_average_confidence(
        self,
        routing_engine: AgentRoutingEngine,
        benchmark_dataset: List[Dict]
    ):
        """Test average confidence score."""
        confidences = []

        for example in benchmark_dataset:
            request = RoutingRequest(
                node_id=example["id"],
                node_text=example["text"]
            )
            result = routing_engine.route_single_node(request)
            confidences.append(result.confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        print(f"\nAverage confidence: {avg_confidence:.2%}")

        # Average should be at least 0.75
        assert avg_confidence >= 0.75, \
            f"Average confidence {avg_confidence:.2%} is below 75%"
