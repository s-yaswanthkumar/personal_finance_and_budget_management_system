import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Sparkles, 
  AlertOctagon, 
  AlertTriangle, 
  CheckCircle2, 
  Cpu, 
  ArrowRight
} from 'lucide-react';

export default function TransactionModal({ 
  isOpen, 
  onClose, 
  accounts, 
  categories, 
  userId = 1,
  onTransactionSuccess 
}) {
  const [amount, setAmount] = useState('');
  const [accountId, setAccountId] = useState('');
  const [transactionType, setTransactionType] = useState('expense');
  const [rawMemo, setRawMemo] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  
  // AI Dynamic Prediction State
  const [predictedCat, setPredictedCat] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successInfo, setSuccessInfo] = useState(null);

  const debounceTimer = useRef(null);

  useEffect(() => {
    if (accounts && accounts.length > 0 && !accountId) {
      setAccountId(accounts[0].account_id);
    }
  }, [accounts, accountId]);

  // Debounced NLP category prediction as user types memo
  useEffect(() => {
    if (!rawMemo || rawMemo.trim().length < 3) {
      setPredictedCat(null);
      return;
    }

    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(async () => {
      setIsPredicting(true);
      try {
        const res = await fetch('/api/ml/predict-category', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ memo: rawMemo.trim() })
        });
        if (res.ok) {
          const data = await res.json();
          setPredictedCat(data);
          // If user hasn't explicitly chosen a category, auto-select predicted
          if (!selectedCategoryId && data.category_id) {
            setSelectedCategoryId(data.category_id);
          }
        }
      } catch (err) {
        console.error('NLP Prediction Error:', err);
      } finally {
        setIsPredicting(false);
      }
    }, 280);

    return () => clearTimeout(debounceTimer.current);
  }, [rawMemo]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessInfo(null);
    setLoading(true);

    const numAmount = parseFloat(amount);
    if (!numAmount || numAmount <= 0) {
      setErrorMsg('Please enter a valid amount greater than 0.');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId || 1,
          account_id: parseInt(accountId),
          amount: numAmount,
          transaction_type: transactionType,
          raw_memo: rawMemo.trim(),
          category_id: selectedCategoryId ? parseInt(selectedCategoryId) : null
        })
      });

      const data = await res.json();

      if (!res.ok) {
        // Active Trigger Hard Cap Breach abort or database error
        const detail = data.detail || 'Transaction failed.';
        setErrorMsg(detail);
      } else {
        // Success
        setSuccessInfo(data);
        setTimeout(() => {
          onTransactionSuccess();
          handleReset();
          onClose();
        }, 1400);
      }
    } catch (err) {
      setErrorMsg(`Network or server error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setAmount('');
    setRawMemo('');
    setSelectedCategoryId('');
    setPredictedCat(null);
    setErrorMsg(null);
    setSuccessInfo(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden text-[#283139] animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-2xl bg-[#00BC7C]/10 border border-[#00BC7C]/20 flex items-center justify-center text-[#00BC7C]">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-[#283139]">Log New Transaction</h2>
              <p className="text-xs text-slate-500">Real-time NLP tagging & PostgreSQL trigger evaluation</p>
            </div>
          </div>
          <button
            onClick={() => { handleReset(); onClose(); }}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error Banner (e.g. Budget Hard Cap Exception) */}
          {errorMsg && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2.5">
              <AlertOctagon className="h-4 w-4 text-[#FE5A61] flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block text-rose-900 font-bold mb-0.5">PostgreSQL Trigger Abort:</strong>
                <span>{typeof errorMsg === 'string' ? errorMsg.replace(/\$/g, '₹') : errorMsg}</span>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {successInfo && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2.5">
              <CheckCircle2 className="h-4 w-4 text-[#00BC7C] flex-shrink-0" />
              <span className="font-bold">Transaction verified and committed to PostgreSQL! Updating dashboard...</span>
            </div>
          )}

          {/* Type Toggle & Account */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Transaction Type</label>
              <div className="grid grid-cols-2 gap-1 p-1 bg-slate-50 rounded-2xl border border-slate-200">
                <button
                  type="button"
                  onClick={() => setTransactionType('expense')}
                  className={`py-1.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                    transactionType === 'expense'
                      ? 'bg-[#FE5A61] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#283139]'
                  }`}
                >
                  Expense
                </button>
                <button
                  type="button"
                  onClick={() => setTransactionType('income')}
                  className={`py-1.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                    transactionType === 'income'
                      ? 'bg-[#00BC7C] text-white shadow-xs'
                      : 'text-slate-600 hover:text-[#283139]'
                  }`}
                >
                  Income
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Account</label>
              <select
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3.5 py-2 text-xs text-[#283139] focus:outline-none focus:border-[#00BC7C] focus:bg-white cursor-pointer"
              >
                {accounts.map((acc) => (
                  <option key={acc.account_id} value={acc.account_id}>
                    {acc.account_name} (₹{acc.balance.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Amount (₹)</label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-slate-400 font-bold text-sm">₹</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-base font-bold text-[#283139] placeholder-slate-400 focus:outline-none focus:border-[#00BC7C] focus:bg-white focus:ring-2 focus:ring-[#00BC7C]/10"
                required
              />
            </div>
          </div>

          {/* Raw Memo Input with Real-Time NLP Tagging */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-600">
                Raw Memo / Merchant Description
              </label>
              {isPredicting && (
                <span className="text-[10px] text-[#00BC7C] flex items-center space-x-1 animate-pulse font-bold">
                  <Cpu className="h-3 w-3" />
                  <span>AI predicting...</span>
                </span>
              )}
            </div>
            <input
              type="text"
              placeholder="e.g. Walmart Supercenter 49.99, Starbucks Coffee, Uber Ride..."
              value={rawMemo}
              onChange={(e) => setRawMemo(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs text-[#283139] placeholder-slate-400 focus:outline-none focus:border-[#00BC7C] focus:bg-white"
              required
            />

            {/* Dynamic Auto-Predicted Category Chip */}
            {predictedCat && (
              <div className="mt-2 p-2.5 rounded-2xl bg-[#00BC7C]/10 border border-[#00BC7C]/20 flex items-center justify-between animate-in fade-in slide-in-from-top-1 duration-150">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-3.5 w-3.5 text-[#00BC7C] flex-shrink-0" />
                  <span className="text-xs text-slate-700 font-medium">
                    AI Auto-Tag: <strong className="text-[#00BC7C] font-bold">{predictedCat.predicted_category}</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-white text-[#00BC7C] border border-[#00BC7C]/20 font-bold">
                    {Math.round(predictedCat.confidence * 100)}% confidence
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedCategoryId(predictedCat.category_id)}
                  className="text-[11px] text-[#00BC7C] hover:text-[#0ea573] underline font-bold cursor-pointer"
                >
                  Apply
                </button>
              </div>
            )}
          </div>

          {/* Category Selector (Override or manual pick) */}
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">
              Category <span className="text-slate-400 font-normal">(Auto-selected by NLP, or pick manual override)</span>
            </label>
            <select
              value={selectedCategoryId}
              onChange={(e) => setSelectedCategoryId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3.5 py-2 text-xs text-[#283139] focus:outline-none focus:border-[#00BC7C] focus:bg-white cursor-pointer"
            >
              <option value="">Auto-tag with NLP pipeline</option>
              {categories.map((c) => (
                <option key={c.category_id} value={c.category_id}>
                  {c.category_name}
                </option>
              ))}
            </select>
          </div>

          {/* Trigger Alert Notice */}
          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-[11px] text-slate-500 font-medium">
            <span className="text-[#00BC7C] font-bold">Active Integrity Guard:</span> Expenses exceeding 100% monthly budget will be rejected by database triggers. Expenses pushing spend ≥80% write alert logs to MongoDB.
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => { handleReset(); onClose(); }}
              className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-[#00BC7C] hover:bg-[#0ea573] text-white rounded-full text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer transform active:scale-95"
            >
              {loading ? (
                <span>Evaluating Triggers...</span>
              ) : (
                <>
                  <span>Commit Transaction</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}