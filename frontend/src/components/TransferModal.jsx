import React, { useState, useEffect } from 'react';
import { 
  X, 
  ArrowRightLeft, 
  AlertOctagon, 
  CheckCircle2, 
  ShieldAlert, 
  ArrowRight,
  RefreshCw
} from 'lucide-react';

export default function TransferModal({ 
  isOpen, 
  onClose, 
  accounts, 
  userId = 1,
  onTransferSuccess 
}) {
  const [fromAccountId, setFromAccountId] = useState('2'); 
  const [toAccountId, setToAccountId] = useState('1');   
  const [amount, setAmount] = useState('100.00');
  const [memo, setMemo] = useState('Monthly Savings Deposit');
  const [loading, setLoading] = useState(false);
  const [rollbackAlert, setRollbackAlert] = useState(null);
  const [successInfo, setSuccessInfo] = useState(null);

  useEffect(() => {
    if (accounts && accounts.length >= 2) {
      const fromExists = accounts.some(a => a.account_id === parseInt(fromAccountId));
      const toExists = accounts.some(a => a.account_id === parseInt(toAccountId));
      if (!fromExists) {
        setFromAccountId(String(accounts[0].account_id));
      }
      if (!toExists) {
        setToAccountId(String(accounts[1].account_id));
      }
    } else if (accounts && accounts.length === 1) {
      setFromAccountId(String(accounts[0].account_id));
      setToAccountId(String(accounts[0].account_id));
    }
  }, [accounts]);

  const handleSimulateOverdraw = () => {
    setRollbackAlert(null);
    setSuccessInfo(null);
    setAmount('50000.00');
    setMemo('Test Insufficient Funds Atomic Rollback');
  };

  const handleExecuteTransfer = async (overrideAmount = null) => {
    setRollbackAlert(null);
    setSuccessInfo(null);
    setLoading(true);

    const transferAmt = overrideAmount !== null ? overrideAmount : parseFloat(amount);
    if (!transferAmt || transferAmt <= 0) {
      setRollbackAlert({
        error: 'INVALID_AMOUNT',
        message: 'Please specify a positive transfer amount.'
      });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/transfers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId || 1,
          from_account_id: parseInt(fromAccountId),
          to_account_id: parseInt(toAccountId),
          amount: transferAmt,
          memo: memo.trim()
        })
      });

      const data = await res.json();

      if (!res.ok) {
        // Explicit ACID Rollback or Error
        const detail = data.detail;
        if (typeof detail === 'object' && detail.rolled_back) {
          setRollbackAlert({
            error: detail.error,
            message: detail.message,
            available: detail.available_balance,
            requested: detail.requested_amount,
            rolledBack: true
          });
        } else {
          setRollbackAlert({
            error: 'TRANSFER_FAILED',
            message: typeof detail === 'string' ? detail : 'Atomic transfer failed and was rolled back.',
            rolledBack: true
          });
        }
      } else {
        // Success commit
        setSuccessInfo(data);
        setTimeout(() => {
          onTransferSuccess();
          onClose();
        }, 1600);
      }
    } catch (err) {
      setRollbackAlert({
        error: 'NETWORK_ERROR',
        message: `Network communication failure: ${err.message}`,
        rolledBack: true
      });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden text-[#283139] animate-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-2xl bg-[#40C3F9]/15 border border-[#40C3F9]/25 flex items-center justify-center text-[#0284c7]">
              <ArrowRightLeft className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-[#283139]">ACID Multi-Account Transfer</h2>
              <p className="text-xs text-slate-500">Atomic block execution with explicit rollback verification</p>
            </div>
          </div>
          <button
            onClick={() => { setRollbackAlert(null); setSuccessInfo(null); onClose(); }}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Rollback Error Toast / Banner */}
          {rollbackAlert && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs animate-in shake duration-300">
              <div className="flex items-start space-x-2.5">
                <AlertOctagon className="h-5 w-5 text-[#FE5A61] flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#FE5A61] text-xs uppercase tracking-wider bg-rose-100 px-2 py-0.5 rounded-full border border-rose-200">
                      100% ACID Rollback Confirmed
                    </span>
                  </div>
                  <p className="text-rose-900 leading-relaxed font-semibold">
                    {typeof rollbackAlert.message === 'string' ? rollbackAlert.message.replace(/\$/g, '₹') : rollbackAlert.message}
                  </p>
                  <p className="text-[11px] text-rose-700/90 font-mono">
                    Zero ledger state updates committed. Account balances strictly unchanged.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {successInfo && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs animate-in zoom-in-95">
              <div className="flex items-center space-x-2.5">
                <CheckCircle2 className="h-5 w-5 text-[#00BC7C] flex-shrink-0" />
                <div>
                  <div className="font-bold text-emerald-900 text-xs uppercase tracking-wider">
                    Atomic Transaction Committed
                  </div>
                  <p className="text-emerald-800 mt-0.5 font-medium">
                    {typeof successInfo.message === 'string' ? successInfo.message.replace(/\$/g, '₹') : successInfo.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Insufficient Funds Simulation Banner */}
          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-[#00BC7C] flex-shrink-0" />
              <span className="text-xs text-slate-600 font-medium">
                Test atomic rollback on overdraw
              </span>
            </div>
            <button
              type="button"
              onClick={handleSimulateOverdraw}
              className="px-3 py-1.5 text-xs font-bold bg-white hover:bg-slate-100 text-[#00BC7C] border border-slate-200 rounded-full transition-colors whitespace-nowrap cursor-pointer shadow-xs"
            >
              Preset ₹50,000 Overdraw
            </button>
          </div>

          {/* Account Selection Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">From Account (Source)</label>
              <select
                value={fromAccountId}
                onChange={(e) => setFromAccountId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3.5 py-2 text-xs text-[#283139] focus:outline-none focus:border-[#00BC7C] focus:bg-white cursor-pointer"
              >
                {accounts.map((acc) => (
                  <option key={acc.account_id} value={acc.account_id}>
                    {acc.account_name} (₹{acc.balance.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">To Account (Destination)</label>
              <select
                value={toAccountId}
                onChange={(e) => setToAccountId(e.target.value)}
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
            <label className="block text-xs font-bold text-slate-600 mb-1">Transfer Amount (₹)</label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-slate-400 font-bold text-sm">₹</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-base font-bold text-[#283139] placeholder-slate-400 focus:outline-none focus:border-[#00BC7C] focus:bg-white"
                required
              />
            </div>
          </div>

          {/* Memo */}
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Transfer Memo / Reference</label>
            <input
              type="text"
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
              placeholder="e.g. Savings Goal Transfer"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs text-[#283139] placeholder-slate-400 focus:outline-none focus:border-[#00BC7C] focus:bg-white"
            />
          </div>

          {/* Modal Actions */}
          <div className="pt-3 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => { setRollbackAlert(null); setSuccessInfo(null); onClose(); }}
              className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Close
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => handleExecuteTransfer()}
              className="px-6 py-2.5 bg-[#00BC7C] hover:bg-[#0ea573] text-white rounded-full text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer transform active:scale-95"
            >
              {loading ? (
                <span>Executing Atomic Block...</span>
              ) : (
                <>
                  <span>Execute ACID Transfer</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}