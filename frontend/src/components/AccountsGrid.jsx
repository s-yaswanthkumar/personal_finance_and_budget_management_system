import React from 'react';
import { CreditCard, Landmark, PiggyBank, ArrowRightLeft } from 'lucide-react';

export default function AccountsGrid({ accounts, onOpenTransferModal }) {
  const getAccountIcon = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'savings':
        return <PiggyBank className="h-5 w-5 text-[#00BC7C]" />;
      case 'checking':
        return <Landmark className="h-5 w-5 text-[#40C3F9]" />;
      case 'credit card':
        return <CreditCard className="h-5 w-5 text-[#FF6FAF]" />;
      default:
        return <Landmark className="h-5 w-5 text-[#8B5CF6]" />;
    }
  };

  const getBadgeColor = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'savings':
        return 'bg-[#00BC7C]/10 text-[#00BC7C] border-[#00BC7C]/20';
      case 'checking':
        return 'bg-[#40C3F9]/10 text-[#0284c7] border-[#40C3F9]/20';
      case 'credit card':
        return 'bg-[#FF6FAF]/10 text-[#db2777] border-[#FF6FAF]/20';
      default:
        return 'bg-purple-50 text-purple-600 border-purple-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-extrabold text-[#283139] uppercase tracking-wider">
            Connected Accounts <span className="text-xs text-slate-500 lowercase font-normal">(PostgreSQL ACID Tables)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Real-time balances protected with row-level transaction locks</p>
        </div>
        <button
          onClick={onOpenTransferModal}
          className="px-4 py-2 bg-slate-50 hover:bg-slate-100 text-[#00BC7C] hover:text-[#0ea573] border border-slate-200 rounded-full text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer shadow-xs"
        >
          <ArrowRightLeft className="h-3.5 w-3.5" />
          <span>Transfer Funds</span>
        </button>
      </div>

      <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {accounts.map((acc) => (
          <div
            key={acc.account_id}
            className="p-5 rounded-2xl bg-slate-50/70 border border-slate-200/80 hover:border-[#00BC7C]/40 hover:bg-white transition-all flex flex-col justify-between shadow-xs"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                {getAccountIcon(acc.account_type)}
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getBadgeColor(acc.account_type)}`}>
                {acc.account_type}
              </span>
            </div>

            <div className="mt-4">
              <h4 className="text-xs font-bold text-slate-600 truncate">
                {acc.account_name}
              </h4>
              <p className="text-xl font-black text-[#283139] mt-0.5">
                ₹{acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}