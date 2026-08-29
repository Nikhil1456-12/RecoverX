import { Settings, Server, Shield, CreditCard, Database } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold flex items-center gap-2 mb-8"><Settings className="w-6 h-6 text-primary" /> Settings</h1>

      <div className="space-y-6 max-w-2xl">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><Server className="w-4 h-4" /> System</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-border/30">
              <div><p className="text-sm">Demo Mode</p><p className="text-xs text-text-muted">All actions simulated</p></div>
              <span className="px-3 py-1 bg-warning/10 text-warning text-xs font-medium rounded-lg">ENABLED</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-border/30">
              <div><p className="text-sm">ML Model</p><p className="text-xs text-text-muted">recovery_probability v1.0.0</p></div>
              <span className="px-3 py-1 bg-accent/10 text-accent text-xs font-medium rounded-lg">ACTIVE</span>
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><Shield className="w-4 h-4" /> Recovery Policy</h3>
          <div className="space-y-3">
            <div className="flex justify-between"><span className="text-sm text-text-secondary">Max Retries per Transaction</span><span className="text-sm font-medium">3</span></div>
            <div className="flex justify-between"><span className="text-sm text-text-secondary">Retry Cooldown</span><span className="text-sm font-medium">15 minutes</span></div>
            <div className="flex justify-between"><span className="text-sm text-text-secondary">Max Recovery per Customer</span><span className="text-sm font-medium">5 attempts</span></div>
            <div className="flex justify-between"><span className="text-sm text-text-secondary">Daily Recovery Budget</span><span className="text-sm font-medium">₹5,000</span></div>
            <div className="flex justify-between"><span className="text-sm text-text-secondary">Max Auto-Recovery Amount</span><span className="text-sm font-medium">₹50,000</span></div>
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><CreditCard className="w-4 h-4" /> Razorpay Integration</h3>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-warning" />
            <span className="text-sm text-text-secondary">Not configured (using demo mode)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
