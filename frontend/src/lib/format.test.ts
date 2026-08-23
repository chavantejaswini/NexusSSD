import { describe, expect, it } from "vitest";
import { formatBytes, formatDate, formatPct } from "./format";

describe("formatBytes", () => {
  it("formats capacities in decimal units", () => {
    expect(formatBytes(960197124096)).toBe("960 GB");
    expect(formatBytes(1920383410176)).toBe("1.9 TB");
    expect(formatBytes(0)).toBe("0 B");
  });
});

describe("formatPct", () => {
  it("scales fractions and honors digits", () => {
    expect(formatPct(0.1234, 1)).toBe("12.3%");
    expect(formatPct(0.5)).toBe("50%");
  });
  it("renders a dash for null", () => {
    expect(formatPct(null)).toBe("—");
  });
});

describe("formatDate", () => {
  it("keeps the ISO date portion", () => {
    expect(formatDate("2026-01-31T12:00:00Z")).toBe("2026-01-31");
  });
});
