import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricCards from './components/MetricCards';
import AccountsGrid from './components/AccountsGrid';
import SpendingCharts from './components/SpendingCharts';
import DailyForecastChart from './components/DailyForecastChart';
import AlertsStream from './components/AlertsStream';
import TransactionsTable from './components/TransactionsTable';
import TransactionModal from './components/TransactionModal';
import TransferModal from './components/TransferModal';
import CsvImportModal from './components/CsvImportModal';
import LoginScreen from './components/LoginScreen';
import SpendeeLanding from './components/SpendeeLanding';
import { 
  Sparkles, 
  RefreshCw, 
  Database, 
  ShieldCheck, 
  ArrowRightLeft,
  Plus,
  Upload,
  ArrowUpRight
} from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('budget_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  const [viewMode, setViewMode] = useState('landing'); // 'landing' | 'auth' | 'dashboard'
  const [health, setHealth] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [isTxModalOpen, setIsTxModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);

  const fetchDashboardData = async () => {
    if (!currentUser?.user_id) return;
    const uid = currentUser.user_id;

    try {
      // Parallel fetches for user-isolated responsiveness
      const [healthRes, accountsRes, budgetsRes, txRes, alertsRes, analyticsRes] = await Promise.all([
        fetch('/api/health').catch(() => null),
        fetch(`/api/accounts?user_id=${uid}`),
        fetch(`/api/budgets?user_id=${uid}`),
        fetch(`/api/transactions?user_id=${uid}&limit=50`),
        fetch(`/api/alerts?user_id=${uid}&limit=50`),
        fetch(`/api/analytics/summary?user_id=${uid}`)
      ]);

      if (healthRes && healthRes.ok) setHealth(await healthRes.json());
      if (accountsRes && accountsRes.ok) {
        const d = await accountsRes.json();
        setAccounts(d.accounts || []);
      }
      if (budgetsRes && budgetsRes.ok) {
        const d = await budgetsRes.json();
        setBudgets(d.budgets || []);
      }
      if (txRes && txRes.ok) {
        const d = await txRes.json();
        setTransactions(d.transactions || []);
      }
      if (alertsRes && alertsRes.ok) {
        const d = await alertsRes.json();
        setAlerts(d.alerts || []);
      }
      if (analyticsRes && analyticsRes.ok) {
        setAnalytics(await analyticsRes.json());
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser?.user_id) {
      setLoading(true);
      fetchDashboardData();
      // Poll alerts & health every 10 seconds for the active user
      const interval = setInterval(fetchDashboardData, 10000);
      return () => clearInterval(interval);
    }
  }, [currentUser?.user_id]);

  const handleLoginSuccess = (user) => {
    localStorage.setItem('budget_user', JSON.stringify(user));
    setCurrentUser(user);
    setViewMode('dashboard');
    showToast(`Welcome back, ${user.name || user.username}!`);
  };

  const handleDemoLogin = async (username, password) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (res.ok) {
        const data = await res.json();
        handleLoginSuccess(data.user);
      } else {
        setViewMode('auth');
      }
    } catch (e) {
      setViewMode('auth');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('budget_user');
    setCurrentUser(null);
    setViewMode('landing');
    setAccounts([]);
    setBudgets([]);
    setTransactions([]);
    setAlerts([]);
    setAnalytics(null);
  };

  const handleMarkAlertRead = async (alertId) => {
    try {
      await fetch('/api/alerts/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId })
      });
      fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    if (!currentUser?.user_id) return;
    try {
      await fetch('/api/alerts/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: currentUser.user_id, mark_all: true })
      });
      fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  // If user is not logged in:
  if (!currentUser) {
    if (viewMode === 'auth') {
      return (
        <LoginScreen 
          onLoginSuccess={handleLoginSuccess} 
          onBackToLanding={() => setViewMode('landing')}
        />
      );
    }
    return (
      <SpendeeLanding 
        onGoToLogin={() => setViewMode('auth')} 
        onDemoLogin={handleDemoLogin}
      />
    );
  }

  // If user is logged in but clicked to view the Spendee landing showcase:
  if (viewMode === 'landing') {
    return (
      <SpendeeLanding 
        onGoToLogin={() => setViewMode('dashboard')} 
        onDemoLogin={() => setViewMode('dashboard')}
      />
    );
  }

  const unreadAlertsCount = (alerts || []).filter(a => !a.is_read).length;

  return (
    <div className="min-h-screen bg-[#F8FAF9] text-[#283139] flex flex-col font-sans selection:bg-[#00BC7C] selection:text-white">
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed bottom-5 right-5 z-50 p-4 rounded-2xl bg-[#283139] text-white shadow-2xl border border-slate-700 text-xs font-semibold animate-in slide-in-from-bottom-3 duration-200 flex items-center space-x-2">
          <Sparkles className="h-4 w-4 text-[#00BC7C]" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        health={health}
        unreadAlertsCount={unreadAlertsCount}
        alerts={alerts}
        currentUser={currentUser}
        onLogout={handleLogout}
        onMarkAllRead={handleMarkAllRead}
        onMarkAlertRead={handleMarkAlertRead}
        onRefresh={fetchDashboardData}
        onGoToLanding={() => setViewMode('landing')}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Spendee Quick Actions Header Card */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5 bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-xs">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-[#00BC7C]/10 text-[#00BC7C] border border-[#00BC7C]/20">
                Spendee Predictive Engine
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-xs font-medium text-slate-500">ACID + Document + Scikit-Learn</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#283139] tracking-tight mt-1.5">
              Personal Finance & Predictive Budget Management
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
              PostgreSQL active triggers prevent budget breaches; Scikit-Learn forecasts daily cadence and flags spend anomalies in real time.
            </p>
          </div>

          <div className="flex items-center space-x-2.5 flex-wrap gap-y-2">
            <button
              onClick={() => setIsCsvModalOpen(true)}
              className="px-4 py-2.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-[#283139] text-xs font-bold border border-slate-200 transition-all flex items-center space-x-1.5 shadow-xs cursor-pointer"
            >
              <Upload className="h-3.5 w-3.5 text-[#00BC7C]" />
              <span>Import CSV</span>
            </button>
            <button
              onClick={() => setIsTransferModalOpen(true)}
              className="px-4 py-2.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-[#283139] text-xs font-bold border border-slate-200 transition-all flex items-center space-x-1.5 shadow-xs cursor-pointer"
            >
              <ArrowRightLeft className="h-3.5 w-3.5 text-[#40C3F9]" />
              <span>ACID Transfer</span>
            </button>
            <button
              onClick={() => setIsTxModalOpen(true)}
              className="px-5 py-2.5 rounded-full bg-[#00BC7C] hover:bg-[#0ea573] text-white text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center space-x-1.5 cursor-pointer transform active:scale-95"
            >
              <Plus className="h-4 w-4" />
              <span>Add Transaction</span>
            </button>
          </div>
        </div>

        {/* 1. Metric Cards */}
        <MetricCards
          netWorth={analytics?.net_worth || 0}
          monthlySpent={analytics?.current_month_expense || 0}
          monthlyBudget={analytics?.predictive_burn_rate?.total_budget_limit || 1600}
          burnRateData={analytics?.predictive_burn_rate}
          unreadAlertsCount={unreadAlertsCount}
          onOpenTxModal={() => setIsTxModalOpen(true)}
          onOpenTransferModal={() => setIsTransferModalOpen(true)}
        />

        {/* 2. Connected Accounts Grid */}
        <AccountsGrid
          accounts={accounts}
          onOpenTransferModal={() => setIsTransferModalOpen(true)}
        />

        {/* 3. Spending Breakdown & Trend Visualizations */}
        <SpendingCharts
          categoryData={analytics?.category_spend_breakdown || []}
          monthlyTrends={analytics?.monthly_trends || []}
          burnRateData={analytics?.predictive_burn_rate}
        />

        {/* 4. AI Day-by-Day Spending Prediction Graph */}
        <DailyForecastChart
          forecastData={analytics?.daily_forecast}
        />

        {/* 5. Live Alert Stream from MongoDB */}
        <AlertsStream
          alerts={alerts}
          onMarkRead={handleMarkAlertRead}
          onMarkAllRead={handleMarkAllRead}
        />

        {/* 6. PostgreSQL Transactions Ledger */}
        <TransactionsTable
          transactions={transactions}
          categories={budgets.map(b => ({ category_id: b.category_id, category_name: b.category_name }))}
          onOpenTxModal={() => setIsTxModalOpen(true)}
        />
      </main>

      {/* Footer System Architecture Info */}
      <footer className="border-t border-slate-200/80 py-6 bg-white text-center text-xs text-slate-500 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="font-medium text-slate-600">Spendee AI • Personal Finance & Predictive Management Platform</span>
          <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
            <span className="text-[#00BC7C] font-semibold">PostgreSQL (3NF + B-Tree + Triggers)</span>
            <span>•</span>
            <span className="text-[#40C3F9] font-semibold">MongoDB Atlas</span>
            <span>•</span>
            <span className="text-[#8B5CF6] font-semibold">FastAPI & Scikit-Learn</span>
          </div>
        </div>
      </footer>

      {/* Modals with user-isolated scope */}
      <TransactionModal
        isOpen={isTxModalOpen}
        onClose={() => setIsTxModalOpen(false)}
        accounts={accounts}
        categories={budgets.map(b => ({ category_id: b.category_id, category_name: b.category_name }))}
        userId={currentUser.user_id}
        onTransactionSuccess={() => {
          fetchDashboardData();
          showToast('Transaction inserted and analyzed successfully!');
        }}
      />

      <TransferModal
        isOpen={isTransferModalOpen}
        onClose={() => setIsTransferModalOpen(false)}
        accounts={accounts}
        userId={currentUser.user_id}
        onTransferSuccess={() => {
          fetchDashboardData();
          showToast('ACID atomic transfer committed successfully!');
        }}
      />

      <CsvImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        accounts={accounts}
        userId={currentUser.user_id}
        onImportSuccess={() => {
          fetchDashboardData();
          showToast('CSV statement imported and committed successfully!');
        }}
      />
    </div>
  );
}
