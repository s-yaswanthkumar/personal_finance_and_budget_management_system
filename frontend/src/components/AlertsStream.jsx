import React, { useState } from 'react';
import { 
  AlertOctagon, 
  AlertTriangle, 
  Cpu, 
  CheckCircle2, 
  Clock, 
  Filter,
  Check,
  Sparkles,
  Calendar
} from 'lucide-react';

export default function AlertsStream({ 
  alerts, 
  onMarkRead, 
  onMarkAllRead 
}) {
  const [filter, setFilter] = useState('all');

  const filteredAlerts = (alerts || []).filter((a) => {
    if (filter === 'all') return true;
    if (filter === 'predicted') return a.type === 'predictive_overspend' || a.category === 'Predicted Overspend';
    return a.severity === filter;
  });

  const getSeverityBadge = (severity, type) => {
    if (type === 'predictive_overspend') {
      return {
        bg: 'bg-[#8B5CF6]/15 text-[#8B5CF6] border-[#8B5CF6]/25',
        icon: <Sparkles className="h-3.5 w-3.5 text-[#8B5CF6]" />,
        label: 'Predicted Overspend'
      };
    }

    switch (severity) {
      case 'breach':
        return {
          bg: 'bg-[#FE5A61]/15 text-[#FE5A61] border-[#FE5A61]/25',
          icon: <AlertOctagon className="h-3.5 w-3.5 text-[#FE5A61]" />,
          label: 'Hard Cap Breach'
        };
      case 'warning':
        return {
          bg: 'bg-[#FFC053]/20 text-[#d97706] border-[#FFC053]/30',
          icon: <AlertTriangle className="h-3.5 w-3.5 text-[#d97706]" />,
          label: 'Budget Warning'
        };
      case 'anomaly':
        return {
          bg: 'bg-[#8B5CF6]/15 text-[#8B5CF6] border-[#8B5CF6]/25',
          icon: <Cpu className="h-3.5 w-3.5 text-[#8B5CF6]" />,
          label: 'Isolation Forest Anomaly'
        };
      default:
        return {
          bg: 'bg-[#00BC7C]/15 text-[#00BC7C] border-[#00BC7C]/25',
          icon: <CheckCircle2 className="h-3.5 w-3.5 text-[#00BC7C]" />,
          label: severity
        };
    }
  };

  return (
    <div id="live-alerts-stream" className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs text-[#283139]">
      {/* Header & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <div className="h-3 w-3 rounded-full bg-[#00BC7C] animate-pulse"></div>
          <h3 className="text-sm font-extrabold text-[#283139] uppercase tracking-wider">
            Live Alert & Notification Stream <span className="text-xs text-slate-400 lowercase font-normal">(MongoDB Document Store)</span>
          </h3>
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-y-2">
          {/* Filter Pills */}
          <div className="flex items-center p-1 bg-slate-50 rounded-full border border-slate-200 text-xs">
            {[
              { id: 'all', label: 'All' },
              { id: 'predicted', label: 'Predicted (AI)' },
              { id: 'warning', label: 'Warnings' },
              { id: 'anomaly', label: 'Anomalies' },
              { id: 'breach', label: 'Breaches' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  filter === tab.id
                    ? 'bg-[#00BC7C] text-white shadow-xs'
                    : 'text-slate-600 hover:text-[#283139]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={onMarkAllRead}
            className="px-3.5 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-bold text-slate-700 transition-colors flex items-center space-x-1 cursor-pointer shadow-xs"
            title="Mark all as read"
          >
            <Check className="h-3.5 w-3.5 text-[#00BC7C]" />
            <span className="hidden sm:inline">Mark All Read</span>
          </button>
        </div>
      </div>

      {/* Alert Feed */}
      <div className="mt-4 space-y-3 max-h-[380px] overflow-y-auto pr-1">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => {
            const badge = getSeverityBadge(alert.severity, alert.type);
            const isRead = alert.is_read;
            const isPredicted = alert.type === 'predictive_overspend';

            return (
              <div
                key={alert._id}
                className={`p-4 rounded-2xl border transition-all ${
                  isRead 
                    ? 'bg-slate-50/40 border-slate-200/50 opacity-60' 
                    : isPredicted
                      ? 'bg-slate-50/90 border-[#8B5CF6]/30 shadow-xs'
                      : 'bg-slate-50/70 border-slate-200/80 shadow-xs hover:bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                        {badge.icon}
                        <span>{badge.label}</span>
                      </span>

                      {/* Target Date Pill for Predictive Alerts */}
                      {isPredicted && alert.metadata?.predicted_date && (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#FE5A61]/10 text-[#FE5A61] border border-[#FE5A61]/20">
                          <Calendar className="h-2.5 w-2.5 mr-0.5" />
                          <span>Target: {alert.metadata.day_name || ''} {alert.metadata.display_date || alert.metadata.predicted_date}</span>
                        </span>
                      )}

                      <span className="text-xs font-bold text-slate-700">
                        {alert.category}
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-[11px] text-slate-400 flex items-center font-mono">
                        <Clock className="h-3 w-3 mr-1" />
                        {new Date(alert.timestamp).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed font-normal">
                      {typeof alert.message === 'string' ? alert.message.replace(/\$/g, '₹') : alert.message}
                    </p>

                    {/* Metadata details for predictive overspend */}
                    {isPredicted && alert.metadata && (
                      <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                        <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 font-mono">
                          Projected: <strong className="text-[#00BC7C]">₹{Number(alert.metadata.predicted_amount || 0).toFixed(2)}</strong>
                        </span>
                        {alert.metadata.multiplier && (
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-mono font-semibold">
                            {alert.metadata.multiplier}x standard burn rate
                          </span>
                        )}
                        {alert.metadata.likely_categories && alert.metadata.likely_categories.length > 0 && (
                          <div className="flex items-center space-x-1 text-slate-500">
                            <span>Likely:</span>
                            {alert.metadata.likely_categories.map((c, i) => (
                              <span key={i} className="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700 font-medium">
                                {c}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {!isRead && (
                    <button
                      onClick={() => onMarkRead(alert._id)}
                      className="text-xs text-[#00BC7C] hover:text-[#0ea573] p-1.5 rounded-full hover:bg-slate-200/60 transition-colors flex-shrink-0 cursor-pointer"
                      title="Mark as read"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-8 text-center text-slate-400 text-xs">
            No alert logs found for filter '{filter}'.
          </div>
        )}
      </div>
    </div>
  );
}