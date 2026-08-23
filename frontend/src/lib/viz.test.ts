import { describe, expect, it } from "vitest";
import { DRIVE_STATUS_META, RISK_META, riskBand } from "./viz";

describe("riskBand", () => {
  it("maps probabilities to bands at the documented thresholds", () => {
    expect(riskBand(null)).toBeNull();
    expect(riskBand(0.0)).toBe("low");
    expect(riskBand(0.29)).toBe("low");
    expect(riskBand(0.3)).toBe("medium");
    expect(riskBand(0.69)).toBe("medium");
    expect(riskBand(0.7)).toBe("high");
    expect(riskBand(1.0)).toBe("high");
  });
});

describe("status/risk metadata", () => {
  it("labels every drive status", () => {
    expect(DRIVE_STATUS_META.healthy.label).toBe("Healthy");
    expect(DRIVE_STATUS_META.failed.label).toBe("Failed");
    expect(DRIVE_STATUS_META.at_risk.color).toBeTruthy();
  });
  it("labels every risk band", () => {
    expect(RISK_META.low.label).toBe("Low");
    expect(RISK_META.high.color).toBeTruthy();
  });
});
