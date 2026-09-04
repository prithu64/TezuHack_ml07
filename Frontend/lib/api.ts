import type {
  HistoryRecord,
  ModelResult,
  PredictionRequest,
  PredictionResponse,
} from "@/types/prediction";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function getApiUrl(): string {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  }

  return API_URL.replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}.`);
  }

  return response.json() as Promise<T>;
}

export function predictStudent(input: PredictionRequest): Promise<PredictionResponse> {
  return request<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getPredictionHistory(): Promise<HistoryRecord[]> {
  const data = await request<HistoryRecord[] | { predictions?: HistoryRecord[] }>("/history");
  return Array.isArray(data) ? data : data.predictions ?? [];
}

export async function getModelResults(): Promise<ModelResult[]> {
  const data = await request<Record<string, Omit<ModelResult, "model">> | ModelResult[]>("/model-results");

  if (Array.isArray(data)) {
    return data;
  }

  return Object.entries(data).map(([model, metrics]) => ({ model, ...metrics }));
}
