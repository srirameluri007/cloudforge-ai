"""Static security rules engine.

Scans the concatenated generated-asset contents with regexes and produces
findings shaped like the provider contract's SecurityFinding. All UI-visible
output is labeled: "Automated guidance, not a formal security audit."
Rules-engine findings get the title prefix "Rule: ".

Severity levels: critical | high | medium | low | informational.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

GUIDANCE_LABEL = "Automated guidance, not a formal security audit."


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    title: str
    description: str
    recommendation: str
    pattern: re.Pattern[str]
    # If True, the finding fires when the pattern is ABSENT (missing control).
    missing_control: bool = False


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


RULES: list[Rule] = [
    Rule(
        rule_id="unrestricted-ingress",
        severity="critical",
        title="Rule: Unrestricted ingress (0.0.0.0/0)",
        description=(f"A network rule allows ingress from 0.0.0.0/0. {GUIDANCE_LABEL}"),
        recommendation="Restrict ingress to known CIDR ranges or private network space.",
        pattern=_rx(r"0\.0\.0\.0/0"),
    ),
    Rule(
        rule_id="hardcoded-secret",
        severity="critical",
        title="Rule: Possible hardcoded secret",
        description=(
            f"Content matches a hardcoded-secret pattern (e.g. password=..., "
            f"api_key assignment, or a private key block). {GUIDANCE_LABEL}"
        ),
        recommendation="Move the value to a managed vault and reference it via managed identity.",
        pattern=_rx(
            r"(password|passwd|pwd|api[-_]?key|secret)\s*[:=]\s*['\"]?[^\s'\"]{4,}"
            r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            r"|\bAKIA[0-9A-Z]{16}\b"
        ),
    ),
    Rule(
        rule_id="public-access",
        severity="high",
        title="Rule: Public access enabled",
        description=(
            f"A resource appears to allow public access (public network access "
            f"enabled, public IP, or public ingress). {GUIDANCE_LABEL}"
        ),
        recommendation="Disable public access and use private endpoints for data services.",
        pattern=_rx(
            r"public[-_]?network[-_]?access\s*[:=]\s*['\"]?(enabled|true)"
            r"|associate[-_]?public[-_]?ip\s*[:=]\s*true"
            r"|\bpublic-ip\b"
        ),
    ),
    Rule(
        rule_id="broad-iam",
        severity="high",
        title="Rule: Overly broad IAM permissions",
        description=(
            f"An IAM statement grants wildcard actions or admin-level roles. "
            f"{GUIDANCE_LABEL}"
        ),
        recommendation="Scope permissions to the minimum actions and resources required.",
        pattern=_rx(
            r'"Action"\s*:\s*"[^"]*\*"|actions\s*:\s*\[[^\]]*\*|role[-_]?definition[-_]?names?\s*[:=].*owner|Owner\b.*role'
        ),
    ),
    Rule(
        rule_id="missing-encryption",
        severity="high",
        title="Rule: Missing encryption guidance",
        description=(
            f"No mention of encryption at rest or in transit was found. {GUIDANCE_LABEL}"
        ),
        recommendation="Document encryption at rest (customer-managed keys where required) and TLS in transit.",
        pattern=_rx(r"encrypt|tls|ssl|customer-managed|cmk"),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-private-endpoint",
        severity="high",
        title="Rule: Missing private endpoint guidance",
        description=(
            f"No private endpoint or private-link configuration was found. {GUIDANCE_LABEL}"
        ),
        recommendation="Add private endpoints for data services and disable public network access.",
        pattern=_rx(r"private[-_ ]?endpoint|private[-_ ]?link|privateendpoint"),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-network-controls",
        severity="medium",
        title="Rule: Missing network controls",
        description=(
            f"No network security group, firewall, or network policy was found. "
            f"{GUIDANCE_LABEL}"
        ),
        recommendation="Add NSGs / security groups / network policies with default-deny posture.",
        pattern=_rx(
            r"network[-_ ]?security[-_ ]?group|security[-_ ]?group|firewall|network[-_ ]?policy|nsg\b"
        ),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-monitoring",
        severity="medium",
        title="Rule: Missing monitoring guidance",
        description=(
            f"No logging, metrics, or alerting configuration was found. {GUIDANCE_LABEL}"
        ),
        recommendation="Ship logs and metrics to a central workspace and alert on key signals.",
        pattern=_rx(
            r"log[-_ ]?analytics|monitor|alert|diagnostic|observability|metrics"
        ),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-backup",
        severity="medium",
        title="Rule: Missing backup guidance",
        description=(
            f"No backup or disaster-recovery guidance was found. {GUIDANCE_LABEL}"
        ),
        recommendation="Define backup schedules, retention, and tested restore procedures.",
        pattern=_rx(r"backup|disaster[-_ ]?recovery|point-in-time|snapshot|restore"),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-managed-identity",
        severity="medium",
        title="Rule: Missing managed identity",
        description=(f"No managed identity usage was found. {GUIDANCE_LABEL}"),
        recommendation="Use managed identities instead of connection strings or keys.",
        pattern=_rx(
            r"managed[-_ ]?identity|user[-_ ]?assigned|system[-_ ]?assigned|workload[-_ ]?identity"
        ),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-tagging",
        severity="low",
        title="Rule: Missing tagging guidance",
        description=(
            f"No resource tagging (project/environment/cost-center) was found. "
            f"{GUIDANCE_LABEL}"
        ),
        recommendation="Tag all resources for ownership, environment, and cost attribution.",
        pattern=_rx(r"\btags?\b\s*[:=]|\"tags\"|tag:"),
        missing_control=True,
    ),
    Rule(
        rule_id="missing-ha",
        severity="low",
        title="Rule: Missing high-availability consideration",
        description=(
            f"No availability-zone, multi-AZ, or replica guidance was found. "
            f"{GUIDANCE_LABEL}"
        ),
        recommendation="Document zone redundancy and replica counts for production.",
        pattern=_rx(
            r"availability[-_ ]?zone|multi[-_ ]?az|zone[-_ ]?redundant|replicas|high[-_ ]?availability"
        ),
        missing_control=True,
    ),
]


def scan_assets(assets: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    """Scan (asset_type, file_name, content) triples; return findings dicts.

    A rule with missing_control=True fires only when its pattern is absent from
    the concatenated contents; others fire when the pattern is present.
    """
    combined = "\n".join(content for _, _, content in assets)
    findings: list[dict[str, str]] = []
    for rule in RULES:
        matched = bool(rule.pattern.search(combined))
        fires = (not matched) if rule.missing_control else matched
        if fires:
            findings.append(
                {
                    "severity": rule.severity,
                    "title": rule.title,
                    "description": rule.description,
                    "recommendation": rule.recommendation,
                    "rule_id": rule.rule_id,
                }
            )
    return findings


def merge_findings(
    ai_findings: list[dict[str, str]], rule_findings: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Merge AI and rules findings, deduping on normalized title."""
    merged: list[dict[str, str]] = []
    seen: set[str] = set()

    def _key(title: str) -> str:
        return re.sub(r"\s+", " ", title.strip().lower())

    for finding in list(ai_findings) + list(rule_findings):
        key = _key(finding.get("title", ""))
        if key and key not in seen:
            seen.add(key)
            merged.append(
                {
                    "severity": finding.get("severity", "informational"),
                    "title": finding.get("title", ""),
                    "description": finding.get("description", ""),
                    "recommendation": finding.get("recommendation", ""),
                }
            )
    return merged
