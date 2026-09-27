"""Rules engine + zero-trust scoring unit tests (no DB, no network)."""

from __future__ import annotations

from app.providers.demo import DEMO_DISCLAIMER, DemoProvider
from app.providers.schemas import GenerationRequest
from app.services import security_rules, zerotrust


def _assets() -> list[tuple[str, str, str]]:
    request = GenerationRequest(
        project_name="Rules Test",
        cloud_target="azure",
        environment="production",
        region="eastus",
        availability_requirement="high-availability",
        compliance_framework="soc2",
    )
    result = DemoProvider().generate(request)
    return [(a.asset_type, a.file_name, a.content) for a in result.assets]


def test_rules_fire_on_demo_assets() -> None:
    findings = security_rules.scan_assets(_assets())
    titles = [f["title"] for f in findings]
    # Every rules-engine finding is labeled and prefixed.
    assert findings
    assert all(t.startswith("Rule: ") for t in titles)
    assert all(
        "Automated guidance, not a formal security audit." in f["description"]
        for f in findings
    )
    severities = {f["severity"] for f in findings}
    assert severities <= {"critical", "high", "medium", "low", "informational"}


def test_rules_detect_unrestricted_ingress() -> None:
    findings = security_rules.scan_assets(
        [("terraform", "main.tf", 'cidr_blocks = ["0.0.0.0/0"]')]
    )
    critical = [f for f in findings if f["severity"] == "critical"]
    assert any("0.0.0.0/0" in f["title"] for f in critical)


def test_rules_detect_hardcoded_secret() -> None:
    findings = security_rules.scan_assets(
        [("terraform", "main.tf", 'admin_password = "SuperSecret123"')]
    )
    assert any(f["rule_id"] == "hardcoded-secret" for f in findings)


def test_rules_missing_control_fires_when_absent() -> None:
    findings = security_rules.scan_assets([("readme", "README.md", "hello world")])
    assert any(f["rule_id"] == "missing-encryption" for f in findings)
    assert any(f["rule_id"] == "missing-backup" for f in findings)


def test_rules_missing_control_silent_when_present() -> None:
    findings = security_rules.scan_assets(
        [
            (
                "terraform",
                "main.tf",
                "# encryption at rest with TLS and backup snapshots and tags",
            )
        ]
    )
    assert not any(f["rule_id"] == "missing-encryption" for f in findings)
    assert not any(f["rule_id"] == "missing-backup" for f in findings)


def test_merge_dedupes_by_title() -> None:
    ai = [
        {
            "severity": "high",
            "title": "Weak TLS",
            "description": "d",
            "recommendation": "r",
        },
        {
            "severity": "low",
            "title": "Unique AI finding",
            "description": "d",
            "recommendation": "r",
        },
    ]
    rules = [
        {
            "severity": "high",
            "title": "weak  tls",
            "description": "d2",
            "recommendation": "r2",
            "rule_id": "x",
        },
    ]
    merged = security_rules.merge_findings(ai, rules)
    assert len(merged) == 2
    assert {f["title"] for f in merged} == {"Weak TLS", "Unique AI finding"}


def test_zero_trust_scores_clamped_and_averaged() -> None:
    findings = [
        {
            "severity": "critical",
            "title": "network ingress open",
            "description": "",
            "recommendation": "close it",
        },
        {
            "severity": "critical",
            "title": "more network exposure",
            "description": "network",
            "recommendation": "fix",
        },
        {
            "severity": "critical",
            "title": "network again",
            "description": "network",
            "recommendation": "fix",
        },
        {
            "severity": "critical",
            "title": "network wide open",
            "description": "network",
            "recommendation": "fix",
        },
        {
            "severity": "critical",
            "title": "network fully open",
            "description": "network",
            "recommendation": "fix",
        },
    ]
    scores = zerotrust.compute_zero_trust(findings)
    assert scores["network_score"] == 0  # clamped
    assert scores["identity_score"] == 100
    expected_overall = round(
        (
            scores["identity_score"]
            + scores["network_score"]
            + scores["data_score"]
            + scores["workload_score"]
        )
        / 4
    )
    assert scores["overall_score"] == expected_overall
    assert scores["recommendations"]


def test_finalize_result_merges_rule_findings() -> None:
    """The generation service merges rules-engine findings into persisted output."""
    from app.providers.schemas import GeneratedFile, StructuredGenerationResult
    from app.services.generation_service import _finalize_result

    result = StructuredGenerationResult(
        summary="s",
        assumptions=["a"],
        architecture={
            "overview": "o",
            "components": [{"name": "c", "purpose": "p"}],
            "traffic_flow": ["t"],
        },
        assets=[
            GeneratedFile(
                asset_type="terraform",
                file_name="main.tf",
                language="hcl",
                content='ingress {\n  cidr_blocks = ["0.0.0.0/0"]\n}\n',
            )
        ],
        security_findings=[
            {
                "severity": "low",
                "title": "AI note",
                "description": "d",
                "recommendation": "r",
            }
        ],
        zero_trust={
            "identity_score": 90,
            "network_score": 90,
            "data_score": 90,
            "workload_score": 90,
            "overall_score": 90,
            "recommendations": ["r"],
        },
        cost_guidance={
            "disclaimer": "d",
            "cost_drivers": ["c"],
            "optimization_recommendations": ["o"],
        },
    )
    finalized = _finalize_result(result)
    titles = [f.title for f in finalized.security_findings]
    assert "AI note" in titles
    assert any(t.startswith("Rule: ") and "0.0.0.0/0" in t for t in titles)
    assert finalized.zero_trust.network_score < 90  # critical finding reduced the score


def test_demo_provider_disclaimer_everywhere() -> None:
    for _, _, content in _assets():
        assert DEMO_DISCLAIMER in content


def test_demo_provider_all_asset_types() -> None:
    from app.providers.schemas import ASSET_TYPES

    assets = _assets()
    present = {t for t, _, _ in assets}
    assert set(ASSET_TYPES) <= present
    assert all(content.strip() for _, _, content in assets)
