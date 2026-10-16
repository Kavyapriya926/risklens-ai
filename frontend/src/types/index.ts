// RiskLens AI — TypeScript type definitions

export type RiskLevel = 'low' | 'medium' | 'high';

export interface FeatureContribution {
  feature: string;
  value: number;
  contribution: number;
  direction: 'increases_risk' | 'decreases_risk' | 'neutral';
  human_label: string;
}

export interface RiskExplanation {
  primary_reason: string;
  factors: FeatureContribution[];
  evidence_summary: string;
}

export interface TransactionResult {
  transaction_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  prediction_confidence: number;
  model_version: string;
  explanation: RiskExplanation;
  processing_time_ms: number;
}

export interface TransactionInput {
  transaction_id?: string;
  amount: number;
  merchant_category: string;
  merchant_id?: string;
  hour_of_day: number;
  day_of_week: number;
  is_international: boolean;
  is_new_merchant: boolean;
  card_age_days?: number;
  velocity_24h: number;
  distance_from_home_km?: number;
  is_fraud_actual?: boolean;
}

export interface TransactionDetail {
  id: string;
  transaction_id: string;
  created_at: string;
  amount: number;
  merchant_category: string;
  merchant_id?: string;
  hour_of_day: number;
  day_of_week: number;
  is_international: boolean;
  is_new_merchant: boolean;
  card_age_days?: number;
  velocity_24h: number;
  distance_from_home_km?: number;
  risk_score?: number;
  risk_level?: RiskLevel;
  model_version?: string;
  prediction_confidence?: number;
  explanation_text?: string;
  feature_contributions?: Record<string, number>;
  status: string;
  is_fraud_actual?: boolean;
}

export interface BatchUploadResult {
  batch_id: string;
  total_rows: number;
  processed: number;
  failed: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  errors: string[];
}

export interface DashboardStats {
  total_transactions: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  pending_investigations: number;
  fraud_rate_pct: number;
  avg_risk_score: number;
  transactions_today: number;
  high_risk_today: number;
}

export interface DashboardCharts {
  risk_distribution: { range: string; count: number; percentage: number }[];
  daily_trends: { date: string; total: number; high_risk: number; reviewed: number }[];
  category_breakdown: { category: string; total: number; high_risk: number }[];
}

export interface AnalystNote {
  id: string;
  investigation_id: string;
  created_at: string;
  analyst_id: string;
  content: string;
  note_type: string;
}

export interface AuditLog {
  id: string;
  investigation_id: string;
  created_at: string;
  actor_id: string;
  action: string;
  description: string;
  before_state?: Record<string, unknown>;
  after_state?: Record<string, unknown>;
}

export interface Investigation {
  id: string;
  transaction_id: string;
  created_at: string;
  updated_at: string;
  status: string;
  priority: string;
  assigned_to?: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  analyst_verdict?: string;
  analyst_id?: string;
  reviewed_at?: string;
  notes: AnalystNote[];
  audit_logs: AuditLog[];
}

export interface SimulatorInput {
  low_threshold: number;
  high_threshold: number;
  review_cost_per_case: number;
  fraud_loss_per_case: number;
}

export interface SimulatorResult {
  threshold_config: SimulatorInput;
  total_transactions: number;
  detected_fraud: number;
  missed_fraud: number;
  false_positives: number;
  true_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  estimated_review_cost: number;
  estimated_fraud_loss: number;
  total_cost: number;
  comparison_baseline?: Record<string, number>;
}

export interface ModelEvaluationReport {
  model_name: string;
  model_version: string;
  trained_at: string;
  dataset_size: number;
  train_size: number;
  test_size: number;
  fraud_rate_pct: number;
  metrics: {
    precision: number;
    recall: number;
    f1_score: number;
    pr_auc: number;
    false_positive_rate: number;
  };
  confusion_matrix: number[][];
  threshold_used: number;
  pr_curve_points: { precision: number; recall: number }[];
  feature_importances: { feature: string; label: string; importance: number }[];
  disclaimer: string;
}
