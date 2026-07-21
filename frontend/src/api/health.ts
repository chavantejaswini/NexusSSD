import { apiGet } from "./client";

export interface HealthResponse {
  status: "ok" | "degraded";
  db: "ok" | "error";
  version: string;
  environment: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
