import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const { push, refresh } = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
  useParams: () => ({}),
  usePathname: () => "/login",
  useSearchParams: () => new URLSearchParams(),
}));

import LoginPage from "@/app/(auth)/login/page";
import { mockJsonResponse } from "./test-utils";

describe("LoginPage API failure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("displays the backend error message from the error envelope", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValue(
      mockJsonResponse(401, {
        error: {
          code: "invalid_credentials",
          message: "The email or password you entered is incorrect.",
          request_id: "req-123",
        },
      }),
    );
    render(<LoginPage />);
    await user.type(screen.getByLabelText("Email"), "demo@example.com");
    await user.type(screen.getByLabelText("Password"), "WrongPassword1!");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The email or password you entered is incorrect.");
    expect(push).not.toHaveBeenCalled();
  });
});
