const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
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
