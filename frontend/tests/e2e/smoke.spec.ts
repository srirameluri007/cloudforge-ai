import { test, expect } from "@playwright/test";

/**
 * Smoke test for the CloudForge AI full stack.
 *
 * Requires the full stack running: `docker compose up` (backend on
 * http://localhost:8000 with the demo provider enabled) and the frontend
 * dev server on http://localhost:3000 (started automatically via
 * playwright.config.ts webServer unless already running).
 *
 * NOT run in CI here — written but not executed against a live stack.
 */

const DEMO_EMAIL = process.env.E2E_EMAIL ?? "demo@example.com";
const DEMO_PASSWORD = process.env.E2E_PASSWORD ?? "DemoPass123!";
const PROJECT_NAME = "Azure Network Demo";
const SPEC_PROMPT =
  "Create an Azure virtual network with three subnets for AKS, Application Gateway, and Azure Bastion. Add NSGs, diagnostic settings, secure defaults, required tags, and a GitHub Actions pipeline.";

test("full smoke: login, create project, generate, browse tabs, export ZIP", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => {
    consoleErrors.push(String(err));
  });

  // Landing page
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "CloudForge AI" })).toBeVisible();
  await expect(
    page.getByText("Generated infrastructure must be reviewed by a qualified engineer before deployment."),
  ).toBeVisible();

  // Login with demo credentials
  await page.goto("/login");
  await page.getByLabel("Email").fill(DEMO_EMAIL);
  await page.getByLabel("Password").fill(DEMO_PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Create project
  await page.getByRole("button", { name: "Create Project", exact: true }).click();
  await page.getByLabel(/Project name/).fill(PROJECT_NAME);
  await page.getByLabel(/Region/).fill("eastus");
  await page.getByRole("button", { name: "Create project", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\//);

  // Enter the spec prompt and generate
  await page.getByLabel("Infrastructure requirements").fill(SPEC_PROMPT);
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(page.getByText("Generation in progress", { exact: false })).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByRole("button", { name: "Download Complete Project" })).toBeEnabled({
    timeout: 120_000,
  });

  // Open at least three tabs and verify content renders
  for (const tabName of ["Terraform", "Security", "README"]) {
    await page.getByRole("tab", { name: tabName }).click();
    const panel = page.getByRole("tabpanel");
    await expect(panel).toContainText(/.+/, { timeout: 30_000 });
  }

  // Request the project ZIP
  const downloadPromise = page.waitForEvent("download", { timeout: 60_000 });
  await page.getByRole("button", { name: "Download Complete Project" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.zip$/i);

  // No console/page errors across the whole journey
  expect(consoleErrors).toEqual([]);
});
