"""Run Murmura upgrade benchmarks and save JSON results.

This lightweight runner is intentionally deterministic and offline-friendly.
It verifies smoke surfaces and fixture-level behavioral quality, then produces
due-diligence artifacts under ``data/benchmarks``.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_FIXTURE_DIR = Path("data/benchmarks/fixtures")


def run_smoke_benchmarks() -> dict[str, Any]:
    """Return deterministic smoke surface benchmark results."""
    checks = [
        _check("graph_rag_correctness", _importable("backend.app.services.graph_rag_query")),
        _check("hidden_actor_discovery", _importable("backend.app.services.implicit_stakeholder_service")),
        _check("agent_generation", _importable("backend.app.services.kg_agent_factory")),
        _check("simulation_memory_loop", _importable("backend.app.services.simulation_memory_graph_loop")),
        _check("report_quality", _importable("backend.app.services.grounded_report")),
        _check("mode_productisation", _importable("backend.app.services.mode_presets")),
        _check("deployment_diagnostics", _importable("backend.app.services.setup_diagnostics")),
    ]
    passed = sum(1 for check in checks if check["passed"])
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "suite": "smoke_surface",
        "layer": "smoke_surface",
        "passed": passed,
        "total": len(checks),
        "score": round(passed / max(1, len(checks)), 3),
        "checks": checks,
    }


def run_gold_behavioral_benchmarks(fixture_dir: Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    """Score fixture-level gold benchmarks for graph/report/pipeline behavior."""
    fixtures = _load_fixtures(fixture_dir)
    results = [_score_fixture(fixture) for fixture in fixtures]
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    score = round(sum(result["overall_score"] for result in results) / max(1, total), 3)
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "suite": "gold_behavioral",
        "layer": "gold_behavioral",
        "fixture_dir": str(fixture_dir),
        "passed": passed,
        "total": total,
        "score": score,
        "fixtures": results,
    }


def run_upgrade_benchmarks(fixture_dir: Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    """Return the two-layer upgrade benchmark result."""
    smoke = run_smoke_benchmarks()
    gold = run_gold_behavioral_benchmarks(fixture_dir)
    layers = {
        "smoke_surface": smoke,
        "gold_behavioral": gold,
    }
    passed = smoke["passed"] == smoke["total"] and gold["passed"] == gold["total"]
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "suite": "upgrade_benchmarks",
        "passed": passed,
        "layers": layers,
    }


def write_result(result: dict[str, Any], output_dir: Path) -> Path:
    """Write benchmark result JSON under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suite = str(result.get("suite", "upgrade_benchmarks"))
    output_path = output_dir / f"{suite}_{stamp}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = output_dir / f"{suite}_latest.json"
    latest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "metric": "capability_surface_present",
        "value": 1.0 if passed else 0.0,
    }


def _importable(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def _load_fixtures(fixture_dir: Path) -> list[dict[str, Any]]:
    if not fixture_dir.exists():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(fixture_dir.glob("*.json"))
    ]


def _score_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    expected = fixture["expected"]
    observed = fixture.get("observed_baseline", {})
    graph = _score_graph_quality(expected, observed)
    hidden = _score_hidden_actor(expected, observed)
    report = _score_report_grounding(expected, observed)
    pipeline = _score_pipeline(observed)
    overall = round(
        graph["score"] * 0.4
        + hidden["score"] * 0.15
        + report["score"] * 0.3
        + pipeline["score"] * 0.15,
        3,
    )
    threshold = float(expected.get("overall_threshold", 0.75))
    return {
        "id": fixture["id"],
        "mode": fixture["mode"],
        "passed": overall >= threshold,
        "overall_score": overall,
        "threshold": threshold,
        "scores": {
            "graph_quality": graph,
            "hidden_actor_behavior": hidden,
            "report_grounding": report,
            "end_to_end": pipeline,
        },
    }


