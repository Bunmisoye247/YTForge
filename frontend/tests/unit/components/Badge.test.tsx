import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/ui/Badge";
import { ProjectStatus, ApprovalStatus } from "@/types/enums";

describe("StatusBadge", () => {
  it("renders a title-cased label for a known status", () => {
    render(<StatusBadge status={ProjectStatus.IN_PROGRESS} />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("falls back to neutral tone for an unrecognized status without crashing", () => {
    render(<StatusBadge status="some_future_status" />);
    expect(screen.getByText("Some Future Status")).toBeInTheDocument();
  });

  it("renders the pending approval status", () => {
    render(<StatusBadge status={ApprovalStatus.PENDING} />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });
});
