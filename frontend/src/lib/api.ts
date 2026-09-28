export type PatternSpec = {
  style: string;
  seed: number;
  tile: number;
  cols: number;
  rows: number;
  palette: string;
  colors?: string[] | null;
  line_width: number;
  background?: string | null;
};

export type CompositionSpec = {
  text: string;
  style: string;
  font_size: number;
  text_fill: string;
  background: string;
  width: number;
  height: number;
  pattern: PatternSpec | null;
  pattern_opacity: number;
  text_position: string;
};

export type Meta = {
  styles: { key: string; label: string; font: string }[];
  palettes: Record<string, string[]>;
  pattern_styles: string[];
  ocr_available: boolean;
  max_text_chars: number;
};

export type Issue = { code: string; message: string; severity: string };
export type ValidationReport = {
  ocr_used: boolean;
  ocr_text: string;
  similarity: number;
  passed: boolean;
  issues: Issue[];
};
export type CompositionDoc = {
  id: string;
  status: "draft" | "pending_review" | "approved" | "rejected" | "changes_requested";
  created_at: string;
  updated_at: string;
  params: CompositionSpec;
  review?: { decision: string; reviewer: string; notes: string; at: string } | null;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  meta: () => req<Meta>("/api/meta"),
  preview: (spec: CompositionSpec) =>
    req<{ svg: string; issues: Issue[] }>("/api/render/composition", {
      method: "POST",
      body: JSON.stringify(spec),
    }),
  createComposition: (spec: CompositionSpec) =>
    req<CompositionDoc>("/api/compositions", { method: "POST", body: JSON.stringify(spec) }),
  updateComposition: (id: string, spec: CompositionSpec) =>
    req<CompositionDoc>(`/api/compositions/${id}`, { method: "PUT", body: JSON.stringify(spec) }),
  getComposition: (id: string) => req<CompositionDoc>(`/api/compositions/${id}`),
  listCompositions: (status?: string) =>
    req<{ items: CompositionDoc[] }>(`/api/compositions${status ? `?status=${status}` : ""}`),
  deleteComposition: (id: string) => req<{ ok: boolean }>(`/api/compositions/${id}`, { method: "DELETE" }),
  validate: (id: string) => req<ValidationReport>(`/api/compositions/${id}/validate`, { method: "POST" }),
  submit: (id: string) => req<CompositionDoc>(`/api/compositions/${id}/submit`, { method: "POST" }),
  review: (id: string, decision: string, reviewer: string, notes: string) =>
    req<CompositionDoc>(`/api/compositions/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, reviewer, notes }),
    }),
  reviewQueue: () => req<{ items: CompositionDoc[] }>("/api/review/queue"),
  exportPng: (id: string, scale = 2) => `/api/compositions/${id}/export?scale=${scale}`,
  exportSvg: (id: string) => `/api/compositions/${id}/export/svg`,
};
