// Client for the Acre cloud API (reporting only).
const BASE = process.env.NEXT_PUBLIC_ACRE_API ?? "http://localhost:8000";

export type Zone = {
  zone_id: string;
  crop_type: string | null;
  map_x: number;
  map_y: number;
  score: number | null;
  factors: Record<string, unknown> | null;
  color: "green" | "amber" | "red" | "gray";
};

export type FarmMap = {
  farm_id: string;
  farm_score: number | null;
  zones: Zone[];
};

export type TreatmentRow = {
  zone_id: string;
  class_name: string;
  count: number;
  max_conf: number;
  treatment: {
    id: string;
    pesticide_name: string | null;
    organic_alternative: string | null;
    application_notes: string | null;
    source: string | null;
  } | null;
};

export type Report = {
  period: string;
  health_score: number | null;
  ai_summary: string;
  generated_at: string;
} | null;

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  farmMap: (farmId: string) => getJSON<FarmMap>(`/api/farms/${farmId}/map`),
  treatments: (farmId: string) =>
    getJSON<{ rows: TreatmentRow[] }>(`/api/farms/${farmId}/treatments`),
  latestReport: (farmId: string) =>
    getJSON<{ report: Report }>(`/api/farms/${farmId}/report/latest`),
  generateReport: async (farmId: string) => {
    const res = await fetch(`${BASE}/api/farms/${farmId}/report`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`generate report -> ${res.status}`);
    return res.json();
  },
};
