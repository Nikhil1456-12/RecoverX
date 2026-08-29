const API_BASE = '/api';

const MOCK_SUMMARY = {
  kpis: {
    total_processed_revenue: 150438714.66,
    revenue_at_risk: 31893123.28,
    revenue_recovered: 9017261.64,
    recovery_rate: 0.223,
    net_recovered_revenue: 8993279.54,
    intervention_cost: 23982.1,
    failed_payment_count: 1700,
    checkout_abandonment_count: 112,
    subscription_failure_count: 55,
    invoice_failure_count: 27,
    recovery_budget_total: 5000.0,
    recovery_budget_used: 23982.1,
    recovery_budget_utilization: 1.0,
    incremental_recovery: 3297580.12,
    total_transactions: 10000,
    successful_transactions: 7811,
    failed_transactions: 1700,
    recovered_transactions: 489,
    active_recoveries: 1228,
  }
};

const MOCK_TRENDS = {
  revenue_at_risk: Array.from({ length: 30 }, (_, i) => ({
    date: `Aug ${i + 1}`,
    value: Math.round(900000 + Math.sin(i / 3) * 300000 + Math.random() * 80000),
  })),
  recovery_over_time: Array.from({ length: 30 }, (_, i) => ({
    date: `Aug ${i + 1}`,
    value: Math.round(250000 + Math.cos(i / 3) * 100000 + Math.random() * 40000),
  })),
  recovery_rate_trend: Array.from({ length: 30 }, (_, i) => ({
    date: `Aug ${i + 1}`,
    value: Number((20 + Math.sin(i / 2) * 8).toFixed(1)),
  })),
};

const MOCK_LEAKAGE = {
  categories: [
    { category: 'bank_timeout', amount: 10907448.16, percentage: 34.2, transaction_count: 582, avg_recovery_rate: 0.28 },
    { category: 'expired_card', amount: 7271632.11, percentage: 22.8, transaction_count: 388, avg_recovery_rate: 0.19 },
    { category: 'checkout_abandonment', amount: 5772655.31, percentage: 18.1, transaction_count: 308, avg_recovery_rate: 0.24 },
    { category: 'insufficient_funds', amount: 4496930.38, percentage: 14.1, transaction_count: 240, avg_recovery_rate: 0.15 },
    { category: 'network_error', amount: 3444457.32, percentage: 10.8, transaction_count: 182, avg_recovery_rate: 0.31 },
  ],
  high_risk_hours: [
    { hour: 19, count: 241, amount: 4219000 },
    { hour: 20, count: 289, amount: 5120000 },
    { hour: 21, count: 215, amount: 3890000 },
    { hour: 14, count: 180, amount: 2900000 },
    { hour: 12, count: 154, amount: 2450000 },
  ],
  problematic_methods: [
    { method: 'upi', count: 760, amount: 14200000 },
    { method: 'card', count: 520, amount: 9800000 },
    { method: 'netbanking', count: 280, amount: 5100000 },
    { method: 'wallet', count: 140, amount: 2793123 },
  ],
  affected_segments: [
    { segment: 'returning', count: 680, amount: 12500000 },
    { segment: 'new', count: 510, amount: 9100000 },
    { segment: 'premium', count: 340, amount: 6800000 },
    { segment: 'high_value', count: 170, amount: 3493123 },
  ],
  ai_explanation: '34.2% of revenue at risk comes from UPI bank timeouts during peak evening hours (19:00 - 22:00 IST). Delayed retries (15m/45m) improve recovery by +31% over immediate retries. Expired cards respond best to WhatsApp payment link notifications.'
};

