import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Dna, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, PieChart, Pie } from 'recharts';

const COLORS = ['#ef4444', '#f59e0b', '#6366f1', '#10b981', '#f97316', '#8b5cf6', '#ec4899', '#06b6d4'];
const formatCurrency = (val: number): string => {
  if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
  return `₹${val.toFixed(0)}`;
};

export default function RevenueLeakage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRevenueLeakage().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-text-secondary">Loading...</div>;
  if (!data) return <div className="p-8 text-text-secondary">No data available</div>;

  const pieData = data.categories?.map((c: any, i: number) => ({
    name: c.category.replace(/_/g, ' '),
    value: c.amount,
    color: COLORS[i % COLORS.length],
  })) || [];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Dna className="w-6 h-6 text-primary" /> Revenue Leakage DNA</h1>
        <p className="text-text-secondary mt-1">Identify and diagnose major sources of revenue loss</p>
      </div>

      {/* AI Explanation */}
      <div className="glass-card p-6 mb-8 bg-primary/5 border-primary/20">
        <h3 className="text-sm font-semibold text-primary mb-2">AI Analysis</h3>
        <p className="text-sm text-text-primary leading-relaxed">{data.ai_explanation}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Bar chart */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-4">Revenue at Risk by Failure Reason</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.categories} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#64748b" tick={{fontSize: 11}} tickFormatter={(v: number) => formatCurrency(v)} />
                <YAxis type="category" dataKey="category" stroke="#64748b" tick={{fontSize: 11}} width={120} tickFormatter={(v: string) => v.replace(/_/g, ' ')} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} formatter={(v: number) => [formatCurrency(v), 'Amount']} />
                <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                  {data.categories.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie chart */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-4">Leakage Distribution</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }: any) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                  {pieData.map((entry: any, i: number) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} formatter={(v: number) => [formatCurrency(v), 'Amount']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Details table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Failure Reason</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">Amount</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">% of Total</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">Transactions</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">Avg Recovery</th>
            </tr>
          </thead>
          <tbody>
            {data.categories?.map((cat: any) => (
              <tr key={cat.category} className="border-b border-border/50 hover:bg-surface-light/50">
                <td className="px-4 py-3 text-sm">{cat.category.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3 text-sm text-right font-medium">{formatCurrency(cat.amount)}</td>
                <td className="px-4 py-3 text-sm text-right">{cat.percentage.toFixed(1)}%</td>
                <td className="px-4 py-3 text-sm text-right">{cat.transaction_count}</td>
                <td className="px-4 py-3 text-sm text-right">{(cat.avg_recovery_rate * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* High risk hours + methods */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-3">High-Risk Hours</h3>
          {data.high_risk_hours?.map((h: any) => (
            <div key={h.hour} className="flex justify-between py-2 border-b border-border/30">
              <span className="text-sm">{h.hour}:00 - {h.hour+1}:00</span>
              <span className="text-sm font-medium">{h.count} failures · {formatCurrency(h.amount)}</span>
            </div>
          ))}
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-3">Affected Segments</h3>
          {data.affected_segments?.map((s: any) => (
            <div key={s.segment} className="flex justify-between py-2 border-b border-border/30">
              <span className="text-sm capitalize">{s.segment}</span>
              <span className="text-sm font-medium">{s.count} failures · {formatCurrency(s.amount)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
