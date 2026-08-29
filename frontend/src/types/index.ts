export interface KPISummary {
  total_processed_revenue: number;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  net_recovered_revenue: number;
  intervention_cost: number;
  failed_payment_count: number;
  checkout_abandonment_count: number;
  subscription_failure_count: number;
  invoice_failure_count: number;
  recovery_budget_total: number;
  recovery_budget_used: number;
  recovery_budget_utilization: number;
  incremental_recovery: number;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  recovered_transactions: number;
  active_recoveries: number;
}

export interface Transaction {
  id: string;
  merchant_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  failure_reason: string | null;
  transaction_type: string;
  retry_count: number;
  is_recoverable: boolean;
  recovery_status: string | null;
  recovery_priority: number;
  created_at: string;
  updated_at: string;
  customer_name?: string;
  customer_segment?: string;
  customer_success_rate?: number;
  last_payment_at?: string;
}

export interface TransactionList {
  transactions: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

export interface RecoveryScenario {
  id: number;
  action: string;
  recovery_probability: number;
  expected_revenue: number;
  intervention_cost: number;
  friction_score: number;
  expected_net_recovery: number;
  confidence: number;
  explanation: string | null;
  is_selected: boolean;
  is_policy_approved: boolean;
  policy_rejection_reason: string | null;
}

export interface RecoveryTwin {
  id: string;
  transaction_id: string;
  customer_id: string;
  amount: number;
  payment_method: string;
  failure_reason: string;
  customer_history: Record<string, any> | null;
  payment_history: Record<string, any> | null;
  time_features: Record<string, any> | null;
  risk_features: Record<string, any> | null;
  recovery_features: Record<string, any> | null;
  recovery_probability: number;
  recommended_action: string | null;
  explanation: string | null;
  scenarios: RecoveryScenario[];
  status: string;
  created_at: string;
}

export interface TrendPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendData {
  revenue_at_risk: TrendPoint[];
  recovery_over_time: TrendPoint[];
  recovery_rate_trend: TrendPoint[];
}

export interface LeakageCategory {
  category: string;
  amount: number;
  percentage: number;
  transaction_count: number;
  avg_recovery_rate: number;
}

export interface LeakageDNA {
  categories: LeakageCategory[];
  high_risk_hours: Record<string, any>[];
  problematic_methods: Record<string, any>[];
  affected_segments: Record<string, any>[];
  ai_explanation: string;
}

export interface ExperimentResult {
  group_name: string;
  strategy: string;
  total_transactions: number;
  recovered_count: number;
  recovery_rate: number;
  total_revenue_at_risk: number;
  recovered_revenue: number;
  intervention_cost: number;
  net_recovered: number;
  avg_recovery_time: number;
}

export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  segment: string | null;
  payment_method: string | null;
  failure_reason: string | null;
  control_strategy: string;
  ai_strategy: string;
  status: string;
  results: ExperimentResult[];
  incremental_recovery_rate: number | null;
  incremental_revenue: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface AuditLog {
  id: number;
  transaction_id: string;
  agent: string;
  decision_type: string;
  action: string;
  reasoning: string | null;
  model_version: string | null;
  confidence: number | null;
  policy_result: string | null;
  previous_state: string | null;
  new_state: string | null;
  execution_result: string | null;
  created_at: string;
}

export interface DashboardData {
  kpis: KPISummary;
  trends: TrendData;
  leakage: LeakageDNA;
  top_opportunities: any[];
  recent_recoveries: any[];
}
