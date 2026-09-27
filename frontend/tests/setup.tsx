import "@testing-library/jest-dom";
import { vi } from "vitest";

// Monaco is a heavy browser editor; replace it with a lightweight stand-in
// that still exposes the rendered value so tests can assert on content.
vi.mock("@monaco-editor/react", () => ({
  __esModule: true,
  loader: { config: vi.fn(), init: vi.fn() },
  default: ({
    value,
    language,
  }: {
    value?: string;
    language?: string;
  }) => (
    <div data-testid="monaco-editor" data-language={language}>
      {value}
    </div>
  ),
}));

// jsdom does not implement the clipboard API.
if (!navigator.clipboard) {
  Object.defineProperty(navigator, "clipboard", {
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
    configurable: true,
  });
}
