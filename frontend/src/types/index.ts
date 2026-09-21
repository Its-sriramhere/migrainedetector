export type RiskLevel = "low" | "moderate" | "high";

export interface User {
  id: number;
  name: string;
  email: string;
  consent_given: boolean;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  consent_given: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AssessmentOption {
  label: string;
  value: string;
}

export interface AssessmentQuestion {
  id: number;
  question_text: string;
  question_type: "single" | "multi";
  options: string[];
}

export interface AssessmentAnswer {
  question_id: number;
  answer: string;
}

export interface RiskProfile {
  user_id: number;
  migraine_history_score: number;
  sleep_profile?: string;
  stress_profile?: string;
  activity_profile?: string;
  hydration_profile?: string;
  caffeine_profile?: string;
  trigger_profile: string[];
  resting_hr?: number;
  profile_version: string;
}

export interface BaselineEstimates {
  heart_rate_low: number;
  heart_rate_high: number;
  sleep_hours?: number;
  resting_note: string;
}

export interface SensorReading {
  id: number;
  source: string;
  timestamp?: string;
  heart_rate?: number;
  hrv?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  spo2?: number;
  temperature?: number;
  activity?: number;
  signal_quality?: number;
}

export interface PredictionFeature {
  id: number;
  feature_name: string;
  feature_value?: number;
  contribution: number;
}

export interface Prediction {
  id: number;
  timestamp?: string;
  risk_score: number;
  risk_level: RiskLevel;
  prediction_window: number;
  model_version: string;
  outcome: string;
  source: string;
  features: PredictionFeature[];
  advice?: string[];
}

export interface ReadingWithPrediction {
  reading: SensorReading;
  prediction: Prediction;
}

export interface Device {
  id: number;
  device_identifier: string;
  device_name: string;
  status: string;
  last_seen?: string;
}

export interface Alert {
  id: number;
  timestamp?: string;
  risk_score: number;
  risk_level: RiskLevel;
  message: string;
  acknowledged: boolean;
  feedback?: string;
  prediction_id?: number;
  advice?: string[];
}

export interface MigraineEpisode {
  id: number;
  start_time: string;
  end_time?: string;
  severity?: string;
  symptoms: string[];
  trigger?: string;
  notes?: string;
}

export interface ReportOverview {
  total_readings: number;
  total_predictions: number;
  total_alerts: number;
  total_episodes: number;
  latest_risk_score?: number;
  latest_risk_level?: RiskLevel;
  average_risk?: number;
  risk_band_counts: Record<string, number>;
  days_monitored: number;
}

export interface DemoSessionStatus {
  running: boolean;
  scenario?: string;
}

export type ScenarioName = "normal" | "moderate" | "high";