const MOCK_TRANSACTIONS = Array.from({ length: 20 }, (_, i) => ({
  id: `TXN_${String(i + 1).padStart(6, '0')}`,
  merchant_id: 'MERCH_01',
  customer_id: `CUST_${String((i % 10) + 1).padStart(4, '0')}`,
  customer_name: ['Aditi Sharma', 'Rahul Verma', 'Sneha Patel', 'Vikram Malhotra', 'Priya Nair', 'Amitabh Roy', 'Neha Gupta', 'Karan Mehta'][i % 8],
  customer_segment: ['premium', 'returning', 'high_value', 'new'][i % 4],
  amount: [12500, 3400, 8900, 45000, 1200, 67000, 5200, 18500][i % 8],
  currency: 'INR',
  payment_method: ['upi', 'card', 'netbanking', 'wallet'][i % 4],
  status: ['failed', 'recovered', 'failed', 'failed', 'recovered'][i % 5],
  failure_reason: ['bank_timeout', 'expired_card', 'checkout_abandonment', 'insufficient_funds', 'network_error'][i % 5],
  transaction_type: 'payment',
  retry_count: i % 3,
  is_recoverable: true,
  recovery_status: ['diagnosed', 'recovered', 'simulating', 'detected', 'recovered'][i % 5],
  recovery_priority: 0.85,
  created_at: new Date(Date.now() - i * 3600000 * 4).toISOString(),
  updated_at: new Date().toISOString(),
  customer_success_rate: 0.88,
}));

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    // Return realistic fallback data for static GitHub Pages hosting
    if (url.includes('/dashboard/summary')) return MOCK_SUMMARY as unknown as T;
    if (url.includes('/dashboard/trends')) return MOCK_TRENDS as unknown as T;
    if (url.includes('/revenue-leakage') || url.includes('/leakage')) return MOCK_LEAKAGE as unknown as T;
    if (url.startsWith('/transactions/')) {
      const parts = url.split('/');
      const txnId = parts[2];
      if (url.includes('/simulate')) {
        return {
          transaction_id: txnId,
          scenarios: [
            { action: 'retry_45m', action_label: 'Retry in 45 min', recovery_probability: 0.84, expected_revenue: 10500, intervention_cost: 0, friction_score: 0.08, expected_net_recovery: 10400, confidence: 0.88, explanation: 'UPI bank timeout recovery improves 31% with 45m cooldown during peak hours.', is_recommended: true },
            { action: 'whatsapp', action_label: 'WhatsApp Link', recovery_probability: 0.73, expected_revenue: 9125, intervention_cost: 2.5, friction_score: 0.15, expected_net_recovery: 8937, confidence: 0.85, explanation: 'High open rate WhatsApp recovery link.' },
            { action: 'retry_15m', action_label: 'Retry in 15 min', recovery_probability: 0.68, expected_revenue: 8500, intervention_cost: 0, friction_score: 0.05, expected_net_recovery: 8437, confidence: 0.80, explanation: 'Medium cooldown retry.' },
            { action: 'retry_now', action_label: 'Retry Immediately', recovery_probability: 0.39, expected_revenue: 4875, intervention_cost: 0, friction_score: 0.02, expected_net_recovery: 4875, confidence: 0.65, explanation: 'Immediate retry has low probability during gateway bank downtime.' },
            { action: 'human_escalation', action_label: 'Human Escalation', recovery_probability: 0.89, expected_revenue: 11125, intervention_cost: 50, friction_score: 0.25, expected_net_recovery: 8075, confidence: 0.90, explanation: 'Human concierge recovery for high-value transactions.' },
          ],
          recommended_action: 'retry_45m',
          recommended_action_label: 'Retry in 45 min',
          explanation: 'Customer has 94% historical payment success. 45-minute delayed retry yields ₹10,400 Expected Net Recovery under ₹0 cost policy.',
          policy_decisions: { retry_45m: { approved: true, reason: 'All 10 policy checks passed' } }
        } as unknown as T;
      }
      if (url.includes('/recover')) {
        return { transaction_id: txnId, status: 'recovered', message: 'Recovery successfully executed via AI Policy Twin (DEMO MODE)' } as unknown as T;
      }
      if (url.includes('/timeline')) {
        return {
          transaction_id: txnId,
          timeline: [
            { time: '19:30', agent: 'revenue_risk', decision_type: 'detection', action: 'failure_detected', new_state: 'detected', reasoning: 'UPI gateway bank timeout detected' },
            { time: '19:30', agent: 'root_cause', decision_type: 'diagnosis', action: 'diagnose_root_cause', new_state: 'diagnosed', reasoning: 'Classified as temporary bank system overload' },
            { time: '19:31', agent: 'counterfactual', decision_type: 'simulation', action: 'simulate_counterfactuals', new_state: 'simulating', confidence: 0.88 },
            { time: '19:31', agent: 'policy_engine', decision_type: 'policy_check', action: 'approve_retry_45m', new_state: 'approved', reasoning: 'Approved under 15m cooldown and ₹5,000 budget' },
            { time: '20:16', agent: 'action_executor', decision_type: 'execution', action: 'execute_retry_45m', new_state: 'recovered', reasoning: 'Payment recovered on delayed retry' }
          ]
        } as unknown as T;
      }
      const match = MOCK_TRANSACTIONS.find(t => t.id === txnId) || MOCK_TRANSACTIONS[0];
      return {
        ...match,
        customer: { name: match.customer_name, email: 'customer@example.com', segment: match.customer_segment, payment_success_rate: 0.92, lifetime_value: 125000, is_dnd: false },
        recovery_twin: {
          id: `TWIN_${txnId}`,
          recovery_probability: 0.84,
          recommended_action: 'retry_45m',
          explanation: 'Simulated 45-minute delayed retry achieves highest Expected Net Recovery (₹10,400).',
          scenarios: [
            { id: 1, action: 'retry_45m', recovery_probability: 0.84, expected_revenue: 10500, intervention_cost: 0, friction_score: 0.08, expected_net_recovery: 10400, confidence: 0.88, is_selected: true },
            { id: 2, action: 'whatsapp', recovery_probability: 0.73, expected_revenue: 9125, intervention_cost: 2.5, friction_score: 0.15, expected_net_recovery: 8937, confidence: 0.85 },
            { id: 3, action: 'retry_now', recovery_probability: 0.39, expected_revenue: 4875, intervention_cost: 0, friction_score: 0.02, expected_net_recovery: 4875, confidence: 0.65 },
          ]
        }
      } as unknown as T;
    }
    if (url.startsWith('/transactions')) {
      return { transactions: MOCK_TRANSACTIONS, total: 10000, page: 1, page_size: 20 } as unknown as T;
    }
    if (url.includes('/experiments')) {
      return {
        experiments: [
          {
            id: 'EXP_01',
            name: 'UPI Bank Timeout: Immediate vs Delayed Retry',
            description: 'A/B test comparing immediate retry against 45-minute delayed recovery for peak-hour UPI timeout failures.',
            payment_method: 'upi',
            failure_reason: 'bank_timeout',
            incremental_recovery_rate: 0.365,
            results: [
              { group_name: 'control', strategy: 'retry_now', total_transactions: 1000, recovery_rate: 0.421, recovered_revenue: 5262500, net_recovered: 5262500 },
              { group_name: 'treatment', strategy: 'retry_45m (AI Policy)', total_transactions: 1000, recovery_rate: 0.786, recovered_revenue: 9825000, net_recovered: 9825000 }
            ]
          },
          {
            id: 'EXP_02',
            name: 'Expired Card: Dunning Email vs WhatsApp Link',
            description: 'Testing customer response to WhatsApp payment update link vs generic email reminders.',
            payment_method: 'card',
            failure_reason: 'expired_card',
            incremental_recovery_rate: 0.412,
            results: [
              { group_name: 'control', strategy: 'email', total_transactions: 500, recovery_rate: 0.214, recovered_revenue: 1605000, net_recovered: 1604900 },
              { group_name: 'treatment', strategy: 'whatsapp', total_transactions: 500, recovery_rate: 0.626, recovered_revenue: 4695000, net_recovered: 4693750 }
            ]
          }
        ]
      } as unknown as T;
    }
    if (url.includes('/audit')) {
      return {
        logs: Array.from({ length: 15 }, (_, i) => ({
          id: i + 1,
          transaction_id: `TXN_${String(i + 1).padStart(6, '0')}`,
          agent: ['counterfactual', 'policy_engine', 'action_executor', 'root_cause', 'revenue_risk'][i % 5],
          decision_type: ['simulation', 'policy_check', 'execution', 'diagnosis', 'detection'][i % 5],
          action: ['simulate_counterfactuals', 'approve_retry_45m', 'execute_retry', 'diagnose_root_cause', 'failure_detected'][i % 5],
          previous_state: 'simulating',
          new_state: 'approved',
          confidence: 0.88,
          created_at: new Date(Date.now() - i * 180000).toISOString()
        })),
        total: 10411,
        page: 1,
        page_size: 15
      } as unknown as T;
    }
    if (url.includes('/recovery-actions')) {
      return {
        summary: { total_actions: 961, successful: 489, success_rate: 0.509, total_cost: 23982.1, total_recovered: 9017261.64 },
        actions: MOCK_TRANSACTIONS.map((t, i) => ({
          id: `ACT_${String(i + 1).padStart(6, '0')}`,
          transaction_id: t.id,
          action_type: 'retry_45m',
          result: i % 2 === 0 ? 'success' : 'failed',
          cost: 0,
          outcome: { recovered: i % 2 === 0, recovered_amount: t.amount, net_recovered: t.amount, recovery_time_minutes: 45 },
          executed_at: t.created_at
        }))
      } as unknown as T;
    }
    return {} as T;
  }
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJson<any>('/dashboard/summary'),
  getDashboardTrends: () => fetchJson<any>('/dashboard/trends'),

  // Transactions
  getTransactions: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchJson<any>(`/transactions${query}`);
  },
  getTransaction: (id: string) => fetchJson<any>(`/transactions/${id}`),
  getRecoveryTwin: (id: string) => fetchJson<any>(`/transactions/${id}/recovery-twin`),
  simulateRecovery: (id: string, actions?: string[]) =>
    fetchJson<any>(`/transactions/${id}/simulate`, {
      method: 'POST',
      body: JSON.stringify({ actions }),
    }),
  recoverTransaction: (id: string, action?: string) =>
    fetchJson<any>(`/transactions/${id}/recover`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),
  getTimeline: (id: string) => fetchJson<any>(`/transactions/${id}/timeline`),

  // Revenue Leakage
  getRevenueLeakage: () => fetchJson<any>('/revenue-leakage'),

  // Experiments
  getExperiments: () => fetchJson<any>('/experiments'),
  getExperiment: (id: string) => fetchJson<any>(`/experiments/${id}`),
  runExperiment: (data: any) =>
    fetchJson<any>('/experiments/run', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Audit
  getAuditLogs: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchJson<any>(`/audit${query}`);
  },

  // Recovery Actions
  getRecoveryActions: () => fetchJson<any>('/recovery-actions'),

  // Admin
  generateDemoData: () =>
    fetchJson<any>('/admin/generate-demo-data', { method: 'POST' }),

  // ML
  trainModel: () => fetchJson<any>('/ml/train', { method: 'POST' }),
  getMLStatus: () => fetchJson<any>('/ml/status'),

  // Health
  getHealth: () => fetchJson<any>('/health'),
};
