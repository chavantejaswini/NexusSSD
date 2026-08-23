import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type { PaginatedDrives } from "../api/types";
import { FleetOverview } from "./FleetOverview";

const MOCK: PaginatedDrives = {
  total: 3,
  limit: 200,
  offset: 0,
  items: [
    {
      id: 1, serial_number: "NX-000001", model: "Samsung PM883", capacity_bytes: 960197124096,
      status: "failed", first_seen: "2026-01-01", last_seen: "2026-02-01", latest_failure_probability: 0.95,
    },
    {
      id: 2, serial_number: "NX-000002", model: "Intel S4510", capacity_bytes: 960197124096,
      status: "healthy", first_seen: "2026-01-01", last_seen: "2026-02-01", latest_failure_probability: 0.05,
    },
    {
      id: 3, serial_number: "NX-000003", model: "Micron 5200", capacity_bytes: 480103981056,
      status: "at_risk", first_seen: "2026-01-01", last_seen: "2026-02-01", latest_failure_probability: 0.6,
    },
  ],
};

vi.mock("../api/drives", () => ({
  getDrives: vi.fn(() => Promise.resolve(MOCK)),
}));

function wrap(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("FleetOverview", () => {
  it("renders KPIs and the highest-risk drive from the API", async () => {
    wrap(<FleetOverview />);
    expect(await screen.findByText("Fleet Overview")).toBeInTheDocument();
    // The failed drive (highest risk) appears in the top-risk list.
    await waitFor(() => expect(screen.getByText("NX-000001")).toBeInTheDocument());
    // Total drives KPI reflects the mocked fleet size.
    expect(screen.getByText("Total drives")).toBeInTheDocument();
  });
});
