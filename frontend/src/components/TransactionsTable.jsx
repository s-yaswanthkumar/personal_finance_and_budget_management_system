import React, { useState } from 'react';
import { 
  ArrowDownLeft, 
  ArrowUpRight, 
  Search, 
  Tag, 
  Calendar,
  Layers,
  Plus
} from 'lucide-react';

export default function TransactionsTable({ 
  transactions, 
  categories, 
  onOpenTxModal 
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const filtered = (transactions || []).filter((tx) => {
    const matchesSearch = tx.raw_memo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          tx.category_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tx.category_name.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  const getCategoryColor = (name) => {
    switch ((name || '').toLowerCase()) {
      case 'groceries':
        return 'bg-[#00BC7C]/10 text-[#00BC7C] border-[#00BC7C]/20';
      case 'dining':
        return 'bg-[#FFC053]/20 text-[#d97706] border-[#FFC053]/30';
      case 'utilities':
        return 'bg-[#40C3F9]/10 text-[#0284c7] border-[#40C3F9]/20';
      case 'entertainment':
        return 'bg-[#FF6FAF]/10 text-[#db2777] border-[#FF6FAF]/20';
      case 'transport':
        return 'bg-[#40C3F9]/10 text-[#0284c7] border-[#40C3F9]/20';
      case 'salary':
        return 'bg-[#00BC7C]/10 text-[#00BC7C] border-[#00BC7C]/20';
      case 'transfer':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs text-[#283139]">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-extrabold text-[#283139] uppercase tracking-wider">
            Transaction Ledger <span className="text-xs text-slate-400 lowercase font-normal">(PostgreSQL Indexed Table)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Optimized B-Tree query on (user_id, transaction_date)</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search Box */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search memo or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-full text-xs text-[#283139] placeholder-slate-400 focus:outline-none focus:border-[#00BC7C] focus:bg-white w-48 sm:w-60 shadow-xs"
            />
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-full text-xs text-slate-700 focus:outline-none focus:border-[#00BC7C] focus:bg-white shadow-xs cursor-pointer"
          >
            <option value="all">All Categories</option>
            {categories.map((c) => (
              <option key={c.category_id} value={c.category_name}>
                {c.category_name}
              </option>
            ))}
          </select>

          <button
            onClick={onOpenTxModal}
            className="px-4 py-2 bg-[#00BC7C] hover:bg-[#0ea573] text-white rounded-full text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center space-x-1 cursor-pointer transform active:scale-95"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Tx</span>
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider text-[10px] font-bold">
              <th className="pb-3.5 font-bold">Type</th>
              <th className="pb-3.5 font-bold">Merchant / Raw Memo</th>
              <th className="pb-3.5 font-bold">Category (NLP)</th>
              <th className="pb-3.5 font-bold">Account</th>
              <th className="pb-3.5 font-bold">Date</th>
              <th className="pb-3.5 font-bold text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.length > 0 ? (
              filtered.map((tx) => {
                const isIncome = tx.transaction_type === 'income';
                return (
                  <tr key={tx.transaction_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5">
                      <div className="flex items-center">
                        <span className={`p-1.5 rounded-full mr-2.5 ${
                          isIncome 
                            ? 'bg-[#00BC7C]/15 text-[#00BC7C]' 
                            : 'bg-[#FE5A61]/15 text-[#FE5A61]'
                        }`}>
                          {isIncome ? <ArrowDownLeft className="h-3.5 w-3.5" /> : <ArrowUpRight className="h-3.5 w-3.5" />}
                        </span>
                        <span className={`capitalize font-bold text-[11px] ${
                          isIncome ? 'text-[#00BC7C]' : 'text-slate-600'
                        }`}>
                          {tx.transaction_type}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 font-bold text-[#283139]">
                      {tx.raw_memo}
                    </td>
                    <td className="py-3.5">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getCategoryColor(tx.category_name)}`}>
                        <Tag className="h-2.5 w-2.5" />
                        <span>{tx.category_name}</span>
                      </span>
                    </td>
                    <td className="py-3.5 text-slate-500 font-mono text-[11px]">
                      {tx.account_name}
                    </td>
                    <td className="py-3.5 text-slate-400 text-[11px]">
                      {new Date(tx.transaction_date).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </td>
                    <td className={`py-3.5 text-right font-mono font-black text-xs ${
                      isIncome ? 'text-[#00BC7C]' : 'text-[#283139]'
                    }`}>
                      {isIncome ? '+' : '-'}₹{tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                  No matching transactions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}