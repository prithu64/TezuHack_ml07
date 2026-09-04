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

export interface ContributingFactor {
  feature: string;
  value: string | number;
  reason: string;
}

export interface PredictionResponse {
  risk_category: RiskCategory;
  confidence: number;
  probabilities?: ProbabilityData;
  contributingFactors?: ContributingFactor[];
}

export interface HistoryRecord extends PredictionRequest {
  id?: string;
  created_at?: string;
  timestamp?: string;
  risk_category: RiskCategory;
  confidence: number;
}

export interface ModelResult {
  model: string;
  accuracy: number;
  weighted_f1: number;
  macro_f1: number;
}
