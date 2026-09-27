import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ProjectForm from "@/components/ProjectForm";

describe("ProjectForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows required-field errors and does not submit when empty", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<ProjectForm onSubmit={onSubmit} />);
    await user.click(screen.getByRole("button", { name: "Create project" }));
    expect(await screen.findByText("Project name is required.")).toBeInTheDocument();
    expect(await screen.findByText("Region is required (e.g. eastus).")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits all fields when valid", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<ProjectForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/Project name/), "Azure Network Demo");
    await user.type(screen.getByLabelText(/Region/), "eastus");
    await user.selectOptions(screen.getByLabelText(/Cloud target/), "aws");
    await user.click(screen.getByRole("button", { name: "Create project" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Azure Network Demo",
        region: "eastus",
        cloud_target: "aws",
        environment: "development",
        availability_requirement: "standard",
        compliance_framework: "none",
      }),
    );
  });
});
