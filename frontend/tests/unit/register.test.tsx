import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const { push, refresh } = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
  useParams: () => ({}),
  usePathname: () => "/register",
  useSearchParams: () => new URLSearchParams(),
}));

import RegisterPage from "@/app/(auth)/register/page";

function jsonResponse(status: number, body: unknown): Response {
  const text = JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(),
    json: async () => JSON.parse(text),
    text: async () => text,
    blob: async () => new Blob([text]),
  } as unknown as Response;
}

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("rejects a weak password", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);
    await user.type(screen.getByLabelText("Name"), "Demo User");
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "weak");
    await user.type(screen.getByLabelText("Confirm password"), "weak");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText(/Password must include/)).toBeInTheDocument();
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
  });

  it("rejects mismatched password confirmation", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);
    await user.type(screen.getByLabelText("Name"), "Demo User");
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "StrongPass123!");
    await user.type(screen.getByLabelText("Confirm password"), "DifferentPass123!");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText("Passwords do not match.")).toBeInTheDocument();
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
  });

  it("registers with a valid password and redirects to the dashboard", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch).mockResolvedValue(
      jsonResponse(201, { id: "u1", name: "Demo User", email: "demo@example.com" }),
    );
    render(<RegisterPage />);
    await user.type(screen.getByLabelText("Name"), "Demo User");
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "StrongPass123!");
    await user.type(screen.getByLabelText("Confirm password"), "StrongPass123!");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/auth/register"),
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(push).toHaveBeenCalledWith("/dashboard");
  });
});
