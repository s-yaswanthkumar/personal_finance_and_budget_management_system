import React from 'react';
import { 
  Wallet, 
  TrendingDown, 
  TrendingUp, 
  BrainCircuit, 
  AlertTriangle, 
  Sparkles,
  ArrowUpRight,
  ShieldAlert
} from 'lucide-react';

export default function MetricCards({ 
  netWorth, 
  monthlySpent, 
  monthlyBudget, 
  burnRateData, 
  unreadAlertsCount,
  onOpenTxModal,
  onOpenTransferModal
}) {
  const budgetUtilization = monthlyBudget > 0 
    ? Math.min(100, Math.round((monthlySpent / monthlyBudget) * 100)) 
    : 0;

  const isOverBudget = monthlyBudget > 0 && monthlySpent > monthlyBudget;
  const isNearBudget = monthlyBudget > 0 && monthlySpent >= monthlyBudget * 0.8;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Net Worth Card */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Net Worth</span>
          <div className="h-10 w-10 rounded-2xl bg-[#00BC7C]/10 border border-[#00BC7C]/20 flex items-center justify-center text-[#00BC7C]">
            <Wallet className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4">
          <div className="text-2xl sm:text-3xl font-black text-[#283139] tracking-tight">
            ₹{(netWorth || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span className="text-[#00BC7C] font-semibold flex items-center">
              <TrendingUp className="h-3.5 w-3.5 mr-1" />
              ACID Real-Time Ledger
            </span>
            <button
              onClick={onOpenTransferModal}
              className="text-[#00BC7C] hover:text-[#0ea573] font-bold text-xs underline cursor-pointer"
            >
              Transfer Funds
            </button>
          </div>
        </div>
      </div>

      {/* 2. Monthly Spent vs Budget Card */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Month Spent / Budget</span>
          <div className={`h-10 w-10 rounded-2xl flex items-center justify-center border ${
            isOverBudget 
              ? 'bg-[#FE5A61]/10 border-[#FE5A61]/25 text-[#FE5A61]' 
              : isNearBudget 
              ? 'bg-[#FFC053]/15 border-[#FFC053]/30 text-[#d97706]' 
              : 'bg-[#00BC7C]/10 border-[#00BC7C]/20 text-[#00BC7C]'
          }`}>
            <TrendingDown className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4">
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-black text-[#283139] tracking-tight">
              ₹{(monthlySpent || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-slate-500 font-semibold">
              / ₹{(monthlyBudget || 0).toLocaleString('en-IN', { minimumFractionDigits: 0 })}
            </span>
          </div>

          {/* Progress bar */}
          <div className="mt-3.5 w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                isOverBudget 
                  ? 'bg-[#FE5A61]' 
                  : isNearBudget 
                  ? 'bg-[#FFC053]' 
                  : 'bg-[#00BC7C]'
              }`}
              style={{ width: `${Math.min(100, budgetUtilization)}%` }}
            ></div>
          </div>
          <div className="mt-2 flex justify-between text-[11px] font-semibold text-slate-500">
            <span>{budgetUtilization}% utilized</span>
            <span>Trigger Cap: 100%</span>
          </div>
        </div>
      </div>

      {/* 3. AI 30-Day Projected Spend Card */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-[#8B5CF6] uppercase tracking-wider flex items-center">
            <BrainCircuit className="h-3.5 w-3.5 mr-1 text-[#8B5CF6]" />
            AI 30-Day Forecast
          </span>
          <div className="h-10 w-10 rounded-2xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center text-[#8B5CF6]">
            <Sparkles className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4">
          <div className="text-2xl sm:text-3xl font-black text-[#283139] tracking-tight">
            ₹{(burnRateData?.projected_30_day_spend || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-3 flex flex-col space-y-1 text-xs">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-medium">Daily Burn:</span>
              <span className="font-mono text-[#00BC7C] font-bold">
                ₹{burnRateData?.daily_burn_rate || 0}/day
              </span>
            </div>
            <div className="truncate text-[11px] text-slate-400 font-medium" title={burnRateData?.estimation_method}>
              {burnRateData?.is_cold_start ? 'Empirical Bayes (Cold Start)' : 'Historical Moving Avg'}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Active Alerts & Quick Action Card */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Unresolved Alerts</span>
          <div className={`h-10 w-10 rounded-2xl flex items-center justify-center border ${
            unreadAlertsCount > 0 
              ? 'bg-[#FFC053]/15 border-[#FFC053]/30 text-[#d97706]' 
              : 'bg-[#00BC7C]/10 border-[#00BC7C]/20 text-[#00BC7C]'
          }`}>
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4">
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-black text-[#283139] tracking-tight">
              {unreadAlertsCount}
            </span>
            <span className="text-xs text-slate-500 font-semibold">MongoDB documents</span>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center space-x-2">
            <button
              onClick={onOpenTxModal}
              className="flex-1 py-2 px-3.5 bg-[#00BC7C] hover:bg-[#0ea573] text-white rounded-full text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center justify-center space-x-1 cursor-pointer transform active:scale-95"
            >
              <span>+ Log Transaction</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}