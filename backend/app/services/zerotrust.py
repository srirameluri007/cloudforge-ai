"""Zero-trust scoring: start at 100 per pillar, subtract per related finding."""

from __future__ import annotations

SEVERITY_PENALTY = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "informational": 1,
}

PILLAR_KEYWORDS: dict[str, list[str]] = {
    "identity": [
        "identity",
        "iam",
        "managed identity",
        "mfa",
        "authentication",
        "credential",
        "secret",
        "access",
    ],
    "network": [
        "network",
        "ingress",
        "endpoint",
        "subnet",
        "firewall",
        "nsg",
        "public",
        "private",
    ],
    "data": ["data", "encrypt", "backup", "storage", "database", "retention"],
    "workload": ["workload", "container", "image", "pod", "vm", "compute", "scan"],
}


def _pillar_for_finding(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    best_pillar = "workload"
    best_hits = 0
    for pillar, keywords in PILLAR_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_pillar = pillar
    return best_pillar


def compute_zero_trust(findings: list[dict[str, str]]) -> dict[str, object]:
    """Return pillar scores 0-100, overall average, and recommendations."""
    penalties: dict[str, int] = {"identity": 0, "network": 0, "data": 0, "workload": 0}
    for finding in findings:
        severity = str(finding.get("severity", "informational")).lower()
        penalty = SEVERITY_PENALTY.get(severity, 1)
        pillar = _pillar_for_finding(
            str(finding.get("title", "")), str(finding.get("description", ""))
        )
        penalties[pillar] += penalty

    scores = {pillar: max(0, 100 - total) for pillar, total in penalties.items()}
    overall = round(sum(scores.values()) / 4)

    recommendations = [
        "Enforce MFA and conditional access for all human access.",
        "Give each workload its own managed identity with least-privilege roles.",
        "Deny inter-subnet traffic by default; allow-list explicitly.",
        "Encrypt data at rest and in transit; manage keys centrally.",
    ]
    for finding in findings[:6]:
        rec = str(finding.get("recommendation", "")).strip()
        if rec and rec not in recommendations:
            recommendations.append(rec)

    return {
        "identity_score": scores["identity"],
        "network_score": scores["network"],
        "data_score": scores["data"],
        "workload_score": scores["workload"],
        "overall_score": overall,
        "recommendations": recommendations[:10],
    }
