import { useQuery } from "@tanstack/react-query";
import { getHealth, type HealthResponse } from "../api/health";

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 15_000,
    retry: false,
  });
}
