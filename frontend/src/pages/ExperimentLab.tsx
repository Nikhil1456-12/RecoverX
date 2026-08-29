import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Activity, TrendingUp, ArrowUpRight, ArrowDownRight, Plus } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { clsx } from 'clsx';

const formatCurrency = (val: number): string => {
  if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
  return `₹${val.toFixed(0)}`;
};

export default function ExperimentLab() {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [selectedExp, setSelectedExp] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getExperiments().then(data => {
      setExperiments(data.experiments || []);
      if (data.experiments?.length > 0) setSelectedExp(data.experiments[0]);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const control = selectedExp?.results?.find((r: any) => r.group_name === 'control');
  const treatment = selectedExp?.results?.find((r: any) => r.group_name === 'treatment');

  const comparisonData = control && treatment ? [
    { metric: 'Recovery Rate', control: (control.recovery_rate * 100), treatment: (treatment.recovery_rate * 100) },
    { metric: 'Recovered Revenue', control: control.recovered_revenue / 1000, treatment: treatment.recovered_revenue / 1000 },
    { metric: 'Net Recovery', control: control.net_recovered / 1000, treatment: treatment.net_recovered / 1000 },
  ] : [];

  if (loading) return <div className="p-8 text-text-secondary">Loading experiments...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Activity className="w-6 h-6 text-primary" /> Recovery Experiment Lab</h1>
          <p className="text-text-secondary mt-1">Compare control vs AI-optimized recovery strategies</p>
        </div>
      </div>

      {/* Experiment List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {experiments.map((exp) => (
          <button key={exp.id} onClick={() => setSelectedExp(exp)}
            className={clsx('text-left glass-card p-4 transition-all', selectedExp?.id === exp.id ? 'border-primary/40 ring-1 ring-primary/20' : 'hover:border-border/80')}
          >
            <p className="text-sm font-medium">{exp.name}</p>
            <p className="text-xs text-text-muted mt-1">{exp.payment_method?.toUpperCase() || 'All'} · {exp.failure_reason?.replace(/_/g, ' ') || 'All reasons'}</p>
            {exp.incremental_recovery_rate !== null && (
              <div className="flex items-center gap-1 mt-2">
                <ArrowUpRight className="w-3 h-3 text-accent" />
                <span className="text-xs text-accent font-medium">+{(exp.incremental_recovery_rate * 100).toFixed(1)}% recovery uplift</span>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Selected Experiment Detail */}
      {selectedExp && control && treatment && (
        <div className="space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-lg font-bold mb-2">{selectedExp.name}</h2>
            <p className="text-sm text-text-secondary">{selectedExp.description}</p>
          </div>

          {/* Control vs Treatment */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6 border-l-4 border-l-text-muted">
              <h3 className="text-sm font-semibold text-text-muted mb-4">CONTROL — {control.strategy.replace(/_/g, ' ')}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-xs text-text-muted">Transactions</p><p className="text-lg font-bold">{control.total_transactions}</p></div>
                <div><p className="text-xs text-text-muted">Recovery Rate</p><p className="text-lg font-bold">{(control.recovery_rate * 100).toFixed(1)}%</p></div>
                <div><p className="text-xs text-text-muted">Recovered Revenue</p><p className="text-lg font-bold">{formatCurrency(control.recovered_revenue)}</p></div>
                <div><p className="text-xs text-text-muted">Net Recovered</p><p className="text-lg font-bold">{formatCurrency(control.net_recovered)}</p></div>
              </div>
            </div>

            <div className="glass-card p-6 border-l-4 border-l-accent">
              <h3 className="text-sm font-semibold text-accent mb-4">AI POLICY — {treatment.strategy.replace(/_/g, ' ')}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-xs text-text-muted">Transactions</p><p className="text-lg font-bold">{treatment.total_transactions}</p></div>
                <div><p className="text-xs text-text-muted">Recovery Rate</p><p className="text-lg font-bold text-accent">{(treatment.recovery_rate * 100).toFixed(1)}%</p></div>
                <div><p className="text-xs text-text-muted">Recovered Revenue</p><p className="text-lg font-bold text-accent">{formatCurrency(treatment.recovered_revenue)}</p></div>
                <div><p className="text-xs text-text-muted">Net Recovered</p><p className="text-lg font-bold text-accent">{formatCurrency(treatment.net_recovered)}</p></div>
              </div>
            </div>
          </div>

          {/* Uplift summary */}
          <div className="glass-card p-6 bg-accent/5 border-accent/20">
            <h3 className="text-sm font-semibold text-accent mb-3">Incremental Recovery (AI Uplift)</h3>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-xs text-text-muted">Recovery Rate Uplift</p>
                <p className="text-2xl font-bold text-accent">+{((treatment.recovery_rate - control.recovery_rate) * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Revenue Uplift</p>
                <p className="text-2xl font-bold text-accent">{formatCurrency(treatment.recovered_revenue - control.recovered_revenue)}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Intervention Cost</p>
                <p className="text-2xl font-bold text-warning">{formatCurrency(treatment.intervention_cost)}</p>
              </div>
            </div>
          </div>

          {/* Comparison Chart */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4">Control vs AI Comparison</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="metric" stroke="#64748b" tick={{fontSize: 12}} />
                  <YAxis stroke="#64748b" tick={{fontSize: 11}} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                  <Bar dataKey="control" name="Control" fill="#64748b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="treatment" name="AI Policy" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
