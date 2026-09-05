import type {
  HistoryRecord,
  ModelResult,
  PredictionRequest,
  PredictionResponse,
} from "@/types/prediction";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      errorBody?.detail ?? `Request failed with status ${response.status}.`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function predictStudent(
  input: PredictionRequest,
): Promise<PredictionResponse> {
  return request<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getPredictionHistory(): Promise<HistoryRecord[]> {
  const data = await request<
    HistoryRecord[] | { predictions?: HistoryRecord[] }
  >("/predictions");
  return Array.isArray(data) ? data : (data.predictions ?? []);
}

export function deletePrediction(predictionId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/predictions/${predictionId}`, {
    method: "DELETE",
  });
}

export async function getModelResults(): Promise<ModelResult[]> {
  const data = await request<
    Record<string, Omit<ModelResult, "model">> | ModelResult[]
  >("/model-results");

  if (Array.isArray(data)) {
    return data;
  }

  return Object.entries(data).map(([model, metrics]) => ({
    model,
    ...metrics,
  }));
}
