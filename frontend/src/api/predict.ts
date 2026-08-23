import { apiPost } from "./client";
import type { PredictResponse } from "./types";

export function predictDrive(driveId: number): Promise<PredictResponse> {
  return apiPost<PredictResponse>("/predict", { drive_id: driveId });
}
