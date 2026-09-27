import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import CopyButton from "@/components/CopyButton";

describe("CopyButton", () => {
  let writeText: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
  });

  it("writes the text to the clipboard and shows Copied feedback", async () => {
    // NOTE: fireEvent is used instead of userEvent here because user-event
    // v14 installs its own navigator.clipboard stub during interaction,
    // which would bypass the spy above.
    render(<CopyButton text="resource example" />);
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    expect(writeText).toHaveBeenCalledWith("resource example");
    expect(await screen.findByRole("button", { name: "Copied" })).toBeInTheDocument();
  });
});
