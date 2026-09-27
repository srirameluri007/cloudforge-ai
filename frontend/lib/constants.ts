import type { AssetType } from "./types";

// ---------------------------------------------------------------------------
// Enum option lists shown in selects
// ---------------------------------------------------------------------------

export const CLOUD_TARGET_OPTIONS = [
  { value: "azure", label: "Azure" },
  { value: "aws", label: "AWS" },
  { value: "multi-cloud", label: "Multi-cloud" },
] as const;

export const ENVIRONMENT_OPTIONS = [
  { value: "development", label: "Development" },
  { value: "test", label: "Test" },
  { value: "production", label: "Production" },
] as const;

export const AVAILABILITY_OPTIONS = [
  { value: "standard", label: "Standard" },
  { value: "high-availability", label: "High availability" },
  { value: "multi-region", label: "Multi-region" },
] as const;

export const COMPLIANCE_OPTIONS = [
  { value: "none", label: "None" },
  { value: "cis", label: "CIS" },
  { value: "nist", label: "NIST" },
  { value: "soc2", label: "SOC 2" },
  { value: "pci-dss", label: "PCI-DSS" },
  { value: "iso27001", label: "ISO 27001" },
] as const;

export const CREDENTIAL_PROVIDER_OPTIONS = [
  "Azure",
  "AWS",
  "GitHub",
  "GitLab",
  "Azure DevOps",
  "Jenkins",
  "Kubernetes",
  "Terraform Cloud",
] as const;

export const CREDENTIAL_AUTH_TYPE_OPTIONS = [
  "OAuth",
  "API token",
  "Service principal",
  "SSH key",
  "Managed identity",
  "Other",
] as const;

// ---------------------------------------------------------------------------
// Password policy
// ---------------------------------------------------------------------------

export const PASSWORD_MIN_LENGTH = 10;

export function passwordViolations(password: string): string[] {
  const issues: string[] = [];
  if (password.length < PASSWORD_MIN_LENGTH) {
    issues.push(`at least ${PASSWORD_MIN_LENGTH} characters`);
  }
  if (!/[A-Z]/.test(password)) issues.push("an uppercase letter");
  if (!/[a-z]/.test(password)) issues.push("a lowercase letter");
  if (!/\d/.test(password)) issues.push("a digit");
  if (!/[^A-Za-z0-9]/.test(password)) issues.push("a special character");
  return issues;
}

// ---------------------------------------------------------------------------
// Output tabs
//
// Each asset type maps to an output tab. Monaco does not ship built-in
// grammars for HCL (Terraform) or Bicep, so we use the nearest built-in
// language purely for syntax highlighting while the visible badge shows the
// real language label (HCL / Bicep).
// ---------------------------------------------------------------------------

export interface TabDefinition {
  type: AssetType;
  label: string;
  /** Monaco built-in language used for highlighting. */
  monacoLanguage: string;
  /** Human-readable language label shown in the badge. */
  languageLabel: string;
  kind: "code" | "report";
}

export const TAB_DEFINITIONS: TabDefinition[] = [
  { type: "architecture", label: "Architecture", monacoLanguage: "markdown", languageLabel: "Markdown", kind: "code" },
  { type: "terraform", label: "Terraform", monacoLanguage: "ini", languageLabel: "HCL", kind: "code" },
  { type: "bicep", label: "Bicep", monacoLanguage: "javascript", languageLabel: "Bicep", kind: "code" },
  { type: "arm", label: "ARM", monacoLanguage: "json", languageLabel: "JSON", kind: "code" },
  { type: "cloudformation", label: "CloudFormation", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "kubernetes", label: "Kubernetes", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "helm", label: "Helm", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "github-actions", label: "GitHub Actions", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "azure-devops", label: "Azure DevOps", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "jenkins", label: "Jenkins", monacoLanguage: "groovy", languageLabel: "Groovy", kind: "code" },
  { type: "gitlab-ci", label: "GitLab CI", monacoLanguage: "yaml", languageLabel: "YAML", kind: "code" },
  { type: "deployment", label: "Deployment", monacoLanguage: "markdown", languageLabel: "Markdown", kind: "code" },
  { type: "security", label: "Security", monacoLanguage: "markdown", languageLabel: "Report", kind: "report" },
  { type: "zero-trust", label: "Zero Trust", monacoLanguage: "markdown", languageLabel: "Report", kind: "report" },
  { type: "cost", label: "Cost", monacoLanguage: "markdown", languageLabel: "Report", kind: "report" },
  { type: "readme", label: "README", monacoLanguage: "markdown", languageLabel: "Markdown", kind: "code" },
];

export function tabDefinitionFor(type: AssetType): TabDefinition {
  return (
    TAB_DEFINITIONS.find((t) => t.type === type) ?? {
      type,
      label: type,
      monacoLanguage: "plaintext",
      languageLabel: "Text",
      kind: "code" as const,
    }
  );
}

export const PROMPT_MIN_LENGTH = 20;

export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;
