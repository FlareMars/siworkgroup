/**
 * TanStack Query hooks for Claw data fetching.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";

export interface Claw {
  id: string;
  name: string;
  description: string | null;
  slug: string;
  status: "pending" | "running" | "paused" | "stopped" | "error" | "destroyed";
  owner_id: string;
  container_id: string | null;
  model: string;
  system_prompt: string | null;
  work_dir: string;
  sandbox_config: Record<string, unknown>;
  enabled_tools: string[];
  created_at: string;
  updated_at: string;
  last_active_at: string | null;
}

export interface ClawListResponse {
  items: Claw[];
  total: number;
  page: number;
  page_size: number;
}

export const clawKeys = {
  all: ["claws"] as const,
  lists: () => [...clawKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...clawKeys.lists(), filters] as const,
  details: () => [...clawKeys.all, "detail"] as const,
  detail: (id: string) => [...clawKeys.details(), id] as const,
};

export function useClawsQuery(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: clawKeys.list({ page, pageSize }),
    queryFn: async () => {
      const res = await apiClient.get<ClawListResponse>(
        `/api/v1/claws?page=${page}&page_size=${pageSize}`
      );
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useClawQuery(id: string) {
  return useQuery({
    queryKey: clawKeys.detail(id),
    queryFn: async () => {
      const res = await apiClient.get<Claw>(`/api/v1/claws/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useStartClawMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (clawId: string) => {
      const res = await apiClient.post<Claw>(`/api/v1/claws/${clawId}/start`);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(clawKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: clawKeys.lists() });
    },
  });
}

export function useStopClawMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (clawId: string) => {
      const res = await apiClient.post<Claw>(`/api/v1/claws/${clawId}/stop`);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(clawKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: clawKeys.lists() });
    },
  });
}

export function useDeleteClawMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (clawId: string) => {
      await apiClient.delete(`/api/v1/claws/${clawId}`);
      return clawId;
    },
    onSuccess: (clawId) => {
      queryClient.removeQueries({ queryKey: clawKeys.detail(clawId) });
      queryClient.invalidateQueries({ queryKey: clawKeys.lists() });
    },
  });
}