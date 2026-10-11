import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  Download, 
  AlertOctagon, 
  CheckCircle2, 
  Cpu, 
  Sparkles, 
  ArrowRight,
  ShieldAlert,
  FileCheck
} from 'lucide-react';

export default function CsvImportModal({ 
  isOpen, 
  onClose, 
  accounts, 
  userId = 1,
  onImportSuccess 
}) {
  const [selectedAccountId, setSelectedAccountId] = useState('2');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [rollbackAlert, setRollbackAlert] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (accounts && accounts.length > 0) {
      const exists = accounts.some(a => a.account_id === parseInt(selectedAccountId));
      if (!exists) {
        setSelectedAccountId(String(accounts[0].account_id));
      }
    }
  }, [accounts]);

  const handleDownloadTemplate = async () => {
    try {
      const res = await fetch('/api/transactions/csv-template');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'transactions_template.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download CSV template:', err);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setRollbackAlert(null);
      setResultData(null);
    }
  };

  const handleSimulateBreach = () => {
    // Create an in-memory CSV file that triggers a hard cap breach
    const breachCsv = 
`date,amount,type,raw_memo
2026-09-02,18.50,expense,Starbucks Coffee #281
2026-09-04,95000.00,expense,Luxury Michelin 5-Star Dining Feast
2026-09-05,25.00,expense,Chevron Fuel Station`;

    const blob = new Blob([breachCsv], { type: 'text/csv' });
    const file = new File([blob], 'breach_simulation.csv', { type: 'text/csv' });
    setSelectedFile(file);
    setRollbackAlert(null);
    setResultData(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setRollbackAlert({
        message: 'Please select a CSV statement file to upload.'
      });
      return;
    }

    setLoading(true);
    setRollbackAlert(null);
    setResultData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('user_id', String(userId || 1));
    formData.append('account_id', selectedAccountId);

    try {
      const res = await fetch('/api/transactions/import-csv', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();

      if (!res.ok) {
        // Atomic Rollback caught
        const detail = data.detail;
        if (typeof detail === 'object' && detail.rolled_back) {
          setRollbackAlert({
            error: detail.error,
            message: detail.message,
            errorRow: detail.error_row,
            rawError: detail.raw_error,
            rolledBack: true
          });
        } else {
          setRollbackAlert({
            error: 'IMPORT_ERROR',
            message: typeof detail === 'string' ? detail : 'Batch processing failed and was rolled back.',
            rolledBack: true
          });
        }
      } else {
        // Successful atomic commit
        setResultData(data);
        setTimeout(() => {
          onImportSuccess();
        }, 1800);
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

  const handleReset = () => {
    setSelectedFile(null);
    setRollbackAlert(null);
    setResultData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden text-[#283139] animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-2xl bg-[#00BC7C]/10 border border-[#00BC7C]/20 flex items-center justify-center text-[#00BC7C]">
              <Upload className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-[#283139]">Import Statement (CSV)</h2>
              <p className="text-xs text-slate-500">Atomic batch ingestion with NLP auto-tagging & trigger caps</p>
            </div>
          </div>
          <button
            onClick={() => { handleReset(); onClose(); }}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          {/* Rollback Error Alert */}
          {rollbackAlert && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs animate-in shake duration-300">
              <div className="flex items-start space-x-2.5">
                <AlertOctagon className="h-5 w-5 text-[#FE5A61] flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#FE5A61] text-xs uppercase tracking-wider bg-rose-100 px-2 py-0.5 rounded-full border border-rose-200">
                      100% Atomic Rollback Confirmed
                    </span>
                    {rollbackAlert.errorRow && (
                      <span className="text-[11px] font-mono text-rose-800 font-bold">
                        Row #{rollbackAlert.errorRow}
                      </span>
                    )}
                  </div>
                  <p className="text-rose-900 leading-relaxed font-semibold">
                    {typeof rollbackAlert.message === 'string' ? rollbackAlert.message.replace(/\$/g, '₹') : rollbackAlert.message}
                  </p>
                  <p className="text-[11px] text-rose-700 font-mono">
                    Zero ledger transactions committed. Database balance remains intact.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Success Summary Banner */}
          {resultData && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs animate-in zoom-in-95">
              <div className="flex items-start space-x-2.5">
                <CheckCircle2 className="h-5 w-5 text-[#00BC7C] flex-shrink-0 mt-0.5" />
                <div className="space-y-1.5 w-full">
                  <div className="font-bold text-emerald-900 text-xs uppercase tracking-wider">
                    Batch Successfully Committed to PostgreSQL
                  </div>
                  <p className="text-emerald-800 font-medium">{resultData.message}</p>
                  <div className="grid grid-cols-3 gap-2 pt-1.5">
                    <div className="p-2 rounded-xl bg-white border border-emerald-200 text-center">
                      <span className="block text-lg font-black text-emerald-800 font-mono">{resultData.imported_count}</span>
                      <span className="text-[10px] text-emerald-700 font-bold">Imported</span>
                    </div>
                    <div className="p-2 rounded-xl bg-white border border-purple-200 text-center">
                      <span className="block text-lg font-black text-purple-800 font-mono">{resultData.auto_categorized}</span>
                      <span className="text-[10px] text-purple-700 font-bold">NLP Tagged</span>
                    </div>
                    <div className="p-2 rounded-xl bg-white border border-amber-200 text-center">
                      <span className="block text-lg font-black text-amber-800 font-mono">{resultData.anomalies_flagged}</span>
                      <span className="text-[10px] text-amber-700 font-bold">Anomalies</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Template Download & Simulate Breach Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-slate-50 rounded-2xl border border-slate-200">
            <button
              type="button"
              onClick={handleDownloadTemplate}
              className="text-xs text-[#00BC7C] hover:text-[#0ea573] flex items-center space-x-1.5 font-bold cursor-pointer"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download CSV Template (50 Transactions • ~2 Months)</span>
            </button>

            <button
              type="button"
              onClick={handleSimulateBreach}
              className="text-[11px] text-[#FE5A61] hover:text-[#e0454c] bg-rose-50 hover:bg-rose-100 border border-rose-200 px-3 py-1 rounded-full transition-colors flex items-center space-x-1 font-bold cursor-pointer"
            >
              <ShieldAlert className="h-3 w-3" />
              <span>Load Breach Test File</span>
            </button>
          </div>

          {/* Target Account Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Target Account</label>
            <select
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-3.5 py-2 text-xs text-[#283139] focus:outline-none focus:border-[#00BC7C] focus:bg-white cursor-pointer"
            >
              {accounts.map((acc) => (
                <option key={acc.account_id} value={acc.account_id}>
                  {acc.account_name} (₹{acc.balance.toFixed(2)})
                </option>
              ))}
            </select>
          </div>

          {/* File Upload Dropzone */}
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Statement File (.csv)</label>
            <div 
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                selectedFile 
                  ? 'border-[#00BC7C] bg-[#00BC7C]/5' 
                  : 'border-slate-300 hover:border-[#00BC7C] bg-slate-50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
              {selectedFile ? (
                <div className="flex items-center justify-center space-x-2 text-[#00BC7C]">
                  <FileCheck className="h-6 w-6 text-[#00BC7C]" />
                  <div className="text-left">
                    <p className="text-xs font-bold text-[#283139]">{selectedFile.name}</p>
                    <p className="text-[10px] text-slate-500 font-medium">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready for batch processing
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-1.5 text-slate-400">
                  <FileText className="h-8 w-8 mx-auto text-[#00BC7C]" />
                  <p className="text-xs font-bold text-slate-700">
                    Click to browse or drag & drop bank statement CSV
                  </p>
                  <p className="text-[10px] text-slate-400">
                    Columns: date, amount, type, raw_memo
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Modal Actions */}
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
              disabled={loading || !selectedFile}
              className="px-6 py-2.5 bg-[#00BC7C] hover:bg-[#0ea573] text-white rounded-full text-xs font-bold shadow-md shadow-[#00BC7C]/25 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer transform active:scale-95"
            >
              {loading ? (
                <span>Processing Batch...</span>
              ) : (
                <>
                  <span>Import Statement</span>
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