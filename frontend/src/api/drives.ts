import { apiGet } from "./client";
import type { DriveDetail, DriveStatus, PaginatedDrives } from "./types";

export interface ListDrivesParams {
  status?: DriveStatus;
  limit?: number;
  offset?: number;
}

export function getDrives(params: ListDrivesParams = {}): Promise<PaginatedDrives> {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  const qs = search.toString();
  return apiGet<PaginatedDrives>(`/drives${qs ? `?${qs}` : ""}`);
}

export function getDrive(id: number): Promise<DriveDetail> {
  return apiGet<DriveDetail>(`/drives/${id}`);
}
