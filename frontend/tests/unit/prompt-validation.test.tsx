import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const { push, refresh, replace } = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh, replace }),
  useParams: () => ({ id: "proj-1" }),
  usePathname: () => "/projects/proj-1",
  useSearchParams: () => new URLSearchParams(),
}));

import ProjectStudioPage from "@/app/(app)/projects/[id]/page";
import { mockJsonResponse } from "./test-utils";

const PROJECT = {
  id: "proj-1",
  name: "Azure Network Demo",
  cloud_target: "azure",
  environment: "development",
  region: "eastus",
  availability_requirement: "standard",
  compliance_framework: "none",
};

function installFetch() {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("ProjectStudioPage prompt validation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const fetchMock = installFetch();
    fetchMock.mockImplementation((url: string) => {
      const u = String(url);
      if (u.endsWith("/api/v1/settings/ai-provider")) {
        return Promise.resolve(
          mockJsonResponse(200, { provider: "demo", configured: false, demo_mode: true }),
        );
      }
      if (u.endsWith("/api/v1/projects/proj-1/generations")) {
        return Promise.resolve(mockJsonResponse(200, { items: [] }));
      }
      if (u.endsWith("/api/v1/projects/proj-1")) {
        return Promise.resolve(mockJsonResponse(200, PROJECT));
      }
      return Promise.resolve(mockJsonResponse(404, { error: { code: "not_found", message: "Not found" } }));
    });
  });

  it("rejects a prompt shorter than 20 characters", async () => {
    const user = userEvent.setup();
    render(<ProjectStudioPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Azure Network Demo" })).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText("Infrastructure requirements"));
    await user.type(screen.getByLabelText("Infrastructure requirements"), "too short");
    await user.click(screen.getByRole("button", { name: "Generate" }));

    expect(await screen.findByText(/at least 20 characters/)).toBeInTheDocument();
    // The backend must not be called when client validation fails.
    expect(vi.mocked(fetch)).not.toHaveBeenCalledWith(
      expect.stringContaining("/generate"),
      expect.anything(),
    );
  });
});
