import { useState } from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Tabs from "@/components/Tabs";
import { CodeAssetView, SecurityReportView, ZeroTrustView } from "@/components/ReportViews";
import type { AssetSummary } from "@/lib/types";

const terraformSummary: AssetSummary = {
  id: "asset-tf",
  asset_type: "terraform",
  file_name: "main.tf",
  language: "HCL",
};

const securitySummary: AssetSummary = {
  id: "asset-sec",
  asset_type: "security",
  file_name: "security.json",
  language: "JSON",
};

const zerotrustSummary: AssetSummary = {
  id: "asset-zt",
  asset_type: "zero-trust",
  file_name: "zero-trust.json",
  language: "JSON",
};

const TERRAFORM_CONTENT = 'resource "azurerm_virtual_network" "main" {\n  name = "vnet-demo"\n}';
const SECURITY_CONTENT = JSON.stringify({
  findings: [
    { severity: "high", title: "Public storage account", description: "Storage allows public blob access." },
    { severity: "low", title: "Missing tags", description: "Resources lack cost-center tags." },
  ],
});
const ZEROTRUST_CONTENT = JSON.stringify({
  identity: 85,
  network: 70,
  data: 60,
  workload: 90,
  overall: 76,
  recommendations: ["Enable MFA for all admin accounts."],
});

function TabHarness() {
  const [active, setActive] = useState("terraform");
  return (
    <div>
      <Tabs
        tabs={[
          { key: "terraform", label: "Terraform" },
          { key: "security", label: "Security" },
          { key: "zero-trust", label: "Zero Trust" },
        ]}
        activeKey={active}
        onChange={setActive}
        ariaLabel="Generated asset tabs"
      />
      <div role="tabpanel" aria-label={`${active} panel`}>
        {active === "terraform" && (
          <CodeAssetView summary={terraformSummary} content={TERRAFORM_CONTENT} />
        )}
        {active === "security" && (
          <SecurityReportView summary={securitySummary} content={SECURITY_CONTENT} />
        )}
        {active === "zero-trust" && (
          <ZeroTrustView summary={zerotrustSummary} content={ZEROTRUST_CONTENT} />
        )}
      </div>
    </div>
  );
}

describe("Output tabs", () => {
  it("switches tabs and renders the correct asset content", async () => {
    const user = userEvent.setup();
    render(<TabHarness />);

    // Terraform tab is active by default: code content visible in the editor.
    expect(screen.getByTestId("monaco-editor")).toHaveTextContent(
      'resource "azurerm_virtual_network" "main"',
    );
    expect(screen.getByText("HCL", { selector: "span" })).toBeInTheDocument();

    // Switch to Security: findings grouped by severity.
    await user.click(screen.getByRole("tab", { name: "Security" }));
    expect(screen.getByRole("tab", { name: "Security" })).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText("Public storage account")).toBeInTheDocument();
    expect(screen.getByText("Missing tags")).toBeInTheDocument();
    expect(
      screen.getByText("Automated guidance, not a formal security audit."),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("monaco-editor")).not.toBeInTheDocument();

    // Switch to Zero Trust: score bars and recommendations.
    await user.click(screen.getByRole("tab", { name: "Zero Trust" }));
    expect(screen.getByRole("progressbar", { name: "Identity score" })).toHaveAttribute(
      "aria-valuenow",
      "85",
    );
    expect(screen.getByText("Enable MFA for all admin accounts.")).toBeInTheDocument();

    // Keyboard navigation: ArrowLeft moves back to Security.
    const securityTab = screen.getByRole("tab", { name: "Security" });
    screen.getByRole("tab", { name: "Zero Trust" }).focus();
    await user.keyboard("{ArrowLeft}");
    expect(securityTab).toHaveAttribute("aria-selected", "true");
  });
});
