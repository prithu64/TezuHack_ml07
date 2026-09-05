export type RiskCategory = "Safe" | "At-Risk" | "High-Risk";

export interface PredictionRequest {
  attendance: number;
  study_hours: number;
  past_failures: number;
  assignments_completed_pct: number;
  parental_education: string;
  family_income: string;
  extracurricular: string;
  internet_access: string;
  previous_grade: number;
}

export interface ProbabilityData {
  Safe?: number;
  "At-Risk"?: number;
  "High-Risk"?: number;
  [category: string]: number | undefined;
}

export interface PredictionResponse {
  risk_category: RiskCategory;
  message: string;
  probabilities?: ProbabilityData;
  contributing_factors: string[];
}

export interface HistoryRecord {
  id?: string;
  input_data: PredictionRequest;
  risk_category: RiskCategory;
  probabilities: ProbabilityData;
  contributing_factors: string[];
  message: string;
  created_at: string;
}

export interface ModelResult {
  model: string;
  accuracy: number;
  weighted_f1: number;
  macro_f1: number;
}
