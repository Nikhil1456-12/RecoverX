import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import Transactions from '@/pages/Transactions';
import TransactionDetail from '@/pages/TransactionDetail';
import WhatIfLab from '@/pages/WhatIfLab';
import ExperimentLab from '@/pages/ExperimentLab';
import RevenueLeakage from '@/pages/RevenueLeakage';
import RecoveryActions from '@/pages/RecoveryActions';
import AuditLog from '@/pages/AuditLog';
import SettingsPage from '@/pages/SettingsPage';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/transactions/:id" element={<TransactionDetail />} />
          <Route path="/what-if" element={<WhatIfLab />} />
          <Route path="/experiments" element={<ExperimentLab />} />
          <Route path="/revenue-leakage" element={<RevenueLeakage />} />
          <Route path="/recovery-actions" element={<RecoveryActions />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
