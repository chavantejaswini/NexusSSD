// Shared API types mirroring the backend Pydantic schemas.

export type DriveStatus = "healthy" | "at_risk" | "failed" | "decommissioned";
export type RiskBand = "low" | "medium" | "high";

export interface DriveSummary {
  id: number;
  serial_number: string;
  model: string;
  capacity_bytes: number;
  status: DriveStatus;
  first_seen: string;
  last_seen: string;
  latest_failure_probability: number | null;
}

export interface PaginatedDrives {
  items: DriveSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface TelemetryPoint {
  date: string;
  power_on_hours: number;
  temperature: number;
  reallocated_sectors: number;
  media_wearout_indicator: number;
  pct_used: number;
}

export interface LatestPrediction {
  model_version: string;
  failure_probability: number;
  horizon_days: number;
  predicted_at: string;
}

export interface DriveDetail extends DriveSummary {
  telemetry: TelemetryPoint[];
  latest_prediction: LatestPrediction | null;
}

export interface FeatureContribution {
  name: string;
  value: number;
  importance: number;
}

export interface PredictResponse {
  drive_id: number | null;
  failure_probability: number;
  band: RiskBand;
  model_version: string;
  horizon_days: number;
  top_features: FeatureContribution[];
}

export interface RetrievedChunk {
  chunk_text: string;
  score: number;
  document_id: number;
  document_title: string;
  source: string;
}

export interface RetrieveResponse {
  query: string;
  results: RetrievedChunk[];
}

export interface AgentStep {
  agent: string;
  detail: Record<string, unknown>;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  agents: string[];
  trace: AgentStep[];
}
