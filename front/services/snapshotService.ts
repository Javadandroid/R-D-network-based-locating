import type { SnapshotLocateResponse } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface SnapshotLocateRequest {
  endpoint: string;
  snapshot_id: number;
  registered_only?: boolean;
  max_cells?: number;
  include_anchors?: boolean;
  anchors_limit?: number;
}

export async function locateFromSnapshot(
  req: SnapshotLocateRequest
): Promise<SnapshotLocateResponse> {
  const response = await fetch(`${API_BASE}/api/snapshot/locate/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    credentials: "include",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to locate from snapshot");
  }
  return (await response.json()) as SnapshotLocateResponse;
}

