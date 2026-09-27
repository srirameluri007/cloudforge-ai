// Shared TypeScript types mirroring the CloudForge AI backend contract.

export type CloudTarget = "azure" | "aws" | "multi-cloud";
export type Environment = "development" | "test" | "production";
export type AvailabilityRequirement = "standard" | "high-availability" | "multi-region";
export type ComplianceFramework = "none" | "cis" | "nist" | "soc2" | "pci-dss" | "iso27001";
export type GenerationStatus = "pending" | "running" | "succeeded" | "failed";

export type AssetType =
  | "architecture"
  | "terraform"
  | "bicep"
  | "arm"
  | "cloudformation"
  | "kubernetes"
  | "helm"
  | "github-actions"
  | "azure-devops"
  | "jenkins"
  | "gitlab-ci"
  | "deployment"
  | "security"
  | "zero-trust"
  | "cost"
  | "readme";

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string | string[]>;
    request_id?: string;
  };
}

export interface User {
  id: string;
  name: string;
  email: string;
  org_role?: string;
  [key: string]: unknown;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  original_prompt?: string;
  cloud_target: CloudTarget;
  environment: Environment;
  region?: string;
  availability_requirement: AvailabilityRequirement;
  compliance_framework: ComplianceFramework;
  status?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface ProjectListResponse {
  items: Project[];
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  original_prompt?: string;
  cloud_target: CloudTarget;
  environment: Environment;
  region?: string;
  availability_requirement: AvailabilityRequirement;
  compliance_framework: ComplianceFramework;
}

export type ProjectUpdateInput = Partial<ProjectCreateInput>;

export interface Generation {
  id: string;
  project_id: string;
  status: GenerationStatus;
  prompt?: string;
  provider?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface GenerationListResponse {
  items: Generation[];
}

export interface AssetSummary {
  id: string;
  asset_type: AssetType;
  file_name: string;
  language: string;
  content_hash?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface AssetListResponse {
  items: AssetSummary[];
}

export interface Asset extends AssetSummary {
  content: string;
}

export interface AuditEvent {
  id: string;
  action: string;
  actor?: string;
  resource?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface AuditEventListResponse {
  items: AuditEvent[];
}

export interface CredentialReference {
  id: string;
  name: string;
  provider: string;
  auth_type: string;
  vault_reference?: string;
  description?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface CredentialReferenceInput {
  name: string;
  provider: string;
  auth_type: string;
  vault_reference?: string;
  description?: string;
}

export interface AiProviderSettings {
  provider: string;
  configured: boolean;
  demo_mode: boolean;
}

export interface HealthResponse {
  status: string;
}

export interface SeverityFinding {
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description?: string;
}

export interface SecurityReport {
  findings: SeverityFinding[];
}

export interface ZeroTrustScore {
  identity: number;
  network: number;
  data: number;
  workload: number;
  overall: number;
  recommendations?: string[];
}
