import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import KPICard from '@/components/KPICard';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, Cell, PieChart, Pie,
} from 'recharts';
import {
  AlertTriangle, TrendingUp, DollarSign, Target,
  CreditCard, Wallet, Activity, PieChart as PieIcon,
  ArrowRight, RefreshCw, Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const formatCurrency = (val: number | undefined | null): string => {
  if (val === undefined || val === null || isNaN(val)) return '₹0';
  if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
  if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
  return `₹${val.toFixed(0)}`;
};

const chartTooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '8px',
  color: '#f1f5f9',
  fontSize: '12px',
};

export default function Dashboard() {
  const [kpis, setKpis] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [leakage, setLeakage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, trendsRes, leakageRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getDashboardTrends(),
        api.getRevenueLeakage(),
      ]);
      setKpis(summaryRes.kpis || summaryRes);
      setTrends(trendsRes);
      setLeakage(leakageRes);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      await api.generateDemoData();
      await fetchData();
    } catch (err) {
      console.error('Seed error:', err);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-primary animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!kpis || kpis.total_transactions === 0) {
    return (
      <div className="p-8">
        <div className="glass-card p-12 text-center max-w-lg mx-auto">
          <AlertTriangle className="w-16 h-16 text-warning mx-auto mb-6" />
          <h2 className="text-xl font-bold mb-2">No Data Available</h2>
          <p className="text-text-secondary mb-6">Generate demo data to populate the dashboard with 10,000 synthetic transactions.</p>
          <button
            onClick={handleSeedData}
            disabled={seeding}
            className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {seeding ? (
              <span className="flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</span>
            ) : (
              'Generate Demo Data'
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Revenue Recovery Dashboard</h1>
          <p className="text-text-secondary mt-1">Real-time revenue risk monitoring and recovery intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/what-if"
            className="px-4 py-2 bg-gradient-to-r from-primary to-accent hover:from-primary-dark hover:to-accent-light text-white text-xs font-bold rounded-lg shadow transition-all flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" /> Test Custom Data <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <button onClick={fetchData} className="p-2 hover:bg-surface-light rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 text-text-secondary" />
          </button>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-warning/10 border border-warning/20 rounded-lg">
            <Activity className="w-4 h-4 text-warning" />
            <span className="text-xs font-medium text-warning">DEMO MODE</span>
          </div>
        </div>
      </div>

      {/* Interactive Custom Simulator Banner */}
      <div className="mb-8 p-4 rounded-xl bg-gradient-to-r from-primary/15 via-surface-light to-accent/15 border border-primary/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center text-primary shrink-0">
            <Target className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-text-primary">Interactive Counterfactual Playground</h3>
            <p className="text-xs text-text-secondary">Input your own amounts, UPI/Card failure reasons, customer segments, and DND rules to watch the AI Twin simulate competing actions live.</p>
          </div>
        </div>
        <Link
          to="/what-if"
          className="px-4 py-2 bg-surface-lighter hover:bg-surface-light border border-border hover:border-primary/40 text-text-primary text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 shrink-0"
        >
          Open Custom Simulator <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPICard label="Revenue at Risk" value={formatCurrency(kpis.revenue_at_risk)} variant="danger" icon={<AlertTriangle className="w-4 h-4" />} />
        <KPICard label="Recovered Revenue" value={formatCurrency(kpis.revenue_recovered)} variant="success" icon={<TrendingUp className="w-4 h-4" />} />
        <KPICard label="Recovery Rate" value={`${(kpis.recovery_rate * 100).toFixed(1)}%`} variant="success" icon={<Target className="w-4 h-4" />} />
        <KPICard label="Net Recovery" value={formatCurrency(kpis.net_recovered_revenue)} variant="success" icon={<DollarSign className="w-4 h-4" />} />
        <KPICard label="Intervention Cost" value={formatCurrency(kpis.intervention_cost)} variant="warning" icon={<Wallet className="w-4 h-4" />} />
        <KPICard label="Budget Used" value={`${(kpis.recovery_budget_utilization * 100).toFixed(0)}%`} icon={<PieIcon className="w-4 h-4" />} />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KPICard label="Total Transactions" value={kpis.total_transactions?.toLocaleString()} icon={<CreditCard className="w-4 h-4" />} />
        <KPICard label="Failed Payments" value={kpis.failed_payment_count?.toLocaleString()} variant="danger" />
        <KPICard label="Recovered" value={kpis.recovered_transactions?.toLocaleString()} variant="success" />
        <KPICard label="Active Recoveries" value={kpis.active_recoveries?.toLocaleString()} variant="warning" />
      </div>

      {/* Charts */}
      {trends && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4">Revenue at Risk Trend (30 days)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends.revenue_at_risk}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 11}} />
                  <YAxis stroke="#64748b" tick={{fontSize: 11}} tickFormatter={(v: number) => formatCurrency(v)} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [formatCurrency(v), 'At Risk']} />
                  <Area type="monotone" dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4">Recovery Over Time (30 days)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends.recovery_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 11}} />
                  <YAxis stroke="#64748b" tick={{fontSize: 11}} tickFormatter={(v: number) => formatCurrency(v)} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [formatCurrency(v), 'Recovered']} />
                  <Area type="monotone" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Leakage DNA Preview */}
      {leakage && leakage.categories && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text-secondary">Revenue Leakage DNA</h3>
              <Link to="/revenue-leakage" className="text-xs text-primary hover:text-primary-light flex items-center gap-1">
                View Details <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="space-y-3">
              {leakage.categories.slice(0, 6).map((cat: any) => (
                <div key={cat.category} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-text-primary">{cat.category.replace(/_/g, ' ')}</span>
                      <span className="text-sm font-medium text-text-primary">{cat.percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-surface-lighter rounded-full h-2">
                      <div className="bg-danger h-2 rounded-full" style={{ width: `${Math.min(cat.percentage, 100)}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4">AI Insights</h3>
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
              <p className="text-sm text-text-primary leading-relaxed">{leakage.ai_explanation}</p>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {leakage.problematic_methods?.slice(0, 4).map((m: any) => (
                <div key={m.method} className="bg-surface-lighter/50 rounded-lg p-3">
                  <p className="text-xs text-text-muted">Payment Method</p>
                  <p className="text-sm font-medium">{m.method.toUpperCase()}</p>
                  <p className="text-xs text-danger">{m.count} failures</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
