import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  CreditCard,
  FlaskConical,
  Activity,
  ShieldCheck,
  Settings,
  Dna,
  Zap,
  ClipboardList,
} from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/transactions', label: 'Transactions', icon: CreditCard },
  { path: '/what-if', label: 'What-If Lab', icon: FlaskConical },
  { path: '/experiments', label: 'Experiments', icon: Activity },
  { path: '/revenue-leakage', label: 'Leakage DNA', icon: Dna },
  { path: '/recovery-actions', label: 'Recovery Actions', icon: Zap },
  { path: '/audit', label: 'Audit Log', icon: ClipboardList },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col fixed h-full">
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-text-primary">RecoverX</h1>
              <p className="text-xs text-text-muted">AI Revenue Recovery</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path !== '/dashboard' && location.pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-primary/10 text-primary border border-primary/20'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-light'
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-border">
          <div className="px-3 py-2 rounded-lg bg-warning/10 border border-warning/20">
            <p className="text-xs font-medium text-warning">DEMO MODE</p>
            <p className="text-xs text-text-muted mt-0.5">No live payments processed</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        <Outlet />
      </main>
    </div>
  );
}