def _score_graph_quality(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    nodes = observed.get("nodes", [])
    edges = observed.get("edges", [])
    required_entities = expected.get("required_entities", [])
    required_relations = expected.get("required_relations", [])

    entity_hits = sum(1 for entity in required_entities if _entity_present(entity, nodes))
    relation_hits = sum(1 for relation in required_relations if _relation_present(relation, edges))
    node_recall = entity_hits / max(1, len(required_entities))
    relation_recall = relation_hits / max(1, len(required_relations))
    node_bound = 1.0 if len(nodes) >= expected.get("node_lower_bound", 0) else 0.0
    edge_bound = 1.0 if len(edges) >= expected.get("edge_lower_bound", 0) else 0.0
    score = round((node_recall * 0.35) + (relation_recall * 0.35) + (node_bound * 0.15) + (edge_bound * 0.15), 3)
    return {
        "score": score,
        "node_recall": round(node_recall, 3),
        "required_relation_hit": round(relation_recall, 3),
        "node_lower_bound_passed": bool(node_bound),
        "edge_lower_bound_passed": bool(edge_bound),
    }


def _score_hidden_actor(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    hidden = " ".join(_node_text(actor) for actor in observed.get("hidden_actors", []))
    expected_terms = expected.get("hidden_actor_expected_behavior", [])
    hits = sum(1 for term in expected_terms if _norm(term) in _norm(hidden))
    score = round(hits / max(1, len(expected_terms)), 3)
    return {"score": score, "hits": hits, "total": len(expected_terms)}


def _score_report_grounding(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    claims = observed.get("report_claims", [])
    grounded = [claim for claim in claims if claim.get("evidence_span")]
    missing_citations = [claim for claim in claims if not claim.get("citation")]
    evidence_ratio = len(grounded) / max(1, len(claims))
    missing_penalty = len(missing_citations) / max(1, len(claims)) * 0.25
    score = round(max(0.0, evidence_ratio - missing_penalty), 3)
    threshold = float(expected.get("report_evidence_coverage_threshold", 0.7))
    return {
        "score": score,
        "evidence_span_ratio": round(evidence_ratio, 3),
        "missing_citation_penalty": round(missing_penalty, 3),
        "threshold": threshold,
        "passed": score >= threshold,
    }


def _score_pipeline(observed: dict[str, Any]) -> dict[str, Any]:
    pipeline = observed.get("pipeline", {})
    checks = {
        "graph_build": bool(pipeline.get("graph_build")),
        "simulation_create": bool(pipeline.get("simulation_create")),
        "report_generate": bool(pipeline.get("report_generate")),
    }
    score = round(sum(1 for value in checks.values() if value) / len(checks), 3)
    return {"score": score, "checks": checks}


def _entity_present(entity: str, nodes: list[dict[str, Any]]) -> bool:
    needle = _norm(entity)
    return any(needle in _norm(_node_text(node)) for node in nodes)


def _relation_present(relation: dict[str, Any], edges: list[dict[str, Any]]) -> bool:
    relation_type = _norm(str(relation.get("relation", "")))
    source = _norm(str(relation.get("source", "")))
    target = _norm(str(relation.get("target", "")))
    for edge in edges:
        edge_text = _norm(" ".join(str(edge.get(key, "")) for key in ("source", "target", "relation_type", "label")))
        if relation_type in edge_text and source in edge_text and target in edge_text:
            return True
    return False


def _node_text(node: dict[str, Any]) -> str:
    return " ".join(str(node.get(key, "")) for key in ("id", "title", "name", "role", "description"))


def _norm(value: str) -> str:
    return value.casefold().strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Murmura upgrade benchmarks")
    parser.add_argument("--output-dir", default="data/benchmarks")
    parser.add_argument("--fixture-dir", default=str(DEFAULT_FIXTURE_DIR))
    args = parser.parse_args()

    result = run_upgrade_benchmarks(Path(args.fixture_dir))
    output_path = write_result(result, Path(args.output_dir))
    print(json.dumps({"success": result["passed"], "output": str(output_path)}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
