import { useQuery } from "@tanstack/react-query";
import { getDrive, getDrives, type ListDrivesParams } from "../api/drives";
import type { DriveDetail, PaginatedDrives } from "../api/types";

export function useDrives(params: ListDrivesParams = {}) {
  return useQuery<PaginatedDrives>({
    queryKey: ["drives", params],
    queryFn: () => getDrives(params),
  });
}

export function useDrive(id: number | null) {
  return useQuery<DriveDetail>({
    queryKey: ["drive", id],
    queryFn: () => getDrive(id as number),
    enabled: id != null,
  });
}
