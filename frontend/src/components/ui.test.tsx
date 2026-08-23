import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskBadge, StatTile, StatusBadge } from "./ui";

describe("StatusBadge", () => {
  it("renders the human label for a status", () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });
});

describe("RiskBadge", () => {
  it("shows a dash when there is no band", () => {
    render(<RiskBadge band={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
  it("shows the band label", () => {
    render(<RiskBadge band="high" />);
    expect(screen.getByText("High")).toBeInTheDocument();
  });
});

describe("StatTile", () => {
  it("renders a label and value", () => {
    render(<StatTile label="Total drives" value={42} />);
    expect(screen.getByText("Total drives")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
